# AGENTIC_AAI_PURPOSE_GATE_INTEGRATION_SPEC

## Goal

Add a Purpose Gate pre-promotion step to the Agentic AAI Kernel.

## Intended Flow

`Agentic AAI promotion request → Purpose Gate result → Adapter decision → Promotion / repair / hold / block`

## Integration Contract

Agentic AAI must supply:

- promotion request;
- module contract path or content;
- purpose gate result;
- requested action;
- evidence references;
- approval status;
- authority boundary.

## Adapter Decisions

- `PROMOTE` when Purpose Gate promotes and approval boundaries are clear.
- `PROMOTE_WITH_CONDITIONS` when Purpose Gate has warnings or conditions.
- `HOLD` when human approval is pending.
- `REPAIR` when non-critical evidence or field gaps exist.
- `BLOCK` when Purpose Gate blocks, action exceeds authority, or production/physical/merge is requested without approval.

## Stop Conditions

The adapter must stop for merge to main, production deployment, public release, physical action, credential/secret handling, sensitive/private data exposure, spending, and override of a BLOCK decision.
