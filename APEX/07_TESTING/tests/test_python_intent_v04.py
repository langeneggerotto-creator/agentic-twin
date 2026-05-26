#!/usr/bin/env python3
"""Smoke tests for APEX Python Intent Console v0.4 with Foresight."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "03_APPLICATION" / "consoles" / "python-intent" / "v0.4" / "apex_python_intent_console_v04.py"

spec = importlib.util.spec_from_file_location("apex_python_intent_console_v04", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_foresight_routing_and_output():
    record = module.make_record("Build the next APEX feature with foresight, future scenarios, rollback, and tests.")
    assert_true("foresight" in record.modules, "foresight module should be routed")
    assert_true("foresight_engine" in record.__dataclass_fields__, "record must include foresight_engine")
    assert_true(len(record.foresight_engine["possible_futures"]) >= 3, "foresight must list possible futures")
    assert_true(len(record.foresight_engine["early_warning_signals"]) >= 3, "foresight must list warning signals")
    assert_true("rollback_trigger" in record.foresight_engine, "foresight must include rollback trigger")
    assert_true(record.qa_gates["score"] <= 100, "QA score must be capped at 100")


def test_foresight_and_heart_core_together():
    record = module.make_record("Analyze a YouTube video and plan the future APEX media workflow safely.")
    assert_true("video_analysis" in record.modules, "video_analysis should be routed")
    assert_true("foresight" in record.modules, "foresight should be routed")
    assert_true(record.heart_core["human_control_delta"] == "positive", "human control delta must be positive")
    assert_true("UNKNOWN" in record.truth_status, "truth status must include UNKNOWN")
    assert_true(record.manifest_hash_sha256 != "pending", "manifest hash should be generated")


if __name__ == "__main__":
    test_foresight_routing_and_output()
    test_foresight_and_heart_core_together()
    print("PASS: APEX Python Intent Console v0.4 foresight smoke tests")
