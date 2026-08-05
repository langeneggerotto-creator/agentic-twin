"""Editorial Architecture: stage-5 output contract for the DreamMusicForge
v2 pipeline (Editorial Architecture Engine) -- the last engine before a
Provider-Specific Production Package is assembled.

Three validators are provided:

- validate_editorial_architecture(doc): structural checks within this
  document alone (timeline monotonicity, motif evolution actually
  evolves, callback ordering, ending-type discipline).
- validate_against_cinematic_architecture(doc, cinematic_doc): every
  edit_timeline shot_id must exist in the paired Cinematic Architecture,
  and every one of that document's shots must be covered by at least
  one cut.
- validate_against_musical_architecture(doc, musical_doc): every
  beat-matched cut's linked_tempo_segment_id must exist in the paired
  Musical Architecture's tempo_map.
"""

VALID_CONFIDENCE = {"VERIFIED", "INFERRED", "ASSUMED", "UNKNOWN"}

REQUIRED_ETHICS_NON_GOAL = (
    "This kernel does not claim to guarantee any specific viewer belief, emotion, or decision."
)

MOTIF_STAGES = {"introduced", "recurred", "transformed", "resolved"}
MOTIF_TERMINAL_STAGES = {"transformed", "resolved"}
ENDING_TYPES = {"resolution_stated", "reflection_open_ended", "ambiguous"}


def validate_editorial_architecture(doc: dict) -> list[str]:
    errors = []

    for field in [
        "schema_version", "source_principle_id", "source_human_truth_id",
        "edit_timeline", "motif_evolution", "visual_callbacks", "ending",
        "pacing_notes", "non_goals", "truth_status",
    ]:
        if field not in doc or doc[field] in (None, "", [], {}):
            errors.append(f"missing required field: {field}")

    if "truth_status" in doc and doc["truth_status"] not in VALID_CONFIDENCE:
        errors.append(f"truth_status must be one of {sorted(VALID_CONFIDENCE)}")

    edit_timeline = doc.get("edit_timeline")
    cut_ids_by_order = {}
    if isinstance(edit_timeline, list):
        if len(edit_timeline) < 8:
            errors.append("edit_timeline must contain at least 8 cuts (one per shot)")

        orders, start_times = [], []
        for i, cut in enumerate(edit_timeline):
            for field in ["cut_id", "order", "shot_id", "start_time_seconds", "duration_seconds", "cut_on_beat"]:
                if field not in cut or cut[field] in (None, ""):
                    errors.append(f"edit_timeline[{i}].{field} is required")

            if cut.get("cut_on_beat") and not cut.get("linked_tempo_segment_id"):
                errors.append(f"edit_timeline[{i}].linked_tempo_segment_id is required when cut_on_beat is true")

            duration = cut.get("duration_seconds")
            if isinstance(duration, (int, float)) and duration <= 0:
                errors.append(f"edit_timeline[{i}].duration_seconds must be positive")

            order = cut.get("order")
            if isinstance(order, int):
                orders.append(order)
                if cut.get("cut_id"):
                    cut_ids_by_order[cut["cut_id"]] = order

            start_time = cut.get("start_time_seconds")
            if isinstance(start_time, (int, float)):
                start_times.append(start_time)

        if orders and (orders != sorted(orders) or len(orders) != len(set(orders))):
            errors.append("edit_timeline cuts must have strictly increasing, unique order values")
        if start_times and start_times != sorted(start_times):
            errors.append("edit_timeline cuts must have strictly increasing start_time_seconds")
    elif "edit_timeline" in doc:
        errors.append("edit_timeline must be a list")

    motif_evolution = doc.get("motif_evolution")
    if isinstance(motif_evolution, list):
        by_motif: dict = {}
        for i, entry in enumerate(motif_evolution):
            for field in ["motif_id", "order", "cut_id", "stage", "state_description"]:
                if field not in entry or entry[field] in (None, ""):
                    errors.append(f"motif_evolution[{i}].{field} is required")
            stage = entry.get("stage")
            if stage is not None and stage not in MOTIF_STAGES:
                errors.append(f"motif_evolution[{i}].stage must be one of {sorted(MOTIF_STAGES)}")
            motif_id = entry.get("motif_id")
            if motif_id:
                by_motif.setdefault(motif_id, []).append(entry)

        for motif_id, entries in by_motif.items():
            if len(entries) < 2:
                errors.append(f"motif '{motif_id}' has only {len(entries)} entry -- a motif must evolve across at least 2 beats")
                continue
            ordered = sorted(entries, key=lambda e: e.get("order", 0))
            if ordered[0].get("stage") != "introduced":
                errors.append(f"motif '{motif_id}' must begin with stage 'introduced'")
            if ordered[-1].get("stage") not in MOTIF_TERMINAL_STAGES:
                errors.append(f"motif '{motif_id}' must end with stage 'transformed' or 'resolved', got '{ordered[-1].get('stage')}'")
    elif "motif_evolution" in doc:
        errors.append("motif_evolution must be a list")

    visual_callbacks = doc.get("visual_callbacks")
    if isinstance(visual_callbacks, list):
        if len(visual_callbacks) < 1:
            errors.append("visual_callbacks must contain at least one setup/payoff pair")
        for i, cb in enumerate(visual_callbacks):
            for field in ["callback_id", "setup_cut_id", "payoff_cut_id", "description"]:
                if not cb.get(field):
                    errors.append(f"visual_callbacks[{i}].{field} is required")
            setup_id, payoff_id = cb.get("setup_cut_id"), cb.get("payoff_cut_id")
            if cut_ids_by_order and setup_id and payoff_id:
                if setup_id not in cut_ids_by_order:
                    errors.append(f"visual_callbacks[{i}].setup_cut_id '{setup_id}' is not in edit_timeline")
                elif payoff_id not in cut_ids_by_order:
                    errors.append(f"visual_callbacks[{i}].payoff_cut_id '{payoff_id}' is not in edit_timeline")
                elif cut_ids_by_order[payoff_id] <= cut_ids_by_order[setup_id]:
                    errors.append(f"visual_callbacks[{i}]: payoff_cut_id '{payoff_id}' must occur after setup_cut_id '{setup_id}'")
    elif "visual_callbacks" in doc:
        errors.append("visual_callbacks must be a list")

    ending = doc.get("ending")
    if isinstance(ending, dict):
        ending_type = ending.get("type")
        if ending_type is not None and ending_type not in ENDING_TYPES:
            errors.append(f"ending.type must be one of {sorted(ENDING_TYPES)}")
        if not ending.get("description"):
            errors.append("ending.description is required")
        if ending_type == "resolution_stated" and not ending.get("explicit_statement_rationale"):
            errors.append("ending.explicit_statement_rationale is required when ending.type is 'resolution_stated'")
    elif "ending" in doc:
        errors.append("ending must be an object")

    non_goals = doc.get("non_goals")
    if isinstance(non_goals, list):
        if REQUIRED_ETHICS_NON_GOAL not in non_goals:
            errors.append(f"non_goals must include the required ethics constraint: {REQUIRED_ETHICS_NON_GOAL!r}")
    elif "non_goals" in doc:
        errors.append("non_goals must be a list")

    return errors


def validate_against_cinematic_architecture(doc: dict, cinematic_doc: dict) -> list[str]:
    errors = []

    if doc.get("source_principle_id") != cinematic_doc.get("source_principle_id"):
        errors.append("source_principle_id does not match the paired cinematic document")
    if doc.get("source_human_truth_id") != cinematic_doc.get("source_human_truth_id"):
        errors.append("source_human_truth_id does not match the paired cinematic document")

    shot_ids = {s.get("shot_id") for s in cinematic_doc.get("shots", []) if isinstance(s, dict)}
    referenced = set()

    for i, cut in enumerate(doc.get("edit_timeline", [])):
        shot_id = cut.get("shot_id")
        if not shot_id:
            continue
        if shot_id not in shot_ids:
            errors.append(f"edit_timeline[{i}].shot_id '{shot_id}' is not in the cinematic document's shots")
        else:
            referenced.add(shot_id)

    missing = shot_ids - referenced
    if missing:
        errors.append(f"edit_timeline does not cover every cinematic shot; missing: {sorted(missing)}")

    return errors


def validate_against_musical_architecture(doc: dict, musical_doc: dict) -> list[str]:
    errors = []

    segment_ids = {s.get("segment_id") for s in musical_doc.get("tempo_map", []) if isinstance(s, dict)}

    for i, cut in enumerate(doc.get("edit_timeline", [])):
        if not cut.get("cut_on_beat"):
            continue
        segment_id = cut.get("linked_tempo_segment_id")
        if segment_id and segment_id not in segment_ids:
            errors.append(f"edit_timeline[{i}].linked_tempo_segment_id '{segment_id}' is not in the musical document's tempo_map")

    return errors


EXAMPLE_EDITORIAL_ARCHITECTURE = {
    "schema_version": "1.0.0",
    "source_principle_id": "hope",
    "source_human_truth_id": "rebuilding_after_loss",
    "edit_timeline": [
        # cut1/cut2 durations are REAL, not planned: the first two live Kling AI Avatar
        # generations both came back at 10.04s regardless of the originally-planned 4.5s/5.0s
        # (see providers/kling_ai_avatar.py's DEFAULT_BASE_URL caveat -- duration_seconds in
        # provider_parameters was not honored). Replanned around what the provider actually
        # delivers rather than forcing a >100% drift through reconciliation -- see
        # assembly_package.py's REQUIRED_ASSEMBLY_NON_GOAL discipline against silently
        # papering over exactly this. cut3-cut8 durations remain planned/ASSUMED pending
        # their own real generations, which will likely need the same treatment.
        {"cut_id": "cut1", "order": 1, "shot_id": "shot1", "start_time_seconds": 0.0, "duration_seconds": 10.04, "cut_on_beat": True, "linked_tempo_segment_id": "seg1"},
        {"cut_id": "cut2", "order": 2, "shot_id": "shot2", "start_time_seconds": 10.04, "duration_seconds": 10.04, "cut_on_beat": True, "linked_tempo_segment_id": "seg2"},
        {"cut_id": "cut3", "order": 3, "shot_id": "shot3", "start_time_seconds": 20.08, "duration_seconds": 4.6, "cut_on_beat": True, "linked_tempo_segment_id": "seg3", "reveal_note": "first clear view of the two broken pieces"},
        {"cut_id": "cut4", "order": 4, "shot_id": "shot4", "start_time_seconds": 24.68, "duration_seconds": 3.2, "cut_on_beat": True, "linked_tempo_segment_id": "seg4"},
        {"cut_id": "cut5", "order": 5, "shot_id": "shot5", "start_time_seconds": 27.88, "duration_seconds": 5.8, "cut_on_beat": True, "linked_tempo_segment_id": "seg5"},
        {"cut_id": "cut6", "order": 6, "shot_id": "shot6", "start_time_seconds": 33.68, "duration_seconds": 4.9, "cut_on_beat": True, "linked_tempo_segment_id": "seg6", "reveal_note": "first new plank set in place"},
        {"cut_id": "cut7", "order": 7, "shot_id": "shot7", "start_time_seconds": 38.58, "duration_seconds": 6.4, "cut_on_beat": True, "linked_tempo_segment_id": "seg7", "reveal_note": "unfinished structure standing beside the ruin"},
        {"cut_id": "cut8", "order": 8, "shot_id": "shot8", "start_time_seconds": 44.98, "duration_seconds": 7.0, "cut_on_beat": True, "linked_tempo_segment_id": "seg8"},
    ],
    "motif_evolution": [
        {"motif_id": "rebuilt_object", "order": 1, "cut_id": "cut3", "stage": "introduced", "state_description": "the two broken pieces cannot be joined"},
        {"motif_id": "rebuilt_object", "order": 2, "cut_id": "cut6", "stage": "transformed", "state_description": "the first new plank is set in place, not a repair of the old pieces but a new start beside them"},
        {"motif_id": "rebuilt_object", "order": 3, "cut_id": "cut7", "stage": "resolved", "state_description": "the structure stands, unfinished, beside the ruin"},
    ],
    "visual_callbacks": [
        {
            "callback_id": "cb1",
            "setup_cut_id": "cut1",
            "payoff_cut_id": "cut8",
            "description": "cut1's abnormal headroom and extreme-small framing (isolation imposed by loss) recurs at cut8 with the same composition, now chosen -- a silhouette against the horizon rather than a figure dwarfed by wreckage",
        }
    ],
    "ending": {
        "type": "reflection_open_ended",
        "description": "The final cut holds on the silhouette without narrating what it means; the formal rhyme to cut1 is legible, but the audience is left to draw their own conclusion about what changed.",
    },
    "pacing_notes": "Cuts are beat-matched to every tempo_map segment; duration per cut loosely tracks tempo (faster cuts during conflict/choice, longer holds during sacrifice and the ending) without ever explicitly stating the maxim.",
    "non_goals": [
        REQUIRED_ETHICS_NON_GOAL,
        "This architecture does not specify provider-specific prompt text or final color grade -- those belong to the Provider-Specific Production Package.",
    ],
    "source": (
        "DreamMusicForge v2 Editorial Architecture Engine, worked example completing the Hope chain "
        "(Principle Kernel -> Narrative/Emotional -> Musical -> Cinematic -> Editorial)."
    ),
    "truth_status": "ASSUMED",
}


if __name__ == "__main__":
    errors = validate_editorial_architecture(EXAMPLE_EDITORIAL_ARCHITECTURE)
    if errors:
        raise SystemExit("FAIL: " + "; ".join(errors))
    print("PASS: example Editorial Architecture is valid")
