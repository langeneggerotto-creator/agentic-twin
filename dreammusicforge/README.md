# DreamMusicForge — Intelligent Creative Operating System

**Repository status:** Design-stage. This folder captures a design vision as structure so it survives across sessions and AI systems. Nothing in this folder is executable yet.

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
Provider-Specific Production Package
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
- Musical architecture (emotional progression, instrumentation, tempo map, dynamics, lyrical intent) must be defined before a music provider is selected.

No provider is currently integrated; this is a target architecture, not a built adapter layer.

## The Universal Production Blueprint

Every project should output a complete package: creative brief, principle kernel, audience profile, transformation goal, narrative treatment, character biographies, scene breakdown, sequence plan, shot list, storyboard descriptions, camera directions, lens and framing recommendations, lighting plan, color script, wardrobe notes, production design, symbolism ledger, music brief, lyric brief, vocal direction, choreography and blocking, sound design, editorial timing, transition map, motif evolution, emotional waveform, reflection and legacy statement, provider-specific prompt sets, review checklist.

None of these artifact types have a schema yet. This list is the target output surface, not a built format.

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

## Truth status

| Claim | Status |
|---|---|
| v2 mission and Ultimate Principle statement | DESIGNED, evidenced by this document |
| 12-stage pipeline (Timeless Principle -> Provider-Specific Production Package) | DESIGNED, NOT IMPLEMENTED |
| Seven Core Design Engines | DESIGNED as named responsibilities; none have an input/output schema yet |
| Provider-neutral abstract production spec + per-provider translation | TARGET ARCHITECTURE, NOT BUILT — no provider adapters exist |
| Universal Production Blueprint (~28 artifact types) | TARGET OUTPUT LIST, NOT SCHEMATIZED |
| Review Council (8 councils) | DESIGNED as a review process; no implementation, scoring rubric, or automation exists |
| Principle Kernel schema (Principle Engine output) | IMPLEMENTED — `schemas/principle_kernel.schema.json` (contract) + `schemas/principle_kernel.py` (dependency-free validator) + `tests/test_principle_kernel.py` (5 passing smoke tests, run with `python3 dreammusicforge/tests/test_principle_kernel.py`). Bakes the "no compelled viewer belief" ethics constraint into the schema itself: `non_goals` must contain that exact sentence or validation fails. |
| Narrative + Emotional Architecture schema (Story Architecture Engine + Emotional Architecture Engine outputs) | IMPLEMENTED — `schemas/narrative_emotional_architecture.schema.json` + `schemas/narrative_emotional_architecture.py` + `tests/test_narrative_emotional_architecture.py` (7 passing smoke tests). Enforces: all eight narrative stages present, before/after states differ ("what changes?"), emotional waveform has ≥3 beats with strictly increasing order, and every narrative stage is referenced by at least one waveform beat (coverage check, same discipline as v1's "every beat has ≥1 shot" rule). The worked example builds directly on the Hope Principle Kernel's `rebuilding_after_loss` human truth. |
| Musical Architecture schema (Musical Architecture Engine output) | IMPLEMENTED — `schemas/musical_architecture.schema.json` + `schemas/musical_architecture.py` + `tests/test_musical_architecture.py` (10 passing smoke tests). Enforces a tempo map of ≥3 monotonically-ordered segments, valid dynamic levels, internal referential integrity (silence moments and the melodic motif's `recurs_at` must reference real tempo-map segments), and — the first cross-document check in this repo — `validate_against_narrative_architecture()` confirms every `tempo_map[].linked_waveform_beat_id` actually exists in the paired Narrative + Emotional Architecture's `emotional_waveform`. Fulfills the "define tempo map, instrumentation, dynamics, lyrical intent before selecting a music provider" rule from the provider layer. |
| Cinematic Architecture schema (Cinematic Architecture Engine output — Visual Architecture, Shot Architecture, Performance Direction) | IMPLEMENTED — `schemas/cinematic_architecture.schema.json` + `schemas/cinematic_architecture.py` + `tests/test_cinematic_architecture.py` (10 passing smoke tests). Composition fields (focal point, rule of thirds / golden triangle / centered / frame-within-frame / symmetrical framing, leading lines, positive/negative space, headroom/leadroom, intentional balance, depth layering, focus technique, color/contrast) are drawn from a cited practitioner breakdown of Hollywood composition and made checkable, not left as prose: e.g. `centered` framing requires an explicit `centered_rationale`, and depth layering must populate at least 2 of foreground/midground/background. Every shot must carry a `justification` (exists_because / why_now / audience_state_change) or validation fails — that is the Cinematic Architecture Engine's own stated rule, enforced in code. Cross-checks both prior documents: `validate_against_narrative_architecture()` catches referential breaks *and* stage drift (a shot's declared narrative stage must match its linked beat's actual stage), and `validate_against_musical_architecture()` checks tempo-segment references. The worked 8-shot example bookends shot 1 and shot 8 (isolation imposed vs. isolation chosen) as a deliberate visual rhyme. |
| v1 stage-6 "comprehension test" (vision-LLM checks viewer understood the exact maxim) | SUPERSEDED — conflicts with the "maximize probability of," non-compelled framing above; if revived, it must become a probabilistic/qualitative reflection signal, not a pass/fail check against one intended reading |
| v1's other five stages (maxim, intent card, shot list, generation, assembly) | Mapped onto v2's more detailed architecture above; v1 wording preserved below for evidence continuity, not treated as current spec |

## Non-goals now

- Do not claim, measure, or optimize for "the viewer received the intended belief." The goal is probability of reflection and connection, not compelled comprehension.
- Do not build a hard pass/fail comprehension gate against one canonical interpretation (this was v1's stage 6; it is superseded).
- Do not lock the pipeline to a single video or music provider — the production spec must stay provider-neutral until the translation layer exists.
- Do not treat any of the Seven Engines, the Review Council, or the Universal Production Blueprint as implemented — none have code, schemas, or evidence yet.
- Do not skip the Principle Engine step — every project must trace back to one stated timeless principle.

## Next 3 + 1

- **next_1 (done):** ~~Write the Principle Kernel schema~~ — see `schemas/principle_kernel.schema.json`, `schemas/principle_kernel.py`, `tests/test_principle_kernel.py`.
- **next_2 (done):** ~~Write the Narrative + Emotional Architecture schema~~ — see `schemas/narrative_emotional_architecture.schema.json`, `schemas/narrative_emotional_architecture.py`, `tests/test_narrative_emotional_architecture.py`.
- **next_3 (done):** ~~Musical Architecture Engine schema~~ — see `schemas/musical_architecture.schema.json`, `schemas/musical_architecture.py`, `tests/test_musical_architecture.py`.
- **next_4 (done):** ~~Cinematic Architecture Engine schema~~ — see `schemas/cinematic_architecture.schema.json`, `schemas/cinematic_architecture.py`, `tests/test_cinematic_architecture.py`.
- **next_5:** Define the Universal Production Blueprint as a concrete document schema (even if most fields start as free text) so "complete package" has one canonical shape.
- **next_6:** Editorial Architecture Engine schema (shot timing, reveal timing, motif evolution, expectation/payoff, ending) — the last engine before a Provider-Specific Production Package can be assembled from all prior documents.
- **plus_1_control:** No engine, council, or provider adapter may be documented as built until it has a passing evidence entry — no labeled claim without a check behind it.

## Running the tests

```bash
python3 dreammusicforge/tests/test_principle_kernel.py
python3 dreammusicforge/tests/test_narrative_emotional_architecture.py
python3 dreammusicforge/tests/test_musical_architecture.py
python3 dreammusicforge/tests/test_cinematic_architecture.py
```

No dependencies beyond the Python 3 standard library.

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
