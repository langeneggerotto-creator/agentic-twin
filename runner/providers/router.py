"""Dispatches a delegation contract to the provider named in
contract["provider"] (default: claude_code). Every provider module exposes
the same async run_delegate(contract) -> dict shape (see base.py), so
gating, rollback, and evidence recording behave identically no matter which
model did the work -- this is what "graceful replacement of any provider"
means in practice, not just a design goal.

Usage:
    python3 runner/providers/router.py path/to/contract.json
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runner.providers import claude_code_provider, openai_provider

PROVIDERS = {
    "claude_code": claude_code_provider.run_delegate,
    "openai": openai_provider.run_delegate,
}


async def route_delegate(contract: dict) -> dict:
    provider_name = contract.get("provider", "claude_code")
    if provider_name not in PROVIDERS:
        raise ValueError(f"unknown provider: {provider_name!r} (available: {sorted(PROVIDERS)})")
    return await PROVIDERS[provider_name](contract)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path, help="Path to a JSON delegation contract")
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text())
    outcome = asyncio.run(route_delegate(contract))

    print(json.dumps(outcome, indent=2))
    if not outcome["gate"]["passed"]:
        print("GATE FAILED:", outcome["gate"]["violations"], file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
