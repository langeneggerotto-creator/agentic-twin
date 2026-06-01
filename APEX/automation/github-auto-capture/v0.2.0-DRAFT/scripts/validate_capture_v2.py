from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
CAPTURE_ROOT = REPO_ROOT / "APEX" / "runtime-captures"
TEXT_SUFFIXES = {".md", ".json", ".jsonl", ".yaml", ".yml", ".csv", ".txt", ".html", ".py", ".ps1", ".toml"}


def validate_text_artifact(path: Path, failures: list[str]) -> None:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        failures.append(f"file class not permitted in automatic text capture lane: {path}")
        return
    try:
        path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        failures.append(f"non-text payload found in automatic text capture lane: {path}")


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
            failures.append(f"manifest digest mismatch: {target}")


def main() -> int:
    failures: list[str] = []
    if not CAPTURE_ROOT.exists():
        print("No runtime captures are present yet; v0.2 validator ready.")
        return 0
    for path in CAPTURE_ROOT.rglob("*"):
        if path.is_file():
            validate_text_artifact(path, failures)
            if path.name == "capture_manifest.json":
                validate_manifest(path, failures)
    if failures:
        print("APEX ARX v0.2 automatic capture validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("APEX ARX v0.2 automatic capture validation passed: permitted text payloads are readable and manifest digests match.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
