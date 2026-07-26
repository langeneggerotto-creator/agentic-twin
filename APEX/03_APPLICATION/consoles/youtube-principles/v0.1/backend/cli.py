#!/usr/bin/env python3
"""
APEX Principles Extraction CLI v0.1

The easiest way to run the pipeline: no server, no browser, one command.
Handles both YouTube URLs (transcript-based) and generic article/webpage
URLs (readable-text-based) -- each URL is routed automatically.

    python3 cli.py "https://www.youtube.com/watch?v=..." "https://example.com/some-article"
    python3 cli.py --file urls.txt --out-dir reports/
    cat urls.txt | python3 cli.py

Requires OPENAI_API_KEY in the environment for principle extraction and
summaries; without it, metadata/content still print but principles will
be empty and each report is flagged with an llm_extraction_error risk flag.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import List, Optional

try:
    from . import dispatch, pipeline
except ImportError:  # allow running directly as `python3 cli.py`, not just `python3 -m backend.cli`
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import dispatch, pipeline  # type: ignore


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


def report_slug(report: dict) -> str:
    """Filesystem-safe identifier for a report, for --out-dir filenames."""
    video_id = (report.get("video") or {}).get("video_id")
    if video_id:
        return video_id
    return hashlib.sha256(str(report.get("source_url", "")).encode("utf-8")).hexdigest()[:16]


def format_report_text(report: dict) -> str:
    if report.get("error"):
        return f"✗ {report.get('source_url')}\n  ERROR: {report['error']}"

    source_type = report.get("source_type", "youtube_video")
    meta = report.get("video") or report.get("article") or {}
    status = report.get("transcript_status") or report.get("content_status")
    status_label = "transcript" if source_type == "youtube_video" else "content"
    by_field = "channel" if source_type == "youtube_video" else "author"
    qa = report.get("qa_gates", {})
    lines = [
        "=" * 70,
        f"{meta.get('title', 'Untitled')}  ({meta.get(by_field, 'Unknown')})",
        str(report.get("source_url", "")),
        f"{status_label}: {status} | "
        f"QA score: {qa.get('score', '?')} ({qa.get('release_status', '?')})",
    ]
    error_text = report.get("transcript_error") or report.get("content_error")
    if error_text:
        lines.append(f"  note: {error_text}")
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
        description="Extract core laws/principles/theories/frameworks from YouTube videos and articles/webpages."
    )
    parser.add_argument("urls", nargs="*", help="YouTube or article/webpage URLs to analyze")
    parser.add_argument("--file", help="Path to a text file with one URL per line")
    parser.add_argument("--out-dir", help="Directory to write one JSON report per URL")
    parser.add_argument("--json", action="store_true", help="Print raw JSON instead of formatted text")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    urls = read_urls(args)
    if not urls:
        print("No URLs given. Pass them as arguments, --file, or via stdin.", file=sys.stderr)
        return 1

    reports = dispatch.analyze_urls(urls)

    if args.out_dir:
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for report in reports:
            out_path = out_dir / f"principles_{report_slug(report)}.json"
            out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"Wrote {out_path}")

    for report in reports:
        print(json.dumps(report, indent=2, ensure_ascii=False) if args.json else format_report_text(report))
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
