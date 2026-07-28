# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

`agentic-twin` is Otto Langenegger's self-learning Agentic AI Digital Twin project. It contains two layers that are easy to confuse:

1. **The root-level agent loop** (`agents/`, `runner/`, `governance/`, `vault/`) — a minimal planner → developer → tester → reflector pipeline, currently hardcoded around a toy "CLI Calculator" example.
2. **APEX** (`APEX/`) — a much larger, in-progress governance and product framework ("Perfect AI / Vision-to-Reality Meta-System") layered on top, plus a handful of standalone browser console prototypes at repo root (`apex-*-console*/`).

Both layers repeatedly emphasize labeling claims as `VERIFIED` / `INFERRED` / `ASSUMED` / `UNKNOWN` and never overstating readiness — preserve that convention in any docs or output you add.

## Commands

There is no package.json, test runner config, or lint config at the repo root — commands are plain Python/Node invocations.

**Run the root agent pipeline** (writes `outputs/plan.md`, `outputs/generated_code.py`, `outputs/test_results.txt`, `outputs/reflection.txt`):
```bash
python3 -m runner.controller
# or: PYTHONPATH=. python3 runner/controller.py
```
Note: `agents/` and `runner/` are namespace packages (no `__init__.py`), so plain `python3 runner/controller.py` fails with `ModuleNotFoundError: No module named 'agents'` unless the repo root is on `PYTHONPATH`. Prefer `python3 -m runner.controller` from the repo root.

**Run an APEX smoke test:**
```bash
python3 APEX/07_TESTING/tests/test_python_intent_v04.py
python3 APEX/07_TESTING/tests/test_python_intent_v03.py
python3 APEX/07_TESTING/tests/test_ras2_adapter_v01.py
```
Known issue: as currently written (Python 3.11, this environment), all three smoke tests raise `AttributeError: 'NoneType' object has no attribute '__dict__'` from inside `dataclasses`, because they load the target module via `importlib.util.spec_from_file_location` / `module_from_spec` without registering it in `sys.modules` before `exec_module` runs — and the target modules use `from __future__ import annotations` dataclasses, whose field-type resolution needs `sys.modules[cls.__module__]`. If asked to fix or extend these tests, add `sys.modules[spec.name] = module` before `spec.loader.exec_module(module)`.

**Content/security scan for the two hardened console prototypes:**
```bash
node tools/content-scan-preflight.mjs
```
This walks `apex-mobile-python-console-v161/` and `apex-rightschain-manifest-builder/` only (see `ROOTS` in the script), and fails (exit 1) on: inline HTML event handlers, executable inline `<script>` blocks, `eval`/`Function(...)`, `document.write`, or files over 400 lines. It warns (non-fatal) on dynamic script injection and unguarded clipboard/blob-URL usage.

**CI:** `.github/workflows/twin.yml` runs on every push — it just executes `python runner/controller.py || true` and cats the `outputs/` files (failures are swallowed, so this is a smoke/demo workflow, not a real gate).

**Submodule:** `oil_core` is a git submodule (`langeneggerotto-creator/oil-core`) and is not checked out by default — run `git submodule update --init` if you need it. `oil_core_manifest.yml` documents its expected commit/sync state and says not to hand-edit it ("Update via oil-sync to refresh hash and constants").

**Dependencies:** `requirements.txt` contains only `openai`; nothing in the current codebase actually imports it yet.

## Architecture

### Root agent loop

`runner/controller.py` is the entry point and shows the whole flow in ~25 lines:

1. `agents/planner.py` reads `vault/vision.json` (project goal) and `vault/canon.json` (rules) and emits a Markdown plan.
2. `agents/developer.py` takes the plan and returns generated code — **currently returns a hardcoded calculator implementation regardless of the plan's contents**; it does not actually call an LLM yet.
3. `agents/tester.py` re-runs a fixed set of hardcoded assertions against whatever is in `outputs/generated_code.py`.
4. `agents/reflector.py` does simple heuristic checks (test failures, code length, presence of `input(`) and returns a reflection.
5. `governance/gatekeeper.py` (`enforce_canon`) does a second, independent, very shallow check (looks for `"def "` and `"assert"` substrings) and reports Canon violations.

All four stages are stubs/heuristics, not LLM calls — there is no actual AI inference in this loop today, despite the "agentic" framing. If asked to make this loop real, that means wiring an LLM (the `openai` dependency in `requirements.txt` is the likely intended client) into `developer.py` at minimum.

### APEX layer

`APEX/` is a numbered-folder documentation and governance system layered over the same repo:

| Folder | Purpose |
|---|---|
| `00_INDEX` | Navigation/status dashboard (`00_APEX_MASTER_INDEX.md`) |
| `01_CANON` | Purpose, laws, doctrine — see `01_APEX_HEART_CORE.md`, the human-dignity gate every APEX output is meant to pass |
| `02_ARCHITECTURE` | System design, e.g. the Foresight Engine (structured scenario/risk mapping, not prediction) |
| `03_APPLICATION` | The actual Python console implementations (`consoles/python-intent/v0.3`, `v0.4`) and integrations (`integrations/ras2`) |
| `04_ENGINEERING` | Build/implementation bridges between canon docs and code |
| `05_GOVERNANCE` | Rights/provenance/ethics docs (referenced by the app registry; not yet populated) |
| `06_PRODUCT` | Product strategy and scorecards |
| `07_TESTING` | Smoke tests (`tests/`) and evidence reports (`evidence/`) |

Every substantive APEX doc ends with a "Truth Status" table (`VERIFIED` / `NOT YET` / `ASSUMED` / `UNKNOWN`) and often a "Next 3 Plus 1" section (three concrete next steps plus one "control upgrade"). Follow this pattern when adding or updating APEX docs — see `APEX/03_APPLICATION/03_APEX_APPLICATION_REGISTRY.md` and `APEX/06_PRODUCT/06_APEX_LAYER_2_SCORE_PREDICT_EVOLVE.md` for the canonical shape.

`APEX/03_APPLICATION/03_APEX_APPLICATION_REGISTRY.md` is the source of truth for where each prototype's *real* code currently lives vs. its intended canonical APEX path — several root-level `apex-*-console*/` folders are the live/hosted originals and are deliberately **not yet moved** into `APEX/03_APPLICATION/` because hosted URLs (RawGithack/jsDelivr-style) depend on the current paths. Don't relocate or delete root-level prototype folders without checking that registry first.

### Root-level browser console prototypes

`apex-meta-studio-console/`, `apex-python-intent-console/`, `apex-python-intent-console-v02/`, `apex-rightschain-manifest-builder/`, `apex-mobile-python-console-v161/` are standalone static HTML/CSS/JS apps (no build step, no framework) — open `index.html` directly or serve statically. `apex-rightschain-manifest-builder` and `apex-mobile-python-console-v161` are the two folders the content-scan-preflight tool enforces house rules on (no inline scripts/handlers, no `eval`, 400-line file cap); apply the same constraints if editing those two, since the CI-style scan will fail otherwise.

### Governance/inheritance chain

`CORE_OS_INHERITANCE.md` states this repo inherits laws from an external `langeneggerotto-creator-APEX-CORE-OS` repository (not present locally) and sets the repo's Truth Boundary: simulations/forecasts/designs produced here must never be represented as real-world validation without external calibration. This principle is echoed throughout APEX docs (Heart Core, Foresight Engine) — keep it in mind when writing anything that sounds like a prediction, score, or readiness claim.
