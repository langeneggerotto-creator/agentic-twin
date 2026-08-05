# DreamMusicForge — Intelligent Creative Operating System

**Repository status:** Every pipeline stage from Principle Kernel through Provider-Specific Production Package and Assembly Package has an implemented, tested schema — see [Truth status](#truth-status) for what "implemented" means precisely (dependency-free Python validators + worked examples + passing smoke tests, zero live network calls). What is genuinely not built yet: real API credentials/HTTP calls to any provider, and execution of the generated ffmpeg plans against real media files.

**Version note:** This is the v2 mission and pipeline. It supersedes the v1 video-generation-pipeline framing originally scaffolded here. v1 is preserved, not deleted, at the bottom of this document — see [Superseded v1 design](#superseded-v1-design-preserved-for-evidence-continuity), per the fork-preservation principle in [`CORE_OS_INHERITANCE.md`](../CORE_OS_INHERITANCE.md): "preserve prior models and evidence when scenarios fork."

## Mission

DreamMusicForge is an evidence-informed creative operating system that transforms timeless human principles into emotionally resonant, original audiovisual experiences. It guides creators from an abstract principle to a complete cinematic production blueprint — story, music, lyrics, symbolism, cinematography, performance, editing, color, sound, pacing, and emotional arc — while preserving truth boundaries, originality, and artistic integrity.

It is not a video-clip generator. AI video generation is the last step in the pipeline, not the first.

## The Ultimate DreamMusicForge Principle

DreamMusicForge exists to transform timeless human principles into original audiovisual experiences that help people see themselves, imagine new possibilities, and carry meaningful insights beyond the final frame. Every story begins with an enduring principle, unfolds through authentic human experience, and concludes with reflection rather than instruction. Every creative decision — from lyric to lighting, from camera movement to musical cadence — must serve that transformation while remaining original, truthful, and respectful of the audience's freedom to interpret and grow.

This defines the platform by creative philosophy, not by any particular AI model, video generator, or music generator — the mission stays valid regardless of which tools exist in the future.

## Why the goal is "maximize probability of," not "enforce"

A video cannot guarantee or ethically compel a person's beliefs, emotions, or decisions, and different viewers will interpret the same work differently. The stated goal is therefore:

> Create original audiovisual experiences that maximize the probability of meaningful reflection, emotional connection, and positive personal growth through timeless storytelling, music, symbolism, and cinematic craftsmanship.

This directly constrains the v1 design's stage-6 "comprehension test," which asked whether a viewer received one specific stated lesson — see the note under [Truth status](#truth-status) on how that stage is reframed. It also converges independently with this repository's existing APEX Heart Core gates (`APEX/01_CANON/01_APEX_HEART_CORE.md`): Dignity Gate, Control Gate, and the rule that APEX outputs must not manipulate emotional vulnerability or leave the user unaccountable for their own choices.

## The DreamMusicForge Pipeline

Every project begins with a principle. AI generation is the last stage, not the first.

```text
Timeless Principle
        |
        v
Human Truth
        |
        v
Audience
        |
        v
Transformation Goal
        |
        v
Narrative Architecture
        |
        v
Character Journey
        |
        v
Emotional Architecture
        |
        v
Musical Architecture
        |
        v
Visual Architecture
        |
        v
Shot Architecture
        |
        v
Performance Direction
        |
        v
Editorial Architecture
        |
        v
Character Performance (consistent characters, no narrator)
        |
        v
Provider-Specific Production Package
        |
        v
Assembly Package (native audio-driven generation, duration reconciliation, stitching)
```

## The Seven Core Design Engines

1. **Principle Engine.** Input: a timeless human principle (courage, forgiveness, curiosity, stewardship, resilience, hope, purpose, compassion, ...). Output: a timeless principle kernel.
2. **Human Experience Engine.** Maps the principle onto authentic human experiences. Example: hope may become rebuilding after loss, beginning again, or believing despite uncertainty.
3. **Story Architecture Engine.** Designs beginning, catalyst, conflict, choice, sacrifice, transformation, resolution, reflection. Every story must answer: "What changes?"
4. **Emotional Architecture Engine.** Designs the emotional waveform as explicit transitions (e.g. curiosity -> connection -> tension -> loss -> hope -> wonder -> reflection), not a vague instruction to "make this emotional."
5. **Cinematic Architecture Engine.** Designs composition, camera language, movement, blocking, lighting, wardrobe, production design, symbolic objects, transitions. Every shot must justify why it exists, why it occurs now, and what audience state it changes.
6. **Musical Architecture Engine.** Designs melody, harmony, rhythm, orchestration, vocal tone, dynamics, silence, emotional pacing. Music is another storyteller, not a backing track.
7. **Editorial Architecture Engine.** Designs shot timing, reveal timing, rhythm, motif evolution, visual callbacks, expectation and payoff, emotional pacing, ending.

## Provider layer (provider-neutral)

DreamMusicForge does not depend on one video model or one music model. It produces an abstract production specification, then translates that spec into each provider's prompt format — so the pipeline survives provider churn.

- **Video generation candidates:** Google Veo, Runway, Luma AI Dream Machine, Pika, Kling AI — each with different strengths (cinematic realism, motion consistency, stylization, speed).
- **Music generation candidates:** Suno, Udio.
- **Character-reference candidates:** Nano Banana (Gemini 2.5 Flash Image) — see Character Performance Package.
- **Native audio-driven video candidates** (video + vocal audio + lip sync generated together, required for any shot with a singing performer): Kling AI Avatar, Runway Act-Two, Veo 3 with native audio — see `assembly_package.py`'s `native_av_policy`.
- Musical architecture (emotional progression, instrumentation, tempo map, dynamics, lyrical intent) must be defined before a music provider is selected.

The translation layer (spec -> provider-specific prompts) is implemented and tested; no provider is live-integrated yet -- there are no API credentials, no HTTP calls, and no executed ffmpeg in this repository. See [Truth status](#truth-status).

## The Universal Production Blueprint

Every project should output a complete package: creative brief, principle kernel, audience profile, transformation goal, narrative treatment, character biographies, scene breakdown, sequence plan, shot list, storyboard descriptions, camera directions, lens and framing recommendations, lighting plan, color script, wardrobe notes, production design, symbolism ledger, music brief, lyric brief, vocal direction, choreography and blocking, sound design, editorial timing, transition map, motif evolution, emotional waveform, reflection and legacy statement, provider-specific prompt sets, review checklist.

Most of these artifact types are now covered by an implemented schema somewhere in the chain (Tier 1 of the Universal Production Blueprint below); the remainder live in Tier 2 as required free text, not yet cross-checked the way Tier 1 is. See [Truth status](#truth-status) for the precise split.

## The DreamMusicForge Review Council

Every production is evaluated by specialized reviewers. No single score determines success — councils identify strengths, tradeoffs, and opportunities for refinement.

- Story Council — narrative clarity and transformation.
- Editorial Council — pacing, shot logic, and transitions.
- Music Council — emotional-musical coherence.
- Performance Council — authenticity of acting, movement, and expression.
- Visual Council — cinematography, lighting, color, and composition.
- Symbolism Council — recurring motifs and thematic depth.
- Audience Council — relatability, accessibility, and emotional resonance.
- Ethics Council — originality, respectful representation, and truth boundaries.

## Characters singing themselves, not a narrator (new)

Requested directly: support alternative generation engines (Nano Banana / Gemini 2.5 Flash Image for character-consistent reference images) and replace narration with characters performing their own vocals. Built as a new stage, `schemas/character_performance_package.schema.json` / `.py` / `tests/test_character_performance_package.py` (10 passing smoke tests) — see the truth status table below for `character_performance_package_schema`. It solves two problems:

1. **Character consistency across shots.** This was the "continuity problem" this pipeline named all the way back in its original 6-stage design (SAM 2 / depth-conditioned reference generation) and never actually built. `translate_character_to_reference_prompt()` generates one reference-image prompt per character from the Blueprint's `narrative_supplement.character_biographies`, meant to be conditioned once per character via a provider like Nano Banana, then reused across every shot that character appears in — rather than regenerating the character from text alone each time and hoping it looks the same.
2. **No narrator.** `no_narrator` is a literal hard gate (`const: true`) — the document fails validation if it's `false`. Every `vocal_performers` entry requires `lip_sync_required: true`, and character names are checked against a blocklist (`narrator`, `voiceover`, `announcer`, ...) so a narrator can't sneak back in relabeled as a "character." The worked example replaces narration entirely: The Builder and The Asker between them sing across all 8 shots of the Hope chain, and a test explicitly confirms full shot coverage by singing characters, not narration.

Two cross-document validators: `validate_against_cinematic_architecture()` checks every `sings_during_shot_ids` reference is a real shot, and `validate_against_blueprint()` checks every character singing (or referenced) actually exists in the Blueprint's `character_biographies` — you can't invent a singing character that was never established in the story. To be precise about what that check does and doesn't do: it requires every character to have been *deliberately authored* somewhere in this pipeline's own documents (not silently conjured mid-generation) — it does not require, and must never be read as requiring, real or existing characters. The opposite is the actual goal, covered next.

**Original characters only — a rights-safety requirement, not an afterthought.** Every `character_references` entry now requires `original_character: true` (a hard gate, same pattern as `no_narrator`), a substantive `originality_basis` (≥20 characters — no boilerplate "yes"), and a self-assessed `resembles_existing_ip_risk` (`none_identified` / `possible_overlap_flagged` / `needs_legal_review`). `assess_rights_review_status()` rolls those risk flags into a document-level `rights_review`, following the exact flags → blockers → `hold_for_review` pattern already used in this repo's `apex-rightschain-manifest-builder` — any character flagged above `none_identified` blocks the whole package from `clear_to_proceed`, it isn't just noted and ignored. The validator also reruns `assess_rights_review_status()` and rejects the document if the stored `rights_review` doesn't reproduce from its own `character_references` — same reproducibility discipline as the Monte Carlo `generation_risk_estimate`, so a stale or hand-typed status can't slip through. A best-effort blocklist (`KNOWN_IP_NAME_BLOCKLIST`) also hard-rejects the most obvious slip-up: literally naming or describing a known franchise character (Spider-Man, Batman, Pikachu, etc.) in `character_name` or `reference_prompt`. Be honest about its limits, per `REQUIRED_RIGHTS_NON_GOAL`: this is self-declaration plus a literal-name check, **not** trademark or copyright clearance — it cannot catch a character merely *described* to resemble existing IP without naming it. Final rights clearance is a human/legal judgment, exactly the stance `apex-rightschain-manifest-builder` already takes ("must be verified before public release").

This is additive, not a breaking change to Musical Architecture's existing single `vocal_tone` field — for a character-singing production, read that field as the ensemble/blended texture, and this document as the per-character breakdown needed for lip-sync and character-specific direction.

## Tier 3 wiring (updated)

`provider_specific_prompt_sets` is no longer a hardcoded `"not_yet_built"` placeholder in the worked example. `embed_provider_specific_production_package(blueprint, provider_package)` in `schemas/universal_production_blueprint.py` validates a real Provider-Specific Production Package (its own schema, plus its cross-check against the paired Cinematic Architecture, plus a chain-identity check against the blueprint) and, if clean, promotes tier 3 to `"draft"` with real prompts embedded. If the package doesn't validate or doesn't match the blueprint, tier 3 is left untouched at `"not_yet_built"` and the errors are returned, not swallowed.

Whether to promote is decided by `compute_readiness_activation()` — one artificial neuron, built exactly per the formulation in a cited 3Blue1Brown video on neural networks (weighted sum of inputs plus a bias, squashed through a sigmoid into `[0, 1]`): two features of the Monte Carlo `generation_risk_estimate` (how far below the attempt budget the risk sits, and how efficient the estimated attempts-per-shot are) are combined into a continuous `activation` score rather than a flat if/else threshold on one number. `READINESS_WEIGHTS`, `READINESS_BIAS`, and `READINESS_THRESHOLD` are the "dials" — visible constants, not buried logic. The worked example's activation is **0.741**, well above the 0.5 threshold, so it promotes to `"draft"` with all 9 prompts (8 video + 1 music) embedded. It can only ever reach `"draft"` this way — reaching `"complete"` still requires the `review_checklist`, which is updated by a separate, narrower function (below), not this one.

`embed_provider_specific_production_package()` also calls `sync_review_checklist_with_provider_status()` at the end: once `provider_specific_prompt_sets.build_status` reaches `"draft"` or `"complete"`, the councils with something concrete to review at that point — `visual_council`, `music_council`, `ethics_council` — auto-advance from `"pending"` to `"in_review"`. Story, editorial, performance, symbolism, and audience councils are left `"pending"`, since they depend on more than prompts existing (actual generated footage, an edited assembly). The sync only ever moves a council forward from `"pending"` — it never regresses one a human has already advanced (`in_review`/`approved`/`needs_revision` are left exactly as they are), and it does nothing while `build_status` is still `"not_yet_built"`. In the worked example this leaves `visual_council`, `music_council`, and `ethics_council` at `"in_review"` and the other five at `"pending"`.

## Provider layer status (updated)

The provider layer described earlier is now partially implemented -- see the truth status table below for `provider_specific_production_package_schema`. Three source videos informed this stage, used in three different ways:

- A Monte Carlo simulation walkthrough (estimating whether two uncertain-duration tasks finish before a deadline) became the actual technique behind `generation_risk_estimate`: per-shot pass probability is drawn from a uniform distribution and retries are modeled as geometric, exactly generalizing the video's "sum two uniform durations, check probability of exceeding a threshold" method to "sum N shots' attempt counts, check probability of exceeding an attempt budget." The worked example reproduces the video's own ~12% figure by construction (not by coincidence -- the budget parameter was tuned to land there as a deliberate echo).
- An MCMC / Metropolis-Hastings video was **not** built into this stage. It's the right tool for a later problem this repo doesn't have evidence for yet -- calibrating the per-shot success-probability range from real observed provider outcomes (a Bayesian posterior over provider reliability) rather than the currently-assumed uniform range. Building that now would be speculative infrastructure with no data to calibrate against, which this repo's own non-goals discipline argues against. Noted as a candidate next step below, not implemented.
- A video on the several non-interchangeable meanings of "illusion" and "interface" in neuroscience/perception theory motivated `REQUIRED_INTERFACE_NON_GOAL`: a provider's rendering of a shot is one interface onto the canonical spec (the way different perceptual systems render the same underlying reality differently, per the video's Interface Theory of Perception discussion), not a replacement for the Cinematic/Musical/Editorial documents, which remain the source of truth. Every `video_prompts`/`music_prompt` entry must declare `source_fields_used`, so a provider prompt can't silently invent creative content the canonical spec never authorized.

## Native audio-driven generation and post-generation assembly (new)

Requested directly, after agreeing on the architecture: prefer providers that generate video, vocal audio, and lip sync together in one call (Kling AI Avatar, Runway Act-Two, Veo 3 with native audio) over the older three-step pipeline of silent video → separate TTS/singing voice → bolt-on lip-sync (Wav2Lip-style) — fewer failure points, less audio/video drift, since one provider call handles the sync instead of stitching it on afterward. Built as a new stage, `schemas/assembly_package.schema.json` / `.py` / `tests/test_assembly_package.py` (17 passing smoke tests) — see the truth status table below for `assembly_package_schema`. It solves the two problems no single provider call can:

1. **The native-AV requirement is a checked gate, not a design note.** `native_av_policy.allowed_providers` (documented candidates: `kling_ai_avatar`, `runway_act_two`, `veo3_native_audio`) is required data in the document, and `validate_native_av_requirement()` cross-checks it against the paired Provider-Specific Production Package: every shot with a singing, lip-synced performer (from the Character Performance Package) must be assigned a provider from that allowlist. Because every shot in the Hope chain has a singing performer, this caught a real inconsistency while building it — the Provider Package's worked example was still using plain `runway` (silent-video) for all 8 shots, left over from before this stage existed. Fixed to `kling_ai_avatar` throughout.
2. **Duration reconciliation is worked out as a real algorithm, not hand-waved.** Generated clip length is never exactly the planned cut duration. `reconcile_cut_duration()` derives a strategy deterministically from the drift and whether the cut is beat-matched: negligible drift needs nothing (`exact_match`); drift within tolerance is absorbed with a speed ramp that leaves the planned timeline untouched (`speed_adjust`); on a cut that *isn't* beat-matched, larger drift can be trimmed or padded with a held last frame; anything beyond that — or any drift past a tighter tolerance on a beat-matched cut, where trimming or padding would break the cut-on-beat guarantee the Editorial Architecture already validated — is routed to `requires_manual_review` rather than silently forced to fit. The worked example deliberately gives one cut a 39% simulated drift so `assembly_status` demonstrably lands on `blocked_manual_review_required`, not a rubber-stamped `ready_to_render`.

`render_ffmpeg_command()` builds a real, re-derivable `ffmpeg filter_complex` command from the reconciliation results (per-cut `setpts`/`atempo` for speed ramps, `trim`/`atrim` for cuts, `tpad`/`apad` for holds, then concat) — the validator rebuilds it and rejects the document if the stored command doesn't match, same reproducibility discipline as the Monte Carlo `generation_risk_estimate` and the Character Performance Package's `rights_review`. `build_audio_mix_plan()` ducks the score under any cut where a performer sings, so the vocal stays intelligible — documented as an assumed constant policy (`VOCAL_DUCK_SCORE_VOLUME` / `INSTRUMENTAL_SCORE_VOLUME`), not a measured loudness analysis. `REQUIRED_ASSEMBLY_NON_GOAL` states plainly that no real ffmpeg has been executed and `actual_duration_seconds` in a worked example is simulated, not a real provider result.

**Fixed after a real, reported failure.** The first manual stitch of two real Kling clips (cut1/cut2) produced a file with no audible audio for the person actually testing it, despite ffmpeg's own tools reporting valid, non-corrupt, non-silent audio in it. The cause: every clip's per-input timestamps were being passed straight through (`copy`/`acopy`, no reset) into the concat, and independently-generated clips don't share a common timestamp origin -- ffmpeg's decoder tolerated the resulting discontinuity well enough to still report audio levels, but at least one real player did not play the track at all. `render_ffmpeg_command()` now resets every clip's video and audio timestamps to start at 0 (`setpts=PTS-STARTPTS` / `asetpts=PTS-STARTPTS`) before concatenation, and specifies explicit, broadly-compatible output settings (`-pix_fmt yuv420p`, 44.1kHz AAC, `-movflags +faststart`) instead of leaving them to ffmpeg's defaults. Verified by actually running the regenerated command against the real cut1/cut2 clips outside this environment -- clean encode, no timestamp warnings, matching what worked when re-tested manually. `test_concat_command_resets_timestamps_per_clip_not_copy` and `test_concat_command_uses_broadly_compatible_output_settings` lock this in.

Three cross-document validators: `validate_against_editorial_architecture()` checks cut coverage and that planned duration / `cut_on_beat` weren't silently altered, `validate_against_character_performance_package()` checks `has_singing_performer` against who actually sings where, and `validate_native_av_requirement()` is the provider-allowlist check described above.

## Live provider integration -- Kling AI Avatar (new)

Everything above this section makes zero network calls. `providers/` is the first part of this repository that does (or is built to) -- `schemas/*.py` stays pure validation logic, by design; this is a genuinely different kind of module and is kept structurally separate. Scoped to one provider first, per the plan: `providers/{transport,exceptions,kling_ai_avatar}.py` + `tests/test_kling_ai_avatar_client.py` (14 passing smoke tests, all offline).

**What this proves, and what it doesn't.** No API key is available in this environment, so nothing here has been exercised against Kling's real endpoint -- that's stated plainly in `kling_ai_avatar.py`'s module docstring, not glossed over. What *is* real: the request-building logic (JWT signing, the create-task/poll-task shape, the 2500-character prompt limit, the retry loop), all grounded in Kling's publicly documented API pattern (access-key/secret-key-signed JWT bearer auth, async task creation, a `sound` flag for native audio) and fully exercised by tests via a `FakeTransport` that scripts responses -- no real network call happens anywhere in this repo's test suite, matching every other module here. `DEFAULT_BASE_URL` is explicitly flagged as an unconfirmed placeholder: Kling has both a first-party API and third-party resellers with different paths, and whoever adds a real key needs to confirm which one applies before the first live call.

Concretely:

- `build_jwt()` is a stdlib-only (`hmac` + `hashlib` + `base64`, no PyJWT dependency) HS256 JWT signer, with `now` injectable so signing is deterministic in tests.
- `KlingCredentials.from_env()` reads `KLING_ACCESS_KEY` / `KLING_SECRET_KEY` and fails closed with a clear error (never leaking a value, since there isn't one to leak) if either is missing. No credential is ever hardcoded or committed anywhere in this repository.
- `KlingAIAvatarClient.create_task()` takes a real `video_prompts[]` entry straight from the Provider-Specific Production Package -- the exact shape `translate_shot_to_video_prompt()` already produces -- and rejects an oversized prompt *before* any request goes out, per Kling's documented 2500-character limit.
- `generate_with_retries()` polls until a terminal state and raises `GenerationBudgetExceededError` rather than fabricating a result if it never gets one. Its `max_attempts` is meant to come from the paired `generation_risk_estimate.budget_max_total_attempts` -- the same ceiling the Monte Carlo model already estimated risk against, not a separate made-up number; `test_real_shot1_prompt_through_a_scripted_success` proves this end to end using the actual Hope-chain worked example.
- `transport.py`'s `Transport` protocol is the seam that makes all of this testable offline: `UrllibTransport` is the real (stdlib-only, no `requests` dependency) network implementation; `FakeTransport` in the test file is what every test actually uses.

## Truth status

| Claim | Status |
|---|---|
| v2 mission and Ultimate Principle statement | DESIGNED, evidenced by this document |
| 13-stage pipeline (Timeless Principle -> Provider-Specific Production Package) | DESIGNED; every stage now has at least one implemented schema in the chain (see rows below) |
| Seven Core Design Engines | Each has an implemented schema below except Human Experience (folded into Principle Kernel's `human_truths`) and Human Experience Engine's standalone form |
| Provider-neutral abstract production spec + per-provider translation | IMPLEMENTED for one video provider (Kling AI Avatar) and one music provider (Suno) — see Provider-Specific Production Package below. Not yet built for the other 4 video / 1 music candidates. |
| Universal Production Blueprint (~28 artifact types) | IMPLEMENTED — see Universal Production Blueprint below |
| Review Council (8 councils) | IMPLEMENTED as a structured checklist with auto-advancing status for 3 of 8 councils (see Tier 3 wiring below); no scoring rubric or actual human review process exists yet — councils only ever reach `"in_review"` automatically, never `"approved"` |
| Principle Kernel schema (Principle Engine output) | IMPLEMENTED — `schemas/principle_kernel.schema.json` (contract) + `schemas/principle_kernel.py` (dependency-free validator) + `tests/test_principle_kernel.py` (5 passing smoke tests, run with `python3 dreammusicforge/tests/test_principle_kernel.py`). Bakes the "no compelled viewer belief" ethics constraint into the schema itself: `non_goals` must contain that exact sentence or validation fails. |
| Narrative + Emotional Architecture schema (Story Architecture Engine + Emotional Architecture Engine outputs) | IMPLEMENTED — `schemas/narrative_emotional_architecture.schema.json` + `schemas/narrative_emotional_architecture.py` + `tests/test_narrative_emotional_architecture.py` (7 passing smoke tests). Enforces: all eight narrative stages present, before/after states differ ("what changes?"), emotional waveform has ≥3 beats with strictly increasing order, and every narrative stage is referenced by at least one waveform beat (coverage check, same discipline as v1's "every beat has ≥1 shot" rule). The worked example builds directly on the Hope Principle Kernel's `rebuilding_after_loss` human truth. |
| Musical Architecture schema (Musical Architecture Engine output) | IMPLEMENTED — `schemas/musical_architecture.schema.json` + `schemas/musical_architecture.py` + `tests/test_musical_architecture.py` (10 passing smoke tests). Enforces a tempo map of ≥3 monotonically-ordered segments, valid dynamic levels, internal referential integrity (silence moments and the melodic motif's `recurs_at` must reference real tempo-map segments), and — the first cross-document check in this repo — `validate_against_narrative_architecture()` confirms every `tempo_map[].linked_waveform_beat_id` actually exists in the paired Narrative + Emotional Architecture's `emotional_waveform`. Fulfills the "define tempo map, instrumentation, dynamics, lyrical intent before selecting a music provider" rule from the provider layer. |
| Cinematic Architecture schema (Cinematic Architecture Engine output — Visual Architecture, Shot Architecture, Performance Direction) | IMPLEMENTED — `schemas/cinematic_architecture.schema.json` + `schemas/cinematic_architecture.py` + `tests/test_cinematic_architecture.py` (10 passing smoke tests). Composition fields (focal point, rule of thirds / golden triangle / centered / frame-within-frame / symmetrical framing, leading lines, positive/negative space, headroom/leadroom, intentional balance, depth layering, focus technique, color/contrast) are drawn from a cited practitioner breakdown of Hollywood composition and made checkable, not left as prose: e.g. `centered` framing requires an explicit `centered_rationale`, and depth layering must populate at least 2 of foreground/midground/background. Every shot must carry a `justification` (exists_because / why_now / audience_state_change) or validation fails — that is the Cinematic Architecture Engine's own stated rule, enforced in code. Cross-checks both prior documents: `validate_against_narrative_architecture()` catches referential breaks *and* stage drift (a shot's declared narrative stage must match its linked beat's actual stage), and `validate_against_musical_architecture()` checks tempo-segment references. The worked 8-shot example bookends shot 1 and shot 8 (isolation imposed vs. isolation chosen) as a deliberate visual rhyme. |
| Editorial Architecture schema (Editorial Architecture Engine output — shot timing, motif evolution, visual callbacks, ending) | IMPLEMENTED — `schemas/editorial_architecture.schema.json` + `schemas/editorial_architecture.py` + `tests/test_editorial_architecture.py` (11 passing smoke tests). The last engine before a Provider-Specific Production Package. Enforces a beat-matched edit timeline (strictly increasing order and start times, beat-matched cuts must reference a real tempo segment), motif evolution that actually evolves (each motif needs ≥2 entries, must start `introduced`, must end `transformed` or `resolved` — a motif that never changes is rejected), visual callbacks where the payoff must occur after its setup, and an ending-type discipline: `resolution_stated` requires an explicit `explicit_statement_rationale`, since stating a resolution outright is the exception under the v2 non-compulsion mission, not the default. Cross-checks both prior documents: `validate_against_cinematic_architecture()` requires every cinematic shot to be covered by at least one cut, and `validate_against_musical_architecture()` checks tempo-segment references. The worked example formalizes the shot 1 / shot 8 visual rhyme as an actual `visual_callbacks` entry and ends `reflection_open_ended`, completing the full Hope chain: Principle Kernel → Narrative/Emotional → Musical → Cinematic → Editorial. |
| Universal Production Blueprint schema (assembles all five documents into the mission's package) | IMPLEMENTED — `schemas/universal_production_blueprint.schema.json` + `schemas/universal_production_blueprint.py` + `tests/test_universal_production_blueprint.py` (20 passing smoke tests, including the tier-3 wiring and review-checklist auto-sync — see "Tier 3 wiring" above). Deliberately keeps three tiers separate instead of flattening the mission's ~28 sections into one undifferentiated document: **Tier 1** `embedded_documents` (VERIFIED_STRUCTURED — the five already-implemented documents, embedded whole); **Tier 2** `narrative_supplement` (DESIGNED_FREE_TEXT — creative brief, audience profile, character bios, scene breakdown, sequence plan, wardrobe, production design, symbolism ledger, choreography/blocking, sound design, reflection-and-legacy statement — required, but not cross-checked the way tier 1 is); **Tier 3** `provider_specific_prompt_sets` (`build_status` must be `"not_yet_built"` with an empty `prompts` array, or `"draft"`/`"complete"` with prompts present — mismatches fail validation either direction; now actually wired, see below). Also includes a `review_checklist` requiring all eight named Review Councils present exactly once, all starting `"pending"`. This tiering is a direct application of a cited video's argument that "dimension" covers several non-interchangeable meanings in physics and math (settled 3+1 spacetime vs. speculative 10/11-dimensional string/M-theory vs. bookkeeping state-space dimension) — applied here to keep validated, free-text, and unbuilt sections from being mistaken for the same kind of claim. **`validate_full_chain()`** re-runs all nine previously-built validators (5 single-document + 4 cross-document) against the embedded documents plus a new identity check across all five documents' `source_principle_id`/`source_human_truth_id` — the closest thing this repo has to a full pipeline integration test, and it passes clean on the worked example. |
| Provider-Specific Production Package schema (the provider translation layer, scoped to one video + one music provider) | IMPLEMENTED — `schemas/provider_specific_production_package.schema.json` + `schemas/provider_specific_production_package.py` + `tests/test_provider_specific_production_package.py` (12 passing smoke tests). This is the first stage with real translation functions, not just a validated data contract: `translate_shot_to_video_prompt()` builds a video prompt directly from a Cinematic Architecture shot's composition/camera/lighting fields, and `translate_musical_architecture_to_music_prompt()` does the same from the Musical Architecture. Every prompt entry must declare `source_fields_used` (which canonical fields it was actually derived from) — see `REQUIRED_INTERFACE_NON_GOAL` below. Adds a dependency-free Monte Carlo `generation_risk_estimate`: per-shot pass probability drawn from a uniform range, retries modeled as geometric, estimating the probability the full shot list needs more attempts than a stated budget — the worked example lands at ~12%, deliberately echoing its source video's own worked example. The validator **reruns the simulation from its stored parameters** and rejects the document if the stored probability doesn't reproduce within tolerance, catching a hand-typed or stale number rather than an actually-simulated one. `REQUIRED_INTERFACE_NON_GOAL` (new, alongside the standing ethics non-goal) states that no provider's rendering is authoritative — the Cinematic/Musical/Editorial documents remain canonical, a principle drawn from a video on interface/perception theory. Cross-checks full shot coverage against the paired Cinematic Architecture via `validate_against_cinematic_architecture()`. |
| Character Performance Package schema (character-consistent reference images + characters singing instead of narration + originality/rights gate) | IMPLEMENTED — `schemas/character_performance_package.schema.json` + `schemas/character_performance_package.py` + `tests/test_character_performance_package.py` (17 passing smoke tests). See "Characters singing themselves, not a narrator" above. `no_narrator`, `lip_sync_required`, and `original_character` are all literal hard gates (`const: true`), not descriptions. Worked example: The Builder and The Asker (both original, invented for this production) cover all 8 Hope-chain shots between them, using Nano Banana as the character-reference provider, with `rights_review.status: "clear_to_proceed"` reproducibly computed from their risk flags. |
| Assembly Package schema (native audio-driven generation requirement + duration reconciliation + ffmpeg stitching plan) | IMPLEMENTED — `schemas/assembly_package.schema.json` + `schemas/assembly_package.py` + `tests/test_assembly_package.py` (19 passing smoke tests). See "Native audio-driven generation and post-generation assembly" above. `reconciliation_strategy`, `assembly_status`, and `concat_command` are all reproducibility-checked, not just asserted. Worked example deliberately routes one of 8 cuts to `requires_manual_review` (39% simulated drift) so `assembly_status` demonstrably blocks rather than rubber-stamping. `render_ffmpeg_command()` was fixed after a real reported playback failure (timestamps not reset per-clip before concat) and re-verified against real Kling output -- see "Fixed after a real, reported failure" above. |
| Live provider integration -- Kling AI Avatar client | IMPLEMENTED (request-building, auth, retry logic) but NOT LIVE-VERIFIED — `providers/{transport,exceptions,kling_ai_avatar}.py` + `tests/test_kling_ai_avatar_client.py` (14 passing smoke tests, all offline via `FakeTransport`). See "Live provider integration" above. No API key exists in this environment; `DEFAULT_BASE_URL` is an explicitly-flagged unconfirmed placeholder. This is the first module in the repository that makes (or is built to make) real network calls -- everything else stays pure validation logic with zero network dependency. |
| v1 stage-6 "comprehension test" (vision-LLM checks viewer understood the exact maxim) | SUPERSEDED — conflicts with the "maximize probability of," non-compelled framing above; if revived, it must become a probabilistic/qualitative reflection signal, not a pass/fail check against one intended reading |
| v1's other five stages (maxim, intent card, shot list, generation, assembly) | Mapped onto v2's more detailed architecture above; v1 wording preserved below for evidence continuity, not treated as current spec |

## Non-goals now

- Do not claim, measure, or optimize for "the viewer received the intended belief." The goal is probability of reflection and connection, not compelled comprehension.
- Do not build a hard pass/fail comprehension gate against one canonical interpretation (this was v1's stage 6; it is superseded).
- Do not lock the pipeline to a single video or music provider — the production spec must stay provider-neutral until the translation layer exists.
- Do not skip the Principle Engine step — every project must trace back to one stated timeless principle.
- Do not label a Character Performance Package's characters as narrators in disguise — `no_narrator` and `lip_sync_required` are hard gates, not descriptions.
- Do not use real or existing copyrighted/trademarked characters — every character must be original, invented for the production. `original_character`, `originality_basis`, `resembles_existing_ip_risk`, and `rights_review` exist specifically so this stays a structural requirement, not a hope. This is self-declaration plus a best-effort literal-name check, not legal clearance — a `clear_to_proceed` `rights_review` is not a substitute for human/legal review before public release.
- Do not assign a silent-video-only provider to a shot with a singing, lip-synced performer — `native_av_policy.allowed_providers` and `validate_native_av_requirement()` exist specifically to catch that, not just to document a preference.
- Do not silently force a badly-drifted generated clip to fit its planned duration — `reconcile_cut_duration()` routes anything past tolerance to `requires_manual_review`, which blocks `assembly_status`, rather than trimming/padding/speed-ramping something that would look wrong.
- Do not hardcode, log, or commit a provider credential anywhere — `providers/kling_ai_avatar.py` reads `KLING_ACCESS_KEY`/`KLING_SECRET_KEY` from the environment only, and fails closed with no secret value in the error message if either is missing.
- Do not claim a provider integration is live-verified when it isn't — `providers/kling_ai_avatar.py`'s request-building and retry logic are fully tested offline, but nothing has been exercised against a real Kling endpoint in this environment, and its docstring says so plainly.

## Next 3 + 1

- **next_1 (done):** ~~Write the Principle Kernel schema~~ — see `schemas/principle_kernel.schema.json`, `schemas/principle_kernel.py`, `tests/test_principle_kernel.py`.
- **next_2 (done):** ~~Write the Narrative + Emotional Architecture schema~~ — see `schemas/narrative_emotional_architecture.schema.json`, `schemas/narrative_emotional_architecture.py`, `tests/test_narrative_emotional_architecture.py`.
- **next_3 (done):** ~~Musical Architecture Engine schema~~ — see `schemas/musical_architecture.schema.json`, `schemas/musical_architecture.py`, `tests/test_musical_architecture.py`.
- **next_4 (done):** ~~Cinematic Architecture Engine schema~~ — see `schemas/cinematic_architecture.schema.json`, `schemas/cinematic_architecture.py`, `tests/test_cinematic_architecture.py`.
- **next_5 (done):** ~~Editorial Architecture Engine schema~~ — see `schemas/editorial_architecture.schema.json`, `schemas/editorial_architecture.py`, `tests/test_editorial_architecture.py`. All seven Core Design Engines named in the mission now have at least one implemented schema link in the chain (Principle, Human Experience is implicit in human_truths, Story + Emotional combined, Musical, Cinematic, Editorial).
- **next_6 (done):** ~~Universal Production Blueprint schema~~ — see `schemas/universal_production_blueprint.schema.json`, `schemas/universal_production_blueprint.py`, `tests/test_universal_production_blueprint.py`. Assembles all five prior documents and re-validates the whole chain via `validate_full_chain()`.
- **next_7 (done):** ~~Provider-Specific Production Package~~ — see `schemas/provider_specific_production_package.schema.json`, `schemas/provider_specific_production_package.py`, `tests/test_provider_specific_production_package.py`. Scoped to Kling AI Avatar (video) and Suno (music) in the worked example; `selected_video_provider`/`selected_music_provider` are free strings, not locked to these two, so switching providers doesn't require a schema change.
- **next_8 (done):** ~~Wire `provider_specific_prompt_sets`~~ — see `embed_provider_specific_production_package()` and `compute_readiness_activation()` in `schemas/universal_production_blueprint.py`. The worked example is now genuinely wired (`build_status: "draft"`, 9 real prompts), not hand-set.
- **next_9 (done):** ~~Wire the readiness neuron's `"draft"` outcome into `review_checklist`~~ — see `sync_review_checklist_with_provider_status()` in `schemas/universal_production_blueprint.py`, now called automatically by `embed_provider_specific_production_package()`.
- **next_10 (done):** ~~Character Performance Package (character consistency + no-narrator singing)~~ — see `schemas/character_performance_package.schema.json`, `schemas/character_performance_package.py`, `tests/test_character_performance_package.py`. Nano Banana as the character-reference provider; `no_narrator` and `lip_sync_required` are literal hard gates.
- **next_11:** Wire `character_references`/`vocal_performers` into the Provider-Specific Production Package's `video_prompts` — each shot's video prompt should include its performer's `reference_image_asset_id` for conditioning, and `translate_shot_to_video_prompt()` should accept an optional character-reference argument rather than treating character identity as text-only.
- **next_12 (done):** ~~Assembly Package (native audio-driven generation requirement + duration reconciliation + ffmpeg stitching plan)~~ — see `schemas/assembly_package.schema.json`, `schemas/assembly_package.py`, `tests/test_assembly_package.py`. Fixed the Provider-Specific Production Package's worked example along the way (`runway` -> `kling_ai_avatar`), since the new `validate_native_av_requirement()` correctly caught it as non-compliant.
- **next_13 (done, partially):** ~~Live API integration layer~~ — see `providers/{transport,exceptions,kling_ai_avatar}.py`, `tests/test_kling_ai_avatar_client.py`. Scoped to one provider (Kling AI Avatar) as planned. Credential loading, JWT auth, request-building, and a fail-closed retry loop are implemented and fully tested offline. What's still outstanding: no real API key exists in this environment, so nothing has been fired against Kling's actual endpoint, and `DEFAULT_BASE_URL` needs confirming against whichever real access (first-party vs. reseller) is actually used. `actual_duration_seconds` in the Assembly Package is therefore still simulated, not real, until that first live call happens.
- **next_14 (done, cut1/cut2 only):** ~~Fire the first real Kling AI Avatar call and feed the real `actual_duration_seconds` back into the Assembly Package~~ — done manually outside this environment (no live credentials here; see "Live provider integration" above). Both came back at 10.0417s against an originally-planned 4.5s/5.0s — over 100% drift on a beat-matched cut, which correctly triggered `requires_manual_review` rather than being silently absorbed. Rather than force it through reconciliation, `editorial_architecture.py`'s `edit_timeline` was replanned so cut1/cut2's *planned* duration matches what the provider actually delivers (10.04s each, cascading cut3-cut8's start times forward by ~10.58s); `assembly_package.py`'s worked example now uses the real 10.0417s figures for cut1/cut2 and reconciles cleanly to `exact_match`. Stitched with `ffmpeg -f concat -c copy` (stream copy, no re-encode — both clips share codec/resolution) into a 20.13s file. cut3-cut8 remain simulated pending their own real generations, and are very likely to need the same treatment if Kling keeps defaulting to ~10s regardless of the requested duration.
- **next_15:** Fire the remaining 6 shots (cut3-cut8) for real, and check whether Kling's API actually takes a duration parameter with discrete allowed values (5s/10s buckets, most likely) rather than an arbitrary float — `providers/kling_ai_avatar.py`'s `create_task()` currently just passes `provider_parameters.duration_seconds` through unvalidated against whatever Kling's real constraint is.
- **next_16 (candidate, not started):** Calibrate `generation_risk_estimate`'s per-shot success-probability range from real observed provider outcomes (an MCMC/Metropolis-Hastings posterior over provider reliability) instead of the currently-assumed uniform range. Deliberately not built yet — there is no observed data to calibrate against, and building the calibration machinery ahead of that data would be speculative infrastructure this repo's own non-goals discipline argues against.
- **plus_1_control:** No engine, council, or provider adapter may be documented as built until it has a passing evidence entry — no labeled claim without a check behind it.

## Running the tests

```bash
python3 dreammusicforge/tests/test_principle_kernel.py
python3 dreammusicforge/tests/test_narrative_emotional_architecture.py
python3 dreammusicforge/tests/test_musical_architecture.py
python3 dreammusicforge/tests/test_cinematic_architecture.py
python3 dreammusicforge/tests/test_editorial_architecture.py
python3 dreammusicforge/tests/test_universal_production_blueprint.py
python3 dreammusicforge/tests/test_provider_specific_production_package.py
python3 dreammusicforge/tests/test_character_performance_package.py
python3 dreammusicforge/tests/test_assembly_package.py
python3 dreammusicforge/tests/test_kling_ai_avatar_client.py
```

No dependencies beyond the Python 3 standard library (the Monte Carlo simulation uses stdlib `random`; `providers/` uses only `hmac`/`hashlib`/`base64`/`urllib`, not `PyJWT` or `requests`). `test_universal_production_blueprint.py` is the closest thing to a full pipeline integration test — it re-validates all five prior documents and their cross-document links in one run. `test_kling_ai_avatar_client.py` is the only suite touching a module that would make real network calls outside tests; every test in it runs against `FakeTransport`, so `python3 -m unittest` here still never touches the network or needs an API key.

## Source

v2 mission, pipeline, Seven Engines, provider layer, Universal Production Blueprint, and Review Council contributed 2026-08-02, reframing the platform from a music-video generator to an Intelligent Creative Operating System / Human Transformation Studio.

---

## Superseded v1 design (preserved for evidence continuity)

The following was the original scaffold for this folder. It is kept for evidence continuity per the fork-preservation principle, not as current spec. Where it conflicts with the v2 mission above (notably its stage-6 comprehension gate), v2 governs.

### v1 purpose (superseded)

DreamMusicForge exists to turn a single testable causal claim (a maxim) into a music video whose visuals demonstrably teach that claim — a structured argument stated in shots, tracked through a numeric state ladder, resolved by a threshold event, and confirmed by an automated comprehension check.

### v1 pipeline — 6 stages (superseded)

1. **Principle -> Maxim.** Hard gate: reduce an idea to one causal claim with a concrete before/after.
2. **Editorial Intent Card.** Structured output: one tracked entity, a numeric state ladder, dismissal/repeat beats, one threshold event, a bookend rhyme, two independent causal chains (audio, visual).
3. **Shot List + Lyrics, time-locked.** Coverage set per beat (5 angles x 2 takes), timecode, framing, object-state number, link back to the intent-card beat.
4. **Generation layer.** SAM 2, DepthAnything v2, img2img/reference-locked conditioning, ProPainter, SMPL-X, CogVideoX; composition QA gate; single-shot quality before cross-shot continuity.
5. **Assembly & sync.** Timecode-grid stitching, beat-matched cuts, automated continuity check.
6. **Comprehension test (superseded by v2's non-compelled framing above).** Automated vision-LLM proxy checking the viewer's stated takeaway against one intended maxim, plus a human panel.

### v1 non-goals, named-subsystem caution, and source note (superseded, retained for evidence)

Named subsystems appearing only in the conversation that produced v1 (e.g. "Trust Evolution Engine," "Timelessness Gate," "Multi-Layer Intent Lock," "Editorial Resonance Index") were flagged UNVERIFIED and never adopted into this repo's spec. That caution still applies under v2. v1 structure was derived from a design conversation on 2026-08-02, plus a practitioner shot-coverage breakdown (Full Time Filmmaker, "Top 10 Tips for Shooting Cinematic Music Videos," https://youtu.be/BX86dUlokQY).
