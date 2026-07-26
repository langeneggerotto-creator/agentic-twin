#!/usr/bin/env python3
"""Smoke tests for APEX YouTube Principles Extraction Pipeline v0.1."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "03_APPLICATION" / "consoles" / "youtube-principles" / "v0.1" / "backend" / "pipeline.py"

spec = importlib.util.spec_from_file_location("youtube_principles_pipeline", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module  # dataclasses needs the module registered before exec
spec.loader.exec_module(module)


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
                "domains": ["Productivity Time Management", "productivity-time-management"],
                "aliases": ["Parkinson's Law of Bureaucracy"],
                "description": "Work expands to fill the time available for its completion.",
                "application": "Set shorter deadlines to force focus.",
                "quote": "work expands so as to fill the time available",
            }]
        return []

    def summarize(self, text, video_title):
        return "A short test summary."


def test_parse_video_id_handles_common_url_shapes():
    cases = {
        "https://www.youtube.com/watch?v=abc123XYZ_9": "abc123XYZ_9",
        "https://youtu.be/abc123XYZ_9?t=10": "abc123XYZ_9",
        "https://www.youtube.com/shorts/abc123XYZ_9": "abc123XYZ_9",
        "https://www.youtube.com/embed/abc123XYZ_9": "abc123XYZ_9",
        "abc123XYZ_9": "abc123XYZ_9",
        "not a url": None,
    }
    for url, expected in cases.items():
        assert_true(module.parse_video_id(url) == expected, f"parse_video_id failed for {url}")


def test_split_urls_handles_newlines_and_commas():
    raw = "https://youtu.be/a\nhttps://youtu.be/b, https://youtu.be/c"
    cleaned = module.split_urls(raw)
    assert_true(
        cleaned == ["https://youtu.be/a", "https://youtu.be/b", "https://youtu.be/c"],
        "split_urls should split cleanly on newlines and commas",
    )


def test_chunk_transcript_respects_char_limit_and_preserves_order():
    segments = [{"text": "word " * 50, "start": float(i), "duration": 1.0} for i in range(10)]
    chunks = module.chunk_transcript(segments, char_limit=100)
    assert_true(len(chunks) > 1, "long transcript should split into multiple chunks")
    joined = " ".join(c.text for c in chunks)
    assert_true("word" in joined, "chunk text should retain transcript content")
    assert_true(chunks[0].start_seconds == 0.0, "first chunk should start at the first segment's timestamp")


def test_verify_quote_accepts_exact_and_rejects_unrelated():
    chunk = "The key idea is that work expands so as to fill the time available for its completion."
    assert_true(
        module.verify_quote("work expands so as to fill the time available", chunk),
        "exact substring should verify",
    )
    assert_true(
        not module.verify_quote("this quote does not appear anywhere near here", chunk),
        "unrelated quote should not verify",
    )


def test_merge_candidates_dedupes_by_name_and_prefers_verified():
    items = [
        {"name": "Parkinson's Law", "quote_verified": False},
        {"name": "parkinson's law", "quote_verified": True},
        {"name": "80/20 Rule", "quote_verified": True},
    ]
    merged = module.merge_candidates(items)
    assert_true(len(merged) == 2, "duplicate names (case-insensitive) should merge")
    parkinson = next(m for m in merged if "parkinson" in m["name"].lower())
    assert_true(parkinson["quote_verified"] is True, "merge should prefer the verified duplicate")


def test_build_report_with_available_transcript_extracts_principles():
    video = module.VideoMeta(
        video_id="abc123XYZ_9",
        url="https://youtu.be/abc123XYZ_9",
        title="Time Management 101",
        channel="Test Channel",
    )
    transcript = module.TranscriptResult(
        status="ok",
        segments=[{
            "text": "Today we talk about Parkinson's Law: work expands so as to fill the time available.",
            "start": 0.0,
            "duration": 5.0,
        }],
    )
    report = module.build_report("https://youtu.be/abc123XYZ_9", video, transcript, FakeLLMClient())
    assert_true(report["transcript_status"] == "ok", "transcript status should be ok")
    assert_true(report["principle_count"] == 1, "expected exactly one extracted principle")
    assert_true(report["principles"][0]["quote_verified"] is True, "quote should verify against source segment")
    assert_true(report["principles"][0]["domains"] == ["productivity-time-management"], "domain tags should be normalized and deduped")
    assert_true(report["principles"][0]["aliases"] == ["Parkinson's Law of Bureaucracy"], "aliases should pass through")
    assert_true(report["qa_gates"]["release_status"] == "PROTOTYPE_OK", "clean report should pass QA")
    assert_true(report["manifest_hash_sha256"], "manifest hash must be generated")


def test_normalize_domains_and_aliases():
    assert_true(
        module.normalize_domains(["Business Strategy", "business-strategy", ""]) == ["business-strategy"],
        "domains should be kebab-cased and deduped",
    )
    assert_true(module.normalize_domains("not a list") == [], "non-list input should return empty")
    assert_true(
        module.normalize_aliases(["80/20 Rule", "80/20 Rule", ""]) == ["80/20 Rule"],
        "aliases should be deduped while preserving original casing",
    )


def test_merge_candidates_unions_domains_and_aliases_across_duplicates():
    items = [
        {"name": "Parkinson's Law", "quote_verified": False, "domains": ["productivity-time-management"], "aliases": []},
        {"name": "parkinson's law", "quote_verified": True, "domains": ["business-strategy"], "aliases": ["Parkinson's Law of Bureaucracy"]},
    ]
    merged = module.merge_candidates(items)
    assert_true(len(merged) == 1, "duplicate names should merge into one entry")
    entry = merged[0]
    assert_true(
        set(entry["domains"]) == {"productivity-time-management", "business-strategy"},
        "domains should union across duplicate sightings instead of only keeping one chunk's tags",
    )
    assert_true(
        entry["aliases"] == ["Parkinson's Law of Bureaucracy"],
        "aliases should union across duplicate sightings",
    )


def test_build_report_without_transcript_holds_for_review():
    video = module.VideoMeta(video_id="zzz999ZZZ_1", url="https://youtu.be/zzz999ZZZ_1")
    transcript = module.TranscriptResult(status="disabled", error="Captions are disabled for this video.")
    report = module.build_report("https://youtu.be/zzz999ZZZ_1", video, transcript, FakeLLMClient())
    assert_true(report["principle_count"] == 0, "no transcript means no principles")
    assert_true(report["qa_gates"]["release_status"] == "HOLD_FOR_REVIEW", "missing transcript should hold for review")
    assert_true("no_transcript_available" in report["risk_flags"], "risk flags should note missing transcript")


class FailingLLMClient:
    """Simulates every LLM call failing (e.g. a bad/placeholder API key)."""

    def extract_principles(self, chunk_text, video_title):
        raise RuntimeError("Error code: 401 - invalid_api_key")

    def summarize(self, text, video_title):
        raise RuntimeError("Error code: 401 - invalid_api_key")


def test_build_report_surfaces_llm_errors_instead_of_swallowing_them():
    video = module.VideoMeta(video_id="abc123XYZ_9", url="https://youtu.be/abc123XYZ_9")
    transcript = module.TranscriptResult(
        status="ok",
        segments=[
            {"text": "word " * 800, "start": 0.0, "duration": 5.0},
            {"text": "word " * 800, "start": 5.0, "duration": 5.0},
        ],
    )
    report = module.build_report("https://youtu.be/abc123XYZ_9", video, transcript, FailingLLMClient())
    assert_true(report["principle_count"] == 0, "a fully failing LLM should yield zero principles")
    assert_true(report["llm_failed_chunk_count"] >= 1, "failed chunk count should be tracked")
    assert_true(len(report["llm_error_samples"]) >= 1, "at least one real error message should be captured")
    assert_true(
        "401" in report["llm_error_samples"][0],
        "the actual exception text should be surfaced, not swallowed",
    )
    assert_true(
        report["risk_flags"].count("llm_extraction_error") == 1,
        "one llm_extraction_error flag should be set regardless of how many chunks failed",
    )


def test_analyze_url_reports_invalid_url_gracefully():
    report = module.analyze_url("not a youtube url", FakeLLMClient())
    assert_true(report["principle_count"] == 0, "invalid URL should yield zero principles")
    assert_true("invalid_url" in report["risk_flags"], "invalid URL should be flagged")


if __name__ == "__main__":
    test_parse_video_id_handles_common_url_shapes()
    test_split_urls_handles_newlines_and_commas()
    test_chunk_transcript_respects_char_limit_and_preserves_order()
    test_verify_quote_accepts_exact_and_rejects_unrelated()
    test_merge_candidates_dedupes_by_name_and_prefers_verified()
    test_build_report_with_available_transcript_extracts_principles()
    test_normalize_domains_and_aliases()
    test_merge_candidates_unions_domains_and_aliases_across_duplicates()
    test_build_report_without_transcript_holds_for_review()
    test_build_report_surfaces_llm_errors_instead_of_swallowing_them()
    test_analyze_url_reports_invalid_url_gracefully()
    print("PASS: APEX YouTube Principles Extraction Pipeline v0.1 smoke tests")
