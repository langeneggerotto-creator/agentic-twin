#!/usr/bin/env python3
"""
APEX Lyric-Scene Correlation CLI v0.1

Correlates a music video's actual lyrics (from its caption track) against
its already-analyzed visual scenes (from an av_craft_pipeline.py report),
describing how each scene relates to what's being sung at that moment.

Run av_craft_cli.py first to produce the craft report this needs:

    python3 av_craft_cli.py "https://youtu.be/VIDEO_ID" --out-dir reports/
    python3 lyric_scene_cli.py "https://youtu.be/VIDEO_ID" --craft-report reports/av_craft_VIDEOID.json --out-dir reports/

Requires OPENAI_API_KEY for the correlation commentary.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

try:
    from . import lyric_scene_pipeline
except ImportError:  # allow running directly as `python3 lyric_scene_cli.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import lyric_scene_pipeline  # type: ignore


def format_report_text(report: dict) -> str:
    if report.get("error"):
        return f"✗ {report.get('source_url')}\n  ERROR: {report['error']}"

    lines = [
        "=" * 70,
        f"Video: {report.get('video_id')}",
        str(report.get("source_url", "")),
        f"transcript: {report.get('transcript_status')} | "
        f"correlations: {report.get('correlation_count', 0)} "
        f"({report.get('meaningful_connection_count', 0)} with a meaningful connection)",
    ]
    if report.get("transcript_error"):
        lines.append(f"  note: {report['transcript_error']}")
    if report.get("scenes_skipped_no_timestamp") or report.get("scenes_skipped_no_lyrics_in_range"):
        lines.append(
            f"  (skipped {report.get('scenes_skipped_no_timestamp', 0)} scene(s) with no parseable timestamp, "
            f"{report.get('scenes_skipped_no_lyrics_in_range', 0)} with no lyrics in range)"
        )

    lines.append("")
    for i, c in enumerate(report.get("correlations", []), 1):
        marker = "✓" if c.get("has_meaningful_connection") else "·"
        lines.append(f"  {i}. [{marker}] {c.get('evidence_timestamp', '?')}  scene: {c.get('scene_name', '?')} ({c.get('scene_category', '?')})")
        lines.append(f"     lyric: \"{c.get('lyric_text', '')}\"")
        lines.append(f"     correlation: {c.get('correlation', '')}")
        lines.append("")

    if report.get("llm_error_samples"):
        lines.append(f"LLM errors ({len(report['llm_error_samples'])} sample(s)):")
        for err in report["llm_error_samples"]:
            lines.append(f"  {err}")
        lines.append("")

    if report.get("risk_flags"):
        lines.append("Risk flags: " + ", ".join(report["risk_flags"]))
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Correlate a music video's lyrics against its analyzed scenes.")
    parser.add_argument("url", help="YouTube URL of the music video (must match the --craft-report)")
    parser.add_argument("--craft-report", required=True, help="Path to an existing av_craft_pipeline.py report JSON for this same video")
    parser.add_argument("--out-dir", help="Directory to write the JSON report")
    parser.add_argument("--json", action="store_true", help="Print raw JSON instead of formatted text")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = lyric_scene_pipeline.analyze(args.url, args.craft_report)

    if args.out_dir:
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        video_id = report.get("video_id") or "unknown"
        out_path = out_dir / f"lyric_scene_{video_id}.json"
        out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote {out_path}")

    print(json.dumps(report, indent=2, ensure_ascii=False) if args.json else format_report_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
