from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
TARGET_ROOTS = [
    REPO_ROOT / "APEX" / "os" / "canon",
    REPO_ROOT / "APEX" / "governance" / "project-rules",
]
TEXT_SUFFIXES = {".md", ".json", ".jsonl", ".yaml", ".yml", ".csv", ".txt", ".html", ".py", ".ps1", ".toml"}
REQUIRED_CANON = [
    "00_INDEX/APEX_OS_PERMANENT_INGEST_INDEX_v1.0.0-ACTIVE-CANDIDATE.md",
    "01_SPEC/APEX_OS_GENESIS_SAFE_AUTONOMY_INTEGRATION_SPEC_v1.0.0-ACTIVE-CANDIDATE.md",
    "02_WORKING_PROMPT/APEX_OS_STARTUP_KERNEL_v1.0.0-ACTIVE-CANDIDATE.md",
    "02A_READABLE_PROMPT_MIRROR/APEX_OS_STARTUP_KERNEL_READABLE_MIRROR_v1.0.0-ACTIVE-CANDIDATE.md",
    "03_GOVERNANCE/SAFE_AUTONOMY_GOVERNANCE_POLICY_v1.0.0-ACTIVE.md",
    "04_REGISTRIES/APEX_OS_RULE_REGISTRY_v1.0.0-ACTIVE-CANDIDATE.json",
    "04_REGISTRIES/APEX_OS_INGEST_SOURCE_REGISTER_v1.0.0.json",
    "05_SCHEMAS/APEX_OS_MODULE_STATUS_RECORD.schema.json",
    "08_QUARANTINE/CONSENT_GATED_REFERENCE_BOUNDARY.md",
    "09_PENDING_RETRIEVAL/PENDING_EXTERNAL_CONTENT_REGISTER.md",
]


def validate_text_lane(path: Path, failures: list[str]) -> None:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        failures.append(f"unsupported binary or media file in governed text lane: {path}")
        return
    try:
        path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        failures.append(f"non-text payload in governed text lane: {path}")


def main() -> int:
    failures: list[str] = []
    canon_root = TARGET_ROOTS[0]
    if not canon_root.exists():
        failures.append(f"OS canon root is missing: {canon_root}")
    else:
        for relative in REQUIRED_CANON:
            if not (canon_root / relative).exists():
                failures.append(f"required OS canon artifact missing: {relative}")
    for target_root in TARGET_ROOTS:
        if target_root.exists():
            for path in target_root.rglob("*"):
                if path.is_file():
                    validate_text_lane(path, failures)
    if failures:
        print("APEX governed canon v0.2 validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("APEX governed canon v0.2 validation passed: required source-of-truth artifacts exist and the governed paths contain permitted text/code payloads only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
