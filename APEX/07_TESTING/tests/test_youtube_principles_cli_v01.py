#!/usr/bin/env python3
"""Smoke tests for APEX YouTube Principles Extraction CLI v0.1."""
import argparse
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONSOLE_DIR = ROOT / "03_APPLICATION" / "consoles" / "youtube-principles" / "v0.1" / "backend"

spec = importlib.util.spec_from_file_location("youtube_principles_cli", CONSOLE_DIR / "cli.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_cli_imports_pipeline_when_run_as_a_bare_script():
    assert_true(hasattr(module, "pipeline"), "cli.py should fall back to a plain import of pipeline.py")
    assert_true(module.pipeline.parse_video_id("https://youtu.be/abc123XYZ_9") == "abc123XYZ_9", "pipeline functions should work through the cli module")


def test_read_urls_merges_args_file_and_dedupes(tmp_path=None):
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        file_path = Path(tmp) / "urls.txt"
        file_path.write_text("https://youtu.be/b\nhttps://youtu.be/a\n", encoding="utf-8")
        args = argparse.Namespace(urls=["https://youtu.be/a"], file=str(file_path))
        urls = module.read_urls(args)
    assert_true(urls == ["https://youtu.be/a", "https://youtu.be/b"], "read_urls should merge positional args and --file, deduping while preserving order")


def test_format_report_text_includes_title_summary_and_principles():
    report = {
        "source_url": "https://youtu.be/abc123XYZ_9",
        "video": {"title": "Time Management 101", "channel": "Test Channel"},
        "transcript_status": "ok",
        "qa_gates": {"score": 100, "release_status": "PROTOTYPE_OK"},
        "summary": "A short test summary.",
        "principles": [{
            "category": "law",
            "name": "Parkinson's Law",
            "description": "Work expands to fill the time available.",
            "application": "Set shorter deadlines.",
            "quote": "work expands so as to fill the time available",
            "approx_timestamp": "00:00",
            "quote_verified": True,
        }],
        "risk_flags": ["verify_named_laws_against_primary_source"],
    }
    text = module.format_report_text(report)
    assert_true("Time Management 101" in text, "formatted output should include the video title")
    assert_true("Parkinson's Law" in text, "formatted output should include the extracted principle name")
    assert_true("verified" in text and "UNVERIFIED" not in text, "verified quotes should not be marked unverified")
    assert_true("A short test summary." in text, "formatted output should include the summary")


def test_format_report_text_handles_error_reports():
    text = module.format_report_text({"source_url": "not a url", "error": "Could not parse a YouTube video ID from this URL."})
    assert_true("ERROR" in text, "error reports should render an ERROR line instead of crashing")


def test_format_report_text_handles_article_shaped_reports():
    report = {
        "source_type": "article",
        "source_url": "https://example.com/post",
        "article": {"title": "80/20 Rule Explained", "author": "Jane Doe"},
        "content_status": "ok",
        "qa_gates": {"score": 100, "release_status": "PROTOTYPE_OK"},
        "summary": "An article about the Pareto Principle.",
        "principles": [{"category": "principle", "name": "Pareto Principle", "quote": "", "quote_verified": False}],
        "risk_flags": [],
    }
    text = module.format_report_text(report)
    assert_true("80/20 Rule Explained" in text, "formatted output should include the article title")
    assert_true("Jane Doe" in text, "formatted output should include the author for article reports")
    assert_true("content:" in text, "article reports should use 'content' status wording, not 'transcript'")


def test_report_slug_prefers_video_id_then_falls_back_to_url_hash():
    video_report = {"video": {"video_id": "abc123XYZ_9"}, "source_url": "https://youtu.be/abc123XYZ_9"}
    assert_true(module.report_slug(video_report) == "abc123XYZ_9", "video reports should slug by video_id")

    article_report = {"source_url": "https://example.com/post"}
    slug = module.report_slug(article_report)
    assert_true(slug and slug != "unknown", "article reports should get a stable non-empty slug")
    assert_true(module.report_slug(article_report) == slug, "the slug should be deterministic for the same URL")


if __name__ == "__main__":
    test_cli_imports_pipeline_when_run_as_a_bare_script()
    test_read_urls_merges_args_file_and_dedupes()
    test_format_report_text_includes_title_summary_and_principles()
    test_format_report_text_handles_error_reports()
    test_format_report_text_handles_article_shaped_reports()
    test_report_slug_prefers_video_id_then_falls_back_to_url_hash()
    print("PASS: APEX YouTube Principles Extraction CLI v0.1 smoke tests")
