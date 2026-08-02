"""The APEX Evidence Ledger referenced in CORE_OS_INHERITANCE.md: an
append-only record of compliance/readiness evidence for governed actions
(contract-gated delegations, etc). Never mutates or deletes prior entries --
only appends, so history stays intact when scenarios fork or later runs
disagree with earlier ones."""
import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LEDGER_PATH = "vault/evidence_ledger.jsonl"


def record_evidence(entry: dict, ledger_path: str = DEFAULT_LEDGER_PATH) -> dict:
    record = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        **entry,
    }
    path = Path(ledger_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")
    return record


def read_ledger(ledger_path: str = DEFAULT_LEDGER_PATH) -> list:
    path = Path(ledger_path)
    if not path.exists():
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]
