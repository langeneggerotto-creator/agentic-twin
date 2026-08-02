#!/usr/bin/env python3
"""Integration tests for runner.providers.openai_provider.run_delegate() --
the actual execution path, not just execute_tool()'s pure denial logic
(already covered by test_openai_provider.py). Scripts a fake OpenAI client
(no OPENAI_API_KEY needed) but lets execute_tool() really touch disk and
really run allowed shell commands, against a real isolated temp git repo --
never the actual agentic-twin working tree.
"""
import asyncio
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from governance.evidence_ledger import read_ledger
from runner.providers.openai_provider import run_delegate


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def make_temp_repo() -> Path:
    tmp = Path(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.local"], cwd=tmp, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp, check=True)
    (tmp / "README.md").write_text("init\n")
    subprocess.run(["git", "add", "."], cwd=tmp, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp, check=True)
    return tmp


def make_tool_call(call_id: str, name: str, arguments: dict):
    return SimpleNamespace(id=call_id, function=SimpleNamespace(name=name, arguments=json.dumps(arguments)))


def make_response(content=None, tool_calls=None, total_tokens=100):
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=SimpleNamespace(total_tokens=total_tokens))


class FakeOpenAIClient:
    """Returns a fixed sequence of chat.completions.create() responses,
    shaped like the real SDK's return value (verified field names:
    choices[0].message.{content,tool_calls}, tool_calls[i].{id,function},
    function.{name,arguments}, usage.total_tokens)."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        return self._responses.pop(0)


def test_compliant_run_passes_gate_and_survives():
    repo = make_temp_repo()
    ledger_path = str(repo / "evidence_ledger.jsonl")
    contract = {
        "goal": "Repair the camera driver crash",
        "allowed_paths": ["src/camera/**"],
        "allowed_commands": ["echo test_passed"],
    }
    client = FakeOpenAIClient([
        make_response(tool_calls=[
            make_tool_call("call_1", "write_file", {"path": "src/camera/driver.py", "content": "fixed = True\n"}),
            make_tool_call("call_2", "run_command", {"command": "echo test_passed"}),
        ]),
        make_response(content="Done."),
    ])

    outcome = asyncio.run(run_delegate(contract, repo_root=repo, evidence_ledger_path=ledger_path, client=client))

    assert_true(outcome["gate"]["passed"], f"a compliant scripted run must pass the real gate: {outcome['gate']['violations']}")
    assert_true(not outcome["rolled_back"], "a passing run must not roll back")
    assert_true((repo / "src/camera/driver.py").exists(),
                "the compliant change (in a brand-new untracked directory) must be detected and survive")

    ledger = read_ledger(ledger_path)
    assert_true(len(ledger) == 1 and ledger[0]["gate_passed"] is True, "evidence must record the real outcome")


def test_out_of_scope_write_is_denied_before_execution():
    repo = make_temp_repo()
    ledger_path = str(repo / "evidence_ledger.jsonl")
    contract = {
        "goal": "Repair the camera driver crash",
        "allowed_paths": ["src/camera/**"],
        "allowed_commands": ["echo test_passed"],
    }
    client = FakeOpenAIClient([
        make_response(tool_calls=[
            make_tool_call("call_1", "write_file", {"path": "src/robotics/actuator.py", "content": "# nope\n"}),
        ]),
        make_response(content="Done."),
    ])

    outcome = asyncio.run(run_delegate(contract, repo_root=repo, evidence_ledger_path=ledger_path, client=client))

    assert_true(not (repo / "src/robotics/actuator.py").exists(),
                "execute_tool must deny the write before it ever touches disk")
    # Nothing actually changed (the write never happened, and unlike
    # run_command there's no "attempted but denied" record for file writes),
    # so the gate correctly finds no violation -- denial prevented harm,
    # which is success, not a false-negative gate.
    assert_true(outcome["gate"]["passed"],
                "a fully-denied write with no other action must pass the gate: nothing in scope actually changed")
    assert_true(outcome["changed_files_verified_by_git"] == [], "git must confirm nothing changed")


def test_denied_command_is_never_actually_run_and_gate_fails_too():
    repo = make_temp_repo()
    ledger_path = str(repo / "evidence_ledger.jsonl")
    marker = repo / "should_not_exist.txt"
    contract = {
        "goal": "Repair the camera driver crash",
        "allowed_paths": ["src/camera/**"],
        "allowed_commands": ["echo test_passed"],
    }
    client = FakeOpenAIClient([
        make_response(tool_calls=[
            make_tool_call("call_1", "run_command", {"command": f"touch {marker.name}"}),
        ]),
        make_response(content="Done."),
    ])

    outcome = asyncio.run(run_delegate(contract, repo_root=repo, evidence_ledger_path=ledger_path, client=client))

    assert_true(not marker.exists(), "a command outside allowed_commands must never actually execute")
    assert_true(not outcome["gate"]["passed"], "the gate must also independently reject the out-of-scope command")


if __name__ == "__main__":
    test_compliant_run_passes_gate_and_survives()
    test_out_of_scope_write_is_denied_before_execution()
    test_denied_command_is_never_actually_run_and_gate_fails_too()
    print("PASS: openai_provider integration tests (scripted client, real git, real gate)")
