#!/usr/bin/env python3
"""Smoke tests for APEX Article/Webpage Principles Extraction v0.1."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "03_APPLICATION" / "consoles" / "youtube-principles" / "v0.1" / "backend"


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, BACKEND_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pipeline = load_module("youtube_principles_pipeline", "pipeline.py")
article_pipeline = load_module("youtube_principles_article_pipeline", "article_pipeline.py")


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


class FakeLLMClient:
    """Deterministic LLM stand-in so tests never call the network."""

    def extract_principles(self, chunk_text, video_title):
        if "parkinson" in chunk_text.lower():
            return [{
                "name": "Parkinson's Law",
                "category": "law",
                "domains": ["productivity-time-management"],
                "aliases": [],
                "description": "Work expands to fill the time available for its completion.",
                "application": "Set shorter deadlines to force focus.",
                "quote": "work expands so as to fill the time available",
            }]
        return []

    def summarize(self, text, video_title):
        return "A short test summary."


def test_is_probably_url():
    assert_true(article_pipeline.is_probably_url("https://example.com/post"), "https URL should be recognized")
    assert_true(article_pipeline.is_probably_url("http://example.com"), "http URL should be recognized")
    assert_true(not article_pipeline.is_probably_url("not a url"), "plain text should not be recognized as a URL")


def test_chunk_plain_text_splits_long_articles():
    text = "\n".join(["Paragraph " + str(i) + " " + ("word " * 30) for i in range(20)])
    chunks = article_pipeline.chunk_plain_text(text, char_limit=200)
    assert_true(len(chunks) > 1, "a long article should split into multiple chunks")
    assert_true(all(c.start_seconds == 0.0 for c in chunks), "article chunks carry no real timestamps")


def test_build_report_with_ok_content_extracts_principles():
    meta = article_pipeline.ArticleMeta(url="https://example.com/post", title="Time Management Tips", author="Jane Doe", site_name="example.com")
    content = article_pipeline.ArticleContent(
        status="ok",
        text="This article discusses Parkinson's Law: work expands so as to fill the time available.",
    )
    report = article_pipeline.build_report("https://example.com/post", meta, content, FakeLLMClient())
    assert_true(report["source_type"] == "article", "report should be labeled as an article source")
    assert_true(report["content_status"] == "ok", "content status should be ok")
    assert_true(report["principle_count"] == 1, "expected exactly one extracted principle")
    assert_true(report["principles"][0]["quote_verified"] is True, "quote should verify against source text")
    assert_true(report["qa_gates"]["release_status"] == "PROTOTYPE_OK", "clean report should pass QA")
    assert_true("content_fetched" in report["qa_gates"]["passes"], "qa_gates should use content_* terminology, not transcript_*")


def test_build_report_without_content_holds_for_review():
    meta = article_pipeline.ArticleMeta(url="https://example.com/paywalled")
    content = article_pipeline.ArticleContent(status="unavailable", error="No extractable article text found.")
    report = article_pipeline.build_report("https://example.com/paywalled", meta, content, FakeLLMClient())
    assert_true(report["principle_count"] == 0, "no content means no principles")
    assert_true(report["qa_gates"]["release_status"] == "HOLD_FOR_REVIEW", "missing content should hold for review")
    assert_true("no_content_available" in report["risk_flags"], "risk flags should note missing content")
    assert_true(not any("transcript_" in issue for issue in report["qa_gates"]["issues"]), "issues should not leak transcript_* naming")


def test_analyze_url_rejects_non_url_input():
    report = article_pipeline.analyze_url("not a url at all", FakeLLMClient())
    assert_true(report["principle_count"] == 0, "non-URL input should yield zero principles")
    assert_true("invalid_url" in report["risk_flags"], "non-URL input should be flagged")


if __name__ == "__main__":
    test_is_probably_url()
    test_chunk_plain_text_splits_long_articles()
    test_build_report_with_ok_content_extracts_principles()
    test_build_report_without_content_holds_for_review()
    test_analyze_url_rejects_non_url_input()
    print("PASS: APEX Article/Webpage Principles Extraction v0.1 smoke tests")
