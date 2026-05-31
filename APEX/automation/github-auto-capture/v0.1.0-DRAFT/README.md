# APEX ARX GitHub Auto-Capture Layer v0.1.0-DRAFT

## Purpose

Automatically preserve each safe APEX/ARX execution-cycle output in GitHub, update its manifest and capture ledger, push the commit, and allow the executor to continue to the next target without manual GitHub submission work.

## Truth Boundary

This package automates **authorized GitHub capture** after one unavoidable setup step: the user's Windows machine must be authenticated to GitHub once. It does not authorize uploading secrets, sensitive personal data, physical-autonomy promotions, unsafe changes, or unverified claims.

## Operating Design

```text
ARX cycle completes
  → collect approved output files
  → secret/private-data preflight
  → reject/hold prohibited files
  → copy approved files into repository capture folder
  → calculate hashes + create manifest
  → append capture ledger
  → git commit + git push
  → GitHub Actions validation runs
  → ARX moves to next queued target
```

## Default Automation Mode

- Repository: `langeneggerotto-creator/agentic-twin`
- Branch: `arx-autonomous-capture`
- Capture path: `APEX/runtime-captures/<session_id>/`
- Safe automatic artifact types: Markdown, JSON, JSONL, YAML, CSV, TXT, HTML, Python, PowerShell and approved workflow/config text.
- Held automatically: secrets, credentials, local databases, keys/certificates, oversized binaries, raw private media, files failing preflight validation.

Capturing on a dedicated branch means there is no manual effort to preserve each cycle in GitHub while avoiding silent mutation of the primary branch until promotion rules are approved.

## One-Time Setup

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\Setup-ARXGitHubAutoCapture.ps1
```

The setup verifies Git and GitHub CLI, requests GitHub authentication only when not already active, clones the repository and selects the automatic capture branch.

## Run One ARX Cycle and Automatically Submit to GitHub

```powershell
.\scripts\Run-ARXCycle-And-AutoSubmit.ps1
```

## Enable Recurring Software-Only Execution and GitHub Capture

```powershell
.\scripts\Install-ARXAutoCaptureSchedule.ps1 -IntervalMinutes 60
```

## Safety Gates

The script never automatically commits secrets, passwords, private keys, certificates, SQLite databases, private raw data, physical execution approvals, authority expansions or unsupported claims of verified outcomes.

## Binary Assets

Generated images, video and audio are marked `HELD_FOR_MEDIA_PIPELINE` in v0.1 until a governed binary/media repository pipeline is enabled and verified.
