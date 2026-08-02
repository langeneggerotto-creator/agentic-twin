"""Human-readable status over the APEX Evidence Ledger -- the practical
local equivalent of the OCode architecture's "evidence report appears on
your iPhone" step, since there's no mobile surface in this environment.

Reads what evidence_ledger.py already recorded and approvals.py already
holds, and answers the two questions a human actually needs from that raw
history: what happened, and what's still waiting on me. "Still pending" is
recomputed live against the current approvals store (not read from the
stored snapshot), so a decision made after a run shows up correctly here
without needing to re-run anything.

Usage:
    python3 governance/report.py [--ledger PATH] [--json]
"""
import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from governance.approvals import DEFAULT_APPROVALS_PATH, approved_actions_for
from governance.evidence_ledger import DEFAULT_LEDGER_PATH, read_ledger


def summarize(ledger_path: str = DEFAULT_LEDGER_PATH, approvals_path: str = DEFAULT_APPROVALS_PATH) -> dict:
    entries = read_ledger(ledger_path)

    total_runs = len(entries)
    passed = sum(1 for e in entries if e.get("gate_passed"))
    failed = total_runs - passed
    rolled_back = sum(1 for e in entries if e.get("rolled_back"))
    total_cost_usd = sum(e.get("cost_usd") or 0 for e in entries)
    total_tokens = sum(e.get("total_tokens") or 0 for e in entries)

    still_pending = []
    for entry in entries:
        contract = entry.get("contract")
        pending = entry.get("pending_approval") or []
        if not pending or contract is None:
            continue
        remaining = sorted(set(pending) - approved_actions_for(contract, approvals_path))
        if remaining:
            still_pending.append({
                "goal": entry.get("goal"),
                "provider": entry.get("provider", "claude_code"),
                "recorded_at": entry.get("recorded_at"),
                "actions_awaiting_approval": remaining,
            })

    return {
        "total_runs": total_runs,
        "passed": passed,
        "failed": failed,
        "rolled_back": rolled_back,
        "total_cost_usd": round(total_cost_usd, 4),
        "total_tokens": total_tokens,
        "still_pending_approval": still_pending,
    }


def format_report(summary: dict) -> str:
    lines = [
        "=== Agentic Twin Governance Report ===",
        f"Runs recorded: {summary['total_runs']} "
        f"({summary['passed']} passed, {summary['failed']} failed, {summary['rolled_back']} rolled back)",
        f"Total spend: ${summary['total_cost_usd']:.4f}"
        + (f"  |  total tokens: {summary['total_tokens']}" if summary["total_tokens"] else ""),
        "",
    ]

    pending = summary["still_pending_approval"]
    if pending:
        lines.append(f"AWAITING HUMAN APPROVAL ({len(pending)}):")
        for p in pending:
            lines.append(
                f"  - [{p['provider']}] {p['goal']} -- needs: "
                f"{', '.join(p['actions_awaiting_approval'])}  (run at {p['recorded_at']})"
            )
        lines.append("  Approve with: python3 governance/approvals.py grant <contract.json> <action> <your name>")
    else:
        lines.append("No runs awaiting human approval.")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", default=DEFAULT_LEDGER_PATH, help="Path to the evidence ledger")
    parser.add_argument("--approvals", default=DEFAULT_APPROVALS_PATH, help="Path to the approvals store")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of the text report")
    args = parser.parse_args()

    summary = summarize(args.ledger, args.approvals)
    print(json.dumps(summary, indent=2) if args.json else format_report(summary))


if __name__ == "__main__":
    main()
