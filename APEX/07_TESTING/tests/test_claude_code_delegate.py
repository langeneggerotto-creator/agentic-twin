#!/usr/bin/env python3
"""Smoke tests for runner.claude_code_delegate's contract-to-prompt/options
wiring. Does not call the Anthropic API -- only exercises the pure functions."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.claude_code_delegate import build_options, build_prompt

CAMERA_CONTRACT = {
    "goal": "Repair the camera service startup failure",
    "allowed_paths": ["src/camera/**", "tests/camera/**"],
    "allowed_commands": ["pytest tests/camera"],
    "forbidden_actions": ["install_system_packages"],
    "acceptance_criteria": ["All camera tests pass"],
}


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_prompt_states_the_contract():
    prompt = build_prompt(CAMERA_CONTRACT)
    assert_true("Repair the camera service startup failure" in prompt, "prompt must state the goal")
    assert_true("src/camera/**" in prompt, "prompt must state allowed paths")
    assert_true("pytest tests/camera" in prompt, "prompt must state allowed commands")
    assert_true("install_system_packages" in prompt, "prompt must state forbidden actions")


def test_options_are_locked_down():
    options = build_options(CAMERA_CONTRACT)
    assert_true(options.permission_mode == "dontAsk",
                "unattended runs must deny anything not pre-approved, never prompt")
    assert_true(str(options.cwd) == str(ROOT), "session must be scoped to the repo root")
    assert_true("Edit(src/camera/**)" in options.allowed_tools, "allowed_paths must become Edit() rules")
    assert_true("Bash(pytest tests/camera)" in options.allowed_tools, "allowed_commands must become Bash() rules")
    assert_true("Bash" not in options.allowed_tools,
                "must never grant bare Bash -- only scoped Bash(...) rules from the contract")
    assert_true("Edit" not in options.allowed_tools,
                "must never grant bare Edit -- only scoped Edit(...) rules from the contract")


def test_options_default_to_zero_commands_and_paths_when_contract_is_empty():
    options = build_options({"goal": "no-op"})
    assert_true(options.allowed_tools == ["Read", "Glob", "Grep"],
                "an empty contract must grant no write or execute access")


if __name__ == "__main__":
    test_prompt_states_the_contract()
    test_options_are_locked_down()
    test_options_default_to_zero_commands_and_paths_when_contract_is_empty()
    print("PASS: claude_code_delegate smoke tests")
