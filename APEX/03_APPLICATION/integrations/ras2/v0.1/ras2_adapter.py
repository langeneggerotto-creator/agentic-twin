#!/usr/bin/env python3
"""
APEX RAS2 Adapter v0.1

Safe adaptation of the uploaded RAS2_System_Installer package.

Original package had useful ideas: text analysis, missing-field detection,
scoring, Word review, and GitHub sync. This adapter keeps the useful parts
but removes automatic git push and makes document review non-destructive.

Standard library only.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List


REQUIRED_FIELDS = [
    "objective",
    "risks",
    "implementation",
    "evidence",
    "owner",
    "next step",
]


@dataclass
class Ras2ApexRecord:
    artifact_type: str
    input_summary: str
    word_count: int
    detected_keywords: List[str]
    missing_fields: List[str]
    score: float
    review_notes: List[str]
    heart_core: Dict[str, Any]
    foresight: Dict[str, Any]
    repo_action: Dict[str, Any]
    truth_status: Dict[str, List[str]]
    manifest_hash_sha256: str = "pending"


def summarize(text: str, limit: int = 220) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    return clean if len(clean) <= limit else clean[:limit] + "..."


def keywords(text: str, limit: int = 30) -> List[str]:
    words = re.findall(r"[A-Za-z0-9_]+", text.lower())
    seen: List[str] = []
    for word in words:
        if len(word) < 4 or word in seen:
            continue
        seen.append(word)
        if len(seen) >= limit:
            break
    return seen


def missing_fields(text: str) -> List[str]:
    lower = text.lower()
    missing = []
    for field in REQUIRED_FIELDS:
        if field not in lower:
            missing.append(field)
    return missing


def score_from_missing(missing: List[str]) -> float:
    if not REQUIRED_FIELDS:
        return 1.0
    return round(max(0.0, 1.0 - (len(missing) / len(REQUIRED_FIELDS))), 3)


def review_notes(missing: List[str]) -> List[str]:
    if not missing:
        return ["No required planning gaps detected by the current RAS2 adapter."]
    return [f"Add or clarify: {field}." for field in missing]


def heart_core(missing: List[str]) -> Dict[str, Any]:
    return {
        "status": "HOLD" if missing else "PASS",
        "dignity_preserved": True,
        "truth_labels_present": True,
        "user_control_surface_present": True,
        "next_small_step": "Address the first missing field before expanding the artifact.",
        "human_control_delta": "positive",
        "minimal_law": "Keep the person whole while the product grows.",
    }


def foresight(missing: List[str]) -> Dict[str, Any]:
    return {
        "possible_futures": [
            "The artifact becomes clearer as missing fields are completed.",
            "The artifact stalls if gaps remain hidden.",
            "The artifact becomes safer if risks, evidence, owner, and next step are explicit.",
        ],
        "early_warning_signals": [
            "No objective is stated.",
            "Risks are absent.",
            "No implementation path or owner is named.",
        ],
        "recommended_next_step": "Complete the highest-priority missing field.",
        "rollback_trigger": "Rollback or pause if score decreases or review notes are ignored.",
        "missing_fields": missing,
    }


def repo_action_plan() -> Dict[str, Any]:
    return {
        "auto_push_enabled": False,
        "reason": "APEX blocks automatic git add, commit, and push without explicit human approval.",
        "allowed_next_action": "Prepare a change summary for human review.",
        "blocked_actions": ["git add .", "git commit", "git push"],
    }


def analyze(text: str) -> Ras2ApexRecord:
    missing = missing_fields(text)
    record = Ras2ApexRecord(
        artifact_type="apex_ras2_operational_intelligence_record",
        input_summary=summarize(text),
        word_count=len(text.split()),
        detected_keywords=keywords(text),
        missing_fields=missing,
        score=score_from_missing(missing),
        review_notes=review_notes(missing),
        heart_core=heart_core(missing),
        foresight=foresight(missing),
        repo_action=repo_action_plan(),
        truth_status={
            "VERIFIED": ["text analyzed by local adapter", "score calculated from configured required fields"],
            "INFERRED": ["missing planning fields", "review notes"],
            "ASSUMED": ["required fields are suitable for the current artifact type"],
            "UNKNOWN": ["real-world quality until human review", "document-specific requirements until provided"],
        },
    )
    payload = json.dumps(asdict(record), sort_keys=True, ensure_ascii=False)
    record.manifest_hash_sha256 = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return record


def main() -> None:
    sample = "Build an APEX feature with objective, risks, implementation, evidence, owner, and next step."
    print(json.dumps(asdict(analyze(sample)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
