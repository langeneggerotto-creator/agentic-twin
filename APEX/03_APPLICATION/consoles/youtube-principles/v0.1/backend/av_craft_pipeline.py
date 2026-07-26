#!/usr/bin/env python3
"""
APEX Audiovisual Craft Analysis Pipeline v0.1

Extracts cinematography, editing, color grading, lighting, set/costume
design, visual effects, choreography, narrative devices, and sound/music
production craft from a video (music videos especially, but general
enough for any video) -- things that are impossible to see from a
caption/transcript alone.

Truth boundary (DIFFERENT from pipeline.py / article_pipeline.py): this
module DOES temporarily download the video via yt-dlp, strictly for local
frame and audio-signal analysis. The downloaded video/audio/frame files
are deleted immediately after processing (see the `finally` block in
analyze_url) and are never uploaded, stored persistently, redistributed,
or included in the output report. This is a deliberate, narrower
exception to the "never downloads video/audio" rule used elsewhere in
this project, made because cinematography/tempo/color-grading etc. are
genuinely not observable from text. You are responsible for ensuring your
use complies with the source platform's terms of service and applicable
law for your jurisdiction -- this is built for personal, transient,
non-commercial analysis, not redistribution.

Two kinds of output, kept clearly separate:
  - audio_analysis: MEASURED via real signal processing (librosa) --
    tempo/BPM, duration, beat count, energy. Not an LLM guess.
  - craft_elements: INFERRED by a vision-capable LLM looking at sampled
    frames -- qualitative, and only as good as what's visible in the
    frames actually sampled.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from . import pipeline
except ImportError:  # allow loading/running this module standalone
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pipeline  # type: ignore

CRAFT_CATEGORIES = [
    "cinematography", "editing", "color_grading", "lighting", "set_design",
    "costume_design", "visual_effects", "choreography", "narrative_device",
    "sound_design", "music_production",
]

CRAFT_DOMAIN_TAGS = [
    "music-video-production", "cinematography", "color-grading", "lighting-design",
    "costume-design", "set-design", "visual-effects", "choreography",
    "editing-technique", "narrative-structure", "sound-design", "performance",
]

DEFAULT_FRAME_INTERVAL_SECONDS = 6
DEFAULT_MAX_FRAMES = 40
FRAME_BATCH_SIZE = 6


def check_dependencies() -> List[str]:
    """Return a list of missing dependency names, empty if everything needed is present."""
    missing = []
    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        missing.append("yt-dlp (pip install yt-dlp)")
    try:
        import librosa  # noqa: F401
    except ImportError:
        missing.append("librosa (pip install librosa)")
    if shutil.which("ffmpeg") is None:
        missing.append("ffmpeg (install via your OS package manager, must be on PATH)")
    if shutil.which("ffprobe") is None:
        missing.append("ffprobe (ships with ffmpeg)")
    return missing


# --------------------------------------------------------------------------
# Media acquisition (temporary; deleted after analysis -- see analyze_url)
# --------------------------------------------------------------------------

def download_media(url: str, workdir: Path) -> Path:
    """Download the video at moderate quality into workdir. Caller is responsible
    for deleting it after analysis."""
    import yt_dlp

    outtmpl = str(workdir / "media.%(ext)s")
    ydl_opts = {
        "format": "best[height<=480]/best",
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
    return Path(filename)


def probe_duration_seconds(video_path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def extract_frames(
    video_path: Path, workdir: Path,
    interval_seconds: int = DEFAULT_FRAME_INTERVAL_SECONDS,
    max_frames: int = DEFAULT_MAX_FRAMES,
) -> List[Tuple[float, Path]]:
    """Sample frames at a fixed interval via ffmpeg. Returns (timestamp_seconds, path) pairs."""
    frames_dir = workdir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(video_path),
            "-vf", f"fps=1/{interval_seconds}",
            "-frames:v", str(max_frames),
            str(frames_dir / "frame_%04d.jpg"),
        ],
        capture_output=True, check=True,
    )
    frame_paths = sorted(frames_dir.glob("frame_*.jpg"))
    return [(i * float(interval_seconds), path) for i, path in enumerate(frame_paths)]


def extract_audio(video_path: Path, workdir: Path) -> Path:
    audio_path = workdir / "audio.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video_path), "-vn", "-acodec", "pcm_s16le",
         "-ar", "22050", "-ac", "1", str(audio_path)],
        capture_output=True, check=True,
    )
    return audio_path


def cleanup_workdir(workdir: Path) -> None:
    shutil.rmtree(workdir, ignore_errors=True)


# --------------------------------------------------------------------------
# Audio analysis (measured, not LLM-inferred)
# --------------------------------------------------------------------------

@dataclass
class AudioAnalysis:
    status: str  # "ok" | "error"
    error: str = ""
    duration_seconds: float = 0.0
    tempo_bpm: float = 0.0
    beat_count: int = 0
    avg_rms_energy: float = 0.0


def analyze_audio(audio_path: Path) -> AudioAnalysis:
    try:
        import librosa
        import numpy as np

        y, sr = librosa.load(str(audio_path), sr=22050, mono=True)
        duration = float(librosa.get_duration(y=y, sr=sr))
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        tempo = float(tempo) if not hasattr(tempo, "item") else float(tempo.item())
        rms = float(np.mean(librosa.feature.rms(y=y)))
        return AudioAnalysis(
            status="ok",
            duration_seconds=round(duration, 1),
            tempo_bpm=round(tempo, 1),
            beat_count=int(len(beats)),
            avg_rms_energy=round(rms, 4),
        )
    except Exception as exc:  # noqa: BLE001
        return AudioAnalysis(status="error", error=f"{type(exc).__name__}: {exc}")


# --------------------------------------------------------------------------
# Vision-LLM frame analysis (inferred, qualitative)
# --------------------------------------------------------------------------

CRAFT_EXTRACTION_SYSTEM_PROMPT = (
    "You are a film/music-video craft analyst. You are shown several still frames "
    "sampled from a video, each labeled with its approximate timestamp. Identify "
    "concrete craft techniques actually visible in these frames -- cinematography "
    "(shot type, framing, camera angle, apparent camera movement inferred across "
    "consecutive frames), editing/transitions (only if inferable from consecutive "
    "frames), color grading (palette, contrast, saturation style), lighting (style, "
    "mood, direction), set design, costume design, visual effects, choreography/"
    "staging, and narrative devices. Only describe what is actually visible -- never "
    "invent details, camera brands, locations, or people's identities you cannot see. "
    "For each item return a JSON object with: name (short label for the technique), "
    "category (one of cinematography, editing, color_grading, lighting, set_design, "
    "costume_design, visual_effects, choreography, narrative_device), domains (1-3 tags "
    "from this fixed list, closest fit even if imperfect: " + ", ".join(CRAFT_DOMAIN_TAGS) +
    "), description (1-2 sentences of what you observe), application (why this choice "
    "works or what effect it creates, 1 sentence), evidence (what specifically in the "
    "frame(s) supports this, 1 sentence). Respond with a JSON object: {\"items\": [...]}. "
    "If nothing concrete stands out in this batch, return {\"items\": []}."
)

SUMMARY_SYSTEM_PROMPT = (
    "Summarize the overall visual and musical style of this video in 3-5 sentences, "
    "based on the craft observations and audio measurements provided."
)


def _encode_frame(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


class AVCraftOpenAIClient:
    """Vision-capable OpenAI client for frame analysis. Imported lazily so this module
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

    def analyze_frame_batch(self, frames: List[Tuple[float, Path]], video_title: str) -> List[Dict[str, Any]]:
        client = self._get_client()
        content: List[Dict[str, Any]] = [
            {"type": "text", "text": f"Video title: {video_title}\n\nFrames follow, each labeled with its timestamp."}
        ]
        for timestamp, path in frames:
            content.append({"type": "text", "text": f"Timestamp: {timestamp:.1f}s"})
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{_encode_frame(path)}", "detail": "low"},
            })
        response = client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            temperature=0.3,
            messages=[
                {"role": "system", "content": CRAFT_EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
        )
        payload = json.loads(response.choices[0].message.content)
        return payload.get("items", [])

    def summarize(self, craft_elements: List[Dict[str, Any]], audio: "AudioAnalysis", video_title: str) -> str:
        client = self._get_client()
        context = {
            "video_title": video_title,
            "audio_measurements": asdict(audio),
            "craft_elements": [{"name": e["name"], "category": e["category"], "description": e["description"]} for e in craft_elements],
        }
        response = client.chat.completions.create(
            model=self.model,
            temperature=0.4,
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
            ],
        )
        return response.choices[0].message.content.strip()


# --------------------------------------------------------------------------
# Report assembly
# --------------------------------------------------------------------------

def qa_gates(media_status: str, audio: "AudioAnalysis", craft_elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    issues: List[str] = []
    passes: List[str] = []
    if media_status == "ok":
        passes.append("media_downloaded_and_processed")
    else:
        issues.append(f"media_{media_status}")
    if audio.status == "ok":
        passes.append("audio_measured")
    else:
        issues.append("audio_analysis_failed")
    if craft_elements:
        passes.append("craft_elements_extracted")
    else:
        issues.append("no_craft_elements_extracted")
    score = max(0, min(100, 100 - 15 * len(issues) + 5 * len(passes)))
    return {
        "score": score,
        "passes": passes,
        "issues": issues,
        "release_status": "HOLD_FOR_REVIEW" if issues else "PROTOTYPE_OK",
    }


def build_report(
    url: str,
    video: "pipeline.VideoMeta",
    media_status: str,
    media_error: str,
    audio: AudioAnalysis,
    frame_count: int,
    all_items: List[Dict[str, Any]],
    llm: AVCraftOpenAIClient,
) -> Dict[str, Any]:
    for item in all_items:
        item["domains"] = pipeline.normalize_domains(item.get("domains"))
        if item.get("category") not in CRAFT_CATEGORIES:
            item["category"] = "cinematography"
    craft_elements = pipeline.merge_candidates(all_items)

    summary = ""
    risk_flags = [
        "vision_analysis_is_qualitative_not_ground_truth",
        "only_sampled_frames_analyzed_not_full_video",
        "source_media_deleted_after_local_analysis_never_stored",
    ]
    if media_status != "ok":
        risk_flags.append("media_download_or_processing_failed")
    if audio.status != "ok":
        risk_flags.append("audio_analysis_failed")

    if craft_elements or audio.status == "ok":
        try:
            summary = llm.summarize(craft_elements, audio, video.title)
        except Exception as exc:  # noqa: BLE001
            summary = "Summary unavailable (LLM call failed)."
            risk_flags.append(f"llm_summary_error: {type(exc).__name__}")

    report: Dict[str, Any] = {
        "artifact_type": "apex_av_craft_report_v01",
        "source_type": "music_video_craft",
        "video": asdict(video),
        "source_url": url,
        "media_status": media_status,
        "media_error": media_error,
        "frame_count_analyzed": frame_count,
        "audio_analysis": asdict(audio),
        "summary": summary,
        "craft_elements": craft_elements,
        "craft_element_count": len(craft_elements),
        "risk_flags": sorted(set(risk_flags)),
        "qa_gates": qa_gates(media_status, audio, craft_elements),
        "truth_status": {
            "VERIFIED": [
                "tempo_bpm, duration_seconds, beat_count, avg_rms_energy are measured via real audio signal analysis (librosa), not LLM guesses"
                if audio.status == "ok" else "audio measurement attempted",
            ],
            "INFERRED": [
                "craft_elements (cinematography/editing/color grading/etc.) are a vision LLM's qualitative reading of sampled still frames",
                "overall style summary produced by an LLM",
            ],
            "ASSUMED": ["sampled frames are representative of the video's overall visual style"],
            "UNKNOWN": ["craft choices occurring only between sampled frames (missed by the sampling interval)"],
        },
        "next_3_plus_1": {
            "next_1": "Watch the actual video to confirm/expand on flagged craft elements -- this is a starting read, not a full shot-by-shot breakdown.",
            "next_2": "Reduce --frame-interval for a music video with fast cuts, since a coarse interval can miss rapid editing/transitions.",
            "next_3": "Cross-check tempo_bpm against the track's actual BPM if precision matters (algorithmic beat tracking is not infallible).",
            "plus_1_control": "The downloaded video/audio/frames are deleted immediately after this report is produced; nothing is retained or redistributed.",
        },
    }
    payload = json.dumps(report, sort_keys=True, ensure_ascii=False, default=str)
    report["manifest_hash_sha256"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return report


def analyze_url(
    url: str,
    llm: Optional[AVCraftOpenAIClient] = None,
    frame_interval: int = DEFAULT_FRAME_INTERVAL_SECONDS,
    max_frames: int = DEFAULT_MAX_FRAMES,
) -> Dict[str, Any]:
    llm = llm or AVCraftOpenAIClient()
    video_id = pipeline.parse_video_id(url)
    if not video_id:
        return {
            "artifact_type": "apex_av_craft_report_v01",
            "source_type": "music_video_craft",
            "source_url": url,
            "error": "Could not parse a YouTube video ID from this URL.",
            "media_status": "error",
            "craft_elements": [],
            "craft_element_count": 0,
            "risk_flags": ["invalid_url"],
        }

    missing = check_dependencies()
    if missing:
        return {
            "artifact_type": "apex_av_craft_report_v01",
            "source_type": "music_video_craft",
            "source_url": url,
            "error": "Missing dependencies: " + "; ".join(missing),
            "media_status": "error",
            "craft_elements": [],
            "craft_element_count": 0,
            "risk_flags": ["missing_dependencies"],
        }

    video = pipeline.fetch_video_meta(video_id, url)
    workdir = Path(tempfile.mkdtemp(prefix="av_craft_"))
    media_status, media_error = "ok", ""
    audio = AudioAnalysis(status="error", error="not attempted")
    all_items: List[Dict[str, Any]] = []
    frame_count = 0

    try:
        try:
            video_path = download_media(url, workdir)
        except Exception as exc:  # noqa: BLE001
            media_status, media_error = "download_failed", f"{type(exc).__name__}: {exc}"
            return build_report(url, video, media_status, media_error, audio, 0, all_items, llm)

        frames = extract_frames(video_path, workdir, interval_seconds=frame_interval, max_frames=max_frames)
        frame_count = len(frames)

        audio_path = None
        try:
            audio_path = extract_audio(video_path, workdir)
            audio = analyze_audio(audio_path)
        except Exception as exc:  # noqa: BLE001
            audio = AudioAnalysis(status="error", error=f"{type(exc).__name__}: {exc}")

        for i in range(0, len(frames), FRAME_BATCH_SIZE):
            batch = frames[i:i + FRAME_BATCH_SIZE]
            try:
                items = llm.analyze_frame_batch(batch, video.title)
            except Exception:  # noqa: BLE001
                continue
            for item in items:
                item["evidence_timestamp"] = f"{batch[0][0]:.1f}s-{batch[-1][0]:.1f}s"
                all_items.append(item)

        return build_report(url, video, media_status, media_error, audio, frame_count, all_items, llm)
    finally:
        cleanup_workdir(workdir)
