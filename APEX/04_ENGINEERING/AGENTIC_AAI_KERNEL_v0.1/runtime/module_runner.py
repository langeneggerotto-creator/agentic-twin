"""Validate APEX module contracts before any draft-delivery promotion."""
from pathlib import Path
import json

REQUIRED = {
    "module_id", "purpose", "user_outcome", "authority_required",
    "outputs", "tests", "promotion_gate"
}


def validate_contract(contract: dict) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED - set(contract))
    if missing:
        errors.append("Missing fields: " + ", ".join(missing))
    if contract.get("physical_action_requested") is True:
        errors.append("Physical action is blocked in AAI Kernel v0.1.")
    if contract.get("authority_required") not in {
        "A0_DEFINE", "A1_BUILD", "A2_TEST", "A3_DRAFT_DELIVERY"
    }:
        errors.append("Requested authority exceeds AAI Kernel v0.1 ceiling.")
    if not contract.get("tests"):
        errors.append("At least one test is required before promotion.")
    return errors


def build_record(contract_path: Path, output_dir: Path) -> dict:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    errors = validate_contract(contract)
    output_dir.mkdir(parents=True, exist_ok=True)
    if errors:
        result = {"module_id": contract.get("module_id", "UNKNOWN"), "status": "BLOCK", "errors": errors}
    else:
        (output_dir / "GENERATED_MODULE_RECORD.md").write_text(
            f"# Generated Module Record — {contract['module_id']}\n\n"
            f"## Purpose\n{contract['purpose']}\n\n"
            "## Truth Boundary\nDraft-delivery artifact only; no merge, release, production or physical action.\n",
            encoding="utf-8",
        )
        result = {"module_id": contract["module_id"], "status": "BUILT_FOR_TEST", "physical_actions": 0}
    (output_dir / "BUILD_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
