# GitHub Delivery Bridge Purpose Gate Requirements v0.1

## Goal

Require Purpose Gate evidence before a draft PR can be promoted from draft-review staging.

## Required Draft PR Artifacts

- `MODULE_CONTRACT.json`
- `PURPOSE_GATE_RESULT.json`
- `EVIDENCE_LEDGER.json`
- `QA_REPORT.md`
- `RISK_REGISTER.md`
- `NEXT_TASK_PLAN.md`
- Approval boundary statement

## Bridge Rule

A draft PR may be created automatically when authorized, but it may not be marked ready, merged, released, or converted to live enforcement unless human approval is explicit.
