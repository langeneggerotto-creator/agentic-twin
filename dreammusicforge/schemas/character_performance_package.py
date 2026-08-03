"""Character Performance Package: replaces narration with characters
performing themselves, for the DreamMusicForge v2 pipeline.

Two problems, one document:

1. Character consistency across independently generated shots. Historically
   this pipeline named the problem (SAM 2 / depth-conditioned reference
   generation, back in the original 6-stage design) but never built a
   solution. This document builds the simplest real version: generate one
   character-reference image per character, then reuse that reference as
   conditioning for every shot the character appears in, rather than
   regenerating the character from text alone each time. The motivating
   provider is Google's Gemini 2.5 Flash Image model ("Nano Banana"),
   chosen specifically for cross-image character consistency.

2. Characters sing themselves, not a narrator. no_narrator is a literal
   hard gate (must be True), not a design note. Every vocal_performers
   entry requires lip_sync_required = True, and character names are
   checked against a blocklist so "Narrator" can't sneak in relabeled.

Three validators:

- validate_character_performance_package(doc): structural checks.
- validate_against_cinematic_architecture(doc, cinematic_doc): every
  sings_during_shot_ids entry must be a real shot.
- validate_against_blueprint(doc, blueprint_doc): every character_name
  must match a name in narrative_supplement.character_biographies.
"""

VALID_CONFIDENCE = {"VERIFIED", "INFERRED", "ASSUMED", "UNKNOWN"}

REQUIRED_ETHICS_NON_GOAL = (
    "This kernel does not claim to guarantee any specific viewer belief, emotion, or decision."
)

NARRATOR_NAME_BLOCKLIST = {"narrator", "voiceover", "voice-over", "announcer", "voice of god", "off-screen voice"}


def _is_blocked_name(name: str) -> bool:
    return name.strip().lower() in NARRATOR_NAME_BLOCKLIST


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------

def translate_character_to_reference_prompt(character_bio: dict, provider: str) -> dict:
    name = character_bio["name"]
    role = character_bio["role"]
    description = character_bio["description"]

    prompt_text = (
        f"Character reference turnaround for '{name}' ({role}). {description} "
        f"Consistent identity across every generated image: same face, build, and wardrobe every time."
    )
    slug = name.lower().replace(" ", "_").replace("'", "")

    return {
        "character_name": name,
        "reference_prompt": prompt_text,
        "consistency_notes": (
            f"Use this exact reference image as the conditioning input for every shot featuring {name}, "
            f"via {provider}'s character-consistency / reference-image feature, rather than regenerating "
            f"the character from text alone each time."
        ),
        "reference_image_asset_id": f"ref_{slug}",
        "source_fields_used": ["name", "role", "description"],
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_character_performance_package(doc: dict) -> list[str]:
    errors = []

    for field in [
        "schema_version", "source_principle_id", "source_human_truth_id", "no_narrator",
        "character_reference_provider", "character_references", "vocal_performers",
        "non_goals", "truth_status",
    ]:
        if field not in doc or doc[field] in (None, "", [], {}):
            if field == "no_narrator" and doc.get(field) is False:
                continue  # handled explicitly below with a clearer message
            errors.append(f"missing required field: {field}")

    if "no_narrator" in doc and doc["no_narrator"] is not True:
        errors.append("no_narrator must be true -- this document exists to eliminate narration, not describe it")

    if "truth_status" in doc and doc["truth_status"] not in VALID_CONFIDENCE:
        errors.append(f"truth_status must be one of {sorted(VALID_CONFIDENCE)}")

    references = doc.get("character_references")
    reference_names = set()
    if isinstance(references, list):
        if len(references) < 1:
            errors.append("character_references must contain at least one entry")
        for i, entry in enumerate(references):
            for field in ["character_name", "reference_prompt", "consistency_notes", "reference_image_asset_id", "source_fields_used"]:
                if field not in entry or entry[field] in (None, "", []):
                    errors.append(f"character_references[{i}].{field} is required")
            name = entry.get("character_name")
            if name:
                if _is_blocked_name(name):
                    errors.append(f"character_references[{i}].character_name '{name}' reads as a narrator/voiceover role, not a character")
                reference_names.add(name)
    elif "character_references" in doc:
        errors.append("character_references must be a list")

    performers = doc.get("vocal_performers")
    if isinstance(performers, list):
        if len(performers) < 1:
            errors.append("vocal_performers must contain at least one entry")
        for i, entry in enumerate(performers):
            for field in ["character_name", "register", "texture", "description", "sings_during_shot_ids", "lip_sync_required"]:
                if field not in entry or entry[field] in (None, "", []):
                    errors.append(f"vocal_performers[{i}].{field} is required")

            name = entry.get("character_name")
            if name:
                if _is_blocked_name(name):
                    errors.append(f"vocal_performers[{i}].character_name '{name}' reads as a narrator/voiceover role, not a character")
                elif name not in reference_names:
                    errors.append(f"vocal_performers[{i}].character_name '{name}' has no matching character_references entry -- a singing character must have an established visual reference first")

            if "lip_sync_required" in entry and entry["lip_sync_required"] is not True:
                errors.append(f"vocal_performers[{i}].lip_sync_required must be true -- a character singing on camera always needs lip sync")

            shot_ids = entry.get("sings_during_shot_ids")
            if isinstance(shot_ids, list) and len(shot_ids) < 1:
                errors.append(f"vocal_performers[{i}].sings_during_shot_ids must contain at least one shot")
    elif "vocal_performers" in doc:
        errors.append("vocal_performers must be a list")

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

    for i, performer in enumerate(doc.get("vocal_performers", [])):
        for shot_id in performer.get("sings_during_shot_ids", []):
            if shot_id not in shot_ids:
                errors.append(f"vocal_performers[{i}].sings_during_shot_ids references unknown shot_id '{shot_id}'")

    return errors


def validate_against_blueprint(doc: dict, blueprint_doc: dict) -> list[str]:
    errors = []

    bios = blueprint_doc.get("narrative_supplement", {}).get("character_biographies", [])
    known_names = {b.get("name") for b in bios if isinstance(b, dict)}

    for i, entry in enumerate(doc.get("character_references", [])):
        name = entry.get("character_name")
        if name and name not in known_names:
            errors.append(f"character_references[{i}].character_name '{name}' does not match any character in the blueprint's narrative_supplement.character_biographies")

    for i, entry in enumerate(doc.get("vocal_performers", [])):
        name = entry.get("character_name")
        if name and name not in known_names:
            errors.append(f"vocal_performers[{i}].character_name '{name}' does not match any character in the blueprint's narrative_supplement.character_biographies")

    return errors


# ---------------------------------------------------------------------------
# Worked example
# ---------------------------------------------------------------------------

def _build_example():
    import importlib.util
    from pathlib import Path

    def load(name):
        spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(f"{name}.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    blueprint = load("universal_production_blueprint")
    bios = blueprint.EXAMPLE_UNIVERSAL_PRODUCTION_BLUEPRINT["narrative_supplement"]["character_biographies"]
    bios_by_name = {b["name"]: b for b in bios}

    provider = "nano_banana"
    character_references = [
        translate_character_to_reference_prompt(bios_by_name["The Builder"], provider),
        translate_character_to_reference_prompt(bios_by_name["The Asker"], provider),
    ]

    return {
        "schema_version": "1.0.0",
        "source_principle_id": "hope",
        "source_human_truth_id": "rebuilding_after_loss",
        "no_narrator": True,
        "character_reference_provider": provider,
        "character_references": character_references,
        "vocal_performers": [
            {
                "character_name": "The Builder",
                "register": "low-mid, conversational",
                "texture": "unprocessed, breath and imperfection left in",
                "description": "Sings the way someone talks to themselves before they believe it, not the way someone performs conviction -- matches the Musical Architecture's vocal_tone.",
                "sings_during_shot_ids": ["shot1", "shot3", "shot4", "shot5", "shot6", "shot7", "shot8"],
                "lip_sync_required": True,
            },
            {
                "character_name": "The Asker",
                "register": "mid, direct",
                "texture": "plain, unornamented",
                "description": "Delivers the catalyst question as a single sung line, not spoken -- the only line they have in the piece.",
                "sings_during_shot_ids": ["shot2"],
                "lip_sync_required": True,
            },
        ],
        "non_goals": [
            REQUIRED_ETHICS_NON_GOAL,
            "This package does not claim lip-sync accuracy has been measured -- lip_sync_required flags intent, not verified output quality.",
            "This package does not claim character_reference_provider has been benchmarked for consistency -- Nano Banana is a starting candidate, not a validated choice.",
        ],
        "source": (
            "DreamMusicForge v2 Character Performance Package, worked example replacing narration with the "
            "Hope chain's two characters (The Builder, The Asker) singing themselves across all 8 shots, "
            "using Nano Banana (Gemini 2.5 Flash Image) as the character-reference provider for consistency."
        ),
        "truth_status": "ASSUMED",
    }


EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE = _build_example()


if __name__ == "__main__":
    errors = validate_character_performance_package(EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE)
    if errors:
        raise SystemExit("FAIL: " + "; ".join(errors))
    print(
        f"PASS: example Character Performance Package is valid "
        f"(no_narrator={EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE['no_narrator']}, "
        f"{len(EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE['vocal_performers'])} singing characters covering all 8 shots)"
    )
