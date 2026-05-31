# APEX Agentic AAI Kernel v0.1

## Purpose

Create the first bounded autonomous module factory for APEX:

`Intent → Module Contract → Build → Test → Repair → Evidence → Draft PR → Human Review`

## Activated Configuration

| Control | Value |
|---|---|
| Authority ceiling | `A3_DRAFT_DELIVERY` |
| Runtime target | Hybrid: local package + GitHub Actions testing |
| Monthly compute/API ceiling | `USD 50` |
| Maximum automated repairs per run | `5` |
| First visible proof module | `GITHUB_DELIVERY_BRIDGE_v0.1` |

## Included in v0.1

- Autonomy charter.
- Activation configuration.
- Module contract schema.
- Executable policy guard.
- Contract validation and bounded module runner.
- Software unit tests.
- CI workflow.
- GitHub Delivery Bridge documentation and QA record.

## Truth Boundary

This initial kernel is a deterministic software governance scaffold. Local bounded tests passed before branch staging. It is not yet a continuously operating LLM agent runtime, a release pipeline, a production deployment system, or a physical-control system.

## Decision

`PROMOTE_TO_DRAFT_REVIEW`

Merge, release, production deployment, sensitive media upload and physical action remain human-approved only.
