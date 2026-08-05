#!/usr/bin/env python3
"""Smoke tests for the DreamMusicForge Principle Kernel schema (pipeline stage 1)."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "schemas" / "principle_kernel.py"

spec = importlib.util.spec_from_file_location("principle_kernel", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_example_kernel_is_valid():
    errors = module.validate_principle_kernel(module.EXAMPLE_PRINCIPLE_KERNEL)
    assert_true(errors == [], f"example kernel should be valid, got: {errors}")


def test_missing_kernel_statement_is_rejected():
    kernel = dict(module.EXAMPLE_PRINCIPLE_KERNEL)
    del kernel["kernel_statement"]
    errors = module.validate_principle_kernel(kernel)
    assert_true(any("kernel_statement" in e for e in errors), "missing kernel_statement should be flagged")


def test_missing_required_ethics_non_goal_is_rejected():
    kernel = dict(module.EXAMPLE_PRINCIPLE_KERNEL)
    kernel["non_goals"] = ["some other non-goal"]
    errors = module.validate_principle_kernel(kernel)
    assert_true(any("ethics constraint" in e for e in errors), "dropping the required ethics non-goal should be flagged")


def test_human_truths_require_before_and_after_state():
    kernel = dict(module.EXAMPLE_PRINCIPLE_KERNEL)
    kernel["human_truths"] = [{"human_truth_id": "x", "description": "y", "confidence": "ASSUMED"}]
    errors = module.validate_principle_kernel(kernel)
    assert_true(any("before_state" in e for e in errors), "missing before_state should be flagged")
    assert_true(any("after_state" in e for e in errors), "missing after_state should be flagged")


def test_invalid_truth_status_is_rejected():
    kernel = dict(module.EXAMPLE_PRINCIPLE_KERNEL)
    kernel["truth_status"] = "DEFINITELY"
    errors = module.validate_principle_kernel(kernel)
    assert_true(any("truth_status" in e for e in errors), "invalid truth_status should be flagged")


if __name__ == "__main__":
    test_example_kernel_is_valid()
    test_missing_kernel_statement_is_rejected()
    test_missing_required_ethics_non_goal_is_rejected()
    test_human_truths_require_before_and_after_state()
    test_invalid_truth_status_is_rejected()
    print("PASS: DreamMusicForge Principle Kernel smoke tests")
