from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TARGET_ROOTS = [
    ROOT / "APEX" / "os" / "canon",
    ROOT / "APEX" / "governance" / "project-rules",
]
BLOCKED_EXTENSIONS = {".env", ".pem", ".key", ".pfx", ".p12", ".sqlite", ".db", ".kdbx"}
BLOCKED_NAME_FRAGMENTS = {"credential", "private-key", "password", "local-secret"}
SENSITIVE_MARKERS = {
    "BEGIN PRIVATE KEY",
    "BEGIN RSA PRIVATE KEY",
    "AUTHORIZATION: BEARER",
    "CLIENT_SECRET=",
    "ACCESS_TOKEN=",
    "API_KEY=",
    "PASSWORD=",
}
ALLOWED_EXTENSIONS = {".md", ".json", ".jsonl", ".yaml", ".yml", ".csv", ".txt", ".html", ".py", ".ps1", ".toml"}
REQUIRED_CANON = [
    "00_INDEX/APEX_OS_PERMANENT_INGEST_INDEX_v1.0.0-ACTIVE-CANDIDATE.md",
    "01_SPEC/APEX_OS_GENESIS_SAFE_AUTONOMY_INTEGRATION_SPEC_v1.0.0-ACTIVE-CANDIDATE.md",
    "02_WORKING_PROMPT/APEX_OS_STARTUP_KERNEL_v1.0.0-ACTIVE-CANDIDATE.md",
    "03_GOVERNANCE/SAFE_AUTONOMY_GOVERNANCE_POLICY_v1.0.0-ACTIVE.md",
    "08_QUARANTINE/CONSENT_GATED_REFERENCE_BOUNDARY.md",
]


def validate_file(path: Path, failures: list[str]) -> None:
    lower_name = path.name.lower()
    if path.suffix.lower() in BLOCKED_EXTENSIONS:
        failures.append(f"blocked extension committed: {path}")
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        failures.append(f"unsupported binary/media file in governed text lane: {path}")
    if any(fragment in lower_name for fragment in BLOCKED_NAME_FRAGMENTS):
        failures.append(f"blocked sensitive filename committed: {path}")
    try:
        text = path.read_text(encoding="utf-8").upper()
    except UnicodeDecodeError:
        failures.append(f"binary file found in governed text lane: {path}")
        return
    for marker in SENSITIVE_MARKERS:
        if marker in text:
            failures.append(f"sensitive marker found in governed text: {path}")


def main() -> int:
    failures: list[str] = []
    canon_root = TARGET_ROOTS[0]
    if canon_root.exists():
        missing = [str(canon_root / p) for p in REQUIRED_CANON if not (canon_root / p).exists()]
        failures.extend(f"required canon artifact missing: {p}" for p in missing)
    for target_root in TARGET_ROOTS:
        if not target_root.exists():
            continue
        for path in target_root.rglob("*"):
            if path.is_file():
                validate_file(path, failures)
    if failures:
        print("APEX governed automatic capture validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("APEX governed automatic capture validation passed: permitted text/code artifacts satisfy lane constraints.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
