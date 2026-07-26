#!/usr/bin/env python3
"""
APEX YouTube Principles Extraction CLI v0.1

The easiest way to run the pipeline: no server, no browser, one command.

    python3 cli.py "https://www.youtube.com/watch?v=..." [more urls...]
    python3 cli.py --file urls.txt --out-dir reports/
    cat urls.txt | python3 cli.py

Requires OPENAI_API_KEY in the environment for principle extraction and
summaries; without it, transcripts/metadata still print but principles
will be empty and each report is flagged with an llm_extraction_error
risk flag.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

try:
    from . import pipeline
except ImportError:  # allow running directly as `python3 cli.py`, not just `python3 -m backend.cli`
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pipeline  # type: ignore


def read_urls(args: argparse.Namespace) -> List[str]:
    urls: List[str] = list(args.urls)
    if args.file:
        urls.extend(pipeline.split_urls(Path(args.file).read_text(encoding="utf-8")))
    if not urls and not sys.stdin.isatty():
        urls.extend(pipeline.split_urls(sys.stdin.read()))
    seen = set()
    deduped = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            deduped.append(url)
    return deduped


def format_report_text(report: dict) -> str:
    if report.get("error"):
        return f"✗ {report.get('source_url')}\n  ERROR: {report['error']}"

    video = report.get("video", {})
    qa = report.get("qa_gates", {})
    lines = [
        "=" * 70,
        f"{video.get('title', 'Untitled')}  ({video.get('channel', 'Unknown channel')})",
        str(report.get("source_url", "")),
        f"transcript: {report.get('transcript_status')} | "
        f"QA score: {qa.get('score', '?')} ({qa.get('release_status', '?')})",
    ]
    if report.get("transcript_error"):
        lines.append(f"  note: {report['transcript_error']}")
    if report.get("summary"):
        lines += ["", "Summary:", f"  {report['summary']}"]

    principles = report.get("principles", [])
    lines += ["", f"Core principles ({len(principles)}):"]
    for i, p in enumerate(principles, 1):
        verified = "verified" if p.get("quote_verified") else "UNVERIFIED"
        lines.append(f"  {i}. [{p.get('category', 'principle')}] {p.get('name', 'Untitled')}")
        if p.get("aliases"):
            lines.append(f"     aka: {', '.join(p['aliases'])}")
        if p.get("domains"):
            lines.append(f"     domains: {', '.join(p['domains'])}")
        if p.get("description"):
            lines.append(f"     {p['description']}")
        if p.get("application"):
            lines.append(f"     Apply it: {p['application']}")
        if p.get("quote"):
            lines.append(f"     \"{p['quote']}\" ({p.get('approx_timestamp', '?')}, {verified})")

    if report.get("llm_error_samples"):
        lines += ["", f"LLM call errors ({report.get('llm_failed_chunk_count', 0)} chunk(s) failed), sample:"]
        for err in report["llm_error_samples"]:
            lines.append(f"  {err}")

    if report.get("risk_flags"):
        lines += ["", "Risk flags: " + ", ".join(report["risk_flags"])]
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract core laws/principles/theories/frameworks from YouTube videos."
    )
    parser.add_argument("urls", nargs="*", help="YouTube URLs to analyze")
    parser.add_argument("--file", help="Path to a text file with one URL per line")
    parser.add_argument("--out-dir", help="Directory to write one JSON report per video")
    parser.add_argument("--json", action="store_true", help="Print raw JSON instead of formatted text")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    urls = read_urls(args)
    if not urls:
        print("No URLs given. Pass them as arguments, --file, or via stdin.", file=sys.stderr)
        return 1

    reports = pipeline.analyze_urls(urls)

    if args.out_dir:
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for report in reports:
            video_id = (report.get("video") or {}).get("video_id", "unknown")
            out_path = out_dir / f"youtube_principles_{video_id}.json"
            out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"Wrote {out_path}")

    for report in reports:
        print(json.dumps(report, indent=2, ensure_ascii=False) if args.json else format_report_text(report))
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
