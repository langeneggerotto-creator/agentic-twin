#!/usr/bin/env python3
"""
APEX Lyric-Scene Correlation Pipeline v0.1

Correlates a music video's lyrics (from its official/auto caption track,
with timestamps) against its visual craft elements (from an existing
av_craft_pipeline.py report, which has evidence_timestamp ranges),
producing a record of what the song says at each visual moment and how
the two relate thematically -- e.g. does the visual literalize the lyric,
contrast with it, or use metaphor/symbolism?

Truth boundary: reads only the public caption track (no video/audio
download) for lyrics; reuses an already-produced av_craft_pipeline.py
report for scene data (no re-download, no re-analysis of frames). The
correlation commentary itself is LLM-inferred interpretation, not
verified fact -- see each entry's confidence framing in the report.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from . import pipeline
except ImportError:  # allow loading/running this module standalone
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pipeline  # type: ignore

_TIMESTAMP_RANGE_RE = re.compile(r"([\d.]+)s-([\d.]+)s")


def parse_timestamp_range(range_str: str) -> Optional[Tuple[float, float]]:
    """Parse an av_craft_pipeline.py evidence_timestamp string like '36.0s-66.0s'
    into (36.0, 66.0). Returns None if it doesn't match that shape."""
    match = _TIMESTAMP_RANGE_RE.match(str(range_str or "").strip())
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def lyrics_in_range(segments: List[Dict[str, Any]], start: float, end: float) -> str:
    """Join transcript segment text whose start time falls within [start, end)."""
    lines = []
    for seg in segments:
        seg_start = seg.get("start", 0.0)
        if start <= seg_start < end:
            text = str(seg.get("text", "")).replace("\n", " ").strip()
            if text:
                lines.append(text)
    return " ".join(lines)


CORRELATION_SYSTEM_PROMPT = (
    "You analyze the relationship between a song's lyrics at a specific moment and the "
    "visual scene happening at that same moment in its music video. Given a lyric "
    "snippet and a description of the visual scene, describe in 1-2 sentences how they "
    "relate thematically or emotionally -- e.g. does the visual literalize the lyric, "
    "contrast with it, foreshadow a later line, or use metaphor/symbolism? If there is no "
    "meaningful connection (the lyric is background vocals/instrumental filler with no "
    "clear thematic tie to the visual), say so plainly rather than inventing one. Respond "
    "as a JSON object: {\"correlation\": \"...\", \"has_meaningful_connection\": true|false}."
)


class CorrelationLLMClient:
    """Thin OpenAI wrapper for correlation commentary. Imported lazily so this module
    loads fine without the SDK/key present."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        self.model = model
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self._api_key:
                raise RuntimeError("OPENAI_API_KEY is not set.")
            from openai import OpenAI
            self._client = OpenAI(api_key=self._api_key)
        return self._client

    def correlate(self, lyric_text: str, scene_name: str, scene_description: str) -> Dict[str, Any]:
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            temperature=0.4,
            messages=[
                {"role": "system", "content": CORRELATION_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(
                    {"lyric": lyric_text, "scene_name": scene_name, "scene_description": scene_description},
                    ensure_ascii=False,
                )},
            ],
        )
        return json.loads(response.choices[0].message.content)


def build_report(video_id: str, url: str, craft_report: Dict[str, Any], llm: CorrelationLLMClient) -> Dict[str, Any]:
    transcript = pipeline.fetch_transcript(video_id)
    correlations: List[Dict[str, Any]] = []
    llm_errors: List[str] = []
    risk_flags = [
        "correlation_is_llm_inferred_not_verified",
        "lyric_timing_depends_on_caption_accuracy",
    ]
    skipped_no_timestamp = 0
    skipped_no_lyrics = 0

    if transcript.status == "ok":
        for element in craft_report.get("craft_elements", []):
            time_range = parse_timestamp_range(element.get("evidence_timestamp", ""))
            if not time_range:
                skipped_no_timestamp += 1
                continue
            lyric_text = lyrics_in_range(transcript.segments, *time_range)
            if not lyric_text:
                skipped_no_lyrics += 1
                continue
            try:
                result = llm.correlate(lyric_text, element.get("name", ""), element.get("description", ""))
            except Exception as exc:  # noqa: BLE001 - one failed correlation shouldn't sink the whole report
                if len(llm_errors) < 3:
                    llm_errors.append(f"{type(exc).__name__}: {exc}")
                continue
            correlations.append({
                "evidence_timestamp": element.get("evidence_timestamp"),
                "lyric_text": lyric_text,
                "scene_name": element.get("name"),
                "scene_category": element.get("category"),
                "scene_domains": element.get("domains", []),
                "correlation": result.get("correlation", ""),
                "has_meaningful_connection": bool(result.get("has_meaningful_connection")),
            })
        if llm_errors:
            risk_flags.append("llm_correlation_error")
    else:
        risk_flags.append("no_transcript_available")

    meaningful_count = sum(1 for c in correlations if c["has_meaningful_connection"])

    report: Dict[str, Any] = {
        "artifact_type": "apex_lyric_scene_correlation_report_v01",
        "source_type": "lyric_scene_correlation",
        "video_id": video_id,
        "source_url": url,
        "transcript_status": transcript.status,
        "transcript_error": transcript.error,
        "correlation_count": len(correlations),
        "meaningful_connection_count": meaningful_count,
        "scenes_skipped_no_timestamp": skipped_no_timestamp,
        "scenes_skipped_no_lyrics_in_range": skipped_no_lyrics,
        "correlations": correlations,
        "llm_error_samples": llm_errors,
        "risk_flags": sorted(set(risk_flags)),
        "truth_status": {
            "VERIFIED": ["lyric text and timestamps come from the video's actual caption track"] if transcript.status == "ok" else ["transcript fetch attempted"],
            "INFERRED": ["the thematic/emotional correlation commentary is LLM-generated interpretation"],
            "ASSUMED": ["caption timing accurately reflects when each lyric is sung"],
            "UNKNOWN": ["whether auto-generated captions (if used instead of official lyrics) transcribed the words correctly"],
        },
        "next_3_plus_1": {
            "next_1": "Spot-check a few correlations against the actual video before treating them as confirmed creative intent.",
            "next_2": "Lower has_meaningful_connection entries can usually be ignored -- they mark filler/instrumental moments.",
            "next_3": "Pair this with a making-of/commentary video's extracted principles (ingested with --related-to) for the strongest picture of both what was made and why.",
            "plus_1_control": "This never downloads video/audio -- only reads the public caption track and reuses an existing craft report.",
        },
    }
    payload = json.dumps(report, sort_keys=True, ensure_ascii=False, default=str)
    report["manifest_hash_sha256"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return report


def analyze(url: str, craft_report_path: str, llm: Optional[CorrelationLLMClient] = None) -> Dict[str, Any]:
    llm = llm or CorrelationLLMClient()
    video_id = pipeline.parse_video_id(url)
    if not video_id:
        return {
            "artifact_type": "apex_lyric_scene_correlation_report_v01",
            "source_type": "lyric_scene_correlation",
            "source_url": url,
            "error": "Could not parse a YouTube video ID from this URL.",
            "correlation_count": 0,
            "correlations": [],
            "risk_flags": ["invalid_url"],
        }
    craft_report = json.loads(Path(craft_report_path).read_text(encoding="utf-8"))
    craft_video_id = (craft_report.get("video") or {}).get("video_id")
    if craft_video_id and craft_video_id != video_id:
        return {
            "artifact_type": "apex_lyric_scene_correlation_report_v01",
            "source_type": "lyric_scene_correlation",
            "source_url": url,
            "error": f"Craft report is for video {craft_video_id}, not {video_id} -- pass the matching --craft-report.",
            "correlation_count": 0,
            "correlations": [],
            "risk_flags": ["mismatched_craft_report"],
        }
    return build_report(video_id, url, craft_report, llm)
