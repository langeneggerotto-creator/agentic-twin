"""Manual-run only. Delegates a scoped coding task to OpenAI via function
calling, gated by the same governance.gatekeeper.enforce_contract used for
the Claude Code provider -- proof the execution gate is provider-agnostic,
not built around any one model's own scaffolding.

Requires OPENAI_API_KEY to be set and `pip install openai`. Not wired into
any CI workflow: every run makes real, billed API calls.

Unlike the Claude Agent SDK, plain chat completions has no built-in
permission system: every tool call here is checked against the contract's
allowed_paths/allowed_commands BEFORE it runs, not just verified after via
git status. Post-hoc independent verification (git diff, real command
output, the gate itself) still applies on top, same as the Claude Code
provider -- pre-execution checks reduce blast radius, they don't replace
the gate.
"""
import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path

from openai import OpenAI

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from governance.approvals import approved_actions_for
from governance.evidence_ledger import record_evidence
from governance.gatekeeper import command_allowed, enforce_contract, path_allowed

PROVIDER_NAME = "openai"
DEFAULT_MODEL = "gpt-4.1"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file's contents, relative to the repository root.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Overwrite a file with new contents, relative to the repository root.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command in the repository root.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    },
]


def build_prompt(contract: dict) -> str:
    lines = [
        f"Goal: {contract['goal']}",
        "",
        "You are operating under a delegation contract, enforced both by which tool",
        "calls succeed and by an independent review after you finish. Stay strictly within it:",
        f"- Only touch files matching: {', '.join(contract.get('allowed_paths', [])) or '(none allowed)'}",
        f"- Only run commands matching: {', '.join(contract.get('allowed_commands', [])) or '(none allowed)'}",
        f"- Never perform: {', '.join(contract.get('forbidden_actions', [])) or '(n/a)'}",
        "",
        "Acceptance criteria:",
    ]
    lines += [f"- {c}" for c in contract.get("acceptance_criteria", [])]
    return "\n".join(lines)


def execute_tool(name: str, args: dict, contract: dict, repo_root: Path = None) -> tuple[str, bool]:
    """Returns (result_text, is_error). Pre-execution scope check for writes
    and commands -- there is no SDK-level permission mode here, so this is
    the only thing standing between the model and an out-of-scope action
    before it happens."""
    repo_root = repo_root or REPO_ROOT
    allowed_paths = contract.get("allowed_paths", [])
    allowed_commands = contract.get("allowed_commands", [])

    if name == "read_file":
        path = args.get("path", "")
        try:
            return (repo_root / path).read_text(), False
        except OSError as e:
            return f"error: {e}", True

    if name == "write_file":
        path = args.get("path", "")
        if not path_allowed(path, allowed_paths):
            return f"denied: '{path}' is outside allowed_paths", True
        target = repo_root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(args.get("content", ""))
        return f"wrote {path}", False

    if name == "run_command":
        command = args.get("command", "")
        if not command_allowed(command, allowed_commands):
            return f"denied: '{command}' is outside allowed_commands", True
        result = subprocess.run(
            command, shell=True, cwd=repo_root, capture_output=True, text=True, timeout=120,
        )
        output = (result.stdout or "") + (result.stderr or "")
        return output, result.returncode != 0

    return f"unknown tool: {name}", True


def git_changed_files(repo_root: Path) -> dict:
    """--untracked-files=all is required: without it, git collapses a
    brand-new untracked directory to a single entry for the directory
    itself instead of the file inside it, which then fails allowed_paths
    matching against the actual file's path. See the identical fix and
    longer explanation in runner/claude_code_delegate.py."""
    out = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
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


async def run_delegate(
    contract: dict,
    model: str = DEFAULT_MODEL,
    repo_root: Path = None,
    evidence_ledger_path: str = None,
    client: OpenAI = None,
) -> dict:
    """repo_root and evidence_ledger_path default to the real repo and the
    real ledger -- override both in tests so a scripted run never touches
    real git state or writes real evidence. Pass client to inject a fake
    OpenAI client in tests instead of requiring OPENAI_API_KEY."""
    repo_root = Path(repo_root) if repo_root else REPO_ROOT
    client = client or OpenAI()
    messages = [{"role": "user", "content": build_prompt(contract)}]
    commands_run = []
    command_outputs = []  # (command, output, is_error) in call order
    total_tokens = 0

    for _ in range(contract.get("max_turns", 30)):
        response = client.chat.completions.create(
            model=model, messages=messages, tools=TOOLS, tool_choice="auto",
        )
        if response.usage:
            total_tokens += response.usage.total_tokens

        message = response.choices[0].message
        assistant_entry = {"role": "assistant", "content": message.content}
        if message.tool_calls:
            assistant_entry["tool_calls"] = [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in message.tool_calls
            ]
        messages.append(assistant_entry)

        if not message.tool_calls:
            break

        for call in message.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            output, is_error = execute_tool(call.function.name, args, contract, repo_root=repo_root)
            if call.function.name == "run_command":
                cmd = args.get("command", "")
                commands_run.append(cmd)
                command_outputs.append((cmd, output, is_error))
            messages.append({"role": "tool", "tool_call_id": call.id, "content": output})

    # Never trust the model's own account of what it touched -- verify against git.
    changed = git_changed_files(repo_root)

    # Independent verification: use the real captured stdout/stderr from test
    # commands, not the model's narration.
    test_outputs = [
        f"$ {cmd}\n{output}" for cmd, output, is_error in command_outputs
        if "pytest" in cmd or "test" in cmd
    ]
    any_test_errored = any(is_error for cmd, _, is_error in command_outputs if "pytest" in cmd or "test" in cmd)
    test_results = "\n\n".join(test_outputs)
    if any_test_errored and "FAIL" not in test_results:
        test_results += "\nFAIL: test command exited with an error"

    gate = enforce_contract(
        contract,
        changed_files=sorted(changed),
        commands_run=commands_run,
        test_results=test_results,
        approved_actions=approved_actions_for(contract),
        # No verified per-token pricing is looked up here (would go stale
        # fast) -- cost_usd stays unset. total_tokens is recorded as
        # evidence instead of a fabricated dollar figure.
    )

    if not gate["passed"]:
        rollback(repo_root, changed)

    outcome = {
        "provider": PROVIDER_NAME,
        "gate": gate,
        "rolled_back": not gate["passed"],
        "changed_files_verified_by_git": sorted(changed),
        "commands_run": commands_run,
        "session_id": None,
        "cost_usd": None,
        "total_tokens": total_tokens,
        "is_error": not gate["passed"],
    }

    ledger_kwargs = {"ledger_path": evidence_ledger_path} if evidence_ledger_path else {}
    record_evidence({
        "goal": contract.get("goal"),
        "contract": contract,
        "provider": PROVIDER_NAME,
        "gate_passed": gate["passed"],
        "gate_violations": gate["violations"],
        "pending_approval": gate["pending_approval"],
        "rolled_back": outcome["rolled_back"],
        "changed_files": outcome["changed_files_verified_by_git"],
        "commands_run": commands_run,
        "total_tokens": total_tokens,
        "evidence_kind": "simulated_delegation_result",
        "truth_status": "OBSERVED_SDK_OUTPUT_NOT_EXTERNALLY_VALIDATED",
    }, **ledger_kwargs)

    return outcome


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
