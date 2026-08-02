"""Bridges the OCode Evidence Ledger (governance/evidence_ledger.py) into
APEX's own evidence trail (APEX/07_TESTING/evidence/), which previously
had no connection to it -- APEX had its own governance vocabulary (canon,
quality gates, evidence ledgers per APEX/00_INDEX/00_APEX_MASTER_INDEX.md)
and OCode had its own (enforce_contract, evidence_ledger.py), running as
two disconnected systems that both claimed to do evidence-backed
governance. This writes one real artifact into APEX's own directory,
generated from OCode's real (or, so far, simulated-until-a-real-run)
evidence -- not a duplicate governance system, a translation of one into
the other's expected format.
"""
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from governance.report import summarize

DEFAULT_EVIDENCE_DIR = "APEX/07_TESTING/evidence"


def render_apex_evidence(summary: dict, generated_on: str) -> str:
    lines = [
        f"# {generated_on} OCode Governance Evaluation",
        "",
        "## Purpose",
        "",
        "Bridge the OCode Evidence Ledger (governance/evidence_ledger.py) into APEX's",
        "own evidence trail, so delegated-execution history is visible from the APEX",
        "governance surface without maintaining a second, separate ledger.",
        "",
        "## Scope Evaluated",
        "",
        "All contract-gated delegation runs recorded in the OCode Evidence Ledger as of",
        "generation time, across every provider (see runner/providers/router.py).",
        "",
        "## Summary",
        "",
        f"- Runs recorded: {summary['total_runs']}",
        f"- Passed: {summary['passed']}",
        f"- Failed: {summary['failed']}",
        f"- Rolled back: {summary['rolled_back']}",
        f"- Total spend: ${summary['total_cost_usd']:.4f}",
        f"- Total tokens: {summary['total_tokens']}",
        "",
        "## Awaiting Human Approval",
        "",
    ]

    pending = summary["still_pending_approval"]
    if pending:
        lines.append("| Goal | Provider | Actions | Recorded |")
        lines.append("|---|---|---|---|")
        for p in pending:
            actions = ", ".join(p["actions_awaiting_approval"])
            lines.append(f"| {p['goal']} | {p['provider']} | {actions} | {p['recorded_at']} |")
    else:
        lines.append("None.")

    lines += [
        "",
        "## Truth Boundary",
        "",
        "This document reports what the OCode Evidence Ledger recorded. Per",
        "CORE_OS_INHERITANCE.md, a passed gate is evidence the delegation complied with",
        "its contract -- it is not external validation that the resulting change is",
        "correct in the real world. Treat entries with truth_status",
        "OBSERVED_SDK_OUTPUT_NOT_EXTERNALLY_VALIDATED accordingly.",
    ]
    return "\n".join(lines)


def write_apex_evidence_bridge(
    ledger_path: str = None,
    approvals_path: str = None,
    evidence_dir: str = DEFAULT_EVIDENCE_DIR,
) -> Path:
    kwargs = {}
    if ledger_path is not None:
        kwargs["ledger_path"] = ledger_path
    if approvals_path is not None:
        kwargs["approvals_path"] = approvals_path
    summary = summarize(**kwargs)

    generated_on = date.today().isoformat()
    output_dir = Path(evidence_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{generated_on}_OCODE_GOVERNANCE_EVALUATION.md"
    output_path.write_text(render_apex_evidence(summary, generated_on))
    return output_path


if __name__ == "__main__":
    path = write_apex_evidence_bridge()
    print(f"Wrote {path}")
