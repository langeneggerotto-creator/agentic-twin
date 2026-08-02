# agentic-twin

A governed system for delegating scoped coding tasks to an AI provider
(Claude Code or OpenAI) and mechanically verifying what actually happened,
instead of trusting the model's own account of itself. This file is the
map — individual modules carry the detailed rationale in their own
docstrings; this is where to start.

## MVP scope

The MVP is the core loop below: turn a goal into a contract, delegate it to
a provider, and independently verify the result against real git state,
real command output, and real cost. Everything in that loop is implemented
and has real test coverage (see "Testing" below) that exercises it
end-to-end without needing an API key.

Two pieces beyond that loop exist in this repo but are **not** part of the
MVP — see "Experimental / not yet verified" further down.

```
governance/gatekeeper.py::enforce_contract   -- mechanical gate, verifies against real outcomes
governance/approvals.py                      -- human approval store
governance/evidence_ledger.py                -- append-only record of every run
governance/report.py                         -- CLI status report over the ledger
governance/apex_bridge.py                    -- writes that report into APEX/07_TESTING/evidence/

runner/claude_code_delegate.py         -- delegates a contract via the Claude Agent SDK
runner/providers/openai_provider.py    -- delegates a contract via OpenAI function calling
runner/providers/router.py             -- dispatches a contract to whichever provider it names

agents/dream_builder.py -- turns a raw goal into a governed contract
                            (rule-based placeholder; see below)
```

## Core concept: the delegation contract

Every unit of work is a JSON contract:

```json
{
  "goal": "Repair the camera service startup failure",
  "provider": "claude_code",
  "allowed_paths": ["src/camera/**"],
  "allowed_commands": ["pytest tests/camera"],
  "forbidden_actions": ["modify_credentials"],
  "requires_human_approval": ["production_deployment"],
  "max_budget_usd": 2.00,
  "acceptance_criteria": ["All camera tests pass"]
}
```

`enforce_contract()` verifies what actually happened (changed files via `git
status`, real command stdout, real reported cost) against this contract —
never trusting the executor's own account of itself. See
`vault/example_delegation_contract.json` for a full example and
`governance/gatekeeper.py` for the enforcement logic.

## Components and honest status

| Component | What it does | Status |
|---|---|---|
| `governance/gatekeeper.py` | Mechanically enforces a contract against real outcomes | MVP, tested |
| `governance/approvals.py` | CLI-based human approval store, scoped per contract | MVP, tested |
| `governance/evidence_ledger.py` | Append-only run history | MVP, tested |
| `governance/report.py` | Human-readable status over the ledger + approvals | MVP, tested |
| `governance/apex_bridge.py` | Writes that report into APEX's own evidence directory | MVP, tested |
| `runner/claude_code_delegate.py` | Delegates a contract to Claude Code | MVP, tested end-to-end (scripted SDK, real git repo) — needs your own `ANTHROPIC_API_KEY` to actually run |
| `runner/providers/openai_provider.py` | Same, via OpenAI function calling | MVP, tested end-to-end (scripted client, real git repo) — needs your own `OPENAI_API_KEY` to actually run |
| `runner/providers/router.py` | Dispatches a contract to whichever provider it names | MVP, tested |
| `agents/dream_builder.py` | Turns a raw goal into a contract | `RuleBasedDreamPathwayPlaceholder` implemented and tested; `DreamBuilderAdapter` (the real integration) is `AUTHORITATIVE_INTERFACE_UNRESOLVED` — see "Experimental" below |

"MVP, tested" means: passes its test suite in this sandbox with
mocked/no external calls, including — for the two provider delegates —
scripted integration tests that exercise the real execution path (message
loop, git diff detection, gate enforcement, rollback, evidence recording)
against a real isolated temp git repo. It does **not** mean verified
against production traffic or real users — see `CORE_OS_INHERITANCE.md`
for why that distinction is enforced throughout this repo rather than
treated as pedantry.

## Experimental / not yet verified

These exist in the repo but are out of MVP scope — don't rely on them yet:

| Component | Status |
|---|---|
| `runner/jetson_edge_node.py`, `runner/dream_queue_worker.py` | Implemented, tested — logic verified in this sandbox, never run on real Jetson hardware |
| `hardware/gpio_safety.py` | Implemented, tested — **simulated only**, no real Jetson.GPIO backend exercised anywhere |
| `agents/dream_builder.py`'s `DreamBuilderAdapter` | Raises `DreamBuilderUnresolvedError` by design — real APEX Dream Builder implementations exist elsewhere (a browser engine, a v0.1 package, a FastAPI/SQLite v3.1 app) but none of their source has been reachable from this repo yet |

## Testing

```bash
pip install -r requirements.txt
./scripts/run_tests.sh
```

This is the single canonical way to test the MVP — CI
(`.github/workflows/twin.yml`) runs this exact script on every push. No API
keys or hardware are required: every test is either a pure-function test or
a scripted integration test against a real, isolated temp git repo. See the
comments in `scripts/run_tests.sh` for why it lists test files by name
instead of globbing (the `APEX/` tree also holds unrelated, pre-existing
prototype tests with a known, unrelated bug).

## Quickstart

```bash
pip install -r requirements.txt
./scripts/run_tests.sh

# Turn a goal into a contract, then delegate it (needs ANTHROPIC_API_KEY)
python3 -c "
from agents.dream_builder import plan_dream
import json
print(json.dumps(plan_dream('Repair the camera driver crash', ['src/camera/**'], ['pytest tests/camera']), indent=2))
" > /tmp/contract.json
python3 runner/claude_code_delegate.py /tmp/contract.json

# Check what's happened so far / what's awaiting your approval
python3 governance/report.py

# Approve a gated action after reviewing it
python3 governance/approvals.py grant vault/example_delegation_contract.json production_deployment "your name"
```

## Related repos / docs

- `APEX/` — a separate, largely prototype-status governance/meta-system living
  in this same repo; see `APEX/00_INDEX/00_APEX_MASTER_INDEX.md`.
- `CORE_OS_INHERITANCE.md` — the truth-boundary rules this whole system
  inherits and enforces (observed vs. simulated vs. designed-not-proven).
- APEX Dream Builder — the real product `agents/dream_builder.py` is meant to
  eventually call. Not attached to this repo as of this writing; see that
  file's module docstring for exactly what's known and unknown about it.
