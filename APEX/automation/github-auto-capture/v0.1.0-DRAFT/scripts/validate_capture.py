from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CAPTURE_ROOT = ROOT / "APEX" / "runtime-captures"
BLOCKED_EXTENSIONS = {".env", ".pem", ".key", ".pfx", ".p12", ".sqlite", ".db", ".kdbx"}
BLOCKED_NAME_FRAGMENTS = {"credential", "private-key", "password", "local-secret"}
SENSITIVE_MARKERS = {
    "BEGIN PRIVATE KEY",
    "BEGIN RSA PRIVATE KEY",
    "Authorization: Bearer",
    "client_secret",
    "private_key",
}


def validate_file(path: Path, failures: list[str]) -> None:
    lower_name = path.name.lower()
    if path.suffix.lower() in BLOCKED_EXTENSIONS:
        failures.append(f"blocked extension committed: {path}")
    if any(fragment in lower_name for fragment in BLOCKED_NAME_FRAGMENTS):
        failures.append(f"blocked sensitive filename committed: {path}")
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        failures.append(f"binary file found in text auto-capture lane: {path}")
        return
    for marker in SENSITIVE_MARKERS:
        if marker in content:
            failures.append(f"sensitive marker found in captured text: {path}")


def validate_manifest(manifest_path: Path, failures: list[str]) -> None:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        failures.append(f"invalid manifest {manifest_path}: {exc}")
        return
    for item in manifest.get("approved_files", []):
        target = manifest_path.parent / item["file"]
        if not target.exists():
            failures.append(f"manifest references missing file: {target}")
            continue
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        expected = item.get("sha256")
        if expected != actual:
            failures.append(f"manifest SHA mismatch: {target}")


def main() -> int:
    failures: list[str] = []
    if not CAPTURE_ROOT.exists():
        print("No runtime captures are present yet; validator ready.")
        return 0
    for path in CAPTURE_ROOT.rglob("*"):
        if not path.is_file():
            continue
        validate_file(path, failures)
        if path.name == "capture_manifest.json":
            validate_manifest(path, failures)
    if failures:
        print("APEX ARX automatic capture validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("APEX ARX automatic capture validation passed: captured artifacts are structurally acceptable and manifest hashes match.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
