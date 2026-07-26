#!/usr/bin/env python3
"""
APEX Audiovisual Craft Analysis CLI v0.1

Extracts cinematography, editing, color grading, lighting, costume/set
design, visual effects, choreography, narrative devices, and measured
audio features (tempo/BPM, energy) from a video -- built for music
videos, general enough for any video.

    python3 av_craft_cli.py "https://youtu.be/VIDEO_ID"
    python3 av_craft_cli.py "https://youtu.be/VIDEO_ID" --frame-interval 4 --max-frames 60
    python3 av_craft_cli.py "https://youtu.be/VIDEO_ID" --out-dir reports/

Requires OPENAI_API_KEY (for the vision analysis), plus yt-dlp, ffmpeg,
and librosa installed locally -- see the console README's Truth Boundary
section for what this tool does differently from cli.py (it temporarily
downloads video/audio for local analysis, then deletes it).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

try:
    from . import av_craft_pipeline
except ImportError:  # allow running directly as `python3 av_craft_cli.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import av_craft_pipeline  # type: ignore


def format_report_text(report: dict) -> str:
    if report.get("error"):
        return f"✗ {report.get('source_url')}\n  ERROR: {report['error']}"

    video = report.get("video", {})
    qa = report.get("qa_gates", {})
    audio = report.get("audio_analysis", {})
    lines = [
        "=" * 70,
        f"{video.get('title', 'Untitled')}  ({video.get('channel', 'Unknown channel')})",
        str(report.get("source_url", "")),
        f"media: {report.get('media_status')} | frames analyzed: {report.get('frame_count_analyzed', 0)} | "
        f"QA score: {qa.get('score', '?')} ({qa.get('release_status', '?')})",
    ]
    if report.get("media_error"):
        lines.append(f"  note: {report['media_error']}")

    if audio.get("status") == "ok":
        lines += [
            "",
            f"Audio (measured): {audio.get('tempo_bpm')} BPM, "
            f"{audio.get('duration_seconds')}s, {audio.get('beat_count')} beats detected, "
            f"avg energy {audio.get('avg_rms_energy')}",
        ]
    elif audio.get("error"):
        lines += ["", f"Audio analysis failed: {audio['error']}"]

    if report.get("summary"):
        lines += ["", "Overall style summary:", f"  {report['summary']}"]

    craft = report.get("craft_elements", [])
    lines += ["", f"Craft elements ({len(craft)}):"]
    for i, c in enumerate(craft, 1):
        lines.append(f"  {i}. [{c.get('category', '?')}] {c.get('name', 'Untitled')}")
        if c.get("domains"):
            lines.append(f"     domains: {', '.join(c['domains'])}")
        if c.get("description"):
            lines.append(f"     {c['description']}")
        if c.get("application"):
            lines.append(f"     Effect: {c['application']}")
        if c.get("evidence"):
            lines.append(f"     Evidence ({c.get('evidence_timestamp', '?')}): {c['evidence']}")

    if report.get("risk_flags"):
        lines += ["", "Risk flags: " + ", ".join(report["risk_flags"])]
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract cinematography/editing/color-grading/sound/music craft from a video."
    )
    parser.add_argument("url", help="YouTube URL to analyze")
    parser.add_argument("--frame-interval", type=int, default=av_craft_pipeline.DEFAULT_FRAME_INTERVAL_SECONDS,
                         help=f"Seconds between sampled frames (default {av_craft_pipeline.DEFAULT_FRAME_INTERVAL_SECONDS})")
    parser.add_argument("--max-frames", type=int, default=av_craft_pipeline.DEFAULT_MAX_FRAMES,
                         help=f"Maximum frames to sample/analyze (default {av_craft_pipeline.DEFAULT_MAX_FRAMES})")
    parser.add_argument("--out-dir", help="Directory to write the JSON report")
    parser.add_argument("--json", action="store_true", help="Print raw JSON instead of formatted text")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)

    missing = av_craft_pipeline.check_dependencies()
    if missing:
        print("Missing dependencies:\n  " + "\n  ".join(missing), file=sys.stderr)
        return 1

    report = av_craft_pipeline.analyze_url(
        args.url, frame_interval=args.frame_interval, max_frames=args.max_frames
    )

    if args.out_dir:
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        video_id = (report.get("video") or {}).get("video_id", "unknown")
        out_path = out_dir / f"av_craft_{video_id}.json"
        out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote {out_path}")

    print(json.dumps(report, indent=2, ensure_ascii=False) if args.json else format_report_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
