"""Provider adapter wrapping runner.claude_code_delegate to match the
common provider interface in base.py. All the real logic (options, gate
wiring, rollback, evidence) already lives in claude_code_delegate -- this
just tags the outcome with which provider produced it."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runner.claude_code_delegate import run_delegate as _run_delegate

PROVIDER_NAME = "claude_code"


async def run_delegate(contract: dict) -> dict:
    outcome = await _run_delegate(contract)
    return {"provider": PROVIDER_NAME, **outcome}
