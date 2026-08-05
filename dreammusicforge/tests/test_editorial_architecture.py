#!/usr/bin/env python3
"""Smoke tests for the DreamMusicForge Editorial Architecture schema."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "schemas" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


editorial = load("editorial_architecture", "editorial_architecture.py")
cinematic = load("cinematic_architecture", "cinematic_architecture.py")
musical = load("musical_architecture", "musical_architecture.py")


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_example_is_valid():
    errors = editorial.validate_editorial_architecture(editorial.EXAMPLE_EDITORIAL_ARCHITECTURE)
    assert_true(errors == [], f"example architecture should be valid, got: {errors}")


def test_non_monotonic_start_times_are_rejected():
    doc = dict(editorial.EXAMPLE_EDITORIAL_ARCHITECTURE)
    timeline = [dict(c) for c in doc["edit_timeline"]]
    timeline[0]["start_time_seconds"], timeline[1]["start_time_seconds"] = (
        timeline[1]["start_time_seconds"], timeline[0]["start_time_seconds"]
    )
    doc["edit_timeline"] = timeline
    errors = editorial.validate_editorial_architecture(doc)
    assert_true(any("strictly increasing start_time_seconds" in e for e in errors), "out-of-order start times should be flagged")


def test_beat_matched_cut_without_tempo_segment_is_rejected():
    doc = dict(editorial.EXAMPLE_EDITORIAL_ARCHITECTURE)
    timeline = [dict(c) for c in doc["edit_timeline"]]
    timeline[0] = dict(timeline[0])
    del timeline[0]["linked_tempo_segment_id"]
    doc["edit_timeline"] = timeline
    errors = editorial.validate_editorial_architecture(doc)
    assert_true(any("linked_tempo_segment_id is required" in e for e in errors), "a beat-matched cut without a tempo segment should be flagged")


def test_motif_that_never_evolves_is_rejected():
    doc = dict(editorial.EXAMPLE_EDITORIAL_ARCHITECTURE)
    doc["motif_evolution"] = [dict(doc["motif_evolution"][0])]
    errors = editorial.validate_editorial_architecture(doc)
    assert_true(any("must evolve across at least 2 beats" in e for e in errors), "a single-entry motif should be flagged")


def test_motif_ending_on_non_terminal_stage_is_rejected():
    doc = dict(editorial.EXAMPLE_EDITORIAL_ARCHITECTURE)
    entries = [dict(e) for e in doc["motif_evolution"]]
    entries[-1]["stage"] = "recurred"
    doc["motif_evolution"] = entries
    errors = editorial.validate_editorial_architecture(doc)
    assert_true(any("must end with stage 'transformed' or 'resolved'" in e for e in errors), "a motif ending on 'recurred' should be flagged")


def test_callback_payoff_before_setup_is_rejected():
    doc = dict(editorial.EXAMPLE_EDITORIAL_ARCHITECTURE)
    doc["visual_callbacks"] = [{
        "callback_id": "cb_bad", "setup_cut_id": "cut8", "payoff_cut_id": "cut1", "description": "backwards",
    }]
    errors = editorial.validate_editorial_architecture(doc)
    assert_true(any("must occur after setup_cut_id" in e for e in errors), "a payoff occurring before its setup should be flagged")


def test_resolution_stated_ending_requires_rationale():
    doc = dict(editorial.EXAMPLE_EDITORIAL_ARCHITECTURE)
    doc["ending"] = {"type": "resolution_stated", "description": "states the lesson outright"}
    errors = editorial.validate_editorial_architecture(doc)
    assert_true(any("explicit_statement_rationale is required" in e for e in errors), "a stated resolution without rationale should be flagged")


def test_missing_required_ethics_non_goal_is_rejected():
    doc = dict(editorial.EXAMPLE_EDITORIAL_ARCHITECTURE)
    doc["non_goals"] = ["some other non-goal"]
    errors = editorial.validate_editorial_architecture(doc)
    assert_true(any("ethics constraint" in e for e in errors), "dropping the required ethics non-goal should be flagged")


def test_cross_document_validation_passes_against_paired_cinematic_and_musical():
    cinematic_errors = editorial.validate_against_cinematic_architecture(
        editorial.EXAMPLE_EDITORIAL_ARCHITECTURE, cinematic.EXAMPLE_CINEMATIC_ARCHITECTURE
    )
    musical_errors = editorial.validate_against_musical_architecture(
        editorial.EXAMPLE_EDITORIAL_ARCHITECTURE, musical.EXAMPLE_MUSICAL_ARCHITECTURE
    )
    assert_true(cinematic_errors == [], f"example should match its paired cinematic architecture, got: {cinematic_errors}")
    assert_true(musical_errors == [], f"example should match its paired musical architecture, got: {musical_errors}")


def test_cross_document_validation_catches_missing_shot_coverage():
    doc = dict(editorial.EXAMPLE_EDITORIAL_ARCHITECTURE)
    timeline = [dict(c) for c in doc["edit_timeline"]]
    timeline[-1] = dict(timeline[-1])
    timeline[-1]["shot_id"] = "shot1"  # duplicate, leaves "shot8" uncovered
    doc["edit_timeline"] = timeline
    errors = editorial.validate_against_cinematic_architecture(doc, cinematic.EXAMPLE_CINEMATIC_ARCHITECTURE)
    assert_true(any("shot8" in e for e in errors), "dropping coverage of a cinematic shot should be flagged")


def test_cross_document_validation_catches_broken_tempo_reference():
    doc = dict(editorial.EXAMPLE_EDITORIAL_ARCHITECTURE)
    timeline = [dict(c) for c in doc["edit_timeline"]]
    timeline[0] = dict(timeline[0])
    timeline[0]["linked_tempo_segment_id"] = "seg_does_not_exist"
    doc["edit_timeline"] = timeline
    errors = editorial.validate_against_musical_architecture(doc, musical.EXAMPLE_MUSICAL_ARCHITECTURE)
    assert_true(any("is not in the musical document's tempo_map" in e for e in errors), "a broken tempo segment reference should be flagged")


if __name__ == "__main__":
    test_example_is_valid()
    test_non_monotonic_start_times_are_rejected()
    test_beat_matched_cut_without_tempo_segment_is_rejected()
    test_motif_that_never_evolves_is_rejected()
    test_motif_ending_on_non_terminal_stage_is_rejected()
    test_callback_payoff_before_setup_is_rejected()
    test_resolution_stated_ending_requires_rationale()
    test_missing_required_ethics_non_goal_is_rejected()
    test_cross_document_validation_passes_against_paired_cinematic_and_musical()
    test_cross_document_validation_catches_missing_shot_coverage()
    test_cross_document_validation_catches_broken_tempo_reference()
    print("PASS: DreamMusicForge Editorial Architecture smoke tests")
