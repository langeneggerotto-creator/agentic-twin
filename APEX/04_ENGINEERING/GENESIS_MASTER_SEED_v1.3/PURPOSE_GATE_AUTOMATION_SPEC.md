# Purpose Gate Automation Spec v1.3

## Flow

1. Detect module contract.
2. Validate purpose lock.
3. Validate evidence ledger.
4. Validate scope boundary.
5. Run purpose drift detector.
6. Generate promotion decision.
7. Update QA and run logs.
8. Stop at approval gates.

## Outputs

- `PURPOSE_GATE_RESULT.json`
- `PURPOSE_DRIFT_REPORT.json`
- `PROMOTION_DECISION.json`
- `AUTOMATION_RUN_LOG.md`
- `QA_REPORT.md`

## Decision Rule

If validator or drift detector returns BLOCK, promotion stops.
