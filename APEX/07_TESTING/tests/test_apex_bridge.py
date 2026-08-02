#!/usr/bin/env python3
"""Smoke tests for governance.apex_bridge -- translating the OCode Evidence
Ledger into APEX's own evidence-document format."""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from governance.approvals import grant_approval
from governance.apex_bridge import write_apex_evidence_bridge
from governance.evidence_ledger import record_evidence

DEPLOY_CONTRACT = {
    "goal": "Deploy the hotfix",
    "allowed_paths": ["src/**"],
    "allowed_commands": ["kubectl apply -f k8s/hotfix.yaml"],
    "requires_human_approval": ["production_deployment"],
}


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_writes_a_markdown_file_into_the_given_directory():
    with tempfile.TemporaryDirectory() as tmp:
        ledger = f"{tmp}/ledger.jsonl"
        approvals = f"{tmp}/approvals.json"
        record_evidence({"goal": "ok run", "gate_passed": True, "cost_usd": 1.5}, ledger)

        path = write_apex_evidence_bridge(ledger_path=ledger, approvals_path=approvals, evidence_dir=f"{tmp}/evidence")
        assert_true(path.exists(), "the bridge must actually write a file")
        assert_true(path.suffix == ".md", "the file must be markdown, matching APEX's existing evidence convention")

        text = path.read_text()
        assert_true("Runs recorded: 1" in text, "the document must reflect the real ledger contents")
        assert_true("Truth Boundary" in text, "the document must carry the Core OS truth-boundary disclosure")


def test_pending_approvals_are_listed_and_clear_once_granted():
    with tempfile.TemporaryDirectory() as tmp:
        ledger = f"{tmp}/ledger.jsonl"
        approvals = f"{tmp}/approvals.json"
        record_evidence({
            "goal": DEPLOY_CONTRACT["goal"], "contract": DEPLOY_CONTRACT, "provider": "claude_code",
            "gate_passed": False, "pending_approval": ["production_deployment"],
        }, ledger)

        before = write_apex_evidence_bridge(ledger_path=ledger, approvals_path=approvals, evidence_dir=f"{tmp}/evidence")
        assert_true("Deploy the hotfix" in before.read_text(), "an unapproved gated action must be listed")

        grant_approval(DEPLOY_CONTRACT, "production_deployment", "Otto", approvals)

        after = write_apex_evidence_bridge(ledger_path=ledger, approvals_path=approvals, evidence_dir=f"{tmp}/evidence")
        assert_true("None." in after.read_text(), "granting the approval must clear it from the bridged document too")


if __name__ == "__main__":
    test_writes_a_markdown_file_into_the_given_directory()
    test_pending_approvals_are_listed_and_clear_once_granted()
    print("PASS: apex_bridge smoke tests")
