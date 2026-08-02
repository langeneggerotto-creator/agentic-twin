"""Manual-run only. Delegates a scoped coding task to Claude Code via the
Claude Agent SDK, then runs the result through governance.gatekeeper.enforce_contract.

Requires ANTHROPIC_API_KEY to be set and `pip install claude-agent-sdk`.
Not wired into runner/controller.py or CI: every run makes real, billed API
calls, so it only runs when you invoke it yourself.

Usage:
    python3 runner/claude_code_delegate.py path/to/contract.json
"""
import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from governance.gatekeeper import enforce_contract

FILE_WRITE_TOOLS = {"Edit", "Write", "NotebookEdit"}


def build_prompt(contract: dict) -> str:
    lines = [
        f"Goal: {contract['goal']}",
        "",
        "You are operating under a delegation contract. Stay strictly within it:",
        f"- Only touch files matching: {', '.join(contract.get('allowed_paths', [])) or '(none allowed)'}",
        f"- Only run commands matching: {', '.join(contract.get('allowed_commands', [])) or '(none allowed)'}",
        f"- Never perform: {', '.join(contract.get('forbidden_actions', [])) or '(n/a)'}",
        "",
        "Acceptance criteria:",
    ]
    lines += [f"- {c}" for c in contract.get("acceptance_criteria", [])]
    return "\n".join(lines)


def build_options(contract: dict) -> ClaudeAgentOptions:
    allowed = ["Read", "Glob", "Grep"]
    allowed += [f"Edit({p})" for p in contract.get("allowed_paths", [])]
    allowed += [f"Bash({c})" for c in contract.get("allowed_commands", [])]

    return ClaudeAgentOptions(
        cwd=str(REPO_ROOT),
        allowed_tools=allowed,
        # dontAsk: anything not covered by allowed_tools is denied outright,
        # never prompted -- required for an unattended/headless run.
        permission_mode="dontAsk",
        max_turns=contract.get("max_turns", 30),
    )


def git_changed_files(repo_root: Path) -> dict:
    """Returns {path: status} where status is 'modified' or 'untracked'."""
    out = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root, capture_output=True, text=True, check=True,
    )
    changed = {}
    for line in out.stdout.splitlines():
        code, path = line[:2], line[3:].strip()
        changed[path] = "untracked" if code.strip() == "??" else "modified"
    return changed


def rollback(repo_root: Path, changed: dict) -> None:
    for path, status in changed.items():
        if status == "untracked":
            subprocess.run(["git", "clean", "-f", "--", path], cwd=repo_root, check=False)
        else:
            subprocess.run(["git", "checkout", "--", path], cwd=repo_root, check=False)


async def run_delegate(contract: dict) -> dict:
    prompt = build_prompt(contract)
    options = build_options(contract)

    commands_run = []
    declared_write_paths = set()
    transcript = []
    result_message = None

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    transcript.append(block.text)
                elif isinstance(block, ToolUseBlock):
                    if block.name == "Bash":
                        cmd = block.input.get("command", "")
                        if cmd:
                            commands_run.append(cmd)
                    elif block.name in FILE_WRITE_TOOLS:
                        path = block.input.get("file_path")
                        if path:
                            declared_write_paths.add(path)
        elif isinstance(message, ResultMessage):
            result_message = message

    # Never trust the model's own account of what it touched -- verify against git.
    changed = git_changed_files(REPO_ROOT)

    test_results = ""
    if any("pytest" in c or "test" in c for c in commands_run):
        test_results = "\n".join(transcript)

    gate = enforce_contract(
        contract,
        changed_files=sorted(changed),
        commands_run=commands_run,
        test_results=test_results,
    )

    if not gate["passed"]:
        rollback(REPO_ROOT, changed)

    return {
        "gate": gate,
        "rolled_back": not gate["passed"],
        "changed_files_declared_by_model": sorted(declared_write_paths),
        "changed_files_verified_by_git": sorted(changed),
        "commands_run": commands_run,
        "session_id": getattr(result_message, "session_id", None),
        "cost_usd": getattr(result_message, "total_cost_usd", None),
        "subtype": getattr(result_message, "subtype", None),
        "is_error": getattr(result_message, "is_error", None),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path, help="Path to a JSON delegation contract")
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text())
    outcome = asyncio.run(run_delegate(contract))

    print(json.dumps(outcome, indent=2))
    if not outcome["gate"]["passed"]:
        print("GATE FAILED -- changes rolled back:", outcome["gate"]["violations"], file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
