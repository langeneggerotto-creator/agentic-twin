"""Assembly Package: stage-9 post-generation assembly for the
DreamMusicForge v2 pipeline.

Agreed direction: prefer providers that generate video, vocal audio, and
lip sync together in one call (Kling AI Avatar, Runway Act-Two, Veo 3 with
native audio) over the older three-step pipeline of silent video ->
separate TTS/singing voice -> bolt-on lip-sync (Wav2Lip-style). The old way
has more failure points and more drift between audio and mouth movement.
native_av_policy and validate_native_av_requirement() make that a checked
requirement on every shot with a singing, lip-synced performer, not just a
design note.

What no single provider call can do, and what this module actually builds:

1. Duration reconciliation. Generated clip length is never exactly the
   planned cut duration. reconcile_cut_duration() derives a strategy
   deterministically from the drift and whether the cut is beat-matched:
   negligible drift is left alone (exact_match); drift within tolerance is
   absorbed with a speed ramp that preserves the planned timeline exactly
   (speed_adjust); larger drift on a cut that ISN'T beat-matched can be
   trimmed or padded with a held last frame; anything beyond that -- or any
   drift at all beyond a tighter tolerance on a beat-matched cut, where
   trimming or padding would break the cut-on-beat guarantee the Editorial
   Architecture already validated -- is routed to requires_manual_review
   rather than silently forced to fit.
2. An ffmpeg filter_complex command, built deterministically from the
   reconciliation results via render_ffmpeg_command(). Re-derivable: the
   validator rebuilds it from shot_assemblies and rejects the document if
   the stored command doesn't match, same discipline as the Monte Carlo
   generation_risk_estimate and the rights_review checks elsewhere in this
   pipeline.
3. A simple, explicit audio ducking plan (build_audio_mix_plan()): the
   score volume drops under any cut where a performer sings, so the vocal
   stays intelligible. Documented as an assumed constant policy, not a
   measured loudness analysis.

Four validators:

- validate_assembly_package(doc): structural checks, including
  reconciliation and concat_command reproducibility.
- validate_against_editorial_architecture(doc, editorial_doc): cut
  coverage and planned duration / cut_on_beat agreement.
- validate_against_character_performance_package(doc, character_doc):
  has_singing_performer must match who actually sings where.
- validate_native_av_requirement(doc, provider_doc): every shot with a
  singing performer must be assigned a provider in native_av_policy's
  allowlist in the paired Provider-Specific Production Package.
"""

VALID_CONFIDENCE = {"VERIFIED", "INFERRED", "ASSUMED", "UNKNOWN"}

REQUIRED_ETHICS_NON_GOAL = (
    "This kernel does not claim to guarantee any specific viewer belief, emotion, or decision."
)
REQUIRED_ASSEMBLY_NON_GOAL = (
    "This package has not executed real ffmpeg or received real provider output -- concat_command is a "
    "re-derivable plan, not a rendered file, and actual_duration_seconds in a worked example is a "
    "simulated, illustrative figure, not a measured result."
)

NATIVE_AV_PROVIDERS = ["kling_ai_avatar", "runway_act_two", "veo3_native_audio"]

RECONCILIATION_STRATEGIES = {"exact_match", "speed_adjust", "trim", "pad_hold_last_frame", "requires_manual_review"}

EXACT_MATCH_TOLERANCE = 0.01
SPEED_ADJUST_TOLERANCE = 0.08
BEAT_SPEED_ADJUST_TOLERANCE = 0.15
TRIM_PAD_TOLERANCE = 0.25

VOCAL_DUCK_SCORE_VOLUME = 0.22
INSTRUMENTAL_SCORE_VOLUME = 0.85


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------

def reconcile_cut_duration(planned_duration_seconds: float, actual_duration_seconds: float, cut_on_beat: bool) -> tuple:
    """Return (reconciliation_strategy, reconciled_duration_seconds).

    reconciled_duration_seconds is always planned_duration_seconds when a
    strategy is chosen -- reconciliation absorbs drift into how the clip is
    played back, it never silently redefines the planned timeline. Returns
    None for reconciled_duration_seconds when the drift can't be safely
    absorbed and the cut needs a human decision instead.
    """
    ratio = actual_duration_seconds / planned_duration_seconds
    drift = abs(ratio - 1)

    if drift <= EXACT_MATCH_TOLERANCE:
        return "exact_match", planned_duration_seconds

    if cut_on_beat:
        # Trimming or padding a beat-matched cut would break the cut-on-beat
        # guarantee the Editorial Architecture already validated -- only a
        # speed ramp preserves that timing exactly, and only within a wider
        # tolerance than an un-matched cut gets, since the ramp itself needs
        # to stay imperceptible.
        if drift <= BEAT_SPEED_ADJUST_TOLERANCE:
            return "speed_adjust", planned_duration_seconds
        return "requires_manual_review", None

    if drift <= SPEED_ADJUST_TOLERANCE:
        return "speed_adjust", planned_duration_seconds
    if drift <= TRIM_PAD_TOLERANCE:
        strategy = "trim" if actual_duration_seconds > planned_duration_seconds else "pad_hold_last_frame"
        return strategy, planned_duration_seconds
    return "requires_manual_review", None


def build_ffmpeg_filter(strategy: str, planned_duration_seconds: float, actual_duration_seconds: float) -> dict:
    if strategy == "exact_match" or strategy == "requires_manual_review":
        return None
    if strategy == "speed_adjust":
        video_factor = planned_duration_seconds / actual_duration_seconds
        audio_factor = actual_duration_seconds / planned_duration_seconds
        return {
            "video": f"setpts={video_factor:.6f}*PTS",
            "audio": f"atempo={audio_factor:.6f}",
        }
    if strategy == "trim":
        return {
            "video": f"trim=start=0:end={planned_duration_seconds:.3f},setpts=PTS-STARTPTS",
            "audio": f"atrim=start=0:end={planned_duration_seconds:.3f},asetpts=PTS-STARTPTS",
        }
    if strategy == "pad_hold_last_frame":
        pad = planned_duration_seconds - actual_duration_seconds
        return {
            "video": f"tpad=stop_mode=clone:stop_duration={pad:.3f}",
            "audio": f"apad=pad_dur={pad:.3f}",
        }
    raise ValueError(f"unknown reconciliation strategy: {strategy}")


def build_shot_assembly(cut: dict, actual_duration_seconds: float, has_singing_performer: bool) -> dict:
    planned = cut["duration_seconds"]
    strategy, reconciled = reconcile_cut_duration(planned, actual_duration_seconds, cut["cut_on_beat"])
    return {
        "cut_id": cut["cut_id"],
        "shot_id": cut["shot_id"],
        "planned_duration_seconds": planned,
        "actual_duration_seconds": actual_duration_seconds,
        "cut_on_beat": cut["cut_on_beat"],
        "has_singing_performer": has_singing_performer,
        "reconciliation_strategy": strategy,
        "reconciled_duration_seconds": reconciled,
        "ffmpeg_filter": build_ffmpeg_filter(strategy, planned, actual_duration_seconds),
    }


def compute_assembly_status(shot_assemblies: list) -> str:
    if any(s["reconciliation_strategy"] == "requires_manual_review" for s in shot_assemblies):
        return "blocked_manual_review_required"
    return "ready_to_render"


# ---------------------------------------------------------------------------
# Audio mix + ffmpeg command
# ---------------------------------------------------------------------------

def build_audio_mix_plan(shot_assemblies: list) -> list:
    return [
        {
            "cut_id": s["cut_id"],
            "vocal_present": s["has_singing_performer"],
            "score_volume": VOCAL_DUCK_SCORE_VOLUME if s["has_singing_performer"] else INSTRUMENTAL_SCORE_VOLUME,
        }
        for s in shot_assemblies
    ]


def render_ffmpeg_command(shot_assemblies: list, output_filename: str = "final_cut.mp4") -> str:
    usable = [s for s in shot_assemblies if s["reconciliation_strategy"] != "requires_manual_review"]

    inputs = " ".join(f'-i "{s["shot_id"]}.mp4"' for s in usable)
    filter_parts = []
    concat_labels = []
    for i, s in enumerate(usable):
        if s["ffmpeg_filter"] is None:
            filter_parts.append(f"[{i}:v]copy[v{i}]")
            filter_parts.append(f"[{i}:a]acopy[a{i}]")
        else:
            filter_parts.append(f"[{i}:v]{s['ffmpeg_filter']['video']}[v{i}]")
            filter_parts.append(f"[{i}:a]{s['ffmpeg_filter']['audio']}[a{i}]")
        concat_labels.append(f"[v{i}][a{i}]")

    filter_parts.append("".join(concat_labels) + f"concat=n={len(usable)}:v=1:a=1[outv][outa]")
    filter_complex = ";".join(filter_parts)
    return f'ffmpeg {inputs} -filter_complex "{filter_complex}" -map "[outv]" -map "[outa]" "{output_filename}"'


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_assembly_package(doc: dict) -> list[str]:
    errors = []

    for field in [
        "schema_version", "source_principle_id", "source_human_truth_id", "native_av_policy",
        "shot_assemblies", "audio_mix_plan", "assembly_status", "concat_command", "non_goals", "truth_status",
    ]:
        if field not in doc or doc[field] in (None, "", [], {}):
            errors.append(f"missing required field: {field}")

    if "truth_status" in doc and doc["truth_status"] not in VALID_CONFIDENCE:
        errors.append(f"truth_status must be one of {sorted(VALID_CONFIDENCE)}")

    policy = doc.get("native_av_policy")
    if isinstance(policy, dict):
        if policy.get("required_for_singing_shots") is not True:
            errors.append("native_av_policy.required_for_singing_shots must be true")
        allowed = policy.get("allowed_providers")
        if not isinstance(allowed, list) or len(allowed) < 1:
            errors.append("native_av_policy.allowed_providers must be a non-empty list")
    elif "native_av_policy" in doc:
        errors.append("native_av_policy must be an object")

    assemblies = doc.get("shot_assemblies")
    if isinstance(assemblies, list):
        if len(assemblies) < 1:
            errors.append("shot_assemblies must contain at least one entry")
        for i, s in enumerate(assemblies):
            for field in [
                "cut_id", "shot_id", "planned_duration_seconds", "actual_duration_seconds",
                "cut_on_beat", "has_singing_performer", "reconciliation_strategy", "reconciled_duration_seconds",
            ]:
                if field not in s or (field != "reconciled_duration_seconds" and s[field] in (None, "")):
                    errors.append(f"shot_assemblies[{i}].{field} is required")

            strategy = s.get("reconciliation_strategy")
            if strategy is not None and strategy not in RECONCILIATION_STRATEGIES:
                errors.append(f"shot_assemblies[{i}].reconciliation_strategy must be one of {sorted(RECONCILIATION_STRATEGIES)}")

            planned = s.get("planned_duration_seconds")
            actual = s.get("actual_duration_seconds")
            cut_on_beat = s.get("cut_on_beat")
            if isinstance(planned, (int, float)) and isinstance(actual, (int, float)) and isinstance(cut_on_beat, bool) and strategy in RECONCILIATION_STRATEGIES:
                recomputed_strategy, recomputed_duration = reconcile_cut_duration(planned, actual, cut_on_beat)
                if recomputed_strategy != strategy:
                    errors.append(
                        f"shot_assemblies[{i}].reconciliation_strategy '{strategy}' does not reproduce from "
                        f"planned/actual/cut_on_beat (recomputed '{recomputed_strategy}'); looks hand-typed"
                    )
                if s.get("reconciled_duration_seconds") != recomputed_duration:
                    errors.append(
                        f"shot_assemblies[{i}].reconciled_duration_seconds does not reproduce "
                        f"(recomputed {recomputed_duration})"
                    )
                recomputed_filter = build_ffmpeg_filter(strategy, planned, actual) if strategy in RECONCILIATION_STRATEGIES else None
                if s.get("ffmpeg_filter") != recomputed_filter:
                    errors.append(f"shot_assemblies[{i}].ffmpeg_filter does not reproduce from its own strategy")

            if strategy == "requires_manual_review" and s.get("reconciled_duration_seconds") is not None:
                errors.append(f"shot_assemblies[{i}].reconciled_duration_seconds must be null when reconciliation_strategy is requires_manual_review")
    elif "shot_assemblies" in doc:
        errors.append("shot_assemblies must be a list")

    mix_plan = doc.get("audio_mix_plan")
    if isinstance(mix_plan, list) and isinstance(assemblies, list):
        recomputed_mix = build_audio_mix_plan(assemblies) if len(errors) == 0 else None
        if recomputed_mix is not None and mix_plan != recomputed_mix:
            errors.append("audio_mix_plan does not reproduce from shot_assemblies' has_singing_performer flags")
    elif "audio_mix_plan" in doc and not isinstance(mix_plan, list):
        errors.append("audio_mix_plan must be a list")

    if isinstance(assemblies, list) and len(assemblies) > 0 and all(
        isinstance(s.get("reconciliation_strategy"), str) for s in assemblies
    ):
        recomputed_status = compute_assembly_status(assemblies)
        if doc.get("assembly_status") != recomputed_status:
            errors.append(f"assembly_status '{doc.get('assembly_status')}' does not reproduce (recomputed '{recomputed_status}')")

        recomputed_command = render_ffmpeg_command(assemblies)
        if doc.get("concat_command") != recomputed_command:
            errors.append("concat_command does not reproduce from shot_assemblies; looks hand-written or stale")

    non_goals = doc.get("non_goals")
    if isinstance(non_goals, list):
        if REQUIRED_ETHICS_NON_GOAL not in non_goals:
            errors.append(f"non_goals must include the required ethics constraint: {REQUIRED_ETHICS_NON_GOAL!r}")
        if REQUIRED_ASSEMBLY_NON_GOAL not in non_goals:
            errors.append(f"non_goals must include the required assembly-honesty constraint: {REQUIRED_ASSEMBLY_NON_GOAL!r}")
    elif "non_goals" in doc:
        errors.append("non_goals must be a list")

    return errors


def validate_against_editorial_architecture(doc: dict, editorial_doc: dict) -> list[str]:
    errors = []

    if doc.get("source_principle_id") != editorial_doc.get("source_principle_id"):
        errors.append("source_principle_id does not match the paired editorial document")
    if doc.get("source_human_truth_id") != editorial_doc.get("source_human_truth_id"):
        errors.append("source_human_truth_id does not match the paired editorial document")

    cuts_by_id = {c["cut_id"]: c for c in editorial_doc.get("edit_timeline", []) if isinstance(c, dict)}
    referenced = set()

    for i, s in enumerate(doc.get("shot_assemblies", [])):
        cut_id = s.get("cut_id")
        if not cut_id:
            continue
        cut = cuts_by_id.get(cut_id)
        if cut is None:
            errors.append(f"shot_assemblies[{i}].cut_id '{cut_id}' is not in the editorial document's edit_timeline")
            continue
        referenced.add(cut_id)
        if s.get("shot_id") != cut.get("shot_id"):
            errors.append(f"shot_assemblies[{i}].shot_id does not match cut '{cut_id}''s shot_id in the editorial document")
        if s.get("planned_duration_seconds") != cut.get("duration_seconds"):
            errors.append(f"shot_assemblies[{i}].planned_duration_seconds does not match cut '{cut_id}''s duration_seconds in the editorial document")
        if s.get("cut_on_beat") != cut.get("cut_on_beat"):
            errors.append(f"shot_assemblies[{i}].cut_on_beat does not match cut '{cut_id}' in the editorial document")

    missing = set(cuts_by_id) - referenced
    if missing:
        errors.append(f"shot_assemblies does not cover every editorial cut; missing: {sorted(missing)}")

    return errors


def validate_against_character_performance_package(doc: dict, character_doc: dict) -> list[str]:
    errors = []

    singing_shot_ids = set()
    for performer in character_doc.get("vocal_performers", []):
        singing_shot_ids.update(performer.get("sings_during_shot_ids", []))

    for i, s in enumerate(doc.get("shot_assemblies", [])):
        shot_id = s.get("shot_id")
        expected = shot_id in singing_shot_ids
        if s.get("has_singing_performer") != expected:
            errors.append(
                f"shot_assemblies[{i}].has_singing_performer is {s.get('has_singing_performer')} but shot "
                f"'{shot_id}' {'has' if expected else 'does not have'} a vocal performer in the character package"
            )

    return errors


def validate_native_av_requirement(doc: dict, provider_doc: dict) -> list[str]:
    errors = []

    allowed = set(doc.get("native_av_policy", {}).get("allowed_providers", []))
    provider_by_shot = {
        vp.get("shot_id"): vp.get("provider")
        for vp in provider_doc.get("video_prompts", []) if isinstance(vp, dict)
    }

    for i, s in enumerate(doc.get("shot_assemblies", [])):
        if not s.get("has_singing_performer"):
            continue
        shot_id = s.get("shot_id")
        provider = provider_by_shot.get(shot_id)
        if provider is None:
            errors.append(f"shot_assemblies[{i}]: shot '{shot_id}' has no matching video_prompts entry in the provider package")
        elif provider not in allowed:
            errors.append(
                f"shot_assemblies[{i}]: shot '{shot_id}' has a singing performer but is assigned provider "
                f"'{provider}', which is not in native_av_policy.allowed_providers {sorted(allowed)} -- "
                f"a silent-video-plus-bolt-on-lip-sync provider is not allowed here"
            )

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

    editorial = load("editorial_architecture")
    character = load("character_performance_package")

    cuts = editorial.EXAMPLE_EDITORIAL_ARCHITECTURE["edit_timeline"]
    singing_shot_ids = set()
    for performer in character.EXAMPLE_CHARACTER_PERFORMANCE_PACKAGE["vocal_performers"]:
        singing_shot_ids.update(performer["sings_during_shot_ids"])

    # Illustrative, not real generation output -- see REQUIRED_ASSEMBLY_NON_GOAL.
    # cut7 deliberately drifts far past tolerance to demonstrate that a bad
    # generation blocks assembly_status rather than being silently forced to fit.
    simulated_actual_durations = {
        "cut1": 4.52, "cut2": 5.35, "cut3": 4.58, "cut4": 3.65,
        "cut5": 5.90, "cut6": 5.05, "cut7": 8.90, "cut8": 7.15,
    }

    shot_assemblies = [
        build_shot_assembly(cut, simulated_actual_durations[cut["cut_id"]], cut["shot_id"] in singing_shot_ids)
        for cut in cuts
    ]

    return {
        "schema_version": "1.0.0",
        "source_principle_id": "hope",
        "source_human_truth_id": "rebuilding_after_loss",
        "native_av_policy": {
            "required_for_singing_shots": True,
            "allowed_providers": list(NATIVE_AV_PROVIDERS),
        },
        "shot_assemblies": shot_assemblies,
        "audio_mix_plan": build_audio_mix_plan(shot_assemblies),
        "assembly_status": compute_assembly_status(shot_assemblies),
        "concat_command": render_ffmpeg_command(shot_assemblies),
        "non_goals": [
            REQUIRED_ETHICS_NON_GOAL,
            REQUIRED_ASSEMBLY_NON_GOAL,
            "This package does not chain multiple atempo filters for extreme speed ratios -- speed_adjust is "
            "only ever chosen within tolerance (<=15%), which stays inside ffmpeg's single-filter atempo range.",
        ],
        "source": (
            "DreamMusicForge v2 Assembly Package, worked example reconciling the Hope chain's 8 beat-matched "
            "cuts against simulated generation output. cut7's simulated drift (39%) deliberately exceeds "
            "tolerance to demonstrate assembly_status routing to blocked_manual_review_required rather than "
            "silently forcing a bad generation to fit the planned timeline."
        ),
        "truth_status": "ASSUMED",
    }


EXAMPLE_ASSEMBLY_PACKAGE = _build_example()


if __name__ == "__main__":
    errors = validate_assembly_package(EXAMPLE_ASSEMBLY_PACKAGE)
    if errors:
        raise SystemExit("FAIL: " + "; ".join(errors))
    print(
        f"PASS: example Assembly Package is valid "
        f"(status={EXAMPLE_ASSEMBLY_PACKAGE['assembly_status']}, "
        f"{sum(1 for s in EXAMPLE_ASSEMBLY_PACKAGE['shot_assemblies'] if s['reconciliation_strategy'] == 'requires_manual_review')} "
        f"cut(s) need manual review)"
    )
