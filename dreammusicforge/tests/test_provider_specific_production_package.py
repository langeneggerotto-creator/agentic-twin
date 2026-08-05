#!/usr/bin/env python3
"""Smoke tests for the DreamMusicForge Provider-Specific Production Package schema."""
import copy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "schemas" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


provider = load("provider_specific_production_package", "provider_specific_production_package.py")
cinematic = load("cinematic_architecture", "cinematic_architecture.py")


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_example_is_valid():
    errors = provider.validate_provider_specific_production_package(provider.EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE)
    assert_true(errors == [], f"example package should be valid, got: {errors}")


def test_monte_carlo_probability_is_reasonable():
    risk = provider.EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE["generation_risk_estimate"]
    assert_true(0.05 < risk["estimated_probability_exceeds_budget"] < 0.25, f"expected a moderate risk estimate near the source video's ~12%, got {risk['estimated_probability_exceeds_budget']}")
    assert_true(risk["mean_total_attempts"] > 8, "mean total attempts across 8 shots should exceed 8 (at least one attempt per shot)")


def test_monte_carlo_is_monotonic_in_budget():
    kwargs = dict(num_shots=8, per_shot_success_probability_range=(0.55, 0.85), trials=20000, seed=1)
    tight = provider.run_generation_risk_monte_carlo(budget_max_total_attempts=10, **kwargs)
    loose = provider.run_generation_risk_monte_carlo(budget_max_total_attempts=30, **kwargs)
    assert_true(
        tight["estimated_probability_exceeds_budget"] > loose["estimated_probability_exceeds_budget"],
        "a tighter attempt budget should exceed more often than a looser one",
    )


def test_monte_carlo_is_monotonic_in_success_probability():
    common = dict(num_shots=8, budget_max_total_attempts=14, trials=20000, seed=1)
    low_reliability = provider.run_generation_risk_monte_carlo(per_shot_success_probability_range=(0.3, 0.5), **common)
    high_reliability = provider.run_generation_risk_monte_carlo(per_shot_success_probability_range=(0.8, 0.95), **common)
    assert_true(
        low_reliability["estimated_probability_exceeds_budget"] > high_reliability["estimated_probability_exceeds_budget"],
        "a less reliable provider should exceed the budget more often than a more reliable one",
    )


def test_reproducibility_check_catches_hand_typed_probability():
    doc = copy.deepcopy(provider.EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE)
    doc["generation_risk_estimate"]["estimated_probability_exceeds_budget"] = 0.99  # not what the stated parameters produce
    errors = provider.validate_provider_specific_production_package(doc)
    assert_true(any("does not reproduce from its stated parameters" in e for e in errors), "a stale or hand-typed probability should be flagged")


def test_too_few_trials_is_rejected():
    doc = copy.deepcopy(provider.EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE)
    doc["generation_risk_estimate"]["trials"] = 50
    errors = provider.validate_provider_specific_production_package(doc)
    assert_true(any("trials must be an integer >= 1000" in e for e in errors), "too few Monte Carlo trials should be flagged")


def test_inverted_probability_range_is_rejected():
    doc = copy.deepcopy(provider.EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE)
    doc["generation_risk_estimate"]["per_shot_success_probability_range"] = {"min": 0.9, "max": 0.5}
    errors = provider.validate_provider_specific_production_package(doc)
    assert_true(any("min must be less than max" in e for e in errors), "an inverted probability range should be flagged")


def test_video_prompt_without_source_fields_is_rejected():
    doc = copy.deepcopy(provider.EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE)
    doc["video_prompts"][0]["source_fields_used"] = []
    errors = provider.validate_provider_specific_production_package(doc)
    assert_true(any("video_prompts[0].source_fields_used is required" in e for e in errors), "a prompt with no declared source fields should be flagged")


def test_missing_interface_non_goal_is_rejected():
    doc = copy.deepcopy(provider.EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE)
    doc["non_goals"] = [provider.REQUIRED_ETHICS_NON_GOAL]
    errors = provider.validate_provider_specific_production_package(doc)
    assert_true(any("provider-interface constraint" in e for e in errors), "dropping the provider-interface non-goal should be flagged")


def test_missing_ethics_non_goal_is_rejected():
    doc = copy.deepcopy(provider.EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE)
    doc["non_goals"] = [provider.REQUIRED_INTERFACE_NON_GOAL]
    errors = provider.validate_provider_specific_production_package(doc)
    assert_true(any("ethics constraint" in e for e in errors), "dropping the ethics non-goal should be flagged")


def test_cross_document_validation_passes_against_paired_cinematic():
    errors = provider.validate_against_cinematic_architecture(
        provider.EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE, cinematic.EXAMPLE_CINEMATIC_ARCHITECTURE
    )
    assert_true(errors == [], f"example should cover every shot in its paired cinematic architecture, got: {errors}")


def test_cross_document_validation_catches_missing_shot_coverage():
    doc = copy.deepcopy(provider.EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE)
    doc["video_prompts"][-1]["shot_id"] = doc["video_prompts"][0]["shot_id"]  # duplicate, drops coverage of the last shot
    errors = provider.validate_against_cinematic_architecture(doc, cinematic.EXAMPLE_CINEMATIC_ARCHITECTURE)
    assert_true(any("does not cover every cinematic shot" in e for e in errors), "dropping coverage of a cinematic shot should be flagged")


VOCAL_PERFORMER_FIXTURE = {
    "character_name": "The Builder",
    "register": "low-mid, conversational",
    "texture": "unprocessed, breath and imperfection left in",
    "description": "Sings the way someone talks to themselves before they believe it.",
    "sings_during_shot_ids": ["shot1"],
}


def test_video_prompt_without_vocal_performer_has_no_vocal_direction():
    shot = cinematic.EXAMPLE_CINEMATIC_ARCHITECTURE["shots"][0]
    prompt = provider.translate_shot_to_video_prompt(shot, "kling_ai_avatar")
    assert_true("Vocal performance" not in prompt["prompt_text"], "a shot with no vocal_performer argument should not claim one sings")
    assert_true(not any(f.startswith("vocal_performers.") for f in prompt["source_fields_used"]), "no vocal_performers.* source field should be declared without a vocal_performer argument")


def test_video_prompt_with_vocal_performer_includes_lip_sync_direction():
    shot = cinematic.EXAMPLE_CINEMATIC_ARCHITECTURE["shots"][0]
    prompt = provider.translate_shot_to_video_prompt(shot, "kling_ai_avatar", vocal_performer=VOCAL_PERFORMER_FIXTURE)
    assert_true("The Builder sings on camera" in prompt["prompt_text"], "vocal direction should name the actual performer")
    assert_true("lip-sync" in prompt["prompt_text"].lower(), "a sung shot must explicitly direct lip-sync, or a native audio-driven provider has nothing to animate the mouth to")
    for field in ["vocal_performers.register", "vocal_performers.texture", "vocal_performers.description"]:
        assert_true(field in prompt["source_fields_used"], f"{field} should be declared as a source field when vocal_performer is used")


def test_example_wires_real_vocal_performer_data_not_a_silent_prompt():
    """Regression test for the actual gap this closed: shot1 and shot2 in the
    worked example both have a singing performer per
    character_performance_package.py, and the generated Kling prompt for
    each must actually say so -- sound=true in the API call is not enough
    on its own if the prompt text gives the provider nothing to sing."""
    by_shot = {vp["shot_id"]: vp for vp in provider.EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE["video_prompts"]}
    assert_true("The Builder sings on camera" in by_shot["shot1"]["prompt_text"], "shot1's prompt must direct The Builder's vocal performance")
    assert_true("The Asker sings on camera" in by_shot["shot2"]["prompt_text"], "shot2's prompt must direct The Asker's vocal performance")


if __name__ == "__main__":
    test_example_is_valid()
    test_monte_carlo_probability_is_reasonable()
    test_monte_carlo_is_monotonic_in_budget()
    test_monte_carlo_is_monotonic_in_success_probability()
    test_reproducibility_check_catches_hand_typed_probability()
    test_too_few_trials_is_rejected()
    test_inverted_probability_range_is_rejected()
    test_video_prompt_without_source_fields_is_rejected()
    test_missing_interface_non_goal_is_rejected()
    test_missing_ethics_non_goal_is_rejected()
    test_cross_document_validation_passes_against_paired_cinematic()
    test_cross_document_validation_catches_missing_shot_coverage()
    test_video_prompt_without_vocal_performer_has_no_vocal_direction()
    test_video_prompt_with_vocal_performer_includes_lip_sync_direction()
    test_example_wires_real_vocal_performer_data_not_a_silent_prompt()
    print("PASS: DreamMusicForge Provider-Specific Production Package smoke tests")
