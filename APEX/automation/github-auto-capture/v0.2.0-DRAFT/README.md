# APEX GitHub Auto-Capture v0.2.0-DRAFT — Unattended Safe Submission Lane
## `📦🧾🔐☁️✅🔁`

## Purpose

Remove recurring manual GitHub submission effort for eligible APEX artifacts. Once the operator completes the unavoidable one-time GitHub authentication on the local machine, approved output files may be detected, screened, versioned, committed, pushed and validated automatically on the governed `arx-autonomous-capture` branch.

## Truth Boundary

This lane can automate routine safe artifact capture. It cannot and must not silently approve account permissions, bypass GitHub/OpenAI authorization prompts, upload secrets/private data/consent-gated media, mutate `main`, deploy systems, or authorize physical/high-consequence actions.

## Operating Flow

```text
One-time operator authentication, only if not already active
→ Install local unattended capture service/task
→ APEX module writes eligible artifacts to auto_capture_inbox
→ Watcher detects a stable batch
→ Preflight checks and safe submission
→ Manifest + capture ledger created
→ Commit and push to arx-autonomous-capture
→ GitHub Actions validation
→ Move local batch to processed or held
→ Continue waiting for next safe artifact
```

## Components

| File | Purpose |
|---|---|
| `scripts/Install-APEXUnattendedGitHubCapture.ps1` | One-time setup: auth boundary, repository setup, watched folders, scheduled watcher. |
| `scripts/Watch-APEXOutbox-AndAutoSubmit.ps1` | Quiet watcher loop that submits inbox batches automatically. |
| Existing `v0.1.0-DRAFT/scripts/Invoke-ARXGitHubAutoSubmit.ps1` | Secret/file screening, staging, manifest, ledger, git commit and push. |
| Existing workflow plus governed-canon validator | Validates captured runtime records, OS canon and global project rules on push. |

## Watched Folder Contract

Default folder on the operator machine:

```text
<CONTROL_CENTER>\auto_capture_inbox
```

Safe APEX modules or runners place text/code/evidence files there. The unattended watcher automatically submits the batch and archives the local copy:

```text
<CONTROL_CENTER>\auto_capture_processed\<batch timestamp>
<CONTROL_CENTER>\auto_capture_held\<batch timestamp>
<CONTROL_CENTER>\data\auto_capture_logs
```

## Eligible Automatic Submission

- `.md`, `.json`, `.jsonl`, `.yaml`, `.yml`, `.csv`, `.txt`, `.html`, `.py`, `.ps1`, `.toml`
- safe specifications, prompts, registries, reports, schemas, manifests, test outputs and dashboard prototypes;
- bounded software-source artifacts that contain no screened sensitive marker.

## Never Automatically Submitted

- secrets, credentials, private keys, certificates, environment files and local databases;
- sensitive personal data or raw real-person identity/likeness media;
- binary image/video/audio content until a separately governed media lane exists;
- physical authority, safety overrides, production/publication authority or unsupported claims.

## One-Time Activation Boundary

GitHub authentication is a real permission event. The installer checks current authentication; only when missing will it open the lawful browser-based GitHub sign-in flow. That single human authorization cannot be bypassed. After successful setup, eligible submissions run without repeated approvals.

## Intended Setup Command

From a local copy of this directory, run once in PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\Install-APEXUnattendedGitHubCapture.ps1 -IntervalMinutes 5
```

## Success Test

1. Installer confirms authenticated repository and scheduled watcher.
2. Put a safe `.md` test artifact in `auto_capture_inbox`.
3. Within the interval, the watcher creates a capture record and pushes it to `arx-autonomous-capture`.
4. GitHub Actions validates the captured artifact.
5. The processed copy and receipt appear locally.

## Failure Behavior

| Failure | Automatic Handling |
|---|---|
| Authentication missing | One-time operator sign-in required; do not fake completion. |
| Sensitive/prohibited file detected | Hold batch locally; no push; write blocked receipt. |
| Git/push/validation failure | Preserve batch and logs; mark held/retryable; do not claim capture. |
| No safe artifact present | Wait quietly. |

## Integration Position

```text
APEX Mirror
→ Iteration Automator / Module Runner
→ auto_capture_inbox
→ GitHub Auto-Capture Watcher
→ governed branch + validation
→ Mirror evidence state
```

🔮🧭🪞🧿⚙️🔁📊🧾🔐☁️✅🅾️♾️💯
