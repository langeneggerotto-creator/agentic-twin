#!/usr/bin/env python3
"""Smoke tests for governance.gatekeeper.enforce_contract, the OCode-style
delegation-contract execution gate."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from governance.gatekeeper import enforce_contract

CAMERA_CONTRACT = {
    "goal": "Repair the camera service startup failure",
    "allowed_paths": ["src/camera/**", "tests/camera/**"],
    "allowed_commands": ["pytest tests/camera", "python -m compileall src/camera"],
    "forbidden_actions": [
        "install_system_packages",
        "modify_credentials",
        "deploy_to_production",
        "operate_physical_actuators",
    ],
    "acceptance_criteria": [
        "All camera tests pass",
        "No files outside the allowed paths change",
    ],
    "requires_human_approval": ["production_deployment", "hardware_control"],
}


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_compliant_change_passes():
    result = enforce_contract(
        CAMERA_CONTRACT,
        changed_files=["src/camera/driver.py", "tests/camera/test_driver.py"],
        commands_run=["pytest tests/camera"],
        test_results="test_startup: PASS",
    )
    assert_true(result["passed"], f"expected compliant change to pass, got {result['violations']}")
    assert_true(result["violations"] == [], "compliant change must have no violations")


def test_file_outside_allowed_paths_is_rejected():
    result = enforce_contract(
        CAMERA_CONTRACT,
        changed_files=["src/camera/driver.py", "src/robotics/actuator.py"],
        commands_run=["pytest tests/camera"],
        test_results="test_startup: PASS",
    )
    assert_true(not result["passed"], "change touching a file outside allowed_paths must fail")
    assert_true(any("src/robotics/actuator.py" in v for v in result["violations"]),
                "violation must name the out-of-scope file")


def test_command_outside_allowed_commands_is_rejected():
    result = enforce_contract(
        CAMERA_CONTRACT,
        changed_files=["src/camera/driver.py"],
        commands_run=["rm -rf /"],
        test_results="",
    )
    assert_true(not result["passed"], "an unlisted command must fail the gate")


def test_heuristic_detects_undeclared_forbidden_action():
    result = enforce_contract(
        CAMERA_CONTRACT,
        changed_files=["src/camera/driver.py"],
        commands_run=["sudo apt-get install libcamera-dev"],
    )
    assert_true(not result["passed"], "sudo apt-get install must be caught even if not declared")
    assert_true(any("install_system_packages" in v for v in result["violations"]),
                "violation must identify install_system_packages")


def test_declared_forbidden_action_is_rejected_without_a_matching_command():
    result = enforce_contract(
        CAMERA_CONTRACT,
        changed_files=["src/camera/driver.py"],
        commands_run=["pytest tests/camera"],
        test_results="test_startup: PASS",
        declared_actions=["operate_physical_actuators"],
    )
    assert_true(not result["passed"], "a declared forbidden action must fail the gate on its own")


def test_failing_tests_are_rejected():
    result = enforce_contract(
        CAMERA_CONTRACT,
        changed_files=["src/camera/driver.py"],
        commands_run=["pytest tests/camera"],
        test_results="test_startup: FAIL",
    )
    assert_true(not result["passed"], "reported test failures must fail the gate")


def test_requires_human_approval_is_echoed_back():
    result = enforce_contract(CAMERA_CONTRACT, changed_files=[], commands_run=[])
    assert_true(result["requires_human_approval"] == sorted(["production_deployment", "hardware_control"]),
                "gate must surface the contract's human-approval requirements to the caller")


DEPLOY_CONTRACT = {
    "goal": "Deploy the hotfix once the camera driver is patched",
    "allowed_paths": ["src/camera/**"],
    "allowed_commands": ["kubectl apply -f k8s/hotfix.yaml"],
    "forbidden_actions": [],
    "requires_human_approval": ["production_deployment"],
}


def test_observed_approval_gated_action_blocks_without_a_grant():
    result = enforce_contract(
        DEPLOY_CONTRACT,
        changed_files=["src/camera/driver.py"],
        commands_run=["kubectl apply -f k8s/hotfix.yaml"],
    )
    assert_true(not result["passed"], "a production_deployment action must block without an explicit human approval")
    assert_true(result["pending_approval"] == ["production_deployment"],
                "pending_approval must name the exact action awaiting a human decision")


def test_approved_action_unblocks_the_gate():
    result = enforce_contract(
        DEPLOY_CONTRACT,
        changed_files=["src/camera/driver.py"],
        commands_run=["kubectl apply -f k8s/hotfix.yaml"],
        approved_actions=["production_deployment"],
    )
    assert_true(result["passed"], f"an explicitly approved action must unblock the gate, got {result['violations']}")
    assert_true(result["pending_approval"] == [], "no action should remain pending once approved")


def test_approval_for_an_action_not_actually_observed_is_a_no_op():
    result = enforce_contract(
        CAMERA_CONTRACT,
        changed_files=["src/camera/driver.py"],
        commands_run=["pytest tests/camera"],
        test_results="test_startup: PASS",
        approved_actions=["production_deployment"],
    )
    assert_true(result["passed"], "an unused approval must not itself cause a failure")
    assert_true(result["pending_approval"] == [], "nothing is pending when the gated action never happened")


if __name__ == "__main__":
    test_compliant_change_passes()
    test_file_outside_allowed_paths_is_rejected()
    test_command_outside_allowed_commands_is_rejected()
    test_heuristic_detects_undeclared_forbidden_action()
    test_declared_forbidden_action_is_rejected_without_a_matching_command()
    test_failing_tests_are_rejected()
    test_requires_human_approval_is_echoed_back()
    test_observed_approval_gated_action_blocks_without_a_grant()
    test_approved_action_unblocks_the_gate()
    test_approval_for_an_action_not_actually_observed_is_a_no_op()
    print("PASS: enforce_contract smoke tests")
