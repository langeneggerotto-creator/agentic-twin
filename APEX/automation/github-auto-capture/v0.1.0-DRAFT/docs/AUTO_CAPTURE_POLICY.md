# APEX ARX Automated GitHub Capture Policy v0.1.0-DRAFT

## Decision

GitHub submissions may be automated for safe, traceable APEX/ARX execution artifacts. After the one-time local authorization and setup, routine capture should not stop for manual GitHub upload work.

## Automation Boundary

| Artifact Category | Automatic Capture | Destination | Rule |
|---|---:|---|---|
| Reports, ledgers, manifests, KPIs and test results | Yes | `arx-autonomous-capture` branch | Commit after preflight validation |
| Prompt and curriculum documentation | Yes | `arx-autonomous-capture` branch | Commit after preflight validation |
| Code/scripts from bounded software work | Yes | `arx-autonomous-capture` branch | Must pass secret/file checks and tests where available |
| Generated HTML dashboards | Yes | `arx-autonomous-capture` branch | Must not embed secrets/private data |
| Images, video and audio binaries | Not in v0.1 | Future governed media pipeline | Record as `HELD_FOR_MEDIA_PIPELINE` |
| Credentials, tokens, keys and `.env` files | Never | None | Block and report |
| Personal/sensitive raw data | Never automatically | None | Human review required |
| Physical autonomy approval or safety override | Never automatically | None | Human approval required |
| Production deployment-authority change | Never automatically | None | Human approval required |

## Branch Policy

**Automatic capture branch:** `arx-autonomous-capture`

This branch receives accepted execution-cycle artifacts automatically. Direct automatic mutation of `main` is not enabled in v0.1. Promotion to `main` is a separate governance decision after automated validation and repository controls are demonstrated.

## Quality Gates Before Push

1. Allowed-extension check.
2. Excluded-path and prohibited-file check.
3. Secret-pattern scan.
4. File-size limit check.
5. SHA-256 manifest creation.
6. Session metadata and truth-status entry.
7. Git commit with session ID.
8. Push confirmation.
9. GitHub Actions validation after push.

## One-Time Setup Requirement

A local process cannot push to GitHub until the machine has authenticated and has access to the repository. One initial GitHub authorization and scheduler activation are therefore required on the user's machine. After setup, routine safe captures are automatic.

## Failure Behavior

| Condition | Required Action |
|---|---|
| No approved files | Record `NO_SAFE_ARTIFACTS_TO_CAPTURE`; no push |
| Possible secret detected | Block push and create local blocked report |
| Push fails | Preserve local staging package; do not claim GitHub capture |
| Validation workflow fails | Mark capture `HOLD_FOR_REPAIR`; do not promote |
| Binary/media output discovered | Mark `HELD_FOR_MEDIA_PIPELINE` until governed binary path exists |

## Truth Boundary

Automated GitHub capture proves that an artifact was preserved in a repository branch after successful push and verification. It does not prove that the artifact is correct, safe, production-ready or evidence of real-world benefit.