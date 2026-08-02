"""Runs on the control-plane host (NOT the Jetson). Consumes the
file-based queue that runner/jetson_edge_node.py writes to, and routes
each queued dream through runner.providers.router -- the same
enforce_contract gate, approvals, budget check, and evidence ledger apply
here as for any manually-run contract. This is the piece that actually
closes the loop described in the original architecture: "OCode detects a
failing service... creates a bounded repair contract... Claude Code
proposes a patch... evidence report appears on your [report]."

Manual-run only, same posture as runner/claude_code_delegate.py and
runner/providers/openai_provider.py: makes real, billed API calls, so it
is not wired into any automatic trigger. Run it periodically (a cron entry,
a systemd timer) if you want the queue drained continuously.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runner.providers.router import route_delegate

DEFAULT_QUEUE_DIR = "vault/dream_queue/pending"
DEFAULT_PROCESSED_DIR = "vault/dream_queue/processed"
DEFAULT_FAILED_DIR = "vault/dream_queue/failed"


def list_pending(queue_dir: str = DEFAULT_QUEUE_DIR) -> list:
    path = Path(queue_dir)
    if not path.exists():
        return []
    return sorted(path.glob("*.json"))


async def process_one(
    contract_path: Path,
    processed_dir: str = DEFAULT_PROCESSED_DIR,
    failed_dir: str = DEFAULT_FAILED_DIR,
) -> dict:
    contract = json.loads(contract_path.read_text())
    outcome = await route_delegate(contract)

    destination_dir = Path(processed_dir if outcome["gate"]["passed"] else failed_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    contract_path.rename(destination_dir / contract_path.name)

    return outcome


async def drain_queue(
    queue_dir: str = DEFAULT_QUEUE_DIR,
    processed_dir: str = DEFAULT_PROCESSED_DIR,
    failed_dir: str = DEFAULT_FAILED_DIR,
) -> list:
    outcomes = []
    for contract_path in list_pending(queue_dir):
        outcome = await process_one(contract_path, processed_dir, failed_dir)
        outcomes.append(outcome)
    return outcomes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue-dir", default=DEFAULT_QUEUE_DIR)
    parser.add_argument("--processed-dir", default=DEFAULT_PROCESSED_DIR)
    parser.add_argument("--failed-dir", default=DEFAULT_FAILED_DIR)
    args = parser.parse_args()

    outcomes = asyncio.run(drain_queue(args.queue_dir, args.processed_dir, args.failed_dir))
    print(json.dumps(outcomes, indent=2))
    if any(not o["gate"]["passed"] for o in outcomes):
        sys.exit(1)


if __name__ == "__main__":
    main()
