#!/usr/bin/env python3
"""Smoke tests for APEX Python Intent Console v0.3."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "03_APPLICATION" / "consoles" / "python-intent" / "v0.3" / "apex_python_intent_console_v03.py"

spec = importlib.util.spec_from_file_location("apex_python_intent_console_v03", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_youtube_video_routing():
    record = module.make_record("Analyze a YouTube video transcript and create a rights-safe media plan.")
    assert_true("video_analysis" in record.modules, "video_analysis module should be routed")
    assert_true("rights" in record.modules, "rights module should be routed")
    assert_true(record.qa_gates["score"] <= 100, "QA score must be capped at 100")
    assert_true("heart_core" in record.__dataclass_fields__, "record must include Heart Core")
    assert_true(record.heart_core["human_control_delta"] == "positive", "human control delta must be positive")


def test_plain_build_has_heart_core():
    record = module.make_record("Build a small APEX module that creates a testable artifact plan.")
    assert_true(record.heart_core["dignity_preserved"] is True, "dignity must be preserved")
    assert_true(record.heart_core["user_control_surface_present"] is True, "user control surface must exist")
    assert_true(record.manifest_hash_sha256 != "pending", "manifest hash should be generated")


if __name__ == "__main__":
    test_youtube_video_routing()
    test_plain_build_has_heart_core()
    print("PASS: APEX Python Intent Console v0.3 smoke tests")
