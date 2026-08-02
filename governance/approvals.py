"""Human approval store for consequential actions gated by enforce_contract.

There's no mobile/iPhone approval surface in this environment, so this is the
practical local equivalent: a human runs `python3 governance/approvals.py
grant <contract.json> <action> <approver>` after reviewing what Claude Code
proposed, and enforce_contract will accept that action for that exact
contract on the next run. Approval is scoped to one contract (hashed by its
full content) and one action tag -- it does not carry over to a different
goal or a different set of allowed paths/commands.
"""
import argparse
import hashlib
import json
from pathlib import Path

DEFAULT_APPROVALS_PATH = "vault/approvals.json"


def contract_id(contract: dict) -> str:
    canonical = json.dumps(contract, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _load(approvals_path: str) -> list:
    path = Path(approvals_path)
    if not path.exists():
        return []
    return json.loads(path.read_text())


def grant_approval(contract: dict, action: str, approver: str, approvals_path: str = DEFAULT_APPROVALS_PATH) -> dict:
    approvals = _load(approvals_path)
    record = {"contract_id": contract_id(contract), "action": action, "approver": approver}
    approvals.append(record)
    path = Path(approvals_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(approvals, indent=2))
    return record


def approved_actions_for(contract: dict, approvals_path: str = DEFAULT_APPROVALS_PATH) -> set:
    cid = contract_id(contract)
    return {a["action"] for a in _load(approvals_path) if a["contract_id"] == cid}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    grant = sub.add_parser("grant", help="Approve one action tag for one contract")
    grant.add_argument("contract", type=Path, help="Path to the JSON delegation contract")
    grant.add_argument("action", help="Action tag being approved, e.g. production_deployment")
    grant.add_argument("approver", help="Name/identifier of the human granting approval")

    show = sub.add_parser("show", help="List approvals recorded for a contract")
    show.add_argument("contract", type=Path)

    args = parser.parse_args()
    contract = json.loads(args.contract.read_text())

    if args.cmd == "grant":
        record = grant_approval(contract, args.action, args.approver)
        print(json.dumps(record, indent=2))
    elif args.cmd == "show":
        approved = sorted(approved_actions_for(contract))
        print(json.dumps({"contract_id": contract_id(contract), "approved_actions": approved}, indent=2))


if __name__ == "__main__":
    main()
