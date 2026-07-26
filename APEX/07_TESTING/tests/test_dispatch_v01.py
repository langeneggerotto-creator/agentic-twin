#!/usr/bin/env python3
"""Smoke tests for the YouTube/article source dispatcher."""
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


dispatch = load_module("youtube_principles_dispatch", "dispatch.py")


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


class FakeLLMClient:
    def extract_principles(self, chunk_text, video_title):
        return []

    def summarize(self, text, video_title):
        return "summary"


def test_youtube_urls_route_to_the_video_pipeline():
    report = dispatch.analyze_url("https://youtu.be/abc123XYZ_9", FakeLLMClient())
    assert_true(report.get("source_type") == "youtube_video", "a YouTube URL should route to the video pipeline")
    assert_true("video" in report, "a video-routed report should carry a 'video' key")


def test_generic_urls_route_to_the_article_pipeline():
    report = dispatch.analyze_url("https://example.com/some-article", FakeLLMClient())
    assert_true(report.get("source_type") == "article", "a non-YouTube URL should route to the article pipeline")
    assert_true("article" in report, "an article-routed report should carry an 'article' key")


def test_analyze_urls_routes_a_mixed_batch():
    reports = dispatch.analyze_urls(
        ["https://youtu.be/abc123XYZ_9", "https://example.com/some-article"],
        FakeLLMClient(),
    )
    assert_true(len(reports) == 2, "both URLs should produce a report")
    assert_true(
        {r["source_type"] for r in reports} == {"youtube_video", "article"},
        "a mixed batch should route each URL independently",
    )


if __name__ == "__main__":
    test_youtube_urls_route_to_the_video_pipeline()
    test_generic_urls_route_to_the_article_pipeline()
    test_analyze_urls_routes_a_mixed_batch()
    print("PASS: source dispatcher smoke tests")
