"""Narrative + Emotional Architecture: stage-2 output contract for the
DreamMusicForge v2 pipeline (Story Architecture Engine + Emotional
Architecture Engine combined).

Dependency-free validator mirroring narrative_emotional_architecture.schema.json.
Consumes one Principle Kernel and one of its human_truths (see principle_kernel.py).
"""

VALID_CONFIDENCE = {"VERIFIED", "INFERRED", "ASSUMED", "UNKNOWN"}

REQUIRED_ETHICS_NON_GOAL = (
    "This kernel does not claim to guarantee any specific viewer belief, emotion, or decision."
)

NARRATIVE_STAGES = [
    "beginning", "catalyst", "conflict", "choice",
    "sacrifice", "transformation", "resolution", "reflection",
]


def validate_narrative_emotional_architecture(doc: dict) -> list[str]:
    errors = []

    for field in [
        "schema_version", "source_principle_id", "source_human_truth_id",
        "narrative", "what_changes", "emotional_waveform", "non_goals", "truth_status",
    ]:
        if field not in doc or doc[field] in (None, "", [], {}):
            errors.append(f"missing required field: {field}")

    if "truth_status" in doc and doc["truth_status"] not in VALID_CONFIDENCE:
        errors.append(f"truth_status must be one of {sorted(VALID_CONFIDENCE)}")

    narrative = doc.get("narrative")
    if isinstance(narrative, dict):
        for stage in NARRATIVE_STAGES:
            entry = narrative.get(stage)
            if not isinstance(entry, dict) or not entry.get("description"):
                errors.append(f"narrative.{stage}.description is required")
    elif "narrative" in doc:
        errors.append("narrative must be an object keyed by the eight story stages")

    what_changes = doc.get("what_changes")
    if isinstance(what_changes, dict):
        before = what_changes.get("before_state")
        after = what_changes.get("after_state")
        if not before:
            errors.append("what_changes.before_state is required")
        if not after:
            errors.append("what_changes.after_state is required")
        if before and after and before == after:
            errors.append("what_changes.before_state and after_state must differ -- the story must answer 'what changes?'")
    elif "what_changes" in doc:
        errors.append("what_changes must be an object with before_state and after_state")

    waveform = doc.get("emotional_waveform")
    if isinstance(waveform, list):
        if len(waveform) < 3:
            errors.append("emotional_waveform must have at least 3 beats to show an arc")

        orders = []
        referenced_stages = set()
        for i, beat in enumerate(waveform):
            for field in ["beat_id", "order", "emotion", "linked_narrative_stage"]:
                if beat.get(field) in (None, ""):
                    errors.append(f"emotional_waveform[{i}].{field} is required")

            stage = beat.get("linked_narrative_stage")
            if stage is not None and stage not in NARRATIVE_STAGES:
                errors.append(f"emotional_waveform[{i}].linked_narrative_stage must be one of {NARRATIVE_STAGES}")
            elif stage:
                referenced_stages.add(stage)

            order = beat.get("order")
            if isinstance(order, int):
                orders.append(order)

        if orders and (orders != sorted(orders) or len(orders) != len(set(orders))):
            errors.append("emotional_waveform beats must have strictly increasing, unique order values")

        missing_coverage = [s for s in NARRATIVE_STAGES if s not in referenced_stages]
        if missing_coverage:
            errors.append(f"emotional_waveform must reference every narrative stage at least once; missing: {missing_coverage}")
    elif "emotional_waveform" in doc:
        errors.append("emotional_waveform must be a list")

    non_goals = doc.get("non_goals")
    if isinstance(non_goals, list):
        if REQUIRED_ETHICS_NON_GOAL not in non_goals:
            errors.append(f"non_goals must include the required ethics constraint: {REQUIRED_ETHICS_NON_GOAL!r}")
    elif "non_goals" in doc:
        errors.append("non_goals must be a list")

    return errors


EXAMPLE_NARRATIVE_EMOTIONAL_ARCHITECTURE = {
    "schema_version": "1.0.0",
    "source_principle_id": "hope",
    "source_human_truth_id": "rebuilding_after_loss",
    "narrative": {
        "beginning": {"description": "A person stands in the wreckage of what they built, alone, at first light."},
        "catalyst": {"description": "Someone else asks them, plainly, what they're going to do now."},
        "conflict": {"description": "Every attempt to start again is met with visible evidence of how much was lost."},
        "choice": {"description": "They have to decide whether to walk away for good or pick up one piece."},
        "sacrifice": {"description": "They give up the comfort of grieving in place to risk failing again in public."},
        "transformation": {"description": "The first new piece goes up, imperfect, next to the ruin of the old."},
        "resolution": {"description": "The structure is still unfinished, but it is standing, and it is theirs."},
        "reflection": {"description": "The camera holds on the gap between what was and what is now being built, without narrating what it means."},
    },
    "what_changes": {
        "before_state": "convinced there is nothing left worth starting",
        "after_state": "takes one small, visible first action toward rebuilding",
    },
    "emotional_waveform": [
        {"beat_id": "b1", "order": 1, "emotion": "desolation", "linked_narrative_stage": "beginning"},
        {"beat_id": "b2", "order": 2, "emotion": "provocation", "linked_narrative_stage": "catalyst"},
        {"beat_id": "b3", "order": 3, "emotion": "frustration", "linked_narrative_stage": "conflict"},
        {"beat_id": "b4", "order": 4, "emotion": "tension", "linked_narrative_stage": "choice"},
        {"beat_id": "b5", "order": 5, "emotion": "vulnerability", "linked_narrative_stage": "sacrifice"},
        {"beat_id": "b6", "order": 6, "emotion": "tentative_hope", "linked_narrative_stage": "transformation"},
        {"beat_id": "b7", "order": 7, "emotion": "quiet_pride", "linked_narrative_stage": "resolution"},
        {"beat_id": "b8", "order": 8, "emotion": "wonder", "linked_narrative_stage": "reflection"},
    ],
    "non_goals": [
        REQUIRED_ETHICS_NON_GOAL,
        "This architecture does not specify shots, camera movement, or music -- those are downstream engine outputs.",
    ],
    "source": (
        "DreamMusicForge v2 Story Architecture Engine + Emotional Architecture Engine, worked example "
        "built on the Hope Principle Kernel's rebuilding_after_loss human truth."
    ),
    "truth_status": "ASSUMED",
}


if __name__ == "__main__":
    errors = validate_narrative_emotional_architecture(EXAMPLE_NARRATIVE_EMOTIONAL_ARCHITECTURE)
    if errors:
        raise SystemExit("FAIL: " + "; ".join(errors))
    print("PASS: example Narrative + Emotional Architecture is valid")
