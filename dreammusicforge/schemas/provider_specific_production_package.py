"""Provider-Specific Production Package: the final translation-layer output
contract for the DreamMusicForge v2 pipeline.

Translates the provider-neutral Cinematic and Musical Architecture into one
video provider's and one music provider's prompt format, and estimates
generation risk with a dependency-free Monte Carlo simulation (stdlib
`random` only -- no numpy), modeled directly on the classic "will I finish
two uncertain-duration tasks before a deadline" example: each shot's
per-attempt pass probability is drawn from a uniform distribution, and the
number of attempts needed is geometric, so the simulation estimates the
probability that the whole shot list needs more attempts than a stated
budget.

A provider's rendering of a shot is one interface onto the canonical spec,
not a replacement for it: the Cinematic/Musical/Editorial documents remain
the source of truth. Every prompt entry must declare source_fields_used --
which canonical fields it was actually derived from -- so a provider's
prompt can't silently invent creative content the spec never authorized.

Functions:

- translate_shot_to_video_prompt(shot, provider, duration_seconds=None):
  builds one video_prompts entry from a Cinematic Architecture shot.
- translate_musical_architecture_to_music_prompt(musical_doc, provider,
  target_duration_seconds=None): builds the music_prompt.
- run_generation_risk_monte_carlo(num_shots, per_shot_success_probability_range,
  budget_max_total_attempts, trials, seed=None): the simulation itself.
- validate_provider_specific_production_package(doc): structural checks,
  including reproducibility of the stored Monte Carlo estimate.
- validate_against_cinematic_architecture(doc, cinematic_doc): shot coverage.
"""

import random

VALID_CONFIDENCE = {"VERIFIED", "INFERRED", "ASSUMED", "UNKNOWN"}

REQUIRED_ETHICS_NON_GOAL = (
    "This kernel does not claim to guarantee any specific viewer belief, emotion, or decision."
)
REQUIRED_INTERFACE_NON_GOAL = (
    "No single provider's rendering of a shot or track is presented as the authoritative version of "
    "the work; the Cinematic, Musical, and Editorial Architecture documents remain the canonical source, "
    "and provider output is one interface onto that source, not a replacement for it."
)

MAX_ATTEMPTS_CAP = 1000


# ---------------------------------------------------------------------------
# Translation functions
# ---------------------------------------------------------------------------

def translate_shot_to_video_prompt(shot: dict, provider: str, duration_seconds: float = None) -> dict:
    comp = shot["composition"]
    cam = shot["camera"]
    light = shot["lighting"]
    depth = comp.get("depth_layers", {})

    parts = [
        f"{cam['shot_size'].replace('_', ' ')} shot, {cam['movement']} camera movement.",
        f"Focal point: {comp['focal_point']}.",
        f"Composition: {comp['framing_technique'].replace('_', ' ')} framing.",
    ]
    if comp.get("centered_rationale"):
        parts.append(f"Centered because {comp['centered_rationale']}.")
    if comp.get("leading_lines"):
        parts.append(f"Leading lines: {comp['leading_lines']}.")
    parts.append(
        f"Depth layering -- foreground: {depth.get('foreground') or 'none'}, "
        f"midground: {depth.get('midground') or 'none'}, background: {depth.get('background') or 'none'}."
    )
    parts.append(f"Lighting: {light['key_style']} key light. {light['note']}.")
    parts.append(f"Color and contrast: {comp['color_contrast_strategy']}.")
    if shot.get("blocking_or_performance_note"):
        parts.append(f"Performance: {shot['blocking_or_performance_note']}.")

    source_fields_used = [
        "camera.shot_size", "camera.movement", "composition.focal_point",
        "composition.framing_technique", "composition.depth_layers",
        "lighting.key_style", "lighting.note", "composition.color_contrast_strategy",
    ]
    if comp.get("centered_rationale"):
        source_fields_used.append("composition.centered_rationale")
    if comp.get("leading_lines"):
        source_fields_used.append("composition.leading_lines")
    if shot.get("blocking_or_performance_note"):
        source_fields_used.append("blocking_or_performance_note")

    return {
        "shot_id": shot["shot_id"],
        "provider": provider,
        "prompt_text": " ".join(parts),
        "negative_prompt": "no text overlays, no watermark, no extra limbs, no continuity morphing errors",
        "provider_parameters": {
            "duration_seconds": duration_seconds if duration_seconds is not None else 5.0,
            "aspect_ratio": "16:9",
        },
        "source_fields_used": source_fields_used,
    }


def translate_musical_architecture_to_music_prompt(musical_doc: dict, provider: str, target_duration_seconds: float = None) -> dict:
    instruments = ", ".join(f"{i['instrument']} ({i['role']})" for i in musical_doc["instrumentation"])
    bpms = [seg["bpm"] for seg in musical_doc["tempo_map"]]
    harmonic = musical_doc["harmonic_language"]
    vocal = musical_doc["vocal_tone"]
    motif = musical_doc["melodic_motif"]

    prompt_text = (
        f"Instrumentation: {instruments}. "
        f"Tempo: {min(bpms)}-{max(bpms)} BPM, evolving across the track. "
        f"Harmonic language: {harmonic['mode_or_key']} -- {harmonic['description']} "
        f"Vocal tone: {vocal['register']}, {vocal['texture']} -- {vocal['description']} "
        f"Lyrical intent: {musical_doc['lyrical_intent']} "
        f"Melodic motif: {motif['description']}"
    )

    return {
        "provider": provider,
        "prompt_text": prompt_text,
        "negative_prompt": "no clipping, no unintended auto-tune artifacts",
        "provider_parameters": {
            "target_duration_seconds": target_duration_seconds if target_duration_seconds is not None else 40.0,
            "tempo_range_bpm": [min(bpms), max(bpms)],
        },
        "source_fields_used": ["instrumentation", "tempo_map", "harmonic_language", "vocal_tone", "lyrical_intent", "melodic_motif"],
    }


# ---------------------------------------------------------------------------
# Monte Carlo generation risk estimate
# ---------------------------------------------------------------------------

def _simulate_attempts_for_shot(success_probability: float, rng: random.Random) -> int:
    attempts = 0
    while attempts < MAX_ATTEMPTS_CAP:
        attempts += 1
        if rng.random() < success_probability:
            return attempts
    return attempts


def run_generation_risk_monte_carlo(
    num_shots: int,
    per_shot_success_probability_range: tuple,
    budget_max_total_attempts: int,
    trials: int,
    seed: int = None,
) -> dict:
    """Estimate, by simulation, the probability that generating num_shots
    shots takes more than budget_max_total_attempts attempts in total.

    Each trial draws a fresh per-shot success probability uniformly from
    per_shot_success_probability_range for every shot (modeling uncertainty
    about how reliable the provider will be on this particular production),
    then simulates the number of attempts needed for each shot to pass
    (a geometric distribution given that probability), and sums across shots.
    """
    low, high = per_shot_success_probability_range
    rng = random.Random(seed)
    totals = []
    for _ in range(trials):
        total = 0
        for _ in range(num_shots):
            p = rng.uniform(low, high)
            total += _simulate_attempts_for_shot(p, rng)
        totals.append(total)

    exceeds = sum(1 for t in totals if t > budget_max_total_attempts) / trials
    mean_total = sum(totals) / trials
    return {"estimated_probability_exceeds_budget": exceeds, "mean_total_attempts": mean_total}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_provider_specific_production_package(doc: dict, reproducibility_tolerance: float = 0.05) -> list[str]:
    errors = []

    for field in [
        "schema_version", "source_principle_id", "source_human_truth_id",
        "selected_video_provider", "selected_music_provider", "video_prompts",
        "music_prompt", "generation_risk_estimate", "non_goals", "truth_status",
    ]:
        if field not in doc or doc[field] in (None, "", [], {}):
            errors.append(f"missing required field: {field}")

    if "truth_status" in doc and doc["truth_status"] not in VALID_CONFIDENCE:
        errors.append(f"truth_status must be one of {sorted(VALID_CONFIDENCE)}")

    video_prompts = doc.get("video_prompts")
    if isinstance(video_prompts, list):
        if len(video_prompts) < 1:
            errors.append("video_prompts must contain at least one entry")
        for i, entry in enumerate(video_prompts):
            for field in ["shot_id", "provider", "prompt_text", "source_fields_used"]:
                if field not in entry or entry[field] in (None, "", []):
                    errors.append(f"video_prompts[{i}].{field} is required")
    elif "video_prompts" in doc:
        errors.append("video_prompts must be a list")

    music_prompt = doc.get("music_prompt")
    if isinstance(music_prompt, dict):
        for field in ["provider", "prompt_text", "source_fields_used"]:
            if field not in music_prompt or music_prompt[field] in (None, "", []):
                errors.append(f"music_prompt.{field} is required")
    elif "music_prompt" in doc:
        errors.append("music_prompt must be an object")

    risk = doc.get("generation_risk_estimate")
    if isinstance(risk, dict):
        if risk.get("method") != "monte_carlo_uniform_sampling":
            errors.append("generation_risk_estimate.method must be 'monte_carlo_uniform_sampling'")

        trials = risk.get("trials")
        if not isinstance(trials, int) or trials < 1000:
            errors.append("generation_risk_estimate.trials must be an integer >= 1000")

        prob_range = risk.get("per_shot_success_probability_range")
        low = high = None
        if isinstance(prob_range, dict):
            low, high = prob_range.get("min"), prob_range.get("max")
            if not (isinstance(low, (int, float)) and 0 < low <= 1):
                errors.append("generation_risk_estimate.per_shot_success_probability_range.min must be in (0, 1]")
            if not (isinstance(high, (int, float)) and 0 < high <= 1):
                errors.append("generation_risk_estimate.per_shot_success_probability_range.max must be in (0, 1]")
            if isinstance(low, (int, float)) and isinstance(high, (int, float)) and low >= high:
                errors.append("generation_risk_estimate.per_shot_success_probability_range.min must be less than max")
        else:
            errors.append("generation_risk_estimate.per_shot_success_probability_range is required")

        budget = risk.get("budget_max_total_attempts")
        if not isinstance(budget, int) or budget < 1:
            errors.append("generation_risk_estimate.budget_max_total_attempts must be a positive integer")

        stored_prob = risk.get("estimated_probability_exceeds_budget")
        if not (isinstance(stored_prob, (int, float)) and 0 <= stored_prob <= 1):
            errors.append("generation_risk_estimate.estimated_probability_exceeds_budget must be in [0, 1]")

        # Reproducibility check: rerun the simulation from the stored parameters and
        # confirm the stored estimate wasn't hand-typed or stale.
        if (
            isinstance(trials, int) and trials >= 1000
            and isinstance(low, (int, float)) and isinstance(high, (int, float)) and low < high
            and isinstance(budget, int) and budget >= 1
            and isinstance(stored_prob, (int, float))
            and isinstance(doc.get("video_prompts"), list) and len(doc["video_prompts"]) > 0
        ):
            num_shots = len(doc["video_prompts"])
            recomputed = run_generation_risk_monte_carlo(
                num_shots=num_shots,
                per_shot_success_probability_range=(low, high),
                budget_max_total_attempts=budget,
                trials=max(trials, 5000),
                seed=risk.get("seed"),
            )
            if abs(recomputed["estimated_probability_exceeds_budget"] - stored_prob) > reproducibility_tolerance:
                errors.append(
                    f"generation_risk_estimate.estimated_probability_exceeds_budget ({stored_prob}) does not "
                    f"reproduce from its stated parameters (recomputed {recomputed['estimated_probability_exceeds_budget']}); "
                    f"looks hand-typed rather than simulated"
                )
    elif "generation_risk_estimate" in doc:
        errors.append("generation_risk_estimate must be an object")

    non_goals = doc.get("non_goals")
    if isinstance(non_goals, list):
        if REQUIRED_ETHICS_NON_GOAL not in non_goals:
            errors.append(f"non_goals must include the required ethics constraint: {REQUIRED_ETHICS_NON_GOAL!r}")
        if REQUIRED_INTERFACE_NON_GOAL not in non_goals:
            errors.append(f"non_goals must include the required provider-interface constraint: {REQUIRED_INTERFACE_NON_GOAL!r}")
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

    for i, entry in enumerate(doc.get("video_prompts", [])):
        shot_id = entry.get("shot_id")
        if not shot_id:
            continue
        if shot_id not in shot_ids:
            errors.append(f"video_prompts[{i}].shot_id '{shot_id}' is not in the cinematic document's shots")
        else:
            referenced.add(shot_id)

    missing = shot_ids - referenced
    if missing:
        errors.append(f"video_prompts does not cover every cinematic shot; missing: {sorted(missing)}")

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

    cinematic = load("cinematic_architecture")
    musical = load("musical_architecture")
    editorial = load("editorial_architecture")

    shots = cinematic.EXAMPLE_CINEMATIC_ARCHITECTURE["shots"]
    durations_by_shot = {
        cut["shot_id"]: cut["duration_seconds"]
        for cut in editorial.EXAMPLE_EDITORIAL_ARCHITECTURE["edit_timeline"]
    }
    video_prompts = [
        translate_shot_to_video_prompt(shot, "runway", duration_seconds=durations_by_shot.get(shot["shot_id"]))
        for shot in shots
    ]

    last_cut = editorial.EXAMPLE_EDITORIAL_ARCHITECTURE["edit_timeline"][-1]
    total_duration = last_cut["start_time_seconds"] + last_cut["duration_seconds"]
    music_prompt = translate_musical_architecture_to_music_prompt(
        musical.EXAMPLE_MUSICAL_ARCHITECTURE, "suno", target_duration_seconds=total_duration
    )

    num_shots = len(shots)
    trials = 20000
    prob_range = (0.55, 0.85)
    budget = 14
    risk = run_generation_risk_monte_carlo(
        num_shots=num_shots,
        per_shot_success_probability_range=prob_range,
        budget_max_total_attempts=budget,
        trials=trials,
        seed=42,
    )

    return {
        "schema_version": "1.0.0",
        "source_principle_id": "hope",
        "source_human_truth_id": "rebuilding_after_loss",
        "selected_video_provider": "runway",
        "selected_music_provider": "suno",
        "video_prompts": video_prompts,
        "music_prompt": music_prompt,
        "generation_risk_estimate": {
            "method": "monte_carlo_uniform_sampling",
            "trials": trials,
            "per_shot_success_probability_range": {"min": prob_range[0], "max": prob_range[1]},
            "budget_max_total_attempts": budget,
            "estimated_probability_exceeds_budget": risk["estimated_probability_exceeds_budget"],
            "mean_total_attempts": risk["mean_total_attempts"],
            "seed": 42,
        },
        "non_goals": [
            REQUIRED_ETHICS_NON_GOAL,
            REQUIRED_INTERFACE_NON_GOAL,
            "This package does not claim Runway or Suno were benchmarked -- the success-probability range is an assumed planning estimate, not a measured provider statistic.",
        ],
        "source": (
            "DreamMusicForge v2 Provider-Specific Production Package, worked example translating the "
            "Hope chain's Cinematic and Musical Architecture into Runway and Suno prompts. Monte Carlo "
            "risk model follows the classic uncertain-task-duration-vs-deadline technique, generalized "
            "to per-shot geometric retries; source: https://youtu.be/slbZ-SLpIgg."
        ),
        "truth_status": "ASSUMED",
    }


EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE = _build_example()


if __name__ == "__main__":
    errors = validate_provider_specific_production_package(EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE)
    if errors:
        raise SystemExit("FAIL: " + "; ".join(errors))
    risk = EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE["generation_risk_estimate"]
    print(
        f"PASS: example Provider-Specific Production Package is valid "
        f"(P(exceeds budget)={risk['estimated_probability_exceeds_budget']:.3f}, "
        f"mean total attempts={risk['mean_total_attempts']:.2f})"
    )
