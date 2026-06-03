from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "README.md",
    "index.html",
    "styles.css",
    "app.js",
    "Start-DreamDraw.ps1",
    "docs/PRODUCT_SPEC.md",
    "schemas/dream_record.schema.json",
    "schemas/feedback_record.schema.json",
    "evidence/BUILD_RECEIPT.json",
    "evidence/PILOT-DD-001_REAL_INPUT_RECORD.md",
    "integration/APEX_MIRROR_DREAM_DRAW_STATUS_CONTRACT_v0.1.0.md",
]
REQUIRED_HTML_IDS = [
    "dreamForm", "dream", "resultContent", "bestMove", "whyNow", "watchOut",
    "horizons", "feedbackStatus", "exportBtn", "resetBtn"
]
REQUIRED_TRUTH_PHRASES = [
    "PROTOTYPE_RECOMMENDATION_NOT_OUTCOME_PROOF",
    "not a validated outcome prediction",
    "NOT YET EXECUTED",
    "NOT_YET_VALIDATED",
]


def main() -> int:
    failures: list[str] = []
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).exists():
            failures.append(f"required MVP file missing: {relative}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    for relative in ["schemas/dream_record.schema.json", "schemas/feedback_record.schema.json", "evidence/BUILD_RECEIPT.json"]:
        try:
            json.loads((ROOT / relative).read_text(encoding="utf-8"))
        except Exception as exc:
            failures.append(f"invalid JSON file {relative}: {exc}")

    html = (ROOT / "index.html").read_text(encoding="utf-8")
    for item_id in REQUIRED_HTML_IDS:
        if f'id="{item_id}"' not in html:
            failures.append(f"required interface control not found: {item_id}")

    combined_truth_text = "\n".join([
        (ROOT / "schemas/dream_record.schema.json").read_text(encoding="utf-8"),
        (ROOT / "docs/PRODUCT_SPEC.md").read_text(encoding="utf-8"),
        (ROOT / "evidence/PILOT-DD-001_REAL_INPUT_RECORD.md").read_text(encoding="utf-8"),
        (ROOT / "integration/APEX_MIRROR_DREAM_DRAW_STATUS_CONTRACT_v0.1.0.md").read_text(encoding="utf-8"),
    ])
    for phrase in REQUIRED_TRUTH_PHRASES:
        if phrase not in combined_truth_text:
            failures.append(f"truth-boundary phrase missing: {phrase}")

    source_text = (ROOT / "app.js").read_text(encoding="utf-8")
    for source_token in ["localStorage", "createRecord", "PROTOTYPE_RECOMMENDATION_NOT_OUTCOME_PROOF", "DREAM_DRAW_LOCAL_EVIDENCE_EXPORT"]:
        if source_token not in source_text:
            failures.append(f"application engine contract token missing: {source_token}")

    if failures:
        print("Dream Draw MVP validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Dream Draw MVP validation passed: runnable-source baseline, evidence boundary and Mirror contract are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
