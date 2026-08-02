#!/usr/bin/env python3
"""Smoke tests for governance.approvals, the human-in-the-loop approval store
consulted by enforce_contract for requires_human_approval actions."""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from governance.approvals import approved_actions_for, contract_id, grant_approval

DEPLOY_CONTRACT = {
    "goal": "Deploy the hotfix",
    "allowed_paths": ["src/**"],
    "allowed_commands": ["kubectl apply -f k8s/hotfix.yaml"],
    "requires_human_approval": ["production_deployment"],
}

OTHER_CONTRACT = {**DEPLOY_CONTRACT, "goal": "Deploy a different hotfix"}


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_granted_approval_is_readable():
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "approvals.json")
        grant_approval(DEPLOY_CONTRACT, "production_deployment", "Otto", path)
        assert_true(approved_actions_for(DEPLOY_CONTRACT, path) == {"production_deployment"},
                    "a granted action must be readable back for the same contract")


def test_approval_does_not_leak_across_contracts():
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "approvals.json")
        grant_approval(DEPLOY_CONTRACT, "production_deployment", "Otto", path)
        assert_true(approved_actions_for(OTHER_CONTRACT, path) == set(),
                    "an approval for one contract must not apply to a different contract")


def test_contract_id_is_stable_and_content_sensitive():
    assert_true(contract_id(DEPLOY_CONTRACT) == contract_id(dict(DEPLOY_CONTRACT)),
                "identical contract content must hash to the same id regardless of dict identity")
    assert_true(contract_id(DEPLOY_CONTRACT) != contract_id(OTHER_CONTRACT),
                "different contract content must hash to a different id")


def test_missing_approvals_file_reads_as_empty():
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "does_not_exist.json")
        assert_true(approved_actions_for(DEPLOY_CONTRACT, path) == set(),
                    "no approvals file must mean no approvals, not an error")


if __name__ == "__main__":
    test_granted_approval_is_readable()
    test_approval_does_not_leak_across_contracts()
    test_contract_id_is_stable_and_content_sensitive()
    test_missing_approvals_file_reads_as_empty()
    print("PASS: approvals smoke tests")
