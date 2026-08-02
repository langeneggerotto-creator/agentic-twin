# agentic-twin

A self-learning Agentic AI Digital Twin system. Started as a toy plan → code →
test → reflect loop (`agents/`, `runner/controller.py`); has since grown a
governance layer ("OCode") on top, plus integration points into APEX and a
Jetson Nano edge deployment. This file is the map — individual modules carry
the detailed rationale in their own docstrings; this is where to start.

## Architecture

```
Jetson (edge, no Claude/OpenAI on-device -- stock JetPack/Ubuntu is too old)
  runner/jetson_edge_node.py
    monitors systemd services -> agents/dream_builder.py -> file queue

Control-plane host (a real capable machine, or this sandbox for dev/test)
  runner/dream_queue_worker.py
    drains the queue -> runner/providers/router.py
      -> claude_code_provider.py  (Claude Agent SDK)
      -> openai_provider.py       (OpenAI function calling)
    every provider run passes through:
      governance/gatekeeper.py::enforce_contract   (mechanical gate)
      governance/approvals.py                      (human approval store)
      governance/evidence_ledger.py                (append-only record)

Reporting / governance surfaces
  governance/report.py       -- CLI status report over the evidence ledger
  governance/apex_bridge.py  -- writes that report into APEX/07_TESTING/evidence/

Hardware actuation (only if a dream needs it)
  hardware/gpio_safety.py -- simulated by default, gated on hardware_control approval

Dream intake
  agents/dream_builder.py -- turns a raw goal into a governed contract
```

## Core concept: the delegation contract

Every unit of work — whether typed by hand, built by `dream_builder.py`, or
(eventually) produced by the real APEX Dream Builder — is a JSON contract:

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
| `governance/gatekeeper.py` | Mechanically enforces a contract against real outcomes | Implemented, tested |
| `governance/approvals.py` | CLI-based human approval store, scoped per contract | Implemented, tested |
| `governance/evidence_ledger.py` | Append-only run history | Implemented, tested |
| `governance/report.py` | Human-readable status over the ledger + approvals | Implemented, tested |
| `governance/apex_bridge.py` | Writes that report into APEX's own evidence directory | Implemented, tested |
| `runner/claude_code_delegate.py` | Delegates a contract to Claude Code | Implemented, tested — needs your own `ANTHROPIC_API_KEY` to actually run |
| `runner/providers/openai_provider.py` | Same, via OpenAI function calling | Implemented, tested — needs your own `OPENAI_API_KEY` to actually run |
| `runner/providers/router.py` | Dispatches a contract to whichever provider it names | Implemented, tested |
| `runner/jetson_edge_node.py` | Monitors services, queues repair dreams | Implemented, tested — logic verified in this sandbox, never run on real Jetson hardware |
| `runner/dream_queue_worker.py` | Drains the queue through the router | Implemented, tested |
| `hardware/gpio_safety.py` | Actuator interface | Implemented, tested — **simulated only**, no real Jetson.GPIO backend exercised anywhere |
| `agents/dream_builder.py` | Turns a raw goal into a contract | `RuleBasedDreamPathwayPlaceholder` implemented and tested; `DreamBuilderAdapter` (the real integration) is `AUTHORITATIVE_INTERFACE_UNRESOLVED` — real APEX Dream Builder implementations exist (a browser engine, a v0.1 package, a FastAPI/SQLite v3.1 app) but none of their source has been reachable from this repo yet |

Everything under "Implemented, tested" means: passes its test suite in this
sandbox with mocked/no external calls. It does **not** mean verified against
production traffic, real users, or (for the Jetson pieces) real hardware —
see `CORE_OS_INHERITANCE.md` for why that distinction is enforced throughout
this repo rather than treated as pedantry.

## Quickstart

```bash
pip install -r requirements.txt

# Run the test suite (no API keys or hardware required)
for f in APEX/07_TESTING/tests/test_*.py; do python3 "$f"; done

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
