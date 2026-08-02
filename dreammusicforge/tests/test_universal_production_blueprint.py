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
    doc["provider_specific_prompt_sets"] = {
        "build_status": "not_yet_built",
        "prompts": [{"provider": "veo", "prompt_text": "..."}],
    }
    errors = blueprint.validate_universal_production_blueprint(doc)
    assert_true(any("must be empty while build_status is 'not_yet_built'" in e for e in errors), "claiming prompts exist while still not_yet_built should be flagged")


def test_draft_status_requires_prompts():
    doc = copy.deepcopy(blueprint.EXAMPLE_UNIVERSAL_PRODUCTION_BLUEPRINT)
    doc["provider_specific_prompt_sets"] = {"build_status": "draft", "prompts": []}
    errors = blueprint.validate_universal_production_blueprint(doc)
    assert_true(any("must be non-empty when build_status is 'draft'" in e for e in errors), "a draft status with no prompts should be flagged")


def test_example_was_actually_wired_not_left_as_placeholder():
    prompt_sets = blueprint.EXAMPLE_UNIVERSAL_PRODUCTION_BLUEPRINT["provider_specific_prompt_sets"]
    assert_true(prompt_sets["build_status"] == "draft", f"the worked example should be wired to 'draft' via embed_provider_specific_production_package(), got {prompt_sets['build_status']!r}")
    assert_true(len(prompt_sets["prompts"]) == 9, f"expected 8 video prompts + 1 music prompt, got {len(prompt_sets['prompts'])}")


def test_readiness_activation_is_reproducible_and_matches_ready_flag():
    provider_package = blueprint._load_sibling("provider_specific_production_package")
    readiness = blueprint.compute_readiness_activation(provider_package.EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE)
    assert_true(0.0 <= readiness["activation"] <= 1.0, "activation must be a valid sigmoid output in [0, 1]")
    assert_true(readiness["ready"] == (readiness["activation"] >= blueprint.READINESS_THRESHOLD), "ready flag must match the activation vs. threshold comparison")
    assert_true(readiness["ready"] is True, "the worked example's risk profile should be healthy enough to be ready")


def test_readiness_activation_is_monotonic_in_risk():
    provider_package = blueprint._load_sibling("provider_specific_production_package")
    healthy = copy.deepcopy(provider_package.EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE)
    risky = copy.deepcopy(provider_package.EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE)
    risky["generation_risk_estimate"]["estimated_probability_exceeds_budget"] = 0.9
    healthy_activation = blueprint.compute_readiness_activation(healthy)["activation"]
    risky_activation = blueprint.compute_readiness_activation(risky)["activation"]
    assert_true(risky_activation < healthy_activation, "a riskier generation profile should produce a lower readiness activation")


def test_embed_provider_package_rejects_a_broken_provider_package():
    provider_package = blueprint._load_sibling("provider_specific_production_package")
    base_doc = copy.deepcopy(blueprint.EXAMPLE_UNIVERSAL_PRODUCTION_BLUEPRINT)
    base_doc["provider_specific_prompt_sets"] = {"build_status": "not_yet_built", "prompts": []}
    broken_package = copy.deepcopy(provider_package.EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE)
    del broken_package["music_prompt"]["prompt_text"]
    result = blueprint.embed_provider_specific_production_package(base_doc, broken_package)
    assert_true(len(result["errors"]) > 0, "a broken provider package should produce errors")
    assert_true(result["blueprint"]["provider_specific_prompt_sets"]["build_status"] == "not_yet_built", "tier 3 should stay untouched when the provider package doesn't validate")
    assert_true(result["readiness"] is None, "readiness should not be computed when the provider package is broken")


def test_embed_provider_package_rejects_identity_mismatch():
    provider_package = blueprint._load_sibling("provider_specific_production_package")
    base_doc = copy.deepcopy(blueprint.EXAMPLE_UNIVERSAL_PRODUCTION_BLUEPRINT)
    base_doc["provider_specific_prompt_sets"] = {"build_status": "not_yet_built", "prompts": []}
    mismatched_package = copy.deepcopy(provider_package.EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE)
    mismatched_package["source_human_truth_id"] = "believing_despite_uncertainty"
    result = blueprint.embed_provider_specific_production_package(base_doc, mismatched_package)
    assert_true(any("does not match the blueprint" in e for e in result["errors"]), "an identity mismatch between blueprint and provider package should be flagged")


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
    test_example_was_actually_wired_not_left_as_placeholder()
    test_readiness_activation_is_reproducible_and_matches_ready_flag()
    test_readiness_activation_is_monotonic_in_risk()
    test_embed_provider_package_rejects_a_broken_provider_package()
    test_embed_provider_package_rejects_identity_mismatch()
    test_missing_review_council_is_rejected()
    test_missing_required_ethics_non_goal_is_rejected()
    test_full_chain_check_catches_a_broken_embedded_document()
    test_full_chain_check_catches_a_broken_cross_document_reference()
    test_full_chain_check_catches_identity_drift()
    print("PASS: DreamMusicForge Universal Production Blueprint smoke tests")
