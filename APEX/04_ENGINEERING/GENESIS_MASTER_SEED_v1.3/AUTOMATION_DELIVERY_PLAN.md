# AUTOMATION_DELIVERY_PLAN

## Automation Target

Purpose Gate Pre-Promotion Check.

## Triggers

- user says continue
- module contract appears
- draft PR opens or updates
- QA report is created
- promotion decision is requested
- T.A.S.T.E. evaluation completes
- test failure is detected

## Actions

1. Detect module contract.
2. Run Purpose Gate Validator.
3. Verify purpose lock, evidence ledger, scope boundary and approval locks.
4. Calculate purpose MSE.
5. Write `PURPOSE_GATE_RESULT.json`.
6. Update QA report, promotion decision and next task plan.
7. Stop before merge, production, public release, sensitive data or physical action.

## Human Approval Gates

Approval required for merge, live CI activation, production, public release, physical action, sensitive/private data, override of BLOCK and spending.
