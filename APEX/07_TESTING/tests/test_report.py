#!/usr/bin/env python3
"""Smoke tests for governance.report, the human-readable status view over
the evidence ledger and approvals store."""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from governance.approvals import grant_approval
from governance.evidence_ledger import record_evidence
from governance.report import format_report, summarize

DEPLOY_CONTRACT = {
    "goal": "Deploy the hotfix",
    "allowed_paths": ["src/**"],
    "allowed_commands": ["kubectl apply -f k8s/hotfix.yaml"],
    "requires_human_approval": ["production_deployment"],
}

CAMERA_CONTRACT = {
    "goal": "Repair the camera service startup failure",
    "allowed_paths": ["src/camera/**"],
    "allowed_commands": ["pytest tests/camera"],
}


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_counts_runs_by_outcome():
    with tempfile.TemporaryDirectory() as tmp:
        ledger = str(Path(tmp) / "evidence_ledger.jsonl")
        record_evidence({"goal": "ok run", "gate_passed": True, "rolled_back": False, "cost_usd": 0.50}, ledger)
        record_evidence({"goal": "bad run", "gate_passed": False, "rolled_back": True, "cost_usd": 0.25}, ledger)

        summary = summarize(ledger)
        assert_true(summary["total_runs"] == 2, "must count every recorded run")
        assert_true(summary["passed"] == 1 and summary["failed"] == 1, "must split passed vs failed correctly")
        assert_true(summary["rolled_back"] == 1, "must count rollbacks")
        assert_true(summary["total_cost_usd"] == 0.75, "must sum cost across runs")


def test_pending_approval_shows_up_until_granted():
    with tempfile.TemporaryDirectory() as tmp:
        ledger = str(Path(tmp) / "evidence_ledger.jsonl")
        approvals = str(Path(tmp) / "approvals.json")

        record_evidence({
            "goal": DEPLOY_CONTRACT["goal"],
            "contract": DEPLOY_CONTRACT,
            "provider": "claude_code",
            "gate_passed": False,
            "pending_approval": ["production_deployment"],
        }, ledger)

        # No approval granted yet -- must still show as pending.
        summary = summarize(ledger, approvals)
        assert_true(len(summary["still_pending_approval"]) == 1,
                    "an ungranted approval-gated action must show as pending")

        grant_approval(DEPLOY_CONTRACT, "production_deployment", "Otto", approvals)

        summary_after = summarize(ledger, approvals)
        assert_true(summary_after["still_pending_approval"] == [],
                    "granting the approval must clear it from the report, without re-running anything")


def test_entries_without_a_contract_are_skipped_not_crashed_on():
    with tempfile.TemporaryDirectory() as tmp:
        ledger = str(Path(tmp) / "evidence_ledger.jsonl")
        record_evidence({"goal": "legacy entry with no contract field", "pending_approval": ["hardware_control"]}, ledger)
        summary = summarize(ledger)
        assert_true(summary["still_pending_approval"] == [],
                     "an entry with no stored contract can't be re-checked and must not crash the report")


def test_format_report_mentions_pending_and_totals():
    with tempfile.TemporaryDirectory() as tmp:
        ledger = str(Path(tmp) / "evidence_ledger.jsonl")
        record_evidence({"goal": "ok run", "gate_passed": True, "cost_usd": 1.0}, ledger)
        text = format_report(summarize(ledger))
        assert_true("Runs recorded: 1" in text, "report must state the run count")
        assert_true("No runs awaiting human approval." in text, "report must say so when nothing is pending")


if __name__ == "__main__":
    test_counts_runs_by_outcome()
    test_pending_approval_shows_up_until_granted()
    test_entries_without_a_contract_are_skipped_not_crashed_on()
    test_format_report_mentions_pending_and_totals()
    print("PASS: report smoke tests")
