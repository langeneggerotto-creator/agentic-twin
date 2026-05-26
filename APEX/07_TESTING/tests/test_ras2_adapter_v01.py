#!/usr/bin/env python3
"""Smoke tests for APEX RAS2 Adapter v0.1."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "03_APPLICATION" / "integrations" / "ras2" / "v0.1" / "ras2_adapter.py"

spec = importlib.util.spec_from_file_location("ras2_adapter", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_complete_record_passes_core_checks():
    text = "Build an APEX feature with objective, risks, implementation, evidence, owner, and next step."
    record = module.analyze(text)
    assert_true(record.score == 1.0, "complete sample should score 1.0")
    assert_true(record.missing_fields == [], "complete sample should have no missing fields")
    assert_true(record.heart_core["status"] == "PASS", "complete sample should pass Heart Core")
    assert_true(record.repo_action["auto_push_enabled"] is False, "auto push must remain disabled")
    assert_true(record.manifest_hash_sha256 != "pending", "manifest hash must be generated")


def test_missing_fields_hold_for_review():
    text = "Build an APEX feature quickly."
    record = module.analyze(text)
    assert_true(record.score < 1.0, "incomplete sample should score below 1.0")
    assert_true(len(record.missing_fields) > 0, "incomplete sample should identify missing fields")
    assert_true(record.heart_core["status"] == "HOLD", "missing fields should hold Heart Core")
    assert_true(len(record.review_notes) == len(record.missing_fields), "each missing field should create one review note")
    assert_true("rollback_trigger" in record.foresight, "foresight rollback trigger must exist")


if __name__ == "__main__":
    test_complete_record_passes_core_checks()
    test_missing_fields_hold_for_review()
    print("PASS: APEX RAS2 Adapter v0.1 smoke tests")
