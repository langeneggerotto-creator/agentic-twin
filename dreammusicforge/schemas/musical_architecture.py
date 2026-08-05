"""Musical Architecture: stage-3 output contract for the DreamMusicForge v2
pipeline (Musical Architecture Engine).

Dependency-free validator mirroring musical_architecture.schema.json. Must
be fully defined before a music provider (Suno, Udio, ...) is selected.

Two validators are provided:

- validate_musical_architecture(doc): structural checks within this
  document alone (required fields, monotonic tempo_map order, internal
  cross-references like melodic_motif.recurs_at -> tempo_map.segment_id).
- validate_against_narrative_architecture(doc, narrative_doc): referential
  integrity against the paired Narrative + Emotional Architecture --
  every tempo_map[].linked_waveform_beat_id must exist in the narrative
  document's emotional_waveform.
"""

VALID_CONFIDENCE = {"VERIFIED", "INFERRED", "ASSUMED", "UNKNOWN"}
VALID_DYNAMIC_LEVELS = {"pp", "p", "mp", "mf", "f", "ff"}

REQUIRED_ETHICS_NON_GOAL = (
    "This kernel does not claim to guarantee any specific viewer belief, emotion, or decision."
)


def validate_musical_architecture(doc: dict) -> list[str]:
    errors = []

    for field in [
        "schema_version", "source_principle_id", "source_human_truth_id",
        "instrumentation", "tempo_map", "vocal_tone", "harmonic_language",
        "melodic_motif", "lyrical_intent", "emotional_pacing_notes",
        "non_goals", "truth_status",
    ]:
        if field not in doc or doc[field] in (None, "", [], {}):
            errors.append(f"missing required field: {field}")

    if "truth_status" in doc and doc["truth_status"] not in VALID_CONFIDENCE:
        errors.append(f"truth_status must be one of {sorted(VALID_CONFIDENCE)}")

    instrumentation = doc.get("instrumentation")
    if isinstance(instrumentation, list):
        if len(instrumentation) < 1:
            errors.append("instrumentation must contain at least one entry")
        for i, entry in enumerate(instrumentation):
            for field in ["instrument", "role"]:
                if not entry.get(field):
                    errors.append(f"instrumentation[{i}].{field} is required")
    elif "instrumentation" in doc:
        errors.append("instrumentation must be a list")

    tempo_map = doc.get("tempo_map")
    segment_ids = set()
    if isinstance(tempo_map, list):
        if len(tempo_map) < 3:
            errors.append("tempo_map must have at least 3 segments")

        orders = []
        for i, seg in enumerate(tempo_map):
            for field in ["segment_id", "order", "bpm", "dynamic_level", "linked_waveform_beat_id"]:
                if seg.get(field) in (None, ""):
                    errors.append(f"tempo_map[{i}].{field} is required")

            if seg.get("segment_id"):
                segment_ids.add(seg["segment_id"])

            dynamic_level = seg.get("dynamic_level")
            if dynamic_level is not None and dynamic_level not in VALID_DYNAMIC_LEVELS:
                errors.append(f"tempo_map[{i}].dynamic_level must be one of {sorted(VALID_DYNAMIC_LEVELS)}")

            bpm = seg.get("bpm")
            if isinstance(bpm, int) and bpm < 1:
                errors.append(f"tempo_map[{i}].bpm must be a positive integer")

            order = seg.get("order")
            if isinstance(order, int):
                orders.append(order)

        if orders and (orders != sorted(orders) or len(orders) != len(set(orders))):
            errors.append("tempo_map segments must have strictly increasing, unique order values")
    elif "tempo_map" in doc:
        errors.append("tempo_map must be a list")

    silence_moments = doc.get("silence_moments", [])
    if isinstance(silence_moments, list):
        for i, moment in enumerate(silence_moments):
            for field in ["after_segment_id", "duration_qualitative", "purpose"]:
                if not moment.get(field):
                    errors.append(f"silence_moments[{i}].{field} is required")
            after_id = moment.get("after_segment_id")
            if after_id and segment_ids and after_id not in segment_ids:
                errors.append(f"silence_moments[{i}].after_segment_id '{after_id}' does not match any tempo_map segment_id")
    else:
        errors.append("silence_moments must be a list if present")

    vocal_tone = doc.get("vocal_tone")
    if isinstance(vocal_tone, dict):
        for field in ["register", "texture", "description"]:
            if not vocal_tone.get(field):
                errors.append(f"vocal_tone.{field} is required")
    elif "vocal_tone" in doc:
        errors.append("vocal_tone must be an object")

    harmonic_language = doc.get("harmonic_language")
    if isinstance(harmonic_language, dict):
        for field in ["mode_or_key", "description"]:
            if not harmonic_language.get(field):
                errors.append(f"harmonic_language.{field} is required")
    elif "harmonic_language" in doc:
        errors.append("harmonic_language must be an object")

    melodic_motif = doc.get("melodic_motif")
    if isinstance(melodic_motif, dict):
        if not melodic_motif.get("description"):
            errors.append("melodic_motif.description is required")
        recurs_at = melodic_motif.get("recurs_at")
        if isinstance(recurs_at, list):
            if len(recurs_at) < 1:
                errors.append("melodic_motif.recurs_at must reference at least one tempo_map segment")
            for seg_id in recurs_at:
                if segment_ids and seg_id not in segment_ids:
                    errors.append(f"melodic_motif.recurs_at references unknown segment_id '{seg_id}'")
        elif "recurs_at" in melodic_motif:
            errors.append("melodic_motif.recurs_at must be a list")
    elif "melodic_motif" in doc:
        errors.append("melodic_motif must be an object")

    non_goals = doc.get("non_goals")
    if isinstance(non_goals, list):
        if REQUIRED_ETHICS_NON_GOAL not in non_goals:
            errors.append(f"non_goals must include the required ethics constraint: {REQUIRED_ETHICS_NON_GOAL!r}")
    elif "non_goals" in doc:
        errors.append("non_goals must be a list")

    return errors


def validate_against_narrative_architecture(doc: dict, narrative_doc: dict) -> list[str]:
    """Referential integrity against the paired Narrative + Emotional Architecture."""
    errors = []

    waveform = narrative_doc.get("emotional_waveform", [])
    waveform_beat_ids = {beat.get("beat_id") for beat in waveform if isinstance(beat, dict)}

    if doc.get("source_principle_id") != narrative_doc.get("source_principle_id"):
        errors.append("source_principle_id does not match the paired narrative document")
    if doc.get("source_human_truth_id") != narrative_doc.get("source_human_truth_id"):
        errors.append("source_human_truth_id does not match the paired narrative document")

    for i, seg in enumerate(doc.get("tempo_map", [])):
        beat_id = seg.get("linked_waveform_beat_id")
        if beat_id and beat_id not in waveform_beat_ids:
            errors.append(f"tempo_map[{i}].linked_waveform_beat_id '{beat_id}' is not in the narrative document's emotional_waveform")

    return errors


EXAMPLE_MUSICAL_ARCHITECTURE = {
    "schema_version": "1.0.0",
    "source_principle_id": "hope",
    "source_human_truth_id": "rebuilding_after_loss",
    "instrumentation": [
        {"instrument": "solo cello", "role": "carries the melodic motif", "description": "warm, close-mic'd, present from the first bar"},
        {"instrument": "prepared piano", "role": "texture under desolation and conflict", "description": "muted strings, brittle attack"},
        {"instrument": "string section", "role": "swells under transformation and resolution", "description": "enters sparse, builds to full voicing by the resolution segment"},
        {"instrument": "solo voice", "role": "carries lyrical intent from choice onward", "description": "close, unprocessed, breath audible"},
    ],
    "tempo_map": [
        {"segment_id": "seg1", "order": 1, "bpm": 58, "dynamic_level": "pp", "linked_waveform_beat_id": "b1", "description": "desolation: sparse, unmetered feel"},
        {"segment_id": "seg2", "order": 2, "bpm": 66, "dynamic_level": "mp", "linked_waveform_beat_id": "b2", "description": "provocation: pulse enters"},
        {"segment_id": "seg3", "order": 3, "bpm": 74, "dynamic_level": "mf", "linked_waveform_beat_id": "b3", "description": "frustration: rhythmic insistence"},
        {"segment_id": "seg4", "order": 4, "bpm": 80, "dynamic_level": "f", "linked_waveform_beat_id": "b4", "description": "tension: tightest rhythmic grid"},
        {"segment_id": "seg5", "order": 5, "bpm": 70, "dynamic_level": "mp", "linked_waveform_beat_id": "b5", "description": "vulnerability: pulls back to near-silence before the swell"},
        {"segment_id": "seg6", "order": 6, "bpm": 84, "dynamic_level": "mf", "linked_waveform_beat_id": "b6", "description": "tentative hope: motif completes for the first time"},
        {"segment_id": "seg7", "order": 7, "bpm": 92, "dynamic_level": "f", "linked_waveform_beat_id": "b7", "description": "quiet pride: full instrumentation, motif restated"},
        {"segment_id": "seg8", "order": 8, "bpm": 76, "dynamic_level": "p", "linked_waveform_beat_id": "b8", "description": "reflection: strips back to solo cello and voice"},
    ],
    "silence_moments": [
        {
            "after_segment_id": "seg5",
            "duration_qualitative": "two full bars, no click",
            "purpose": "let the sacrifice beat land before the music commits to hope",
        }
    ],
    "vocal_tone": {
        "register": "low-mid, conversational",
        "texture": "unprocessed, breath and imperfection left in",
        "description": "sung the way someone talks to themselves before they believe it, not the way someone performs conviction",
    },
    "harmonic_language": {
        "mode_or_key": "D aeolian, resolving to D major only at seg7",
        "description": "modal ambiguity through conflict and choice; the major resolution is earned, not assumed",
    },
    "melodic_motif": {
        "description": "A three-note rising figure that first appears broken (missing its third note), then completes at seg6 and is restated in full at seg7.",
        "recurs_at": ["seg1", "seg6", "seg7", "seg8"],
    },
    "lyrical_intent": "First-person, present tense, no narration of the lesson -- describes the act of picking up one piece, not what it means.",
    "emotional_pacing_notes": "Tempo and dynamics track the emotional_waveform directly; the only deliberate silence sits at the sacrifice/transformation boundary, matching the narrative's choice-to-sacrifice hinge.",
    "non_goals": [
        REQUIRED_ETHICS_NON_GOAL,
        "This architecture does not specify final mix, mastering, or provider-specific prompt text -- those belong to the provider layer.",
    ],
    "source": (
        "DreamMusicForge v2 Musical Architecture Engine, worked example paired with the "
        "Narrative + Emotional Architecture built on the Hope Principle Kernel."
    ),
    "truth_status": "ASSUMED",
}


if __name__ == "__main__":
    errors = validate_musical_architecture(EXAMPLE_MUSICAL_ARCHITECTURE)
    if errors:
        raise SystemExit("FAIL: " + "; ".join(errors))
    print("PASS: example Musical Architecture is valid")
