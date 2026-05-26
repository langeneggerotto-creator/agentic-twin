#!/usr/bin/env python3
"""
APEX Python Intent Console v0.3

Purpose:
Convert plain text or chat instructions into an APEX aligned Python plan with
Heart Core fields included in the output record.

Boundary:
Standard library only. This scaffold creates an improvement plan and does not
perform external downloads, publishing, repo writes, or expert review.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List


@dataclass
class ApexIntentRecord:
    artifact_type: str
    input_summary: str
    modules: List[str]
    risk_flags: List[str]
    plan: List[str]
    qa_gates: Dict[str, Any]
    heart_core: Dict[str, Any]
    next_3_plus_1: Dict[str, Any]
    truth_status: Dict[str, List[str]]
    manifest_hash_sha256: str = "pending"


def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def summarize(text: str, limit: int = 220) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    return clean if len(clean) <= limit else clean[:limit] + "..."


def contains_any(text: str, terms: List[str]) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in terms)


def infer_modules(text: str) -> List[str]:
    modules: List[str] = []
    if contains_any(text, ["video", "youtube", "transcript", "frame", "reel", "short"]):
        modules += ["video_analysis", "media", "intake", "rights", "qa"]
    if contains_any(text, ["image", "photo", "camera", "cinema", "music", "audio", "voice"]):
        modules += ["media"]
    if contains_any(text, ["rights", "credit", "source", "permission", "license", "provenance"]):
        modules += ["rights"]
    if contains_any(text, ["test", "qa", "debug", "fix", "repair"]):
        modules += ["qa", "debug"]
    if contains_any(text, ["game", "rules", "learning", "drawing", "memory"]):
        modules += ["game"]
    if not modules:
        modules.append("build")
    return sorted(set(modules))


def infer_risks(text: str) -> List[str]:
    risks: List[str] = []
    if contains_any(text, ["youtube", "tiktok", "instagram", "facebook", "music video"]):
        risks += ["platform_review_needed", "source_permission_unknown"]
    if contains_any(text, ["child", "children", "minor", "teen", "student"]):
        risks.append("youth_review_needed")
    if contains_any(text, ["copyright", "license", "artist", "song", "movie"]):
        risks.append("rights_review_needed")
    if contains_any(text, ["always", "never", "guarantee", "100%"]):
        risks.append("certainty_language_review_needed")
    return sorted(set(risks))


def build_plan(modules: List[str]) -> List[str]:
    plan = [
        "Preserve the original user intent.",
        "Infer the APEX modules needed for the task.",
        "Create the smallest useful artifact plan first.",
        "Attach QA, rights, truth-status, and Heart Core checks.",
    ]
    if "video_analysis" in modules:
        plan.append("Use only allowed inputs such as user notes, transcript text, owned files, or permitted metadata.")
    if "rights" in modules:
        plan.append("Create a source, contributor, permission, and release record before public use.")
    if "media" in modules:
        plan.append("Generate original media directions instead of copying protected expression.")
    return plan


def qa_gates(text: str, modules: List[str], risks: List[str]) -> Dict[str, Any]:
    issues: List[str] = []
    passes: List[str] = []
    if len(text.strip()) >= 20:
        passes.append("input_length_ok")
    else:
        issues.append("input_too_short")
    if modules:
        passes.append("module_routing_present")
    for risk in risks:
        issues.append("review_" + risk)
    score = max(0, min(100, 100 - 12 * len(issues) + 4 * len(passes)))
    return {
        "score": score,
        "passes": passes,
        "issues": issues,
        "release_status": "HOLD_FOR_REVIEW" if issues else "PROTOTYPE_OK",
    }


def heart_core_block(text: str, risks: List[str]) -> Dict[str, Any]:
    truth_labels_present = True
    user_control_surface_present = True
    next_small_step = "Review the generated plan, then approve or edit only the smallest next action."
    review_needed = bool(risks)
    return {
        "status": "HOLD" if review_needed else "PASS",
        "truth_labels_present": truth_labels_present,
        "user_control_surface_present": user_control_surface_present,
        "dignity_preserved": True,
        "rights_review_needed": "rights_review_needed" in risks or "source_permission_unknown" in risks,
        "sensitive_context_review_needed": "youth_review_needed" in risks,
        "next_small_step": next_small_step,
        "human_control_delta": "positive",
        "minimal_law": "Keep the person whole while the product grows.",
    }


def next_3_plus_1(risks: List[str]) -> Dict[str, Any]:
    return {
        "next_1": "Run this module on one real sample input.",
        "next_2": "Add one assertion test for routing and Heart Core output.",
        "next_3": "Create a RightsChain record before public reuse.",
        "plus_1_control": "Require Heart Core status before promotion.",
        "stop_rule": "Do not promote outputs while review flags remain unresolved.",
        "risk_flags": risks,
    }


def make_record(text: str) -> ApexIntentRecord:
    modules = infer_modules(text)
    risks = infer_risks(text)
    record = ApexIntentRecord(
        artifact_type="apex_python_intent_plan_v03",
        input_summary=summarize(text),
        modules=modules,
        risk_flags=risks,
        plan=build_plan(modules),
        qa_gates=qa_gates(text, modules, risks),
        heart_core=heart_core_block(text, risks),
        next_3_plus_1=next_3_plus_1(risks),
        truth_status={
            "VERIFIED": ["input captured", "standard library scaffold generated"],
            "INFERRED": ["modules", "risk flags", "plan"],
            "ASSUMED": ["user wants an APEX environment improvement"],
            "UNKNOWN": ["production suitability until tested", "permissions until reviewed"],
        },
    )
    payload = json.dumps(asdict(record), sort_keys=True, ensure_ascii=False)
    record.manifest_hash_sha256 = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return record


def main() -> None:
    sample = (
        "Build an APEX module that accepts a YouTube URL or uploaded video, "
        "extracts a rights-safe analysis plan, generates a storyboard, and includes Heart Core checks."
    )
    print(json.dumps(asdict(make_record(sample)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
