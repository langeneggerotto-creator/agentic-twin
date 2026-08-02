#!/usr/bin/env python3
"""Integration tests for runner.claude_code_delegate.run_delegate() -- the
actual execution path (message loop, git diff detection, gate, rollback,
evidence recording), not just its pure helper functions.

This was the real gap in test coverage: build_prompt()/build_options() were
tested, but run_delegate() itself never was, because doing so normally
needs a real ANTHROPIC_API_KEY. Instead of an API key, this scripts the
Claude Agent SDK's message stream using the SDK's own real dataclasses
(so the test is honest about their shape) via ScriptedSDK below, and runs
everything else for real: a real isolated git repo (never the actual
agentic-twin working tree -- see repo_root threading in
claude_code_delegate.py), real `git status`/`git checkout`/`git clean`,
real governance.gatekeeper.enforce_contract, and a real (temp) evidence
ledger.
"""
import asyncio
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock, ToolResultBlock, ToolUseBlock, UserMessage

from governance.evidence_ledger import read_ledger
from runner.claude_code_delegate import run_delegate


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


def make_result_message(session_id="sess_test", total_cost_usd=0.10, is_error=False, subtype="success"):
    return ResultMessage(
        subtype=subtype, duration_ms=1200, duration_api_ms=900, is_error=is_error,
        num_turns=2, session_id=session_id, total_cost_usd=total_cost_usd,
    )


class ScriptedSDK:
    """Builds a fake claude_agent_sdk.query() replacement that yields a
    scripted message sequence -- and, critically, actually performs the
    same filesystem/command side effects a real Claude Code session's
    tools would have. run_delegate() verifies against real git state and
    real command output, not against the message stream, so a mock that
    only yields messages without touching disk would test nothing real."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self._tool_use_blocks = []
        self._tool_results = []  # (tool_use_id, output, is_error)
        self._next_id = 0

    def _new_id(self) -> str:
        self._next_id += 1
        return f"toolu_{self._next_id}"

    def write_file(self, relative_path: str, content: str) -> "ScriptedSDK":
        target = self.repo_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        self._tool_use_blocks.append(ToolUseBlock(id=self._new_id(), name="Edit", input={"file_path": relative_path}))
        return self

    def run_command(self, command: str, output: str = "", is_error: bool = False) -> "ScriptedSDK":
        tool_id = self._new_id()
        self._tool_use_blocks.append(ToolUseBlock(id=tool_id, name="Bash", input={"command": command}))
        self._tool_results.append((tool_id, output, is_error))
        return self

    def build(self, result_message: ResultMessage):
        blocks = list(self._tool_use_blocks)
        tool_results = list(self._tool_results)

        async def fake_query(prompt, options):
            yield AssistantMessage(content=blocks, model="claude-opus-5")
            if tool_results:
                result_blocks = [
                    ToolResultBlock(tool_use_id=tid, content=out, is_error=err)
                    for tid, out, err in tool_results
                ]
                yield UserMessage(content=result_blocks)
            yield AssistantMessage(content=[TextBlock(text="Done.")], model="claude-opus-5")
            yield result_message

        return fake_query


def test_compliant_run_passes_gate_and_survives():
    repo = make_temp_repo()
    ledger_path = str(repo / "evidence_ledger.jsonl")
    contract = {
        "goal": "Repair the camera driver crash",
        "allowed_paths": ["src/camera/**"],
        "allowed_commands": ["pytest tests/camera"],
        "acceptance_criteria": ["All camera tests pass"],
    }
    sdk = ScriptedSDK(repo)
    sdk.write_file("src/camera/driver.py", "def fixed(): return True\n")
    sdk.run_command("pytest tests/camera", output="1 passed", is_error=False)

    with mock.patch("runner.claude_code_delegate.query", new=sdk.build(make_result_message())):
        outcome = asyncio.run(run_delegate(contract, repo_root=repo, evidence_ledger_path=ledger_path))

    assert_true(outcome["gate"]["passed"], f"a compliant scripted run must pass the real gate: {outcome['gate']['violations']}")
    assert_true(not outcome["rolled_back"], "a passing run must not roll back")
    assert_true((repo / "src/camera/driver.py").exists(), "the compliant change must survive on disk")

    ledger = read_ledger(ledger_path)
    assert_true(len(ledger) == 1 and ledger[0]["gate_passed"] is True, "evidence must record the real outcome")


def test_scope_violation_fails_and_actually_rolls_back():
    repo = make_temp_repo()
    ledger_path = str(repo / "evidence_ledger.jsonl")
    contract = {
        "goal": "Repair the camera driver crash",
        "allowed_paths": ["src/camera/**"],
        "allowed_commands": ["pytest tests/camera"],
    }
    sdk = ScriptedSDK(repo)
    sdk.write_file("src/robotics/actuator.py", "# out of scope\n")  # NOT in allowed_paths
    sdk.run_command("pytest tests/camera", output="1 passed")

    with mock.patch("runner.claude_code_delegate.query", new=sdk.build(make_result_message())):
        outcome = asyncio.run(run_delegate(contract, repo_root=repo, evidence_ledger_path=ledger_path))

    assert_true(not outcome["gate"]["passed"], "an out-of-scope write must fail the gate")
    assert_true(outcome["rolled_back"], "a failed gate must trigger rollback")
    assert_true(not (repo / "src/robotics/actuator.py").exists(),
                "the out-of-scope file must actually be gone from disk, not just flagged")


def test_budget_overrun_fails_even_when_otherwise_compliant():
    repo = make_temp_repo()
    ledger_path = str(repo / "evidence_ledger.jsonl")
    contract = {
        "goal": "Repair the camera driver crash",
        "allowed_paths": ["src/camera/**"],
        "allowed_commands": ["pytest tests/camera"],
        "max_budget_usd": 1.00,
    }
    sdk = ScriptedSDK(repo)
    sdk.write_file("src/camera/driver.py", "def fixed(): return True\n")
    sdk.run_command("pytest tests/camera", output="1 passed")

    with mock.patch("runner.claude_code_delegate.query", new=sdk.build(make_result_message(total_cost_usd=5.00))):
        outcome = asyncio.run(run_delegate(contract, repo_root=repo, evidence_ledger_path=ledger_path))

    assert_true(not outcome["gate"]["passed"], "reported cost over the cap must fail the gate")
    assert_true(any("cost exceeded budget" in v for v in outcome["gate"]["violations"]),
                "violation must explain it was a budget overrun")
    assert_true(outcome["rolled_back"], "a budget failure must still roll back the otherwise-compliant change")


def test_gated_action_blocks_without_a_prior_approval():
    repo = make_temp_repo()
    ledger_path = str(repo / "evidence_ledger.jsonl")
    contract = {
        "goal": "Deploy the hotfix",
        "allowed_paths": ["src/**"],
        "allowed_commands": ["kubectl apply -f k8s/hotfix.yaml"],
        "requires_human_approval": ["production_deployment"],
    }
    sdk = ScriptedSDK(repo)
    sdk.write_file("src/app.py", "# hotfix\n")
    sdk.run_command("kubectl apply -f k8s/hotfix.yaml", output="deployed")

    with mock.patch("runner.claude_code_delegate.query", new=sdk.build(make_result_message())):
        outcome = asyncio.run(run_delegate(contract, repo_root=repo, evidence_ledger_path=ledger_path))

    assert_true(not outcome["gate"]["passed"], "a production_deployment action must block without a granted approval")
    assert_true(outcome["gate"]["pending_approval"] == ["production_deployment"],
                "pending_approval must name the exact action awaiting a decision")
    assert_true(outcome["rolled_back"], "an unapproved gated action must roll back like any other gate failure")


def test_real_test_failure_output_is_what_fails_the_gate_not_narration():
    repo = make_temp_repo()
    ledger_path = str(repo / "evidence_ledger.jsonl")
    contract = {
        "goal": "Repair the camera driver crash",
        "allowed_paths": ["src/camera/**"],
        "allowed_commands": ["pytest tests/camera"],
    }
    sdk = ScriptedSDK(repo)
    sdk.write_file("src/camera/driver.py", "def broken(): raise RuntimeError\n")
    # Real captured stdout says FAIL; the assistant's own text claims success --
    # the gate must trust the captured tool output, not the narration.
    sdk.run_command("pytest tests/camera", output="1 failed, 0 passed  FAIL", is_error=True)

    with mock.patch("runner.claude_code_delegate.query", new=sdk.build(make_result_message())):
        outcome = asyncio.run(run_delegate(contract, repo_root=repo, evidence_ledger_path=ledger_path))

    assert_true(not outcome["gate"]["passed"], "real failing test output must fail the gate")
    assert_true(outcome["rolled_back"], "a failing test run must roll back")


if __name__ == "__main__":
    test_compliant_run_passes_gate_and_survives()
    test_scope_violation_fails_and_actually_rolls_back()
    test_budget_overrun_fails_even_when_otherwise_compliant()
    test_gated_action_blocks_without_a_prior_approval()
    test_real_test_failure_output_is_what_fails_the_gate_not_narration()
    print("PASS: claude_code_delegate integration tests (scripted SDK, real git, real gate)")
