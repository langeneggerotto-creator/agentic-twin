#!/usr/bin/env python3
"""Smoke tests for the DreamMusicForge Cinematic Architecture schema."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "schemas" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cinematic = load("cinematic_architecture", "cinematic_architecture.py")
narrative = load("narrative_emotional_architecture", "narrative_emotional_architecture.py")
musical = load("musical_architecture", "musical_architecture.py")


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_example_is_valid():
    errors = cinematic.validate_cinematic_architecture(cinematic.EXAMPLE_CINEMATIC_ARCHITECTURE)
    assert_true(errors == [], f"example architecture should be valid, got: {errors}")


def test_missing_justification_field_is_rejected():
    doc = dict(cinematic.EXAMPLE_CINEMATIC_ARCHITECTURE)
    shots = [dict(s) for s in doc["shots"]]
    shots[0]["justification"] = dict(shots[0]["justification"])
    del shots[0]["justification"]["why_now"]
    doc["shots"] = shots
    errors = cinematic.validate_cinematic_architecture(doc)
    assert_true(any("justification.why_now" in e for e in errors), "missing why_now justification should be flagged")


def test_centered_framing_requires_rationale():
    doc = dict(cinematic.EXAMPLE_CINEMATIC_ARCHITECTURE)
    shots = [dict(s) for s in doc["shots"]]
    shots[1]["composition"] = dict(shots[1]["composition"])
    shots[1]["composition"]["framing_technique"] = "centered"
    shots[1]["composition"].pop("centered_rationale", None)
    doc["shots"] = shots
    errors = cinematic.validate_cinematic_architecture(doc)
    assert_true(any("centered_rationale is required" in e for e in errors), "centered framing without rationale should be flagged")


def test_flat_depth_layers_are_rejected():
    doc = dict(cinematic.EXAMPLE_CINEMATIC_ARCHITECTURE)
    shots = [dict(s) for s in doc["shots"]]
    shots[0]["composition"] = dict(shots[0]["composition"])
    shots[0]["composition"]["depth_layers"] = {"foreground": None, "midground": "subject", "background": None}
    doc["shots"] = shots
    errors = cinematic.validate_cinematic_architecture(doc)
    assert_true(any("must populate at least 2" in e for e in errors), "a subject flat against the background should be flagged")


def test_missing_stage_coverage_is_rejected():
    doc = dict(cinematic.EXAMPLE_CINEMATIC_ARCHITECTURE)
    shots = [dict(s) for s in doc["shots"]]
    shots[-1]["linked_narrative_stage"] = "beginning"  # duplicate, leaves "reflection" uncovered
    doc["shots"] = shots
    errors = cinematic.validate_cinematic_architecture(doc)
    assert_true(any("reflection" in e for e in errors), "dropping coverage of a narrative stage should be flagged")


def test_invalid_framing_technique_is_rejected():
    doc = dict(cinematic.EXAMPLE_CINEMATIC_ARCHITECTURE)
    shots = [dict(s) for s in doc["shots"]]
    shots[0]["composition"] = dict(shots[0]["composition"])
    shots[0]["composition"]["framing_technique"] = "dutch_angle"
    doc["shots"] = shots
    errors = cinematic.validate_cinematic_architecture(doc)
    assert_true(any("framing_technique must be one of" in e for e in errors), "an invalid framing technique should be flagged")


def test_missing_required_ethics_non_goal_is_rejected():
    doc = dict(cinematic.EXAMPLE_CINEMATIC_ARCHITECTURE)
    doc["non_goals"] = ["some other non-goal"]
    errors = cinematic.validate_cinematic_architecture(doc)
    assert_true(any("ethics constraint" in e for e in errors), "dropping the required ethics non-goal should be flagged")


def test_cross_document_validation_passes_against_paired_narrative_and_musical():
    narrative_errors = cinematic.validate_against_narrative_architecture(
        cinematic.EXAMPLE_CINEMATIC_ARCHITECTURE, narrative.EXAMPLE_NARRATIVE_EMOTIONAL_ARCHITECTURE
    )
    musical_errors = cinematic.validate_against_musical_architecture(
        cinematic.EXAMPLE_CINEMATIC_ARCHITECTURE, musical.EXAMPLE_MUSICAL_ARCHITECTURE
    )
    assert_true(narrative_errors == [], f"example should match its paired narrative, got: {narrative_errors}")
    assert_true(musical_errors == [], f"example should match its paired musical architecture, got: {musical_errors}")


def test_cross_document_validation_catches_stage_drift():
    doc = dict(cinematic.EXAMPLE_CINEMATIC_ARCHITECTURE)
    shots = [dict(s) for s in doc["shots"]]
    shots[0]["linked_narrative_stage"] = "conflict"  # b1 is actually "beginning" in the narrative doc
    doc["shots"] = shots
    errors = cinematic.validate_against_narrative_architecture(doc, narrative.EXAMPLE_NARRATIVE_EMOTIONAL_ARCHITECTURE)
    assert_true(any("does not match" in e for e in errors), "a shot's stage drifting from its beat's stage should be flagged")


def test_cross_document_validation_catches_broken_tempo_reference():
    doc = dict(cinematic.EXAMPLE_CINEMATIC_ARCHITECTURE)
    shots = [dict(s) for s in doc["shots"]]
    shots[0]["linked_tempo_segment_id"] = "seg_does_not_exist"
    doc["shots"] = shots
    errors = cinematic.validate_against_musical_architecture(doc, musical.EXAMPLE_MUSICAL_ARCHITECTURE)
    assert_true(any("is not in the musical document's tempo_map" in e for e in errors), "a broken tempo segment reference should be flagged")


if __name__ == "__main__":
    test_example_is_valid()
    test_missing_justification_field_is_rejected()
    test_centered_framing_requires_rationale()
    test_flat_depth_layers_are_rejected()
    test_missing_stage_coverage_is_rejected()
    test_invalid_framing_technique_is_rejected()
    test_missing_required_ethics_non_goal_is_rejected()
    test_cross_document_validation_passes_against_paired_narrative_and_musical()
    test_cross_document_validation_catches_stage_drift()
    test_cross_document_validation_catches_broken_tempo_reference()
    print("PASS: DreamMusicForge Cinematic Architecture smoke tests")
