#!/usr/bin/env python3
"""Smoke tests for agents.dream_builder -- turning a raw goal into a
governed OCode contract, and that contract round-tripping through the real
enforce_contract gate."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.dream_builder import ALWAYS_FORBIDDEN_ACTIONS, build_dream
from governance.gatekeeper import enforce_contract


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_plain_dream_needs_no_approval():
    dream = build_dream("Repair the camera driver crash", ["src/camera/**"], ["pytest tests/camera"])
    assert_true(dream["requires_human_approval"] == [], "an ordinary dream must not require approval")


def test_deployment_language_triggers_approval():
    dream = build_dream(
        "Deploy the fixed camera service to production",
        ["src/camera/**"], ["kubectl apply -f k8s/camera.yaml"],
    )
    assert_true(dream["requires_human_approval"] == ["production_deployment"],
                "the word 'deploy'/'production' must auto-add the production_deployment approval tag")


def test_hardware_language_triggers_approval():
    dream = build_dream("Adjust the servo motor calibration", ["src/robot/**"], ["python calibrate.py"])
    assert_true(dream["requires_human_approval"] == ["hardware_control"],
                "hardware keywords must auto-add the hardware_control approval tag")


def test_forbidden_actions_always_present():
    dream = build_dream("Anything at all", ["src/**"], ["echo hi"])
    for action in ALWAYS_FORBIDDEN_ACTIONS:
        assert_true(action in dream["forbidden_actions"], f"{action} must always be forbidden by default")


def test_scope_is_never_inferred_only_explicit():
    dream = build_dream("Fix everything everywhere", ["src/camera/**"], ["pytest tests/camera"])
    assert_true(dream["allowed_paths"] == ["src/camera/**"],
                "allowed_paths must come only from the explicit argument, never from the description")


def test_dream_passes_the_real_gate_when_executed_compliantly():
    dream = build_dream("Repair the camera driver crash", ["src/camera/**"], ["pytest tests/camera"])
    gate = enforce_contract(
        dream,
        changed_files=["src/camera/driver.py"],
        commands_run=["pytest tests/camera"],
        test_results="test_startup: PASS",
    )
    assert_true(gate["passed"], f"a compliant execution of a built dream must pass the real gate, got {gate['violations']}")


def test_dream_fails_the_real_gate_when_scope_is_violated():
    dream = build_dream("Repair the camera driver crash", ["src/camera/**"], ["pytest tests/camera"])
    gate = enforce_contract(
        dream,
        changed_files=["src/camera/driver.py", "src/robotics/actuator.py"],
        commands_run=["pytest tests/camera"],
        test_results="test_startup: PASS",
    )
    assert_true(not gate["passed"], "the built contract's scope must actually be enforced, not just decorative")


if __name__ == "__main__":
    test_plain_dream_needs_no_approval()
    test_deployment_language_triggers_approval()
    test_hardware_language_triggers_approval()
    test_forbidden_actions_always_present()
    test_scope_is_never_inferred_only_explicit()
    test_dream_passes_the_real_gate_when_executed_compliantly()
    test_dream_fails_the_real_gate_when_scope_is_violated()
    print("PASS: dream_builder smoke tests")
