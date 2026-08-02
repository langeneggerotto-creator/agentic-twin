"""Universal Production Blueprint: the assembly document for the
DreamMusicForge v2 pipeline.

Keeps three tiers of the mission's ~28-section blueprint explicitly
separate rather than flattening them into one document, because they
carry different epistemic status:

  Tier 1 -- embedded_documents: VERIFIED_STRUCTURED. Full instances of
    the five already-implemented pipeline documents, re-validated here
    against every existing single-document and cross-document check.
  Tier 2 -- narrative_supplement: DESIGNED_FREE_TEXT. Required, real,
    but not cross-checked the way tier 1 is.
  Tier 3 -- provider_specific_prompt_sets: NOT_YET_BUILT. The provider
    translation layer does not exist yet; this section says so rather
    than faking completeness.

This mirrors the discipline in this repo's source material (a video on
the several distinct, non-interchangeable meanings of "dimension" in
physics and mathematics): don't let one word -- here, one document --
cover claims of different reliability without marking which is which.

validate_universal_production_blueprint(doc) checks structure alone.
validate_full_chain(doc) additionally re-runs every validator already
built for principle_kernel, narrative_emotional_architecture,
musical_architecture, cinematic_architecture, and editorial_architecture
-- the closest thing this repo has to a full pipeline integration test.

embed_provider_specific_production_package(blueprint, provider_package)
wires tier 3 up: it validates a real Provider-Specific Production Package,
and if it's clean, promotes provider_specific_prompt_sets from the
not_yet_built placeholder to a "draft" status carrying real prompts.
Whether to promote is decided by compute_readiness_activation(), a single
artificial neuron built exactly per the classic formulation introduced in
3Blue1Brown's "But what is a neural network?" (weighted sum of inputs plus
a bias, squashed through a sigmoid into [0, 1]) -- applied here to two
features of the package's Monte Carlo risk estimate, rather than a flat
if/else, so the promotion decision is a continuous, inspectable score
instead of a single hidden threshold. It can only ever promote to "draft",
never "complete" -- that still requires the review_checklist.

sync_review_checklist_with_provider_status(doc), also called automatically
at the end of embed_provider_specific_production_package(), advances the
councils with something concrete to review once real prompts exist
(visual_council, music_council, ethics_council) from "pending" to
"in_review". It only ever moves a council forward from "pending" -- it
never regresses a council a human has already advanced or reviewed, and it
never advances anything while build_status is still "not_yet_built".
"""

import copy
import importlib.util
import math
from pathlib import Path

VALID_CONFIDENCE = {"VERIFIED", "INFERRED", "ASSUMED", "UNKNOWN"}

REQUIRED_ETHICS_NON_GOAL = (
    "This kernel does not claim to guarantee any specific viewer belief, emotion, or decision."
)

REVIEW_COUNCILS = {
    "story_council", "editorial_council", "music_council", "performance_council",
    "visual_council", "symbolism_council", "audience_council", "ethics_council",
}
REVIEW_STATUSES = {"pending", "in_review", "approved", "needs_revision"}
PROVIDER_BUILD_STATUSES = {"not_yet_built", "draft", "complete"}


def _load_sibling(module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, Path(__file__).with_name(f"{module_name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Readiness neuron -- one artificial neuron, per the classic formulation:
# activation = sigmoid(weighted_sum(inputs) + bias)
# ---------------------------------------------------------------------------

READINESS_WEIGHTS = {"low_risk": 6.0, "efficiency": 4.0}
READINESS_BIAS = -7.0
READINESS_THRESHOLD = 0.5


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def compute_readiness_activation(provider_package_doc: dict) -> dict:
    """Two features of a Provider-Specific Production Package's Monte Carlo
    generation_risk_estimate, combined by a single neuron:

      low_risk_feature  = 1 - estimated_probability_exceeds_budget  (in [0, 1])
      efficiency_feature = num_shots / mean_total_attempts           (in (0, 1])

    weighted_sum = w_low_risk * low_risk_feature + w_efficiency * efficiency_feature + bias
    activation   = sigmoid(weighted_sum)

    This only gates promotion to the Blueprint's "draft" build_status --
    never "complete". A high activation says the risk profile is healthy
    enough to treat the prompts as a real draft; it is not a review.
    """
    risk = provider_package_doc["generation_risk_estimate"]
    num_shots = len(provider_package_doc.get("video_prompts", []))
    mean_total_attempts = risk.get("mean_total_attempts", 0)

    low_risk_feature = 1.0 - risk["estimated_probability_exceeds_budget"]
    efficiency_feature = min(1.0, num_shots / mean_total_attempts) if mean_total_attempts else 0.0

    weighted_sum = (
        READINESS_WEIGHTS["low_risk"] * low_risk_feature
        + READINESS_WEIGHTS["efficiency"] * efficiency_feature
        + READINESS_BIAS
    )
    activation = _sigmoid(weighted_sum)

    return {
        "low_risk_feature": low_risk_feature,
        "efficiency_feature": efficiency_feature,
        "weighted_sum": weighted_sum,
        "activation": activation,
        "ready": activation >= READINESS_THRESHOLD,
    }


REVIEW_COUNCILS_UNLOCKED_BY_DRAFT_PROMPTS = {"visual_council", "music_council", "ethics_council"}


def sync_review_checklist_with_provider_status(doc: dict) -> dict:
    """Advance visual_council, music_council, and ethics_council from
    'pending' to 'in_review' once provider_specific_prompt_sets reaches
    'draft' or 'complete' -- those are the councils with something concrete
    to review (real prompts) at that point. Story, editorial, performance,
    symbolism, and audience councils depend on more than prompts existing
    (actual generated footage, edited assembly) and are left untouched.

    Never regresses a council a human has already moved past 'pending'
    (in_review/approved/needs_revision stay exactly as they are), and never
    advances anything while build_status is still 'not_yet_built'. Does
    not mutate the input.
    """
    updated = copy.deepcopy(doc)
    build_status = updated.get("provider_specific_prompt_sets", {}).get("build_status")
    if build_status not in ("draft", "complete"):
        return updated

    for entry in updated.get("review_checklist", []):
        if entry.get("council_name") in REVIEW_COUNCILS_UNLOCKED_BY_DRAFT_PROMPTS and entry.get("status") == "pending":
            entry["status"] = "in_review"
            note = f"Auto-advanced to in_review: provider_specific_prompt_sets reached '{build_status}'."
            entry["notes"] = f"{entry['notes']} {note}" if entry.get("notes") else note

    return updated


def embed_provider_specific_production_package(blueprint_doc: dict, provider_package_doc: dict) -> dict:
    """Wire a real Provider-Specific Production Package into a Universal
    Production Blueprint's tier-3 provider_specific_prompt_sets, replacing
    the not_yet_built placeholder. Does not mutate either input.

    Returns {"blueprint": ..., "errors": [...], "readiness": ... or None}.
    If the provider package fails its own validation, or doesn't match the
    blueprint's embedded Cinematic Architecture or chain identity, tier 3
    is left untouched (still not_yet_built) and errors explains why.
    """
    provider_module = _load_sibling("provider_specific_production_package")

    errors = list(provider_module.validate_provider_specific_production_package(provider_package_doc))

    cinematic_doc = blueprint_doc.get("embedded_documents", {}).get("cinematic_architecture", {})
    errors.extend(provider_module.validate_against_cinematic_architecture(provider_package_doc, cinematic_doc))

    if provider_package_doc.get("source_principle_id") != blueprint_doc.get("source_principle_id"):
        errors.append("provider package source_principle_id does not match the blueprint")
    if provider_package_doc.get("source_human_truth_id") != blueprint_doc.get("source_human_truth_id"):
        errors.append("provider package source_human_truth_id does not match the blueprint")

    updated = copy.deepcopy(blueprint_doc)

    if errors:
        return {"blueprint": updated, "errors": errors, "readiness": None}

    readiness = compute_readiness_activation(provider_package_doc)

    prompts = [
        {"provider": entry["provider"], "prompt_text": entry["prompt_text"]}
        for entry in provider_package_doc["video_prompts"]
    ]
    music = provider_package_doc["music_prompt"]
    prompts.append({"provider": music["provider"], "prompt_text": music["prompt_text"]})

    build_status = "draft" if readiness["ready"] else "not_yet_built"
    updated["provider_specific_prompt_sets"] = {
        "build_status": build_status,
        "prompts": prompts if build_status != "not_yet_built" else [],
    }
    updated = sync_review_checklist_with_provider_status(updated)

    return {"blueprint": updated, "errors": [], "readiness": readiness}


def validate_universal_production_blueprint(doc: dict) -> list[str]:
    errors = []

    for field in [
        "schema_version", "source_principle_id", "source_human_truth_id",
        "embedded_documents", "narrative_supplement", "provider_specific_prompt_sets",
        "review_checklist", "non_goals", "truth_status",
    ]:
        if field not in doc or doc[field] in (None, "", [], {}):
            errors.append(f"missing required field: {field}")

    if "truth_status" in doc and doc["truth_status"] not in VALID_CONFIDENCE:
        errors.append(f"truth_status must be one of {sorted(VALID_CONFIDENCE)}")

    embedded = doc.get("embedded_documents")
    if isinstance(embedded, dict):
        for key in ["principle_kernel", "narrative_emotional_architecture", "musical_architecture",
                    "cinematic_architecture", "editorial_architecture"]:
            if not embedded.get(key):
                errors.append(f"embedded_documents.{key} is required")
    elif "embedded_documents" in doc:
        errors.append("embedded_documents must be an object")

    supplement = doc.get("narrative_supplement")
    if isinstance(supplement, dict):
        for field in ["creative_brief", "audience_profile", "scene_breakdown", "sequence_plan",
                      "wardrobe_notes", "production_design", "symbolism_ledger",
                      "choreography_and_blocking", "sound_design", "reflection_and_legacy_statement"]:
            if not supplement.get(field):
                errors.append(f"narrative_supplement.{field} is required")
        bios = supplement.get("character_biographies")
        if isinstance(bios, list):
            if len(bios) < 1:
                errors.append("narrative_supplement.character_biographies must contain at least one entry")
            for i, bio in enumerate(bios):
                for field in ["name", "role", "description"]:
                    if not bio.get(field):
                        errors.append(f"narrative_supplement.character_biographies[{i}].{field} is required")
        elif "character_biographies" in supplement:
            errors.append("narrative_supplement.character_biographies must be a list")
        elif supplement:
            errors.append("narrative_supplement.character_biographies is required")
    elif "narrative_supplement" in doc:
        errors.append("narrative_supplement must be an object")

    prompt_sets = doc.get("provider_specific_prompt_sets")
    if isinstance(prompt_sets, dict):
        build_status = prompt_sets.get("build_status")
        if build_status is not None and build_status not in PROVIDER_BUILD_STATUSES:
            errors.append(f"provider_specific_prompt_sets.build_status must be one of {sorted(PROVIDER_BUILD_STATUSES)}")
        prompts = prompt_sets.get("prompts")
        if not isinstance(prompts, list):
            errors.append("provider_specific_prompt_sets.prompts must be a list")
        else:
            if build_status == "not_yet_built" and len(prompts) > 0:
                errors.append("provider_specific_prompt_sets.prompts must be empty while build_status is 'not_yet_built'")
            if build_status in ("draft", "complete") and len(prompts) == 0:
                errors.append(f"provider_specific_prompt_sets.prompts must be non-empty when build_status is '{build_status}'")
    elif "provider_specific_prompt_sets" in doc:
        errors.append("provider_specific_prompt_sets must be an object")

    checklist = doc.get("review_checklist")
    if isinstance(checklist, list):
        seen = set()
        for i, entry in enumerate(checklist):
            name = entry.get("council_name")
            status = entry.get("status")
            if name is None:
                errors.append(f"review_checklist[{i}].council_name is required")
            elif name not in REVIEW_COUNCILS:
                errors.append(f"review_checklist[{i}].council_name must be one of {sorted(REVIEW_COUNCILS)}")
            else:
                seen.add(name)
            if status is None:
                errors.append(f"review_checklist[{i}].status is required")
            elif status not in REVIEW_STATUSES:
                errors.append(f"review_checklist[{i}].status must be one of {sorted(REVIEW_STATUSES)}")
        missing_councils = REVIEW_COUNCILS - seen
        if missing_councils:
            errors.append(f"review_checklist is missing councils: {sorted(missing_councils)}")
        extra = len(checklist) - len(REVIEW_COUNCILS)
        if extra > 0:
            errors.append("review_checklist must contain each council exactly once, no duplicates")
    elif "review_checklist" in doc:
        errors.append("review_checklist must be a list")

    non_goals = doc.get("non_goals")
    if isinstance(non_goals, list):
        if REQUIRED_ETHICS_NON_GOAL not in non_goals:
            errors.append(f"non_goals must include the required ethics constraint: {REQUIRED_ETHICS_NON_GOAL!r}")
    elif "non_goals" in doc:
        errors.append("non_goals must be a list")

    return errors


def validate_full_chain(doc: dict) -> list[str]:
    """Re-run every existing single-document and cross-document validator
    against the embedded documents. The closest thing this repo has to a
    full pipeline integration test."""
    errors = []

    embedded = doc.get("embedded_documents", {})
    principle = embedded.get("principle_kernel", {})
    narrative_doc = embedded.get("narrative_emotional_architecture", {})
    musical_doc = embedded.get("musical_architecture", {})
    cinematic_doc = embedded.get("cinematic_architecture", {})
    editorial_doc = embedded.get("editorial_architecture", {})

    principle_kernel = _load_sibling("principle_kernel")
    narrative = _load_sibling("narrative_emotional_architecture")
    musical = _load_sibling("musical_architecture")
    cinematic = _load_sibling("cinematic_architecture")
    editorial = _load_sibling("editorial_architecture")

    for err in principle_kernel.validate_principle_kernel(principle):
        errors.append(f"[principle_kernel] {err}")

    for err in narrative.validate_narrative_emotional_architecture(narrative_doc):
        errors.append(f"[narrative_emotional_architecture] {err}")

    for err in musical.validate_musical_architecture(musical_doc):
        errors.append(f"[musical_architecture] {err}")
    for err in musical.validate_against_narrative_architecture(musical_doc, narrative_doc):
        errors.append(f"[musical_architecture vs narrative] {err}")

    for err in cinematic.validate_cinematic_architecture(cinematic_doc):
        errors.append(f"[cinematic_architecture] {err}")
    for err in cinematic.validate_against_narrative_architecture(cinematic_doc, narrative_doc):
        errors.append(f"[cinematic_architecture vs narrative] {err}")
    for err in cinematic.validate_against_musical_architecture(cinematic_doc, musical_doc):
        errors.append(f"[cinematic_architecture vs musical] {err}")

    for err in editorial.validate_editorial_architecture(editorial_doc):
        errors.append(f"[editorial_architecture] {err}")
    for err in editorial.validate_against_cinematic_architecture(editorial_doc, cinematic_doc):
        errors.append(f"[editorial_architecture vs cinematic] {err}")
    for err in editorial.validate_against_musical_architecture(editorial_doc, musical_doc):
        errors.append(f"[editorial_architecture vs musical] {err}")

    blueprint_principle_id = doc.get("source_principle_id")
    blueprint_truth_id = doc.get("source_human_truth_id")
    for doc_key, doc_obj in [
        ("narrative_emotional_architecture", narrative_doc),
        ("musical_architecture", musical_doc),
        ("cinematic_architecture", cinematic_doc),
        ("editorial_architecture", editorial_doc),
    ]:
        if doc_obj.get("source_principle_id") != blueprint_principle_id:
            errors.append(f"[chain identity] embedded_documents.{doc_key}.source_principle_id does not match the blueprint's source_principle_id")
        if doc_obj.get("source_human_truth_id") != blueprint_truth_id:
            errors.append(f"[chain identity] embedded_documents.{doc_key}.source_human_truth_id does not match the blueprint's source_human_truth_id")
    if principle.get("principle_id") != blueprint_principle_id:
        errors.append("[chain identity] embedded_documents.principle_kernel.principle_id does not match the blueprint's source_principle_id")

    return errors


def _build_example():
    principle_kernel = _load_sibling("principle_kernel")
    narrative = _load_sibling("narrative_emotional_architecture")
    musical = _load_sibling("musical_architecture")
    cinematic = _load_sibling("cinematic_architecture")
    editorial = _load_sibling("editorial_architecture")
    provider_package = _load_sibling("provider_specific_production_package")

    doc = {
        "schema_version": "1.0.0",
        "source_principle_id": "hope",
        "source_human_truth_id": "rebuilding_after_loss",
        "embedded_documents": {
            "principle_kernel": principle_kernel.EXAMPLE_PRINCIPLE_KERNEL,
            "narrative_emotional_architecture": narrative.EXAMPLE_NARRATIVE_EMOTIONAL_ARCHITECTURE,
            "musical_architecture": musical.EXAMPLE_MUSICAL_ARCHITECTURE,
            "cinematic_architecture": cinematic.EXAMPLE_CINEMATIC_ARCHITECTURE,
            "editorial_architecture": editorial.EXAMPLE_EDITORIAL_ARCHITECTURE,
        },
        "narrative_supplement": {
            "creative_brief": "A short piece exploring hope as the willingness to take one small, visible action toward rebuilding without any guarantee it will work.",
            "audience_profile": "Adults who have experienced a significant setback (career, relationship, creative project) within the past few years; not aimed at anyone currently in acute crisis.",
            "character_biographies": [
                {"name": "The Builder", "role": "protagonist", "description": "Built something over years; it was destroyed by circumstance outside their control. No backstory beyond the wreckage is given -- the piece is about the response, not the cause."},
                {"name": "The Asker", "role": "catalyst", "description": "Present only in the catalyst beat. Asks the question that starts the choice, then exits the piece entirely."},
            ],
            "scene_breakdown": "Eight scenes, one per narrative stage, matching the eight shots in the Cinematic Architecture and the eight cuts in the Editorial Architecture.",
            "sequence_plan": "Linear, no flashbacks. The wreckage is only ever shown as it exists in the present tense of the piece.",
            "wardrobe_notes": "The Builder wears the same clothing throughout, visibly worn by shot 3, so any change the audience perceives is read from the environment and the object, not costume changes.",
            "production_design": "Wreckage built from recognizable but non-branded materials; the new structure uses visibly different, newer material so the two eras are legible without dialogue.",
            "symbolism_ledger": "Primary symbol: the two broken pieces (shot 3) that cannot be rejoined, contrasted with the first new plank (shot 6) which is new material, not a repair -- rebuilding is not restoration.",
            "choreography_and_blocking": "Minimal blocking throughout; the only sustained movement is the Builder's approach to the wreckage in shot 6, kept slow relative to the tempo_map's bpm increase at that segment.",
            "sound_design": "Diegetic sound (wind, debris settling, footsteps) present under the score throughout; drops out entirely for the two-bar silence after seg5, then returns with the transformation beat.",
            "reflection_and_legacy_statement": "The piece aims to leave the audience with an image -- a person choosing to build in view of what was lost -- rather than a stated conclusion about what hope means; what they take from that image is left to them.",
        },
        "provider_specific_prompt_sets": {
            "build_status": "not_yet_built",
            "prompts": [],
        },
        "review_checklist": [
            {"council_name": "story_council", "status": "pending"},
            {"council_name": "editorial_council", "status": "pending"},
            {"council_name": "music_council", "status": "pending"},
            {"council_name": "performance_council", "status": "pending"},
            {"council_name": "visual_council", "status": "pending"},
            {"council_name": "symbolism_council", "status": "pending"},
            {"council_name": "audience_council", "status": "pending"},
            {"council_name": "ethics_council", "status": "pending"},
        ],
        "non_goals": [
            REQUIRED_ETHICS_NON_GOAL,
            "This blueprint does not claim the provider_specific_prompt_sets section is complete -- see its build_status; 'draft' means the readiness neuron passed, not that a human reviewed it.",
            "This blueprint does not claim any review_checklist entry has actually been reviewed -- all entries start pending.",
        ],
        "source": (
            "DreamMusicForge v2 Universal Production Blueprint, worked example assembling the complete Hope "
            "chain (Principle Kernel -> Narrative/Emotional -> Musical -> Cinematic -> Editorial) built across "
            "this repo's prior sessions, with a real Provider-Specific Production Package wired into tier 3 "
            "via embed_provider_specific_production_package()."
        ),
        "truth_status": "ASSUMED",
    }

    wiring = embed_provider_specific_production_package(doc, provider_package.EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE)
    if wiring["errors"]:
        raise RuntimeError(f"failed to wire the example provider package into the example blueprint: {wiring['errors']}")
    return wiring["blueprint"]


EXAMPLE_UNIVERSAL_PRODUCTION_BLUEPRINT = _build_example()


if __name__ == "__main__":
    structural_errors = validate_universal_production_blueprint(EXAMPLE_UNIVERSAL_PRODUCTION_BLUEPRINT)
    chain_errors = validate_full_chain(EXAMPLE_UNIVERSAL_PRODUCTION_BLUEPRINT)
    errors = structural_errors + chain_errors
    if errors:
        raise SystemExit("FAIL: " + "; ".join(errors))
    build_status = EXAMPLE_UNIVERSAL_PRODUCTION_BLUEPRINT["provider_specific_prompt_sets"]["build_status"]
    print(
        f"PASS: example Universal Production Blueprint is valid ({len(chain_errors)} chain errors, "
        f"full 5-document integration check clean, provider_specific_prompt_sets.build_status={build_status!r})"
    )
