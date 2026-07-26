#!/usr/bin/env python3
"""Smoke tests for APEX Lyric-Scene Correlation Pipeline v0.1."""
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


lsp = load_module("lyric_scene_pipeline", "lyric_scene_pipeline.py")
pipeline = lsp.pipeline


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


class FakeLLMClient:
    def correlate(self, lyric_text, scene_name, scene_description):
        if "staircase" in scene_name.lower():
            return {"correlation": "The ascending staircase mirrors the lyric about rising above difficulty.", "has_meaningful_connection": True}
        return {"correlation": "Instrumental section, no clear lyrical tie.", "has_meaningful_connection": False}


class FailingLLMClient:
    def correlate(self, lyric_text, scene_name, scene_description):
        raise RuntimeError("Error code: 401 - invalid_api_key")


SAMPLE_CRAFT_REPORT = {
    "video": {"video_id": "abc123XYZ_9"},
    "craft_elements": [
        {"name": "Grand Staircase", "category": "set_design", "domains": ["set-design"], "description": "An ornate staircase.", "evidence_timestamp": "0.0s-30.0s"},
        {"name": "Black Screen Transition", "category": "editing", "domains": ["editing-technique"], "description": "A cut to black.", "evidence_timestamp": "216.0s-234.0s"},
        {"name": "Untimestamped Scene", "category": "lighting", "domains": ["lighting-design"], "description": "No parseable timestamp.", "evidence_timestamp": ""},
    ],
}


def test_parse_timestamp_range_handles_valid_and_invalid_input():
    assert_true(lsp.parse_timestamp_range("36.0s-66.0s") == (36.0, 66.0), "should parse a valid range")
    assert_true(lsp.parse_timestamp_range("garbage") is None, "should return None for unparseable input")
    assert_true(lsp.parse_timestamp_range("") is None, "should return None for empty input")


def test_lyrics_in_range_selects_only_segments_within_bounds():
    segments = [
        {"text": "first line", "start": 0.0, "duration": 3.0},
        {"text": "second line", "start": 5.0, "duration": 3.0},
        {"text": "third line", "start": 40.0, "duration": 3.0},
    ]
    assert_true(lsp.lyrics_in_range(segments, 0.0, 10.0) == "first line second line", "should join only segments starting within [start, end)")
    assert_true(lsp.lyrics_in_range(segments, 100.0, 200.0) == "", "should return empty string when nothing is in range")


def test_build_report_correlates_scenes_with_matching_lyrics():
    pipeline.fetch_transcript = lambda video_id: pipeline.TranscriptResult(
        status="ok",
        segments=[
            {"text": "I keep climbing higher and higher", "start": 5.0, "duration": 3.0},
            {"text": "past the shadows of my doubt", "start": 10.0, "duration": 3.0},
        ],
    )
    report = lsp.build_report("abc123XYZ_9", "https://youtu.be/abc123XYZ_9", SAMPLE_CRAFT_REPORT, FakeLLMClient())

    assert_true(report["correlation_count"] == 1, "only the staircase scene overlaps a lyric segment")
    assert_true(report["meaningful_connection_count"] == 1, "the one correlation found should be meaningful")
    assert_true(report["scenes_skipped_no_timestamp"] == 1, "the untimestamped scene should be skipped and counted")
    assert_true(report["scenes_skipped_no_lyrics_in_range"] == 1, "the black-screen scene has no lyrics in its range")
    assert_true("climbing higher" in report["correlations"][0]["lyric_text"], "the correlated lyric text should match the overlapping segment")
    assert_true(report["manifest_hash_sha256"], "manifest hash must be generated")


def test_build_report_handles_no_transcript_gracefully():
    pipeline.fetch_transcript = lambda video_id: pipeline.TranscriptResult(status="disabled", error="Captions are disabled for this video.")
    report = lsp.build_report("abc123XYZ_9", "https://youtu.be/abc123XYZ_9", SAMPLE_CRAFT_REPORT, FakeLLMClient())
    assert_true(report["correlation_count"] == 0, "no transcript should yield zero correlations")
    assert_true("no_transcript_available" in report["risk_flags"], "risk flags should note the missing transcript")


def test_build_report_surfaces_llm_errors_without_crashing():
    pipeline.fetch_transcript = lambda video_id: pipeline.TranscriptResult(
        status="ok", segments=[{"text": "some lyric", "start": 5.0, "duration": 3.0}],
    )
    report = lsp.build_report("abc123XYZ_9", "https://youtu.be/abc123XYZ_9", SAMPLE_CRAFT_REPORT, FailingLLMClient())
    assert_true(report["correlation_count"] == 0, "a fully failing LLM should yield zero correlations, not crash")
    assert_true(len(report["llm_error_samples"]) >= 1, "the actual error should be surfaced, not swallowed")
    assert_true("401" in report["llm_error_samples"][0], "the real exception text should be visible")


def test_analyze_rejects_mismatched_craft_report(tmp_path=None):
    import tempfile, json as json_module
    with tempfile.TemporaryDirectory() as tmp:
        craft_path = Path(tmp) / "craft.json"
        craft_path.write_text(json_module.dumps({"video": {"video_id": "differentVideoId"}, "craft_elements": []}), encoding="utf-8")
        report = lsp.analyze("https://youtu.be/abc123XYZ_9", str(craft_path))
        assert_true("mismatched_craft_report" in report["risk_flags"], "a craft report for a different video should be rejected")


if __name__ == "__main__":
    test_parse_timestamp_range_handles_valid_and_invalid_input()
    test_lyrics_in_range_selects_only_segments_within_bounds()
    test_build_report_correlates_scenes_with_matching_lyrics()
    test_build_report_handles_no_transcript_gracefully()
    test_build_report_surfaces_llm_errors_without_crashing()
    test_analyze_rejects_mismatched_craft_report()
    print("PASS: APEX Lyric-Scene Correlation Pipeline v0.1 smoke tests")
