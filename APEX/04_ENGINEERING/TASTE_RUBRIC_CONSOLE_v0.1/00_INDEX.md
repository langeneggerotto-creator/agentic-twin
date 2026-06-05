# APEX T.A.S.T.E. Rubric Console v0.1
## Testable • Aligned • Scalable • Traceable • Evolving Quality Intelligence
🔮🧿🅾️♾️💯

**Status:** `PROTOTYPED_AND_TESTED_SOFTWARE_ONLY`  
**Run ID:** `TASTE-CONSOLE-RUN-0001`  
**Decision:** `PROMOTE_TO_GITHUB_DRAFT_REVIEW`

## Purpose

This package turns APEX “taste” into a repeatable quality-evaluation system.

**T.A.S.T.E. = Testable + Aligned + Scalable + Traceable + Evolving**

Taste is not vague preference. Taste is testable judgment that can be scored, explained, improved, remembered and reused.

## Included Artifacts

| Artifact | Purpose |
|---|---|
| `dashboard/APEX_TASTE_RUBRIC_CONSOLE.html` | Zero-install browser scoring console |
| `schemas/TASTE_RUBRIC_SCHEMA.json` | Machine-readable rubric definition |
| `schemas/TASTE_EVALUATION_RECORD_SCHEMA.json` | Machine-readable evaluation record schema |
| `runtime/taste_evaluator.py` | Deterministic scoring and verdict engine |
| `tests/test_taste_evaluator.py` | Unit tests for scoring, verdicts and guardrails |
| `docs/01_TASTE_ENGINE_SPEC.md` | Specification |
| `docs/02_PROMOTION_RULES.md` | Promotion and blocker rules |
| `docs/03_RUNBOOK.md` | Usage instructions |
| `docs/04_TRACEABILITY_PROTOCOL.md` | Decision/evidence/failure/learning trace model |
| `evidence/QA_REPORT.md` | Local proof record |

## Local Proof

- Initial package built and zipped.
- QA caught one scoring-defect.
- Defect was repaired.
- Retest result: `8 / 8 PASS`.
- ZIP integrity: `PASS`.
- Physical actions: `0`.
- Production release actions: `0`.

## Truth Boundary

This is a working deterministic scoring prototype and browser console. It does not yet prove calibrated human preference, production-grade design judgment or universal quality truth. It gives APEX a repeatable quality-governance skeleton.
