"""Cinematic Architecture: stage-4 output contract for the DreamMusicForge
v2 pipeline (Cinematic Architecture Engine -- Visual Architecture, Shot
Architecture, Performance Direction).

Composition fields (focal point, rule of thirds / golden triangle /
centered / frame-within-frame / symmetrical framing, leading lines,
positive/negative space, headroom, leadroom, balance, depth layering,
focus technique, color/contrast) are drawn from a cited practitioner
breakdown of Hollywood composition technique (see EXAMPLE source note),
made checkable rather than left as prose guidance.

Three validators are provided:

- validate_cinematic_architecture(doc): structural checks within this
  document alone.
- validate_against_narrative_architecture(doc, narrative_doc): every
  shot's linked_waveform_beat_id must exist in the narrative document's
  emotional_waveform, and that beat's linked_narrative_stage must match
  the shot's own linked_narrative_stage (catches drift between the two
  documents, not just missing references).
- validate_against_musical_architecture(doc, musical_doc): every shot's
  linked_tempo_segment_id must exist in the musical document's tempo_map.
"""

VALID_CONFIDENCE = {"VERIFIED", "INFERRED", "ASSUMED", "UNKNOWN"}

REQUIRED_ETHICS_NON_GOAL = (
    "This kernel does not claim to guarantee any specific viewer belief, emotion, or decision."
)

NARRATIVE_STAGES = [
    "beginning", "catalyst", "conflict", "choice",
    "sacrifice", "transformation", "resolution", "reflection",
]

FRAMING_TECHNIQUES = {
    "rule_of_thirds", "golden_triangle", "centered",
    "frame_within_frame", "symmetrical", "off_balance_intentional",
}
SUBJECT_FRAME_PROPORTIONS = {"extreme_small", "small", "medium", "large", "extreme_close"}
HEADROOM_LEVELS = {"minimal", "standard", "abnormal_large"}
LEADROOM_LEVELS = {"standard", "minimal", "none"}
BALANCE_LEVELS = {"balanced", "deliberately_unbalanced"}
FOCUS_TECHNIQUES = {"shallow_isolate", "deep_focus", "rack_focus"}
SHOT_SIZES = {"extreme_wide", "wide", "medium_wide", "medium", "close_up", "extreme_close_up"}
CAMERA_MOVEMENTS = {"static", "glidecam", "slider", "handheld", "dolly"}
LIGHTING_KEY_STYLES = {"soft", "hard"}


def _validate_shot(shot: dict, i: int) -> list[str]:
    errors = []

    for field in [
        "shot_id", "order", "linked_narrative_stage", "linked_waveform_beat_id",
        "linked_tempo_segment_id", "justification", "composition", "camera", "lighting",
    ]:
        if field not in shot or shot[field] in (None, "", [], {}):
            errors.append(f"shots[{i}].{field} is required")

    stage = shot.get("linked_narrative_stage")
    if stage is not None and stage not in NARRATIVE_STAGES:
        errors.append(f"shots[{i}].linked_narrative_stage must be one of {NARRATIVE_STAGES}")

    justification = shot.get("justification")
    if isinstance(justification, dict):
        for field in ["exists_because", "why_now", "audience_state_change"]:
            if not justification.get(field):
                errors.append(f"shots[{i}].justification.{field} is required")
    elif "justification" in shot:
        errors.append(f"shots[{i}].justification must be an object")

    composition = shot.get("composition")
    if isinstance(composition, dict):
        for field in ["focal_point", "framing_technique", "space_balance", "headroom",
                      "leadroom", "balance", "depth_layers", "focus_technique", "color_contrast_strategy"]:
            if field not in composition or composition[field] in (None, "", {}):
                errors.append(f"shots[{i}].composition.{field} is required")

        framing = composition.get("framing_technique")
        if framing is not None and framing not in FRAMING_TECHNIQUES:
            errors.append(f"shots[{i}].composition.framing_technique must be one of {sorted(FRAMING_TECHNIQUES)}")
        if framing == "centered" and not composition.get("centered_rationale"):
            errors.append(f"shots[{i}].composition.centered_rationale is required when framing_technique is 'centered'")

        space_balance = composition.get("space_balance")
        if isinstance(space_balance, dict):
            proportion = space_balance.get("subject_frame_proportion")
            if proportion is not None and proportion not in SUBJECT_FRAME_PROPORTIONS:
                errors.append(f"shots[{i}].composition.space_balance.subject_frame_proportion must be one of {sorted(SUBJECT_FRAME_PROPORTIONS)}")
            if not space_balance.get("negative_space_purpose"):
                errors.append(f"shots[{i}].composition.space_balance.negative_space_purpose is required")
        elif space_balance is not None:
            errors.append(f"shots[{i}].composition.space_balance must be an object")

        headroom = composition.get("headroom")
        if headroom is not None and headroom not in HEADROOM_LEVELS:
            errors.append(f"shots[{i}].composition.headroom must be one of {sorted(HEADROOM_LEVELS)}")

        leadroom = composition.get("leadroom")
        if leadroom is not None and leadroom not in LEADROOM_LEVELS:
            errors.append(f"shots[{i}].composition.leadroom must be one of {sorted(LEADROOM_LEVELS)}")

        balance = composition.get("balance")
        if balance is not None and balance not in BALANCE_LEVELS:
            errors.append(f"shots[{i}].composition.balance must be one of {sorted(BALANCE_LEVELS)}")

        depth_layers = composition.get("depth_layers")
        if isinstance(depth_layers, dict):
            populated = [v for v in depth_layers.values() if v]
            if len(populated) < 2:
                errors.append(f"shots[{i}].composition.depth_layers must populate at least 2 of foreground/midground/background -- a subject flat against the background has no depth")
        elif depth_layers is not None:
            errors.append(f"shots[{i}].composition.depth_layers must be an object")

        focus_technique = composition.get("focus_technique")
        if focus_technique is not None and focus_technique not in FOCUS_TECHNIQUES:
            errors.append(f"shots[{i}].composition.focus_technique must be one of {sorted(FOCUS_TECHNIQUES)}")
    elif "composition" in shot:
        errors.append(f"shots[{i}].composition must be an object")

    camera = shot.get("camera")
    if isinstance(camera, dict):
        shot_size = camera.get("shot_size")
        if shot_size is not None and shot_size not in SHOT_SIZES:
            errors.append(f"shots[{i}].camera.shot_size must be one of {sorted(SHOT_SIZES)}")
        movement = camera.get("movement")
        if movement is not None and movement not in CAMERA_MOVEMENTS:
            errors.append(f"shots[{i}].camera.movement must be one of {sorted(CAMERA_MOVEMENTS)}")
    elif "camera" in shot:
        errors.append(f"shots[{i}].camera must be an object")

    lighting = shot.get("lighting")
    if isinstance(lighting, dict):
        key_style = lighting.get("key_style")
        if key_style is not None and key_style not in LIGHTING_KEY_STYLES:
            errors.append(f"shots[{i}].lighting.key_style must be one of {sorted(LIGHTING_KEY_STYLES)}")
        if not lighting.get("note"):
            errors.append(f"shots[{i}].lighting.note is required")
    elif "lighting" in shot:
        errors.append(f"shots[{i}].lighting must be an object")

    return errors


def validate_cinematic_architecture(doc: dict) -> list[str]:
    errors = []

    for field in ["schema_version", "source_principle_id", "source_human_truth_id", "shots", "non_goals", "truth_status"]:
        if field not in doc or doc[field] in (None, "", [], {}):
            errors.append(f"missing required field: {field}")

    if "truth_status" in doc and doc["truth_status"] not in VALID_CONFIDENCE:
        errors.append(f"truth_status must be one of {sorted(VALID_CONFIDENCE)}")

    shots = doc.get("shots")
    if isinstance(shots, list):
        if len(shots) < 8:
            errors.append("shots must contain at least 8 entries (one per narrative stage)")

        orders = []
        covered_stages = set()
        for i, shot in enumerate(shots):
            errors.extend(_validate_shot(shot, i))
            order = shot.get("order")
            if isinstance(order, int):
                orders.append(order)
            stage = shot.get("linked_narrative_stage")
            if stage:
                covered_stages.add(stage)

        if orders and (orders != sorted(orders) or len(orders) != len(set(orders))):
            errors.append("shots must have strictly increasing, unique order values")

        missing_coverage = [s for s in NARRATIVE_STAGES if s not in covered_stages]
        if missing_coverage:
            errors.append(f"shots must cover every narrative stage at least once; missing: {missing_coverage}")
    elif "shots" in doc:
        errors.append("shots must be a list")

    non_goals = doc.get("non_goals")
    if isinstance(non_goals, list):
        if REQUIRED_ETHICS_NON_GOAL not in non_goals:
            errors.append(f"non_goals must include the required ethics constraint: {REQUIRED_ETHICS_NON_GOAL!r}")
    elif "non_goals" in doc:
        errors.append("non_goals must be a list")

    return errors


def validate_against_narrative_architecture(doc: dict, narrative_doc: dict) -> list[str]:
    """Referential integrity + drift check against the paired Narrative + Emotional Architecture."""
    errors = []

    if doc.get("source_principle_id") != narrative_doc.get("source_principle_id"):
        errors.append("source_principle_id does not match the paired narrative document")
    if doc.get("source_human_truth_id") != narrative_doc.get("source_human_truth_id"):
        errors.append("source_human_truth_id does not match the paired narrative document")

    beats_by_id = {
        beat.get("beat_id"): beat
        for beat in narrative_doc.get("emotional_waveform", [])
        if isinstance(beat, dict)
    }

    for i, shot in enumerate(doc.get("shots", [])):
        beat_id = shot.get("linked_waveform_beat_id")
        if not beat_id:
            continue
        beat = beats_by_id.get(beat_id)
        if beat is None:
            errors.append(f"shots[{i}].linked_waveform_beat_id '{beat_id}' is not in the narrative document's emotional_waveform")
            continue
        if shot.get("linked_narrative_stage") != beat.get("linked_narrative_stage"):
            errors.append(
                f"shots[{i}].linked_narrative_stage '{shot.get('linked_narrative_stage')}' does not match "
                f"beat '{beat_id}''s stage '{beat.get('linked_narrative_stage')}' in the narrative document"
            )

    return errors


def validate_against_musical_architecture(doc: dict, musical_doc: dict) -> list[str]:
    """Referential integrity against the paired Musical Architecture."""
    errors = []

    segment_ids = {
        seg.get("segment_id")
        for seg in musical_doc.get("tempo_map", [])
        if isinstance(seg, dict)
    }

    for i, shot in enumerate(doc.get("shots", [])):
        segment_id = shot.get("linked_tempo_segment_id")
        if segment_id and segment_id not in segment_ids:
            errors.append(f"shots[{i}].linked_tempo_segment_id '{segment_id}' is not in the musical document's tempo_map")

    return errors


EXAMPLE_CINEMATIC_ARCHITECTURE = {
    "schema_version": "1.0.0",
    "source_principle_id": "hope",
    "source_human_truth_id": "rebuilding_after_loss",
    "shots": [
        {
            "shot_id": "shot1", "order": 1, "linked_narrative_stage": "beginning",
            "linked_waveform_beat_id": "b1", "linked_tempo_segment_id": "seg1",
            "justification": {
                "exists_because": "establishes the scale of the loss before any character action",
                "why_now": "opening image; nothing can be understood without this baseline",
                "audience_state_change": "from neutral to oriented-in-desolation",
            },
            "composition": {
                "focal_point": "a lone figure at the edge of the wreckage",
                "framing_technique": "rule_of_thirds",
                "space_balance": {"subject_frame_proportion": "extreme_small", "negative_space_purpose": "isolation and vulnerability against the scale of the loss"},
                "headroom": "abnormal_large", "leadroom": "none", "balance": "deliberately_unbalanced",
                "depth_layers": {"foreground": "debris", "midground": "the figure", "background": "grey sky"},
                "focus_technique": "deep_focus",
                "color_contrast_strategy": "desaturated, near-monochrome, no warm tones",
            },
            "camera": {"shot_size": "extreme_wide", "movement": "static", "lens_note": "wide, minimal distortion"},
            "lighting": {"key_style": "hard", "note": "flat overcast light, no shaping"},
            "blocking_or_performance_note": "figure does not move for the full shot",
            "symbolic_object": "a single unbroken object visible in the debris",
        },
        {
            "shot_id": "shot2", "order": 2, "linked_narrative_stage": "catalyst",
            "linked_waveform_beat_id": "b2", "linked_tempo_segment_id": "seg2",
            "justification": {
                "exists_because": "introduces the question that forces a response",
                "why_now": "immediately after the audience has absorbed the scale of loss",
                "audience_state_change": "from passive witness to expecting a decision",
            },
            "composition": {
                "focal_point": "the second character's face, direct to camera",
                "framing_technique": "centered", "centered_rationale": "direct address carries the authority of the question being asked",
                "space_balance": {"subject_frame_proportion": "large", "negative_space_purpose": "no distraction from the direct question"},
                "headroom": "standard", "leadroom": "none", "balance": "balanced",
                "depth_layers": {"midground": "the character", "background": "out-of-focus wreckage"},
                "focus_technique": "shallow_isolate",
                "color_contrast_strategy": "subject slightly warmer than the cool background",
            },
            "camera": {"shot_size": "medium", "movement": "static"},
            "lighting": {"key_style": "soft", "note": "single soft source, motivated by an unseen window"},
            "blocking_or_performance_note": "no movement; the stillness carries the weight of the question",
            "symbolic_object": None,
        },
        {
            "shot_id": "shot3", "order": 3, "linked_narrative_stage": "conflict",
            "linked_waveform_beat_id": "b3", "linked_tempo_segment_id": "seg3",
            "justification": {
                "exists_because": "shows the repeated, visible cost of every attempt to start again",
                "why_now": "after the question is asked, before a choice is made",
                "audience_state_change": "from anticipation to shared frustration",
            },
            "composition": {
                "focal_point": "hands trying and failing to fit two broken pieces together",
                "framing_technique": "rule_of_thirds",
                "leading_lines": "chaotic, converging fracture lines in the debris, intentionally disorienting",
                "space_balance": {"subject_frame_proportion": "medium", "negative_space_purpose": "the disorder of the space itself is part of the subject"},
                "headroom": "minimal", "leadroom": "minimal", "balance": "deliberately_unbalanced",
                "depth_layers": {"foreground": "broken pieces", "midground": "hands", "background": "more debris"},
                "focus_technique": "shallow_isolate",
                "color_contrast_strategy": "harsh single-source contrast, deep shadow",
            },
            "camera": {"shot_size": "close_up", "movement": "handheld"},
            "lighting": {"key_style": "hard", "note": "unmotivated hard side light, deliberately unflattering"},
            "blocking_or_performance_note": "repeated small failed motions",
            "symbolic_object": "the two broken pieces",
        },
        {
            "shot_id": "shot4", "order": 4, "linked_narrative_stage": "choice",
            "linked_waveform_beat_id": "b4", "linked_tempo_segment_id": "seg4",
            "justification": {
                "exists_because": "the decision point itself must be seen, not implied",
                "why_now": "at the peak of accumulated frustration from the conflict beat",
                "audience_state_change": "from frustration to held tension",
            },
            "composition": {
                "focal_point": "the character's eyes, caught between walking away and staying",
                "framing_technique": "golden_triangle",
                "space_balance": {"subject_frame_proportion": "extreme_close", "negative_space_purpose": "no room to escape the decision"},
                "headroom": "minimal", "leadroom": "none", "balance": "deliberately_unbalanced",
                "depth_layers": {"midground": "the character", "background": "soft blur of the wreckage"},
                "focus_technique": "shallow_isolate",
                "color_contrast_strategy": "high contrast on the eyes only",
            },
            "camera": {"shot_size": "extreme_close_up", "movement": "static"},
            "lighting": {"key_style": "hard", "note": "narrow hard key, rest of frame falls to shadow"},
            "blocking_or_performance_note": "held stillness, no blinking cut",
            "symbolic_object": None,
        },
        {
            "shot_id": "shot5", "order": 5, "linked_narrative_stage": "sacrifice",
            "linked_waveform_beat_id": "b5", "linked_tempo_segment_id": "seg5",
            "justification": {
                "exists_because": "marks the cost of choosing to try again, not just the choice itself",
                "why_now": "immediately after the choice is made, before any visible progress",
                "audience_state_change": "from tension to vulnerability",
            },
            "composition": {
                "focal_point": "the character seen through a broken doorway frame",
                "framing_technique": "frame_within_frame",
                "space_balance": {"subject_frame_proportion": "small", "negative_space_purpose": "creates distance -- the audience becomes a spectator to a private moment"},
                "headroom": "standard", "leadroom": "minimal", "balance": "deliberately_unbalanced",
                "depth_layers": {"foreground": "the broken doorframe", "midground": "the character", "background": "open space beyond"},
                "focus_technique": "rack_focus",
                "color_contrast_strategy": "cool doorway silhouette against warmer light beyond",
            },
            "camera": {"shot_size": "medium_wide", "movement": "static"},
            "lighting": {"key_style": "soft", "note": "warm light source visible only beyond the doorway"},
            "blocking_or_performance_note": "character exhales, shoulders drop, before stepping forward",
            "symbolic_object": "the broken doorframe",
        },
        {
            "shot_id": "shot6", "order": 6, "linked_narrative_stage": "transformation",
            "linked_waveform_beat_id": "b6", "linked_tempo_segment_id": "seg6",
            "justification": {
                "exists_because": "shows the first physical evidence of rebuilding, not just intent",
                "why_now": "directly after the sacrifice, the first visible payoff",
                "audience_state_change": "from vulnerability to tentative hope",
            },
            "composition": {
                "focal_point": "the first new plank, in focus against the blurred ruin",
                "framing_technique": "rule_of_thirds",
                "space_balance": {"subject_frame_proportion": "medium", "negative_space_purpose": "the ruin is still present but no longer dominant"},
                "headroom": "standard", "leadroom": "standard", "balance": "balanced",
                "depth_layers": {"foreground": "the new plank", "midground": "the character's hands", "background": "the out-of-focus ruin"},
                "focus_technique": "rack_focus",
                "color_contrast_strategy": "first warm color introduced against the desaturated ruin",
            },
            "camera": {"shot_size": "close_up", "movement": "slider"},
            "lighting": {"key_style": "soft", "note": "warm practical light newly visible in frame"},
            "blocking_or_performance_note": "focus racks from ruin to plank as hands set it in place",
            "symbolic_object": "the first new plank",
        },
        {
            "shot_id": "shot7", "order": 7, "linked_narrative_stage": "resolution",
            "linked_waveform_beat_id": "b7", "linked_tempo_segment_id": "seg7",
            "justification": {
                "exists_because": "shows the unfinished-but-standing structure as the story's actual endpoint",
                "why_now": "after transformation, the visible result",
                "audience_state_change": "from tentative hope to quiet pride",
            },
            "composition": {
                "focal_point": "the unfinished structure, standing beside the old ruin",
                "framing_technique": "symmetrical",
                "space_balance": {"subject_frame_proportion": "large", "negative_space_purpose": "balanced against the ruin, neither dominates"},
                "headroom": "standard", "leadroom": "standard", "balance": "balanced",
                "depth_layers": {"foreground": "the ruin", "midground": "the new structure", "background": "open sky"},
                "focus_technique": "deep_focus",
                "color_contrast_strategy": "full warm color restored, ruin and structure both legible",
            },
            "camera": {"shot_size": "wide", "movement": "static"},
            "lighting": {"key_style": "soft", "note": "golden-hour motivated key"},
            "blocking_or_performance_note": "character stands still, facing the structure, back to camera",
            "symbolic_object": "the standing, unfinished structure",
        },
        {
            "shot_id": "shot8", "order": 8, "linked_narrative_stage": "reflection",
            "linked_waveform_beat_id": "b8", "linked_tempo_segment_id": "seg8",
            "justification": {
                "exists_because": "closes on the gap between what was and what is now being built, without narrating its meaning",
                "why_now": "final image, deliberately withholding explanation",
                "audience_state_change": "from quiet pride to open-ended wonder -- left to interpret, not told what to conclude",
            },
            "composition": {
                "focal_point": "the character as a silhouette against the lit horizon",
                "framing_technique": "rule_of_thirds",
                "space_balance": {"subject_frame_proportion": "extreme_small", "negative_space_purpose": "mirrors shot1's isolation, but now the space is chosen rather than imposed"},
                "headroom": "abnormal_large", "leadroom": "none", "balance": "deliberately_unbalanced",
                "depth_layers": {"midground": "the silhouette", "background": "the lit horizon"},
                "focus_technique": "deep_focus",
                "color_contrast_strategy": "subject as pure silhouette against a bright horizon, bookending shot1's desaturated flat light",
            },
            "camera": {"shot_size": "extreme_wide", "movement": "static"},
            "lighting": {"key_style": "hard", "note": "backlit, subject unlit -- pure silhouette"},
            "blocking_or_performance_note": "no movement; held on the silhouette until the frame fades",
            "symbolic_object": None,
        },
    ],
    "non_goals": [
        REQUIRED_ETHICS_NON_GOAL,
        "This architecture does not specify provider-specific prompts, editorial timing, or final color grade -- those belong to downstream stages.",
    ],
    "source": (
        "DreamMusicForge v2 Cinematic Architecture Engine, worked example paired with the existing "
        "Hope Principle Kernel, Narrative + Emotional Architecture, and Musical Architecture. Composition "
        "technique fields (focal points, rule of thirds, golden triangle, leading lines, positive/negative "
        "space, headroom/leadroom, balance/symmetry, frame within frame, depth layering, focus pulls, "
        "color/contrast) drawn from a cited practitioner breakdown of Hollywood cinematography composition, "
        "https://youtu.be/ANdLOY4rW04."
    ),
    "truth_status": "ASSUMED",
}


if __name__ == "__main__":
    errors = validate_cinematic_architecture(EXAMPLE_CINEMATIC_ARCHITECTURE)
    if errors:
        raise SystemExit("FAIL: " + "; ".join(errors))
    print("PASS: example Cinematic Architecture is valid")
