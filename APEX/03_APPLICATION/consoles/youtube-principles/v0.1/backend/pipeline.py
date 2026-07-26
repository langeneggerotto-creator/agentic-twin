#!/usr/bin/env python3
"""
APEX YouTube Principles Extraction Pipeline v0.1

Ingests one or more YouTube URLs, fetches only the public oEmbed metadata
and the official caption/transcript track, then uses an LLM to extract
every core law, principle, theory, framework, mental model, and heuristic
taught or referenced in the video.

Truth boundary: this module never downloads video or audio files and
never bypasses platform login, paywalls, or terms of service. It reads
only two public endpoints: YouTube's oEmbed metadata endpoint and the
official caption track YouTube already serves for the video.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Protocol

import requests

try:
    from youtube_transcript_api import (
        NoTranscriptFound,
        TranscriptsDisabled,
        VideoUnavailable,
        YouTubeTranscriptApi,
    )
except ImportError:  # pragma: no cover - exercised only when dependency is missing
    YouTubeTranscriptApi = None
    NoTranscriptFound = TranscriptsDisabled = VideoUnavailable = Exception

PREFERRED_TRANSCRIPT_LANGUAGES = ("en", "en-US", "en-GB")

OEMBED_URL = "https://www.youtube.com/oembed"
PRINCIPLE_CATEGORIES = [
    "law", "principle", "theory", "framework",
    "mental_model", "heuristic", "rule_of_thumb", "key_quote",
    "creative_rationale",
]

# Controlled vocabulary for topic tagging. Kept intentionally broad and mirrored in the
# youtube-principles-kb repo's schema/domains.json so extraction labels line up with how
# the knowledge base is organized for cross-project querying.
DOMAIN_TAGS = [
    "productivity-time-management",
    "business-strategy",
    "marketing-sales",
    "leadership-management",
    "psychology-behavior",
    "decision-making-cognition",
    "learning-education",
    "creativity-innovation",
    "finance-investing",
    "health-fitness",
    "relationships-communication",
    "habits-self-discipline",
    "career-work",
    "systems-thinking",
    "negotiation-influence",
    "writing-content-creation",
    "technology-ai",
    "philosophy-ethics",
    "science-research",
    "personal-growth-mindset",
]

CHUNK_CHAR_LIMIT = 3500


# --------------------------------------------------------------------------
# URL / ID parsing
# --------------------------------------------------------------------------

_VIDEO_ID_PATTERNS = [
    re.compile(r"(?:v=|/shorts/|/embed/|/v/)([A-Za-z0-9_-]{6,})"),
    re.compile(r"youtu\.be/([A-Za-z0-9_-]{6,})"),
]


def parse_video_id(url: str) -> Optional[str]:
    """Extract a YouTube video ID from common URL shapes, or None."""
    url = url.strip()
    if not url:
        return None
    for pattern in _VIDEO_ID_PATTERNS:
        match = pattern.search(url)
        if match:
            return match.group(1).split("?")[0].split("&")[0]
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url
    return None


def split_urls(raw: str) -> List[str]:
    """Split a textarea blob of pasted URLs (newline and/or comma separated)."""
    return [part for part in re.split(r"[\s,]+", raw.strip()) if part]


# --------------------------------------------------------------------------
# Metadata + transcript ingestion (public endpoints only)
# --------------------------------------------------------------------------

@dataclass
class VideoMeta:
    video_id: str
    url: str
    title: str = "Unknown title"
    channel: str = "Unknown channel"
    thumbnail_url: str = ""


def fetch_video_meta(video_id: str, url: str, timeout: float = 8.0) -> VideoMeta:
    """Fetch public oEmbed metadata. Falls back to placeholders on failure."""
    meta = VideoMeta(video_id=video_id, url=url)
    try:
        resp = requests.get(
            OEMBED_URL,
            params={"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"},
            timeout=timeout,
        )
        if resp.ok:
            data = resp.json()
            meta.title = data.get("title", meta.title)
            meta.channel = data.get("author_name", meta.channel)
            meta.thumbnail_url = data.get("thumbnail_url", "")
    except requests.RequestException:
        pass
    return meta


@dataclass
class TranscriptResult:
    status: str  # "ok" | "disabled" | "unavailable" | "error"
    segments: List[Dict[str, Any]] = field(default_factory=list)
    error: str = ""


def fetch_transcript(video_id: str) -> TranscriptResult:
    """Fetch the official transcript, preferring English but falling back to
    whatever language is actually available (this is a 'full analysis on any
    video' pipeline, not an English-only one)."""
    if YouTubeTranscriptApi is None:
        return TranscriptResult(status="error", error="youtube_transcript_api is not installed.")
    try:
        transcript_list = YouTubeTranscriptApi().list(video_id)
        try:
            transcript = transcript_list.find_transcript(PREFERRED_TRANSCRIPT_LANGUAGES)
        except NoTranscriptFound:
            transcript = next(iter(transcript_list))
        segments = transcript.fetch().to_raw_data()
        return TranscriptResult(status="ok", segments=segments)
    except TranscriptsDisabled:
        return TranscriptResult(status="disabled", error="Captions are disabled for this video.")
    except NoTranscriptFound:
        return TranscriptResult(status="unavailable", error="No transcript is available for this video.")
    except VideoUnavailable:
        return TranscriptResult(status="unavailable", error="Video is unavailable or private.")
    except Exception as exc:  # noqa: BLE001 - surface any transcript failure as a graceful report field
        return TranscriptResult(status="error", error=str(exc))


# --------------------------------------------------------------------------
# Transcript chunking
# --------------------------------------------------------------------------

@dataclass
class TranscriptChunk:
    index: int
    text: str
    start_seconds: float
    end_seconds: float


def format_timestamp(seconds: float) -> str:
    seconds = int(seconds)
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"


def chunk_transcript(segments: List[Dict[str, Any]], char_limit: int = CHUNK_CHAR_LIMIT) -> List[TranscriptChunk]:
    chunks: List[TranscriptChunk] = []
    buf_text: List[str] = []
    buf_len = 0
    start = segments[0]["start"] if segments else 0.0
    end = start
    for seg in segments:
        text = seg.get("text", "").replace("\n", " ").strip()
        if not text:
            continue
        if buf_len + len(text) + 1 > char_limit and buf_text:
            chunks.append(TranscriptChunk(len(chunks), " ".join(buf_text), start, end))
            buf_text, buf_len = [], 0
            start = seg["start"]
        buf_text.append(text)
        buf_len += len(text) + 1
        end = seg["start"] + seg.get("duration", 0.0)
    if buf_text:
        chunks.append(TranscriptChunk(len(chunks), " ".join(buf_text), start, end))
    return chunks


def verify_quote(quote: str, chunk_text: str) -> bool:
    """Check a returned quote actually appears in the source chunk (or very nearly does)."""
    if not quote:
        return False

    def norm(s: str) -> str:
        return re.sub(r"\s+", " ", s.lower()).strip()

    q, c = norm(quote), norm(chunk_text)
    if q in c:
        return True
    q_words = set(q.split())
    if not q_words:
        return False
    overlap = len(q_words & set(c.split())) / len(q_words)
    return overlap >= 0.8


def normalize_domain_tag(tag: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(tag).lower()).strip("-")


def normalize_domains(domains: Any) -> List[str]:
    """Kebab-case and dedupe domain tags. Accepts tags outside DOMAIN_TAGS too (the LLM
    is instructed to only use the fixed list, but this stays permissive rather than
    silently dropping a real signal if it drifts)."""
    if not isinstance(domains, list):
        return []
    cleaned: List[str] = []
    for tag in domains:
        norm = normalize_domain_tag(tag)
        if norm and norm not in cleaned:
            cleaned.append(norm)
    return cleaned


def normalize_aliases(aliases: Any) -> List[str]:
    if not isinstance(aliases, list):
        return []
    cleaned: List[str] = []
    for alias in aliases:
        text = str(alias).strip()
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned


def merge_candidates(all_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Dedupe principle candidates across chunks by normalized name. Prefers a verified
    quote as the representative record, but unions domains/aliases across every duplicate
    so labeling stays as complete as possible even if only one chunk tagged it well."""
    seen: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    for item in all_items:
        key = re.sub(r"[^a-z0-9]+", " ", str(item.get("name", "")).lower()).strip()
        if not key:
            continue
        if key not in seen:
            seen[key] = item
            order.append(key)
            continue
        existing = seen[key]
        merged_domains = sorted(set(existing.get("domains", [])) | set(item.get("domains", [])))
        merged_aliases = sorted(set(existing.get("aliases", [])) | set(item.get("aliases", [])))
        if item.get("quote_verified") and not existing.get("quote_verified"):
            item["domains"], item["aliases"] = merged_domains, merged_aliases
            seen[key] = item
        else:
            existing["domains"], existing["aliases"] = merged_domains, merged_aliases
    return [seen[k] for k in order]


# --------------------------------------------------------------------------
# LLM extraction
# --------------------------------------------------------------------------

class LLMClient(Protocol):
    def extract_principles(self, chunk_text: str, video_title: str) -> List[Dict[str, Any]]: ...
    def summarize(self, text: str, video_title: str) -> str: ...


EXTRACTION_SYSTEM_PROMPT = (
    "You study video transcripts and extract every durable, reusable idea taught, "
    "referenced, or reasoned through -- across two different registers of speech, both "
    "equally valuable: (1) FORMAL knowledge: named laws (e.g. Parkinson's Law), "
    "principles, theories, frameworks, mental models, heuristics, and rules of thumb, "
    "explicitly named or clearly implied; (2) CONVERSATIONAL reasoning: the informal, "
    "off-the-cuff explanations people give for a specific choice they made -- 'we wanted "
    "it to feel like...', 'the reason we did this was...', 'this represents...', 'I chose "
    "X because Y'. This second kind is just as important to capture as the first, even "
    "though it is never phrased as a formal principle -- it is often the most valuable "
    "content in a commentary, interview, or making-of video, and a narrow reading of "
    "'principle' will silently miss it. Do not require an idea to be generalizable or "
    "reusable across contexts to count -- a specific creative rationale ('the staircase "
    "represents her rising above the story') is worth capturing on its own terms, not "
    "only when it can be restated as universal advice. Ignore only genuine filler: small "
    "talk with no substance, sponsor reads, and pure repetition. For each item return a "
    "JSON object with: "
    "name (the canonical, most widely recognized name for it, or a short descriptive "
    "label you invent if it has no established name), "
    "aliases (array of other names or phrasings it is commonly known by, or [] if none), "
    "category (one of law, principle, theory, framework, mental_model, heuristic, "
    "rule_of_thumb, key_quote, creative_rationale -- use creative_rationale for the "
    "conversational-reasoning register described above whenever it doesn't fit an "
    "established formal category), "
    "domains (array of 1-3 tags chosen ONLY from this fixed list, picking the closest fit "
    "even if imperfect -- never invent a new tag: " + ", ".join(DOMAIN_TAGS) + "), "
    "description (1-2 sentences, in your own words), "
    "application (how to use it, or -- for creative_rationale -- what it reveals about "
    "the maker's intent, 1 sentence), "
    "quote (a short snippet copied exactly, verbatim, from the transcript segment below "
    "that supports this item, or an empty string if none fits cleanly). Only use text "
    "that actually appears in the provided segment for the quote field -- never invent a "
    "quote. Respond with a JSON object of the shape {\"items\": [...]}. If nothing "
    "qualifies in this segment, return {\"items\": []}."
)

SUMMARY_SYSTEM_PROMPT = (
    "Summarize the following YouTube video transcript in 3-5 sentences: what it is about, "
    "who it is for, and what the viewer walks away knowing how to do."
)


class OpenAIClient:
    """Thin wrapper around the OpenAI Chat Completions API. Imports the SDK lazily so this
    module loads fine without the package installed or an API key set."""

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

    def extract_principles(self, chunk_text: str, video_title: str) -> List[Dict[str, Any]]:
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            temperature=0.2,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Video title: {video_title}\n\nTranscript segment:\n{chunk_text}"},
            ],
        )
        payload = json.loads(response.choices[0].message.content)
        return payload.get("items", [])

    def summarize(self, text: str, video_title: str) -> str:
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            temperature=0.3,
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": f"Video title: {video_title}\n\nTranscript:\n{text[:12000]}"},
            ],
        )
        return response.choices[0].message.content.strip()


# --------------------------------------------------------------------------
# Report assembly
# --------------------------------------------------------------------------

def qa_gates(transcript_status: str, principles: List[Dict[str, Any]]) -> Dict[str, Any]:
    issues: List[str] = []
    passes: List[str] = []
    if transcript_status == "ok":
        passes.append("transcript_fetched")
    else:
        issues.append(f"transcript_{transcript_status}")
    if principles:
        passes.append("principles_extracted")
    else:
        issues.append("no_principles_extracted")
    unverified = [p for p in principles if not p.get("quote_verified")]
    if unverified:
        issues.append(f"{len(unverified)}_unverified_quotes_review")
    score = max(0, min(100, 100 - 15 * len(issues) + 5 * len(passes)))
    return {
        "score": score,
        "passes": passes,
        "issues": issues,
        "release_status": "HOLD_FOR_REVIEW" if issues else "PROTOTYPE_OK",
    }


def build_report(url: str, video: VideoMeta, transcript: TranscriptResult, llm: LLMClient) -> Dict[str, Any]:
    principles: List[Dict[str, Any]] = []
    summary = ""
    risk_flags = [
        "quotes_are_excerpts_verify_before_republishing",
        "verify_named_laws_against_primary_source",
    ]

    llm_errors: List[str] = []
    failed_chunk_count = 0

    if transcript.status == "ok":
        chunks = chunk_transcript(transcript.segments)
        full_text = " ".join(c.text for c in chunks)
        all_items: List[Dict[str, Any]] = []
        for chunk in chunks:
            try:
                items = llm.extract_principles(chunk.text, video.title)
            except Exception as exc:  # noqa: BLE001 - one failed chunk should not sink the whole report
                failed_chunk_count += 1
                if len(llm_errors) < 3:
                    llm_errors.append(f"chunk {chunk.index}: {type(exc).__name__}: {exc}")
                continue
            for item in items:
                item["quote_verified"] = verify_quote(item.get("quote", ""), chunk.text)
                item["approx_timestamp"] = format_timestamp(chunk.start_seconds)
                item["source_chunk_index"] = chunk.index
                if item.get("category") not in PRINCIPLE_CATEGORIES:
                    item["category"] = "principle"
                item["domains"] = normalize_domains(item.get("domains"))
                item["aliases"] = normalize_aliases(item.get("aliases"))
                all_items.append(item)
        if failed_chunk_count:
            risk_flags.append("llm_extraction_error")
        principles = merge_candidates(all_items)
        try:
            summary = llm.summarize(full_text, video.title)
        except Exception as exc:  # noqa: BLE001
            summary = "Summary unavailable (LLM call failed)."
            risk_flags.append("llm_summary_error")
            llm_errors.append(f"summary: {type(exc).__name__}: {exc}")
    else:
        risk_flags.append("no_transcript_available")

    report: Dict[str, Any] = {
        "artifact_type": "apex_youtube_principles_report_v01",
        "source_type": "youtube_video",
        "video": asdict(video),
        "source_url": url,
        "transcript_status": transcript.status,
        "transcript_error": transcript.error,
        "summary": summary,
        "principles": principles,
        "principle_count": len(principles),
        "llm_failed_chunk_count": failed_chunk_count,
        "llm_error_samples": llm_errors,
        "risk_flags": sorted(set(risk_flags)),
        "qa_gates": qa_gates(transcript.status, principles),
        "truth_status": {
            "VERIFIED": [
                "video ID parsed from submitted URL",
                "metadata fetched from public oEmbed endpoint" if video.title != "Unknown title" else "metadata fetch attempted",
            ],
            "INFERRED": ["principle categorization, domain tags, aliases, phrasing, and summary produced by an LLM"],
            "ASSUMED": ["transcript accurately represents spoken audio (auto-captions may contain errors)"],
            "UNKNOWN": ["whether extracted quotes are precisely verbatim beyond the automated substring check"],
        },
        "next_3_plus_1": {
            "next_1": "Read the flagged unverified quotes against the original video before quoting publicly.",
            "next_2": "Cross-check named laws/theories against a primary source before treating them as fact.",
            "next_3": "Re-run with a stronger model if a video's principles feel thin or generic.",
            "plus_1_control": "This pipeline never downloads video/audio and never bypasses caption/API permissions.",
        },
    }
    payload = json.dumps(report, sort_keys=True, ensure_ascii=False, default=str)
    report["manifest_hash_sha256"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return report


def analyze_url(url: str, llm: Optional[LLMClient] = None) -> Dict[str, Any]:
    llm = llm or OpenAIClient()
    video_id = parse_video_id(url)
    if not video_id:
        return {
            "artifact_type": "apex_youtube_principles_report_v01",
            "source_url": url,
            "error": "Could not parse a YouTube video ID from this URL.",
            "transcript_status": "error",
            "principles": [],
            "principle_count": 0,
            "risk_flags": ["invalid_url"],
        }
    video = fetch_video_meta(video_id, url)
    transcript = fetch_transcript(video_id)
    return build_report(url, video, transcript, llm)


def analyze_urls(urls: List[str], llm: Optional[LLMClient] = None) -> List[Dict[str, Any]]:
    llm = llm or OpenAIClient()
    return [analyze_url(u, llm) for u in urls]
