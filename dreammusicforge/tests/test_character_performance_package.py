#!/usr/bin/env python3
"""Smoke tests for the DreamMusicForge Character Performance Package schema."""
import copy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "schemas" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


character = load("character_performance_package", "character_performance_package.py")
cinematic = load("cinematic_architecture", "cinematic_architecture.py")
blueprint = load("universal_production_blueprint", "universal_production_blueprint.py")


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_example_is_valid():
    errors = character.validate_character_performance_package(character.EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE)
    assert_true(errors == [], f"example package should be valid, got: {errors}")


def test_no_narrator_false_is_rejected():
    doc = copy.deepcopy(character.EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE)
    doc["no_narrator"] = False
    errors = character.validate_character_performance_package(doc)
    assert_true(any("no_narrator must be true" in e for e in errors), "no_narrator: false should be flagged")


def test_narrator_labeled_character_is_rejected():
    doc = copy.deepcopy(character.EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE)
    doc["vocal_performers"][0]["character_name"] = "Narrator"
    errors = character.validate_character_performance_package(doc)
    assert_true(any("reads as a narrator/voiceover role" in e for e in errors), "a character named 'Narrator' should be flagged")


def test_lip_sync_required_false_is_rejected():
    doc = copy.deepcopy(character.EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE)
    doc["vocal_performers"][0]["lip_sync_required"] = False
    errors = character.validate_character_performance_package(doc)
    assert_true(any("lip_sync_required must be true" in e for e in errors), "lip_sync_required: false should be flagged")


def test_performer_without_reference_is_rejected():
    doc = copy.deepcopy(character.EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE)
    doc["vocal_performers"].append({
        "character_name": "The Unestablished One",
        "register": "high", "texture": "thin", "description": "appears from nowhere",
        "sings_during_shot_ids": ["shot1"], "lip_sync_required": True,
    })
    errors = character.validate_character_performance_package(doc)
    assert_true(any("has no matching character_references entry" in e for e in errors), "a singer with no established reference should be flagged")


def test_missing_required_ethics_non_goal_is_rejected():
    doc = copy.deepcopy(character.EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE)
    doc["non_goals"] = [character.REQUIRED_RIGHTS_NON_GOAL]
    errors = character.validate_character_performance_package(doc)
    assert_true(any("ethics constraint" in e for e in errors), "dropping the required ethics non-goal should be flagged")


def test_missing_required_rights_non_goal_is_rejected():
    doc = copy.deepcopy(character.EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE)
    doc["non_goals"] = [character.REQUIRED_ETHICS_NON_GOAL]
    errors = character.validate_character_performance_package(doc)
    assert_true(any("rights-review constraint" in e for e in errors), "dropping the required rights non-goal should be flagged")


def test_original_character_false_is_rejected():
    doc = copy.deepcopy(character.EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE)
    doc["character_references"][0]["original_character"] = False
    errors = character.validate_character_performance_package(doc)
    assert_true(any("original_character must be true" in e for e in errors), "original_character: false should be flagged")


def test_boilerplate_originality_basis_is_rejected():
    doc = copy.deepcopy(character.EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE)
    doc["character_references"][0]["originality_basis"] = "yes"
    errors = character.validate_character_performance_package(doc)
    assert_true(any("must be a substantive statement" in e for e in errors), "a trivially short originality_basis should be flagged")


def test_known_ip_character_name_is_rejected():
    doc = copy.deepcopy(character.EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE)
    doc["character_references"][0]["character_name"] = "Spider-Man"
    errors = character.validate_character_performance_package(doc)
    assert_true(any("known trademarked/copyrighted character" in e for e in errors), "a known franchise character name should be flagged")


def test_known_ip_mentioned_in_reference_prompt_is_rejected():
    doc = copy.deepcopy(character.EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE)
    doc["character_references"][0]["reference_prompt"] = "Looks exactly like Batman in every frame."
    errors = character.validate_character_performance_package(doc)
    assert_true(any("known trademarked/copyrighted character" in e for e in errors), "a known franchise character mentioned in the prompt text should be flagged")


def test_rights_review_reflects_flagged_risk():
    doc = copy.deepcopy(character.EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE)
    doc["character_references"][0]["resembles_existing_ip_risk"] = "needs_legal_review"
    recomputed = character.assess_rights_review_status(doc)
    assert_true(recomputed["status"] == "hold_for_review", "flagging any character should force rights_review.status to hold_for_review")
    assert_true(len(recomputed["blockers"]) == 1, "the flagged character should appear as a blocker")


def test_rights_review_reproducibility_check_catches_stale_status():
    doc = copy.deepcopy(character.EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE)
    doc["character_references"][0]["resembles_existing_ip_risk"] = "needs_legal_review"
    # rights_review left as "clear_to_proceed" -- now stale relative to the flagged character above
    errors = character.validate_character_performance_package(doc)
    assert_true(any("does not reproduce from character_references" in e for e in errors), "a stale rights_review that doesn't match its own character_references should be flagged")


def test_cross_document_validation_passes_against_paired_cinematic_and_blueprint():
    cinematic_errors = character.validate_against_cinematic_architecture(
        character.EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE, cinematic.EXAMPLE_CINEMATIC_ARCHITECTURE
    )
    blueprint_errors = character.validate_against_blueprint(
        character.EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE, blueprint.EXAMPLE_UNIVERSAL_PRODUCTION_BLUEPRINT
    )
    assert_true(cinematic_errors == [], f"example should reference only real shots, got: {cinematic_errors}")
    assert_true(blueprint_errors == [], f"example should reference only established characters, got: {blueprint_errors}")


def test_cross_document_validation_catches_unknown_shot_reference():
    doc = copy.deepcopy(character.EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE)
    doc["vocal_performers"][0]["sings_during_shot_ids"] = ["shot_does_not_exist"]
    errors = character.validate_against_cinematic_architecture(doc, cinematic.EXAMPLE_CINEMATIC_ARCHITECTURE)
    assert_true(any("references unknown shot_id" in e for e in errors), "a reference to a nonexistent shot should be flagged")


def test_cross_document_validation_catches_unknown_character():
    doc = copy.deepcopy(character.EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE)
    doc["character_references"][0]["character_name"] = "Someone Not In The Blueprint"
    errors = character.validate_against_blueprint(doc, blueprint.EXAMPLE_UNIVERSAL_PRODUCTION_BLUEPRINT)
    assert_true(any("does not match any character" in e for e in errors), "a character not in the blueprint's character_biographies should be flagged")


def test_all_eight_shots_are_covered_by_some_singer():
    covered = set()
    for performer in character.EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE["vocal_performers"]:
        covered.update(performer["sings_during_shot_ids"])
    all_shots = {s["shot_id"] for s in cinematic.EXAMPLE_CINEMATIC_ARCHITECTURE["shots"]}
    assert_true(covered == all_shots, f"expected every shot to have a singing character instead of a narrator, missing: {all_shots - covered}")


if __name__ == "__main__":
    test_example_is_valid()
    test_no_narrator_false_is_rejected()
    test_narrator_labeled_character_is_rejected()
    test_lip_sync_required_false_is_rejected()
    test_performer_without_reference_is_rejected()
    test_missing_required_ethics_non_goal_is_rejected()
    test_missing_required_rights_non_goal_is_rejected()
    test_original_character_false_is_rejected()
    test_boilerplate_originality_basis_is_rejected()
    test_known_ip_character_name_is_rejected()
    test_known_ip_mentioned_in_reference_prompt_is_rejected()
    test_rights_review_reflects_flagged_risk()
    test_rights_review_reproducibility_check_catches_stale_status()
    test_cross_document_validation_passes_against_paired_cinematic_and_blueprint()
    test_cross_document_validation_catches_unknown_shot_reference()
    test_cross_document_validation_catches_unknown_character()
    test_all_eight_shots_are_covered_by_some_singer()
    print("PASS: DreamMusicForge Character Performance Package smoke tests")
