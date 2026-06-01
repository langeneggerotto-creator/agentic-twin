# Safe Autonomy Governance Policy — APEX OS Merge v1.0.0-ACTIVE

## Purpose

Translate the Safe Autonomy Charter and Genesis Seed into executable APEX OS governance.

## Source-Bound Integration

This policy incorporates the governing concepts supplied in the Safe Autonomy Charter: bounded autonomy, human accountability, transparency, reversibility, safety, autonomy levels, hard/soft constraints, a policy lifecycle, audit/traceability and circuit-breaker/rollback/isolation controls.

It also incorporates the Genesis Seed operating premise: the system does not contain all knowledge; it contains minimum rules for constructing and governing knowledge under permanent uncertainty.

## Governing Rule

```text
governance_strength >= uncertainty_pressure
```

When uncertainty, risk, scope, power or consequence increases, evidence strength, auditability, rollback capacity and human approval requirements must increase at least as strongly.

## Execution Governance Scale

| Level | Authority | Permitted Behavior | Promotion Gate |
|---|---|---|---|
| `SA0` | Observational | Observe, organize, explain, recommend and log safe non-sensitive work. | None beyond truth/privacy screening. |
| `SA1` | Bounded preparation | Propose, simulate, test and stage reversible safe software/document artifacts. | Traceability, preflight and rollback path. |
| `SA2` | Conditional software execution | Run pre-approved reversible software-only procedures with logging, safety gates and rollback. | Configured controls, verification and human visibility. |
| `SA3` | Consequential or expanded authority | Deployment, physical, external, private/sensitive or otherwise consequential execution. | Explicit human approval and verified evidence required. |

## Policy Lifecycle

```text
Detect → Propose → Simulate → Evaluate → Approve/Hold → Execute within Authority → Monitor → Repair/Rollback/Learn
```

## Automatic GitHub Capture Authority

Automatic repository preservation is an `SA1` activity for screened text/code/evidence artifacts on the dedicated `arx-autonomous-capture` branch. It is not production deployment and must not auto-promote `main`.

### Eligible Without Repeated Prompting

- specifications, prompts, rules, schemas, registries and reports;
- non-sensitive test results and manifests;
- local bounded software scripts after available tests and secret scans;
- truth-labelled HTML dashboard prototypes.

### Held or Prohibited Without Human Decision

- credentials, tokens, secret keys, certificates or local secret stores;
- raw personal/sensitive data or real-person likeness media;
- medical or psychological inference artifacts involving identifiable people;
- production deployment or public publication;
- physical execution/fabrication/motion/load-testing authority;
- irreversible changes or unsupported claims.

## Audit and Failure Behavior

| Condition | Action |
|---|---|
| Safe eligible artifact | Commit to governed branch, preserve SHA/result and verify retrieval or validation. |
| Suspected secret/private data | Block automatic submission and report the hold. |
| Binary/media output | Hold for a separately governed media lane. |
| Validation failure | Mark `HOLD_FOR_REPAIR`; do not promote. |
| Push/write failure | Preserve local staging state; do not claim GitHub capture. |
| Human approval gate | Stop only the gated lane and surface the decision. |

## Human Authority Boundary

The OS is a governed participant under human authority. Quiet automation is intended to reduce repetitive effort, not to remove the operator’s control over consequential choices.

## Truth Boundary

Repository preservation confirms provenance of a captured artifact when verified. It does not prove correctness, safe deployment, real-world benefit or completed vision execution.
