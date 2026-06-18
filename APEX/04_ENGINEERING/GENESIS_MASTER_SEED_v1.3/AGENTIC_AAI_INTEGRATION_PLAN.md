# AGENTIC_AAI_INTEGRATION_PLAN

## Goal

Make the Agentic AAI Kernel call the Purpose Gate Validator before module promotion.

## Integration Point

Before any module is marked:

- `PROMOTE`
- `DEPLOYMENT_CANDIDATE`
- `PRODUCTION_READY`
- `DRAFT_PR_READY`

## Required Behavior

1. Require module contract.
2. Run Purpose Gate Validator.
3. Read `PURPOSE_GATE_RESULT.json`.
4. If decision is `BLOCK`, stop and create repair plan.
5. If decision is `PROMOTE_WITH_CONDITIONS`, list conditions.
6. If approval is required, stop.
7. Log result in evidence ledger.

## Boundary

Agentic AAI may stage draft review artifacts. It may not merge, deploy, publish, spend, expose sensitive data, or override approval gates.
