#!/usr/bin/env python3
"""
APEX RAS2 Repository Evaluator v0.2

Purpose:
Evaluate APEX repository work at the system/repository level instead of only
checking whether a single text artifact contains required planning fields.

Standard library only. No git writes. No external network calls.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List


DIMENSIONS = [
    "vision_clarity",
    "repository_structure",
    "implementation_depth",
    "test_readiness",
    "heart_core_enforcement",
    "foresight_coverage",
    "rights_provenance",
    "drift_control",
    "human_control",
    "launch_readiness",
]


@dataclass
class Ras2RepositoryEvaluation:
    artifact_type: str
    evaluated_scope: str
    dimension_scores: Dict[str, float]
    overall_score: float
    strengths: List[str]
    gaps: List[str]
    predictions: Dict[str, List[str]]
    apex_upgrade_plan: Dict[str, Any]
    ras2_upgrade_plan: Dict[str, Any]
    heart_core: Dict[str, Any]
    foresight: Dict[str, Any]
    truth_status: Dict[str, List[str]]
    manifest_hash_sha256: str = "pending"


def clamp_score(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 3)


def has_any(text: str, terms: List[str]) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in terms)


def score_repository(summary: str) -> Dict[str, float]:
    """Heuristic RAS2 v0.2 scoring over a repo/work-summary text."""
    scores = {key: 0.0 for key in DIMENSIONS}

    scores["vision_clarity"] = 0.92 if has_any(summary, ["purpose", "vision", "perfect ai", "apex", "heart core"]) else 0.45
    scores["repository_structure"] = 0.80 if has_any(summary, ["00_index", "01_canon", "02_architecture", "03_application", "07_testing"]) else 0.40
    scores["implementation_depth"] = 0.72 if has_any(summary, ["python intent", "v0.3", "v0.4", "adapter", "implementation"]) else 0.35
    scores["test_readiness"] = 0.62 if has_any(summary, ["smoke test", "test_", "ci", "testing"]) else 0.25
    scores["heart_core_enforcement"] = 0.78 if has_any(summary, ["heart core", "dignity", "human control"]) else 0.30
    scores["foresight_coverage"] = 0.76 if has_any(summary, ["foresight", "rollback", "future", "early warning"]) else 0.30
    scores["rights_provenance"] = 0.74 if has_any(summary, ["rightschain", "rights", "provenance", "license", "source"]) else 0.30
    scores["drift_control"] = 0.44 if has_any(summary, ["root-level", "canonical", "migration", "drift"]) else 0.20
    scores["human_control"] = 0.78 if has_any(summary, ["human approval", "no-auto-push", "review", "control"]) else 0.35
    scores["launch_readiness"] = 0.43 if has_any(summary, ["not production", "ci not", "not yet", "launch readiness"]) else 0.25
    return {k: clamp_score(v) for k, v in scores.items()}


def weighted_overall(scores: Dict[str, float]) -> float:
    weights = {
        "vision_clarity": 1.0,
        "repository_structure": 1.0,
        "implementation_depth": 1.2,
        "test_readiness": 1.3,
        "heart_core_enforcement": 1.1,
        "foresight_coverage": 1.0,
        "rights_provenance": 1.0,
        "drift_control": 1.2,
        "human_control": 1.1,
        "launch_readiness": 1.4,
    }
    total_weight = sum(weights.values())
    total = sum(scores[k] * weights[k] for k in scores)
    return clamp_score(total / total_weight)


def evaluate(summary: str) -> Ras2RepositoryEvaluation:
    scores = score_repository(summary)
    overall = weighted_overall(scores)

    strengths = [
        "APEX has moved from concept into repository structure.",
        "Heart Core and Foresight are now documented and implemented in Python scaffolds.",
        "RAS2 has been safely adapted with auto-push blocked by default.",
        "Smoke test files exist for major new Python pieces.",
    ]

    gaps = [
        "CI execution is not yet verified.",
        "Root-level prototypes and APEX canonical paths can drift.",
        "Browser consoles are not yet aligned with the Python v0.4 kernel path.",
        "RAS2 scoring is still heuristic and needs evidence-ledger integration.",
    ]

    predictions = {
        "success_path": [
            "Create one canonical APEX kernel package.",
            "Run all smoke tests through CI.",
            "Align browser consoles to the same output schema.",
            "Use RAS2 as a recurring evaluator after every build session.",
        ],
        "failure_path": [
            "Continue adding modules without a unified record schema.",
            "Let old prototype paths drift from canonical APEX paths.",
            "Treat test files as proof before CI actually runs them.",
        ],
    }

    apex_upgrade_plan = {
        "next_1": "Build APEX/04_ENGINEERING/kernel/apex_kernel/records.py.",
        "next_2": "Build APEX/04_ENGINEERING/kernel/apex_kernel/ras2.py using this evaluator.",
        "next_3": "Create a GitHub Actions workflow that runs all smoke tests.",
        "plus_1_control": "Create a Drift Ledger for root-level prototype path versus APEX canonical path.",
    }

    ras2_upgrade_plan = {
        "v0_2_added": [
            "repository-level scoring",
            "weighted overall maturity score",
            "prediction path",
            "APEX upgrade plan",
            "RAS2 upgrade plan",
        ],
        "v0_3_should_add": [
            "read file manifests directly",
            "parse test results from CI logs",
            "track score deltas over time",
            "generate patch recommendations automatically",
        ],
    }

    heart_core = {
        "status": "HOLD" if overall < 0.80 else "PASS",
        "human_control_delta": "positive",
        "dignity_preserved": True,
        "next_small_step": "Unify the scoring output into the APEX kernel before adding more modules.",
        "minimal_law": "Keep the person whole while the product grows.",
    }

    foresight = {
        "possible_futures": [
            "APEX becomes a governed execution spine if kernelization and CI happen next.",
            "APEX remains a promising prototype collection if consolidation is delayed.",
            "RAS2 becomes valuable as the recurring evaluator if it tracks deltas over time.",
        ],
        "early_warning_signals": [
            "More modules are added before the kernel is unified.",
            "Test files exist but are not run automatically.",
            "Scores are reported without evidence snapshots.",
        ],
        "recommended_next_step": "Create the canonical APEX kernel and CI workflow.",
        "rollback_trigger": "Pause feature expansion if drift_control or test_readiness remains below 0.65 after the next build.",
    }

    record = Ras2RepositoryEvaluation(
        artifact_type="apex_ras2_repository_evaluation_v02",
        evaluated_scope="APEX repository work from current build session",
        dimension_scores=scores,
        overall_score=overall,
        strengths=strengths,
        gaps=gaps,
        predictions=predictions,
        apex_upgrade_plan=apex_upgrade_plan,
        ras2_upgrade_plan=ras2_upgrade_plan,
        heart_core=heart_core,
        foresight=foresight,
        truth_status={
            "VERIFIED": ["RAS2 v0.2 evaluator generated", "dimension scores calculated from supplied summary"],
            "INFERRED": ["maturity scores", "likely success and failure paths"],
            "ASSUMED": ["summary accurately represents repository state"],
            "UNKNOWN": ["CI execution status until workflow runs", "runtime browser behavior until tested"],
        },
    )
    payload = json.dumps(asdict(record), sort_keys=True, ensure_ascii=False)
    record.manifest_hash_sha256 = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return record


def main() -> None:
    summary = """
    APEX repository has 00_INDEX, 01_CANON, 02_ARCHITECTURE, 03_APPLICATION,
    04_ENGINEERING, 06_PRODUCT, and 07_TESTING. Heart Core, Foresight,
    Python Intent v0.3 and v0.4, RAS2 adapter, RightsChain, smoke tests,
    migration manifest, root-level prototypes, canonical APEX paths, not production,
    CI not verified, human approval and no-auto-push controls.
    """
    print(json.dumps(asdict(evaluate(summary)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
