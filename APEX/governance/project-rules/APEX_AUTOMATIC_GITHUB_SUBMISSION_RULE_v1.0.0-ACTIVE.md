# APEX Automatic GitHub Submission Rule v1.0.0 — ACTIVE
## `📦🧾🔐☁️✅🔁` GitHub Auto-Capture

## Decision

Routine GitHub submission is automatic for safe, traceable APEX project artifacts. The operator does not need to approve each eligible artifact individually during active governed execution.

## Primary Rule

```text
Safe artifact created or changed
→ preflight screen
→ version and label truth state
→ write to `arx-autonomous-capture`
→ validate and fetch-back verify
→ log commit/result
→ continue to next authorized target
```

## Branch Boundary

- Automatic capture target: `arx-autonomous-capture`
- `main` is not automatically mutated by this rule.
- Promotion to `main`, release, deployment, publication or authority expansion remains a separate approval decision.

## Safe Automatic Capture Classes

| Class | Automatic Action |
|---|---|
| Markdown specifications, prompts, rules, reports, indexes | Capture after content/safety screen |
| JSON/JSONL/YAML schemas, registries, evidence records, manifests | Capture after content/safety screen |
| TXT/CSV metrics or logs free of sensitive data | Capture after content/safety screen |
| Python/PowerShell/local software test artifacts | Capture after secret scan and available tests |
| HTML dashboard prototypes free of private/sensitive data | Capture with truth-state label |

## Held or Blocked Classes

| Class | Rule |
|---|---|
| Credentials, API keys, tokens, `.env`, secrets or certificates | Never automatically upload |
| Raw personal/sensitive data or real-person reference media | Hold for explicit consent/provenance review |
| Generated images/video/audio binaries | Hold until governed media-capture lane is explicitly validated |
| Physical action authorization, fabrication or safety override | Human approval required |
| Production deployment or public publication | Human approval required |
| Unsupported outcome or capability claim | Block or relabel truthfully before capture |

## Operation Modes

| Mode | What Is Automated | Boundary |
|---|---|---|
| Active Chat Execution | Eligible text/code artifacts may be written directly to the governed branch and verified without repeated operator prompts. | Connector/platform/account approval gates cannot be bypassed. |
| Local ARX Runner | Authenticated local runner stages, scans, commits, pushes and validates approved artifacts from completed ARX cycles. | One-time machine authentication/setup is required. |
| Background or Scheduled Cycles | May operate only through an installed and authenticated local/scheduled runner. | Chat alone cannot continue working after execution ends. |

## Required Verification Record

Every automated capture batch must preserve:

- artifact ID and version;
- source/purpose and truth-state label;
- files included and excluded;
- preflight result;
- commit SHA or explicit failed/held state;
- validation/fetch-back result;
- next proof gate.

## Integrated OS Rules

- `APEX Mirror First`: automation is visible through the control surface and evidence state.
- `5 = ALL`: unlisted menu number activates all displayed safe lanes under controlled concurrency.
- `C∞`: scoped build/test/repair may iterate toward `MSE ≤ 0.0001`; proxy convergence is not real-world proof.
- `3+1`: qualifying module outputs provide three ranked implementation directions plus one sandboxed innovation direction.

## Truth Boundary

Automatic repository capture proves only that an eligible artifact was preserved on the governed branch after successful validation. It does not prove operational maturity, deployment readiness, scientific validity, human benefit or physical authority.

### Permanent Convergence Option

**C∞ — `♾️🔁📉🎯🧪✅` — APEX CONVERGE 0.0001**  
Iterate the currently authorized scoped build/test/repair loop toward `MSE ≤ 0.0001`, or stop at an evidence, approval, rollback, resource, invalid-metric or no-significant-gain gate.

## Final Direction Stack

| Rank | Direction | Why Now | Evidence / Control Gate | Intended Output | Hold / Stop Rule |
|---:|---|---|---|---|---|
| 1 — Highest Priority | Apply automatic capture to all new safe APEX artifacts on the governed branch. | Removes repeated manual submission effort while preserving history. | Commit SHA plus fetch-back/validation record. | Durable repository continuity. | Block sensitive or unsupported content. |
| 2 — Next Priority | Route Mirror, Iteration Automator, C∞ and Learning Center records into the same capture lane. | Creates a unified OS evidence spine. | Machine-readable status records and validation. | Connected evidence baseline. | Do not imply operation from artifacts alone. |
| 3 — Third Priority | Enable the authenticated local ARX runner for unattended software-only cycles when the operator is ready at the machine. | Enables capture outside active chat execution. | One-time local authentication and successful dry run. | Repeatable hands-off local capture. | No high-consequence action or secret upload. |
| 4 — Random Innovation Area — Sandboxed | Develop a capture-benefit dashboard showing time saved and unresolved evidence gates. | Makes automation payoff visible. | Prototype using recorded commits only. | Capture value panel. | Do not treat projected benefit as measured outcome. |

🔮🧭🧿🅾️♾️💯
