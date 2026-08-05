#!/usr/bin/env python3
"""Smoke tests for the DreamMusicForge Assembly Package schema."""
import copy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "schemas" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


assembly = load("assembly_package", "assembly_package.py")
editorial = load("editorial_architecture", "editorial_architecture.py")
character = load("character_performance_package", "character_performance_package.py")
provider = load("provider_specific_production_package", "provider_specific_production_package.py")


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_example_is_valid():
    errors = assembly.validate_assembly_package(assembly.EXAMPLE_ASSEMBLY_PACKAGE)
    assert_true(errors == [], f"example package should be valid, got: {errors}")


def test_example_flags_the_deliberately_bad_cut_for_manual_review():
    cut7 = next(s for s in assembly.EXAMPLE_ASSEMBLY_PACKAGE["shot_assemblies"] if s["cut_id"] == "cut7")
    assert_true(cut7["reconciliation_strategy"] == "requires_manual_review", "cut7's 39% drift should require manual review")
    assert_true(assembly.EXAMPLE_ASSEMBLY_PACKAGE["assembly_status"] == "blocked_manual_review_required", "one bad cut should block the whole assembly, not be silently absorbed")


def test_reconcile_negligible_drift_is_exact_match():
    strategy, duration = assembly.reconcile_cut_duration(5.0, 5.02, cut_on_beat=True)
    assert_true(strategy == "exact_match" and duration == 5.0, "sub-1% drift should need no reconciliation")


def test_cut1_and_cut2_are_exact_match_after_the_real_generation_replan():
    """Regression test for the actual event this closed: the first two live
    Kling AI Avatar generations both came back at 10.0417s against an
    originally-planned 4.5s/5.0s (>100% drift, would have hit
    requires_manual_review). Rather than force that through reconciliation,
    the Editorial Architecture's plan for cut1/cut2 was replanned to match
    reality -- so reconciling against the *replanned* figures should land
    cleanly on exact_match, proving the plan now reflects what the provider
    actually delivers instead of papering over the drift."""
    by_cut = {s["cut_id"]: s for s in assembly.EXAMPLE_ASSEMBLY_PACKAGE["shot_assemblies"]}
    for cut_id in ("cut1", "cut2"):
        assert_true(by_cut[cut_id]["reconciliation_strategy"] == "exact_match", f"{cut_id} should be exact_match after the replan, got {by_cut[cut_id]['reconciliation_strategy']}")
        assert_true(by_cut[cut_id]["planned_duration_seconds"] == 10.04, f"{cut_id}'s planned duration should reflect the replanned Editorial Architecture, got {by_cut[cut_id]['planned_duration_seconds']}")


def test_reconcile_beat_matched_cut_never_trims_or_pads():
    # 20% drift on a non-beat cut would trim/pad; on a beat-matched cut it must
    # instead require manual review, since trimming/padding breaks cut-on-beat timing.
    strategy, duration = assembly.reconcile_cut_duration(5.0, 6.0, cut_on_beat=True)
    assert_true(strategy == "requires_manual_review", f"beat-matched cut with 20% drift should require manual review, got {strategy}")
    assert_true(duration is None, "requires_manual_review must not report a reconciled duration")


def test_reconcile_non_beat_cut_can_trim_or_pad():
    strategy_over, _ = assembly.reconcile_cut_duration(5.0, 6.0, cut_on_beat=False)
    strategy_under, _ = assembly.reconcile_cut_duration(5.0, 4.2, cut_on_beat=False)
    assert_true(strategy_over == "trim", f"non-beat cut running long within tolerance should trim, got {strategy_over}")
    assert_true(strategy_under == "pad_hold_last_frame", f"non-beat cut running short within tolerance should pad, got {strategy_under}")


def test_reconcile_extreme_drift_always_requires_manual_review():
    strategy, duration = assembly.reconcile_cut_duration(5.0, 15.0, cut_on_beat=False)
    assert_true(strategy == "requires_manual_review", "200% drift should never be auto-reconciled")
    assert_true(duration is None, "requires_manual_review must not report a reconciled duration")


def test_ffmpeg_filter_is_none_for_exact_match_and_manual_review():
    assert_true(assembly.build_ffmpeg_filter("exact_match", 5.0, 5.0) is None, "exact_match needs no filter")
    assert_true(assembly.build_ffmpeg_filter("requires_manual_review", 5.0, 8.0) is None, "requires_manual_review must not produce a filter to apply blindly")


def test_ffmpeg_filter_speed_adjust_has_video_and_audio():
    f = assembly.build_ffmpeg_filter("speed_adjust", 5.0, 5.4)
    assert_true("setpts" in f["video"], "speed_adjust video filter should use setpts")
    assert_true("atempo" in f["audio"], "speed_adjust audio filter should use atempo")


def test_stale_reconciliation_strategy_is_rejected():
    doc = copy.deepcopy(assembly.EXAMPLE_ASSEMBLY_PACKAGE)
    doc["shot_assemblies"][0]["reconciliation_strategy"] = "trim"
    errors = assembly.validate_assembly_package(doc)
    assert_true(any("does not reproduce from planned/actual/cut_on_beat" in e for e in errors), "a hand-typed strategy that doesn't match its own inputs should be flagged")


def test_stale_concat_command_is_rejected():
    doc = copy.deepcopy(assembly.EXAMPLE_ASSEMBLY_PACKAGE)
    doc["concat_command"] = "ffmpeg -i fake.mp4 out.mp4"
    errors = assembly.validate_assembly_package(doc)
    assert_true(any("concat_command does not reproduce" in e for e in errors), "a hand-written concat_command should be flagged")


def test_stale_assembly_status_is_rejected():
    doc = copy.deepcopy(assembly.EXAMPLE_ASSEMBLY_PACKAGE)
    doc["assembly_status"] = "ready_to_render"  # example actually has a manual-review cut
    errors = assembly.validate_assembly_package(doc)
    assert_true(any("assembly_status" in e and "does not reproduce" in e for e in errors), "a stale assembly_status should be flagged")


def test_reconciled_duration_must_be_null_for_manual_review():
    doc = copy.deepcopy(assembly.EXAMPLE_ASSEMBLY_PACKAGE)
    cut7 = next(s for s in doc["shot_assemblies"] if s["cut_id"] == "cut7")
    cut7["reconciled_duration_seconds"] = cut7["planned_duration_seconds"]
    errors = assembly.validate_assembly_package(doc)
    assert_true(any("must be null when reconciliation_strategy is requires_manual_review" in e for e in errors), "a non-null reconciled duration on a manual-review cut should be flagged")


def test_missing_required_assembly_non_goal_is_rejected():
    doc = copy.deepcopy(assembly.EXAMPLE_ASSEMBLY_PACKAGE)
    doc["non_goals"] = [assembly.REQUIRED_ETHICS_NON_GOAL]
    errors = assembly.validate_assembly_package(doc)
    assert_true(any("assembly-honesty constraint" in e for e in errors), "dropping the required assembly non-goal should be flagged")


def test_audio_mix_plan_ducks_under_singing_shots():
    for entry in assembly.EXAMPLE_ASSEMBLY_PACKAGE["audio_mix_plan"]:
        expected = assembly.VOCAL_DUCK_SCORE_VOLUME if entry["vocal_present"] else assembly.INSTRUMENTAL_SCORE_VOLUME
        assert_true(entry["score_volume"] == expected, f"score_volume for {entry['cut_id']} should follow the ducking policy")


def test_cross_document_validation_passes_against_paired_docs():
    editorial_errors = assembly.validate_against_editorial_architecture(assembly.EXAMPLE_ASSEMBLY_PACKAGE, editorial.EXAMPLE_EDITORIAL_ARCHITECTURE)
    character_errors = assembly.validate_against_character_performance_package(assembly.EXAMPLE_ASSEMBLY_PACKAGE, character.EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE)
    native_av_errors = assembly.validate_native_av_requirement(assembly.EXAMPLE_ASSEMBLY_PACKAGE, provider.EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE)
    assert_true(editorial_errors == [], f"example should match its paired editorial cuts, got: {editorial_errors}")
    assert_true(character_errors == [], f"example should match who actually sings where, got: {character_errors}")
    assert_true(native_av_errors == [], f"example should assign only native audio-driven providers to singing shots, got: {native_av_errors}")


def test_native_av_requirement_catches_a_silent_video_provider():
    doc = copy.deepcopy(assembly.EXAMPLE_ASSEMBLY_PACKAGE)
    bad_provider_doc = copy.deepcopy(provider.EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE)
    bad_provider_doc["video_prompts"][0]["provider"] = "pika"  # silent-video-only, not in the allowlist
    errors = assembly.validate_native_av_requirement(doc, bad_provider_doc)
    assert_true(any("is not in native_av_policy.allowed_providers" in e for e in errors), "a silent-video provider on a singing shot should be flagged")


def test_has_singing_performer_mismatch_is_caught():
    doc = copy.deepcopy(assembly.EXAMPLE_ASSEMBLY_PACKAGE)
    doc["shot_assemblies"][0]["has_singing_performer"] = False  # shot1 actually has The Builder singing
    errors = assembly.validate_against_character_performance_package(doc, character.EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE)
    assert_true(len(errors) == 1, "a has_singing_performer flag that contradicts the character package should be flagged")


if __name__ == "__main__":
    test_example_is_valid()
    test_example_flags_the_deliberately_bad_cut_for_manual_review()
    test_cut1_and_cut2_are_exact_match_after_the_real_generation_replan()
    test_reconcile_negligible_drift_is_exact_match()
    test_reconcile_beat_matched_cut_never_trims_or_pads()
    test_reconcile_non_beat_cut_can_trim_or_pad()
    test_reconcile_extreme_drift_always_requires_manual_review()
    test_ffmpeg_filter_is_none_for_exact_match_and_manual_review()
    test_ffmpeg_filter_speed_adjust_has_video_and_audio()
    test_stale_reconciliation_strategy_is_rejected()
    test_stale_concat_command_is_rejected()
    test_stale_assembly_status_is_rejected()
    test_reconciled_duration_must_be_null_for_manual_review()
    test_missing_required_assembly_non_goal_is_rejected()
    test_audio_mix_plan_ducks_under_singing_shots()
    test_cross_document_validation_passes_against_paired_docs()
    test_native_av_requirement_catches_a_silent_video_provider()
    test_has_singing_performer_mismatch_is_caught()
    print("PASS: DreamMusicForge Assembly Package smoke tests")
