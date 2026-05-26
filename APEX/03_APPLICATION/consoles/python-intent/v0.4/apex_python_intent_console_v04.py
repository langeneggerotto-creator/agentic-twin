#!/usr/bin/env python3
"""
APEX Python Intent Console v0.4

Adds the APEX Foresight Engine to the v0.3 Heart Core scaffold.
Standard library only.
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
    foresight_engine: Dict[str, Any]
    qa_gates: Dict[str, Any]
    heart_core: Dict[str, Any]
    next_3_plus_1: Dict[str, Any]
    truth_status: Dict[str, List[str]]
    manifest_hash_sha256: str = "pending"


def summarize(text: str, limit: int = 220) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    return clean if len(clean) <= limit else clean[:limit] + "..."


def contains_any(text: str, terms: List[str]) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in terms)


def infer_modules(text: str) -> List[str]:
    modules: List[str] = []
    if contains_any(text, ["future", "foresight", "roadmap", "predict", "scenario", "vision", "next"]):
        modules.append("foresight")
    if contains_any(text, ["video", "youtube", "transcript", "frame", "reel", "short"]):
        modules += ["video_analysis", "media", "intake", "rights", "qa"]
    if contains_any(text, ["image", "photo", "camera", "cinema", "music", "audio", "voice"]):
        modules.append("media")
    if contains_any(text, ["rights", "credit", "source", "permission", "license", "provenance"]):
        modules.append("rights")
    if contains_any(text, ["test", "qa", "debug", "fix", "repair"]):
        modules += ["qa", "debug"]
    if not modules:
        modules.append("build")
    return sorted(set(modules))


def infer_risks(text: str) -> List[str]:
    risks: List[str] = []
    if contains_any(text, ["future", "predict", "forecast", "guarantee"]):
        risks.append("uncertainty_review_needed")
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
        "Attach QA, rights, truth-status, Heart Core, and Foresight checks.",
    ]
    if "foresight" in modules:
        plan.append("Map possible futures without claiming certainty.")
    if "video_analysis" in modules:
        plan.append("Use only allowed inputs such as user notes, transcript text, owned files, or permitted metadata.")
    if "rights" in modules:
        plan.append("Create a source, contributor, permission, and release record before public use.")
    if "media" in modules:
        plan.append("Generate original media directions instead of copying protected expression.")
    return plan


def foresight_engine(text: str, modules: List[str], risks: List[str]) -> Dict[str, Any]:
    possible_futures = [
        "Prototype stays useful as a planning scaffold.",
        "Prototype becomes a reusable APEX module after tests pass.",
        "Prototype creates risk if users treat inferred outputs as verified truth.",
    ]
    if "video_analysis" in modules:
        possible_futures.append("Video intake becomes powerful once transcript, metadata, and permission workflows are formalized.")
    if "foresight" in modules:
        possible_futures.append("Foresight outputs become a standard decision layer across APEX apps.")
    return {
        "vision": summarize(text),
        "possible_futures": possible_futures,
        "key_assumptions": [
            "The user wants an APEX environment improvement.",
            "The next build should remain small, testable, and reversible.",
            "Permission and evidence must be checked before public release.",
        ],
        "early_warning_signals": [
            "Output claims certainty about future outcomes.",
            "User cannot inspect or reverse the generated plan.",
            "Rights or platform permission is unknown but treated as cleared.",
        ],
        "decision_options": [
            "Option A: document only.",
            "Option B: build a small scaffold with tests.",
            "Option C: promote only after QA, Heart Core, and rights gates pass.",
        ],
        "recommended_next_step": "Build or test the smallest reversible module slice first.",
        "rollback_trigger": "Rollback if QA score fails, Heart Core returns FAIL, or rights status is unknown for public use.",
        "truth_status": {
            "VERIFIED": ["input was captured", "record was generated"],
            "INFERRED": ["module routing", "risk flags", "future scenarios"],
            "ASSUMED": ["user wants a useful next build"],
            "UNKNOWN": ["real-world adoption", "future outcomes", "external permissions"],
        },
    }


def qa_gates(text: str, modules: List[str], risks: List[str]) -> Dict[str, Any]:
    issues: List[str] = []
    passes: List[str] = []
    if len(text.strip()) >= 20:
        passes.append("input_length_ok")
    else:
        issues.append("input_too_short")
    if modules:
        passes.append("module_routing_present")
    if "foresight" in modules:
        passes.append("foresight_engine_present")
    for risk in risks:
        issues.append("review_" + risk)
    score = max(0, min(100, 100 - 12 * len(issues) + 4 * len(passes)))
    return {"score": score, "passes": passes, "issues": issues, "release_status": "HOLD_FOR_REVIEW" if issues else "PROTOTYPE_OK"}


def heart_core_block(risks: List[str]) -> Dict[str, Any]:
    review_needed = bool(risks)
    return {
        "status": "HOLD" if review_needed else "PASS",
        "truth_labels_present": True,
        "user_control_surface_present": True,
        "dignity_preserved": True,
        "rights_review_needed": "rights_review_needed" in risks or "source_permission_unknown" in risks,
        "sensitive_context_review_needed": "youth_review_needed" in risks,
        "next_small_step": "Review the generated plan, then approve or edit only the smallest next action.",
        "human_control_delta": "positive",
        "minimal_law": "Keep the person whole while the product grows.",
    }


def next_3_plus_1(risks: List[str]) -> Dict[str, Any]:
    return {
        "next_1": "Run this module on one real sample input.",
        "next_2": "Add one assertion test for routing, Heart Core, and Foresight output.",
        "next_3": "Create a RightsChain record before public reuse.",
        "plus_1_control": "Require uncertainty labels for every future-facing recommendation.",
        "stop_rule": "Do not promote outputs while review flags remain unresolved.",
        "risk_flags": risks,
    }


def make_record(text: str) -> ApexIntentRecord:
    modules = infer_modules(text)
    risks = infer_risks(text)
    record = ApexIntentRecord(
        artifact_type="apex_python_intent_plan_v04",
        input_summary=summarize(text),
        modules=modules,
        risk_flags=risks,
        plan=build_plan(modules),
        foresight_engine=foresight_engine(text, modules, risks),
        qa_gates=qa_gates(text, modules, risks),
        heart_core=heart_core_block(risks),
        next_3_plus_1=next_3_plus_1(risks),
        truth_status={
            "VERIFIED": ["input captured", "standard library scaffold generated"],
            "INFERRED": ["modules", "risk flags", "plan", "foresight scenarios"],
            "ASSUMED": ["user wants an APEX environment improvement"],
            "UNKNOWN": ["production suitability until tested", "future outcomes until observed", "permissions until reviewed"],
        },
    )
    payload = json.dumps(asdict(record), sort_keys=True, ensure_ascii=False)
    record.manifest_hash_sha256 = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return record


def main() -> None:
    sample = "Build the next APEX console feature with foresight, Heart Core, rights review, and tests."
    print(json.dumps(asdict(make_record(sample)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
