#!/usr/bin/env python3
"""Smoke tests for the DreamMusicForge Musical Architecture schema."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "schemas" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


musical = load("musical_architecture", "musical_architecture.py")
narrative = load("narrative_emotional_architecture", "narrative_emotional_architecture.py")


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_example_is_valid():
    errors = musical.validate_musical_architecture(musical.EXAMPLE_MUSICAL_ARCHITECTURE)
    assert_true(errors == [], f"example architecture should be valid, got: {errors}")


def test_missing_tempo_map_field_is_rejected():
    doc = dict(musical.EXAMPLE_MUSICAL_ARCHITECTURE)
    tempo_map = [dict(s) for s in doc["tempo_map"]]
    del tempo_map[0]["bpm"]
    doc["tempo_map"] = tempo_map
    errors = musical.validate_musical_architecture(doc)
    assert_true(any("tempo_map[0].bpm" in e for e in errors), "missing bpm should be flagged")


def test_short_tempo_map_is_rejected():
    doc = dict(musical.EXAMPLE_MUSICAL_ARCHITECTURE)
    doc["tempo_map"] = doc["tempo_map"][:2]
    errors = musical.validate_musical_architecture(doc)
    assert_true(any("at least 3 segments" in e for e in errors), "a 2-segment tempo map should be flagged")


def test_non_monotonic_tempo_order_is_rejected():
    doc = dict(musical.EXAMPLE_MUSICAL_ARCHITECTURE)
    tempo_map = [dict(s) for s in doc["tempo_map"]]
    tempo_map[0]["order"], tempo_map[1]["order"] = tempo_map[1]["order"], tempo_map[0]["order"]
    doc["tempo_map"] = tempo_map
    errors = musical.validate_musical_architecture(doc)
    assert_true(any("strictly increasing" in e for e in errors), "out-of-order tempo segments should be flagged")


def test_invalid_dynamic_level_is_rejected():
    doc = dict(musical.EXAMPLE_MUSICAL_ARCHITECTURE)
    tempo_map = [dict(s) for s in doc["tempo_map"]]
    tempo_map[0]["dynamic_level"] = "fortissimo"
    doc["tempo_map"] = tempo_map
    errors = musical.validate_musical_architecture(doc)
    assert_true(any("dynamic_level must be one of" in e for e in errors), "an invalid dynamic level should be flagged")


def test_silence_moment_bad_reference_is_rejected():
    doc = dict(musical.EXAMPLE_MUSICAL_ARCHITECTURE)
    doc["silence_moments"] = [{
        "after_segment_id": "seg_does_not_exist",
        "duration_qualitative": "one bar",
        "purpose": "test",
    }]
    errors = musical.validate_musical_architecture(doc)
    assert_true(any("does not match any tempo_map segment_id" in e for e in errors), "a dangling silence reference should be flagged")


def test_melodic_motif_bad_reference_is_rejected():
    doc = dict(musical.EXAMPLE_MUSICAL_ARCHITECTURE)
    doc["melodic_motif"] = dict(doc["melodic_motif"])
    doc["melodic_motif"]["recurs_at"] = ["seg_does_not_exist"]
    errors = musical.validate_musical_architecture(doc)
    assert_true(any("references unknown segment_id" in e for e in errors), "a dangling motif reference should be flagged")


def test_missing_required_ethics_non_goal_is_rejected():
    doc = dict(musical.EXAMPLE_MUSICAL_ARCHITECTURE)
    doc["non_goals"] = ["some other non-goal"]
    errors = musical.validate_musical_architecture(doc)
    assert_true(any("ethics constraint" in e for e in errors), "dropping the required ethics non-goal should be flagged")


def test_cross_document_validation_passes_against_paired_narrative():
    errors = musical.validate_against_narrative_architecture(
        musical.EXAMPLE_MUSICAL_ARCHITECTURE,
        narrative.EXAMPLE_NARRATIVE_EMOTIONAL_ARCHITECTURE,
    )
    assert_true(errors == [], f"example musical architecture should match its paired narrative, got: {errors}")


def test_cross_document_validation_catches_broken_beat_reference():
    doc = dict(musical.EXAMPLE_MUSICAL_ARCHITECTURE)
    tempo_map = [dict(s) for s in doc["tempo_map"]]
    tempo_map[0]["linked_waveform_beat_id"] = "b_does_not_exist"
    doc["tempo_map"] = tempo_map
    errors = musical.validate_against_narrative_architecture(doc, narrative.EXAMPLE_NARRATIVE_EMOTIONAL_ARCHITECTURE)
    assert_true(any("is not in the narrative document's emotional_waveform" in e for e in errors), "a broken beat reference should be flagged")


if __name__ == "__main__":
    test_example_is_valid()
    test_missing_tempo_map_field_is_rejected()
    test_short_tempo_map_is_rejected()
    test_non_monotonic_tempo_order_is_rejected()
    test_invalid_dynamic_level_is_rejected()
    test_silence_moment_bad_reference_is_rejected()
    test_melodic_motif_bad_reference_is_rejected()
    test_missing_required_ethics_non_goal_is_rejected()
    test_cross_document_validation_passes_against_paired_narrative()
    test_cross_document_validation_catches_broken_beat_reference()
    print("PASS: DreamMusicForge Musical Architecture smoke tests")
