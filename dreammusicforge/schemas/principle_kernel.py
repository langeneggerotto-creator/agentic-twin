"""Principle Kernel: stage-1 output contract for the DreamMusicForge v2 pipeline.

Dependency-free validator mirroring principle_kernel.schema.json, so the
contract can be checked without adding a jsonschema dependency to the repo.
"""

VALID_CONFIDENCE = {"VERIFIED", "INFERRED", "ASSUMED", "UNKNOWN"}

REQUIRED_ETHICS_NON_GOAL = (
    "This kernel does not claim to guarantee any specific viewer belief, emotion, or decision."
)


def validate_principle_kernel(kernel: dict) -> list[str]:
    errors = []

    for field in [
        "schema_version", "principle_id", "principle_name", "kernel_statement",
        "polarity", "human_truths", "transformation_goal_seed", "non_goals", "truth_status",
    ]:
        if field not in kernel or kernel[field] in (None, "", []):
            errors.append(f"missing required field: {field}")

    if "truth_status" in kernel and kernel["truth_status"] not in VALID_CONFIDENCE:
        errors.append(f"truth_status must be one of {sorted(VALID_CONFIDENCE)}")

    polarity = kernel.get("polarity")
    if isinstance(polarity, dict):
        for pole in ["principle_pole", "opposing_pole"]:
            if not polarity.get(pole):
                errors.append(f"polarity.{pole} is required")
    elif "polarity" in kernel:
        errors.append("polarity must be an object with principle_pole and opposing_pole")

    human_truths = kernel.get("human_truths")
    if isinstance(human_truths, list):
        if len(human_truths) < 1:
            errors.append("human_truths must contain at least one entry")
        for i, truth in enumerate(human_truths):
            for field in ["human_truth_id", "description", "before_state", "after_state", "confidence"]:
                if not truth.get(field):
                    errors.append(f"human_truths[{i}].{field} is required")
            if "confidence" in truth and truth["confidence"] not in VALID_CONFIDENCE:
                errors.append(f"human_truths[{i}].confidence must be one of {sorted(VALID_CONFIDENCE)}")
    elif "human_truths" in kernel:
        errors.append("human_truths must be a list")

    non_goals = kernel.get("non_goals")
    if isinstance(non_goals, list):
        if REQUIRED_ETHICS_NON_GOAL not in non_goals:
            errors.append(f"non_goals must include the required ethics constraint: {REQUIRED_ETHICS_NON_GOAL!r}")
    elif "non_goals" in kernel:
        errors.append("non_goals must be a list")

    return errors


EXAMPLE_PRINCIPLE_KERNEL = {
    "schema_version": "1.0.0",
    "principle_id": "hope",
    "principle_name": "Hope",
    "kernel_statement": (
        "Believing a better outcome is possible changes what a person is willing to attempt, "
        "even before evidence confirms it."
    ),
    "polarity": {"principle_pole": "hope", "opposing_pole": "despair"},
    "human_truths": [
        {
            "human_truth_id": "rebuilding_after_loss",
            "description": "Someone who lost something they built starts building again, before they feel ready.",
            "before_state": "convinced there is nothing left worth starting",
            "after_state": "takes one small, visible first action toward rebuilding",
            "confidence": "ASSUMED",
        },
        {
            "human_truth_id": "believing_despite_uncertainty",
            "description": "Someone commits to a course of action without proof it will work.",
            "before_state": "waiting for certainty before acting",
            "after_state": "acts on the best available reason, uncertainty intact",
            "confidence": "ASSUMED",
        },
    ],
    "transformation_goal_seed": (
        "May help an audience member feel that starting again, without guarantees, is a legitimate "
        "response to loss -- not a claim that they will feel this."
    ),
    "non_goals": [
        REQUIRED_ETHICS_NON_GOAL,
        "This kernel does not specify the final narrative, characters, or visuals -- those are downstream engine outputs.",
    ],
    "source": "DreamMusicForge v2 Principle Engine, worked example.",
    "truth_status": "ASSUMED",
}


if __name__ == "__main__":
    errors = validate_principle_kernel(EXAMPLE_PRINCIPLE_KERNEL)
    if errors:
        raise SystemExit("FAIL: " + "; ".join(errors))
    print("PASS: example Principle Kernel is valid")
