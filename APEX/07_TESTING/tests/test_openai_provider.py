#!/usr/bin/env python3
"""Smoke tests for runner.providers.openai_provider's pure functions -- the
pre-execution scope checks and prompt construction. Does not call the
OpenAI API."""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.providers import openai_provider

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
    prompt = openai_provider.build_prompt(CAMERA_CONTRACT)
    assert_true("Repair the camera service startup failure" in prompt, "prompt must state the goal")
    assert_true("src/camera/**" in prompt, "prompt must state allowed paths")
    assert_true("pytest tests/camera" in prompt, "prompt must state allowed commands")


def test_write_outside_allowed_paths_is_denied_before_it_happens():
    with tempfile.TemporaryDirectory() as tmp:
        original_root = openai_provider.REPO_ROOT
        openai_provider.REPO_ROOT = Path(tmp)
        try:
            target = Path(tmp) / "src" / "robotics" / "actuator.py"
            output, is_error = openai_provider.execute_tool(
                "write_file", {"path": "src/robotics/actuator.py", "content": "x = 1"}, CAMERA_CONTRACT,
            )
            assert_true(is_error, "a write outside allowed_paths must be denied, not attempted")
            assert_true("denied" in output, "denial reason must be reported back to the model")
            assert_true(not target.exists(), "the out-of-scope file must never actually be written")
        finally:
            openai_provider.REPO_ROOT = original_root


def test_write_inside_allowed_paths_succeeds():
    with tempfile.TemporaryDirectory() as tmp:
        original_root = openai_provider.REPO_ROOT
        openai_provider.REPO_ROOT = Path(tmp)
        try:
            output, is_error = openai_provider.execute_tool(
                "write_file", {"path": "src/camera/driver.py", "content": "x = 1"}, CAMERA_CONTRACT,
            )
            assert_true(not is_error, f"a write inside allowed_paths must succeed, got: {output}")
            assert_true((Path(tmp) / "src" / "camera" / "driver.py").read_text() == "x = 1",
                        "the file must actually contain what was written")
        finally:
            openai_provider.REPO_ROOT = original_root


def test_command_outside_allowed_commands_is_denied_before_it_runs():
    output, is_error = openai_provider.execute_tool("run_command", {"command": "rm -rf /"}, CAMERA_CONTRACT)
    assert_true(is_error, "an unlisted command must be denied, not executed")
    assert_true("denied" in output, "denial reason must be reported back to the model")


def test_command_inside_allowed_commands_actually_runs():
    output, is_error = openai_provider.execute_tool(
        "run_command", {"command": "pytest tests/camera --version"}, CAMERA_CONTRACT,
    )
    # Not asserting on pytest's actual output (may or may not be installed in
    # this env) -- only that it was allowed to attempt execution at all,
    # unlike the denied case above which never reaches subprocess.run.
    assert_true("denied" not in output, "an allowed command must actually be attempted, not denied")


if __name__ == "__main__":
    test_prompt_states_the_contract()
    test_write_outside_allowed_paths_is_denied_before_it_happens()
    test_write_inside_allowed_paths_succeeds()
    test_command_outside_allowed_commands_is_denied_before_it_runs()
    test_command_inside_allowed_commands_actually_runs()
    print("PASS: openai_provider smoke tests")
