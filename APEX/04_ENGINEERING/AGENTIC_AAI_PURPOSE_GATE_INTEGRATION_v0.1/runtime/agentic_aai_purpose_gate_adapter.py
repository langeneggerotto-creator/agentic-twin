#!/usr/bin/env python3
"""APEX Agentic AAI Purpose Gate Adapter v0.1.

Local adapter proof: converts a Purpose Gate result plus a promotion request
into an Agentic AAI promotion decision. It grants no deployment authority.
"""
from __future__ import annotations
from pathlib import Path
import argparse, json

BLOCKED_ACTIONS = {
    "merge_to_main", "production_deploy", "public_release", "physical_action",
    "hardware_control", "credential_handling", "secret_handling",
    "sensitive_data_exposure", "spending", "override_block"
}
VALID_DECISIONS = {"PROMOTE", "PROMOTE_WITH_CONDITIONS", "REPAIR", "HOLD", "BLOCK", "ROLLBACK", "RESEED"}

def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def decide(purpose_result: dict, promotion_request: dict) -> dict:
    failures = []
    warnings = []
    requested_actions = set(promotion_request.get("requested_actions", []))
    approval_status = promotion_request.get("approval_status", "pending")
    purpose_decision = purpose_result.get("decision", "BLOCK")

    prohibited_requested = sorted(requested_actions & BLOCKED_ACTIONS)
    if prohibited_requested and approval_status != "approved":
        failures.append("approval_required_for:" + ",".join(prohibited_requested))

    if purpose_decision == "BLOCK":
        failures.append("purpose_gate_blocked")
    elif purpose_decision not in VALID_DECISIONS:
        failures.append("invalid_purpose_gate_decision")

    if purpose_result.get("failures"):
        failures.append("purpose_gate_failures_present")
    if purpose_result.get("warnings"):
        warnings.append("purpose_gate_warnings_present")
    if not promotion_request.get("evidence_refs"):
        failures.append("missing_evidence_refs")

    if approval_status == "pending" and prohibited_requested:
        decision = "HOLD"
    elif failures:
        decision = "BLOCK"
    elif purpose_decision == "PROMOTE_WITH_CONDITIONS" or warnings:
        decision = "PROMOTE_WITH_CONDITIONS"
    else:
        decision = "PROMOTE"

    return {
        "status": "EVALUATED",
        "adapter_version": "0.1",
        "module_id": promotion_request.get("module_id") or purpose_result.get("module_id"),
        "decision": decision,
        "purpose_gate_decision": purpose_decision,
        "failures": failures,
        "warnings": warnings,
        "requested_actions": sorted(requested_actions),
        "approval_status": approval_status,
        "truth_boundary": "Local Agentic AAI adapter proof only; no merge, deployment, production, physical action, or secret handling authority granted.",
        "next_task": "Wire this adapter into the Agentic AAI Kernel promotion flow after draft review."
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("purpose_result", type=Path)
    parser.add_argument("promotion_request", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = decide(load_json(args.purpose_result), load_json(args.promotion_request))
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)

if __name__ == "__main__":
    main()
