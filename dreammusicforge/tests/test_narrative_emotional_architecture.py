#!/usr/bin/env python3
"""Smoke tests for the DreamMusicForge Narrative + Emotional Architecture schema."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "schemas" / "narrative_emotional_architecture.py"

spec = importlib.util.spec_from_file_location("narrative_emotional_architecture", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_example_is_valid():
    errors = module.validate_narrative_emotional_architecture(module.EXAMPLE_NARRATIVE_EMOTIONAL_ARCHITECTURE)
    assert_true(errors == [], f"example architecture should be valid, got: {errors}")


def test_missing_narrative_stage_description_is_rejected():
    doc = dict(module.EXAMPLE_NARRATIVE_EMOTIONAL_ARCHITECTURE)
    doc["narrative"] = dict(doc["narrative"])
    del doc["narrative"]["conflict"]
    errors = module.validate_narrative_emotional_architecture(doc)
    assert_true(any("narrative.conflict" in e for e in errors), "missing conflict stage should be flagged")


def test_before_equals_after_is_rejected():
    doc = dict(module.EXAMPLE_NARRATIVE_EMOTIONAL_ARCHITECTURE)
    doc["what_changes"] = {"before_state": "same", "after_state": "same"}
    errors = module.validate_narrative_emotional_architecture(doc)
    assert_true(any("must differ" in e for e in errors), "identical before/after state should be flagged")


def test_short_waveform_is_rejected():
    doc = dict(module.EXAMPLE_NARRATIVE_EMOTIONAL_ARCHITECTURE)
    doc["emotional_waveform"] = doc["emotional_waveform"][:2]
    errors = module.validate_narrative_emotional_architecture(doc)
    assert_true(any("at least 3 beats" in e for e in errors), "a 2-beat waveform should be flagged")


def test_non_monotonic_order_is_rejected():
    doc = dict(module.EXAMPLE_NARRATIVE_EMOTIONAL_ARCHITECTURE)
    waveform = [dict(b) for b in doc["emotional_waveform"]]
    waveform[0]["order"], waveform[1]["order"] = waveform[1]["order"], waveform[0]["order"]
    doc["emotional_waveform"] = waveform
    errors = module.validate_narrative_emotional_architecture(doc)
    assert_true(any("strictly increasing" in e for e in errors), "out-of-order beats should be flagged")


def test_missing_stage_coverage_is_rejected():
    doc = dict(module.EXAMPLE_NARRATIVE_EMOTIONAL_ARCHITECTURE)
    waveform = [dict(b) for b in doc["emotional_waveform"]]
    waveform[-1]["linked_narrative_stage"] = "beginning"  # duplicate, leaves "reflection" uncovered
    doc["emotional_waveform"] = waveform
    errors = module.validate_narrative_emotional_architecture(doc)
    assert_true(any("reflection" in e for e in errors), "dropping coverage of a narrative stage should be flagged")


def test_missing_required_ethics_non_goal_is_rejected():
    doc = dict(module.EXAMPLE_NARRATIVE_EMOTIONAL_ARCHITECTURE)
    doc["non_goals"] = ["some other non-goal"]
    errors = module.validate_narrative_emotional_architecture(doc)
    assert_true(any("ethics constraint" in e for e in errors), "dropping the required ethics non-goal should be flagged")


if __name__ == "__main__":
    test_example_is_valid()
    test_missing_narrative_stage_description_is_rejected()
    test_before_equals_after_is_rejected()
    test_short_waveform_is_rejected()
    test_non_monotonic_order_is_rejected()
    test_missing_stage_coverage_is_rejected()
    test_missing_required_ethics_non_goal_is_rejected()
    print("PASS: DreamMusicForge Narrative + Emotional Architecture smoke tests")
