#!/usr/bin/env python3
"""Smoke tests for the DreamMusicForge Universal Production Blueprint schema."""
import copy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "schemas" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


blueprint = load("universal_production_blueprint", "universal_production_blueprint.py")


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_example_is_structurally_valid():
    errors = blueprint.validate_universal_production_blueprint(blueprint.EXAMPLE_UNIVERSAL_PRODUCTION_BLUEPRINT)
    assert_true(errors == [], f"example blueprint should be structurally valid, got: {errors}")


def test_example_passes_full_chain_integration_check():
    errors = blueprint.validate_full_chain(blueprint.EXAMPLE_UNIVERSAL_PRODUCTION_BLUEPRINT)
    assert_true(errors == [], f"example blueprint should pass the full 5-document chain check, got: {errors}")


def test_missing_embedded_document_is_rejected():
    doc = copy.deepcopy(blueprint.EXAMPLE_UNIVERSAL_PRODUCTION_BLUEPRINT)
    del doc["embedded_documents"]["musical_architecture"]
    errors = blueprint.validate_universal_production_blueprint(doc)
    assert_true(any("embedded_documents.musical_architecture is required" in e for e in errors), "a missing embedded document should be flagged")


def test_missing_narrative_supplement_field_is_rejected():
    doc = copy.deepcopy(blueprint.EXAMPLE_UNIVERSAL_PRODUCTION_BLUEPRINT)
    del doc["narrative_supplement"]["sound_design"]
    errors = blueprint.validate_universal_production_blueprint(doc)
    assert_true(any("narrative_supplement.sound_design is required" in e for e in errors), "a missing narrative_supplement field should be flagged")


def test_prompts_present_while_not_yet_built_is_rejected():
    doc = copy.deepcopy(blueprint.EXAMPLE_UNIVERSAL_PRODUCTION_BLUEPRINT)
    doc["provider_specific_prompt_sets"]["prompts"] = [{"provider": "veo", "prompt_text": "..."}]
    errors = blueprint.validate_universal_production_blueprint(doc)
    assert_true(any("must be empty while build_status is 'not_yet_built'" in e for e in errors), "claiming prompts exist while still not_yet_built should be flagged")


def test_draft_status_requires_prompts():
    doc = copy.deepcopy(blueprint.EXAMPLE_UNIVERSAL_PRODUCTION_BLUEPRINT)
    doc["provider_specific_prompt_sets"]["build_status"] = "draft"
    errors = blueprint.validate_universal_production_blueprint(doc)
    assert_true(any("must be non-empty when build_status is 'draft'" in e for e in errors), "a draft status with no prompts should be flagged")


def test_missing_review_council_is_rejected():
    doc = copy.deepcopy(blueprint.EXAMPLE_UNIVERSAL_PRODUCTION_BLUEPRINT)
    doc["review_checklist"] = doc["review_checklist"][:-1]
    errors = blueprint.validate_universal_production_blueprint(doc)
    assert_true(any("ethics_council" in e for e in errors), "a missing review council should be flagged")


def test_missing_required_ethics_non_goal_is_rejected():
    doc = copy.deepcopy(blueprint.EXAMPLE_UNIVERSAL_PRODUCTION_BLUEPRINT)
    doc["non_goals"] = ["some other non-goal"]
    errors = blueprint.validate_universal_production_blueprint(doc)
    assert_true(any("ethics constraint" in e for e in errors), "dropping the required ethics non-goal should be flagged")


def test_full_chain_check_catches_a_broken_embedded_document():
    doc = copy.deepcopy(blueprint.EXAMPLE_UNIVERSAL_PRODUCTION_BLUEPRINT)
    del doc["embedded_documents"]["principle_kernel"]["kernel_statement"]
    errors = blueprint.validate_full_chain(doc)
    assert_true(any("[principle_kernel]" in e and "kernel_statement" in e for e in errors), "a broken embedded principle kernel should be caught by the full-chain check")


def test_full_chain_check_catches_a_broken_cross_document_reference():
    doc = copy.deepcopy(blueprint.EXAMPLE_UNIVERSAL_PRODUCTION_BLUEPRINT)
    doc["embedded_documents"]["musical_architecture"]["tempo_map"][0]["linked_waveform_beat_id"] = "b_does_not_exist"
    errors = blueprint.validate_full_chain(doc)
    assert_true(any("[musical_architecture vs narrative]" in e for e in errors), "a broken cross-document reference inside an embedded document should be caught")


def test_full_chain_check_catches_identity_drift():
    doc = copy.deepcopy(blueprint.EXAMPLE_UNIVERSAL_PRODUCTION_BLUEPRINT)
    doc["source_human_truth_id"] = "believing_despite_uncertainty"  # blueprint claims a different human truth than its embedded documents
    errors = blueprint.validate_full_chain(doc)
    assert_true(any("[chain identity]" in e for e in errors), "a blueprint-level identity mismatch against its embedded documents should be caught")


if __name__ == "__main__":
    test_example_is_structurally_valid()
    test_example_passes_full_chain_integration_check()
    test_missing_embedded_document_is_rejected()
    test_missing_narrative_supplement_field_is_rejected()
    test_prompts_present_while_not_yet_built_is_rejected()
    test_draft_status_requires_prompts()
    test_missing_review_council_is_rejected()
    test_missing_required_ethics_non_goal_is_rejected()
    test_full_chain_check_catches_a_broken_embedded_document()
    test_full_chain_check_catches_a_broken_cross_document_reference()
    test_full_chain_check_catches_identity_drift()
    print("PASS: DreamMusicForge Universal Production Blueprint smoke tests")
