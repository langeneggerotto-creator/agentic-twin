# Automation Delivery Plan v1.3

## Automation Target

Automate the Purpose Gate Pre-Promotion Check.

## Triggers

- module contract changes;
- draft PR opened or updated;
- QA report created;
- promotion decision requested;
- user continuation command.

## Automated Actions

1. Run purpose gate validator.
2. Run purpose drift detector.
3. Generate orchestration decision.
4. Create purpose gate result and drift report.
5. Update QA and evidence records.
6. Stop at human approval gates.

## Human Approval Stops

- merge to main;
- production deployment;
- live CI activation;
- public release;
- physical action;
- override of BLOCK.

## Boundary

Draft review only until human approval is explicit.
