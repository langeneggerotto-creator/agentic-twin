# DreamMusicForge — Editorial-Intent-Driven Music Video Generation Pipeline

**Repository status:** Design-stage. This folder captures a design conversation as structure so it survives across sessions and AI systems. Nothing in this folder is executable yet.

## Purpose

DreamMusicForge exists to turn a single testable causal claim (a maxim) into a music video whose visuals demonstrably teach that claim — a structured argument stated in shots, tracked through a numeric state ladder, resolved by a threshold event, and confirmed by an automated comprehension check. It is not an aesthetic assembly of AI-generated clips.

## Inherited principles

This folder inherits the truth-boundary discipline defined at the repository root in [`CORE_OS_INHERITANCE.md`](../CORE_OS_INHERITANCE.md): separate observed, measured, inferred, simulated, forecast, designed-not-proven, and unknown states; expose uncertainty and assumptions; cap commitment according to evidence strength.

## Pipeline — 6 stages

1. **Principle → Maxim.** Not software. A hard gate: reduce an idea to one causal claim with a concrete before/after. Reject anything that isn't a stated causal claim before it proceeds.
2. **Editorial Intent Card.** Structured-output generation (JSON schema, not prose): one tracked entity, a numeric state ladder, dismissal/repeat beats, one threshold event, a bookend rhyme, and two independent causal chains (audio, visual).
3. **Shot List + Lyrics, time-locked.** Expands the intent card against a song's timestamp structure into a shot-by-shot list. Each beat gets a *coverage set* — 5 angles (wide, full-body, medium, close-up, cutaway) × 2 takes — not a single shot, so assembly has options to cut between. Each shot carries start/end timecode, camera framing, object-state number, and a link back to the intent-card beat it satisfies. Programmatic checks: every state transition is monotonic, every intent-card beat has at least one shot.
4. **Generation layer.** The real engineering, not prompt engineering. Continuity — not per-clip video quality — is the core problem: the tracked object must look like the same object, progressively changed, across independently generated shots.
   - SAM 2 — tracking / re-identification of the object across frames and shots.
   - DepthAnything v2 — consistent depth/perspective so the object sits correctly in each new shot.
   - img2img / reference-locked conditioning — state N+1 visibly derives from state N's final frame rather than being regenerated from scratch.
   - ProPainter — inpainting when a state transition is staged by removal/repaint rather than physically re-shot.
   - SMPL-X — consistent body/pose across shots, needed if dismissal-gesture beats must visually rhyme.
   - CogVideoX (or equivalent) — the generation model itself.
   - Composition QA gate before a frame enters assembly: rule of thirds, eyeline placement, headroom, facing-direction-to-frame-third.
   - Build order: get single-shot generation acceptable first; solve cross-shot continuity as its own subsystem after.
5. **Assembly & sync.** Stitch shots per the timecode grid; beat-match cuts to an audio-onset-detected beat/energy grid; automated continuity check that object state N+1 reads as more advanced than state N.
6. **Comprehension test.** Two tiers: an automated proxy (vision-LLM watches muted, states the lesson, diffed against the maxim — the CI gate that lets this run without a human reviewing every output) and a human panel (ground truth, run before shipping).

## Truth status

| Claim | Status |
|---|---|
| 6-stage pipeline shape | DESIGNED, evidenced by this document |
| Editorial Intent Card JSON schema | NOT YET WRITTEN |
| Shot List JSON schema (with coverage-set field) | NOT YET WRITTEN |
| Any generation, assembly, or comprehension-test code | NOT STARTED |
| Tempo→camera-movement mapping, 5-shot coverage rule, framing rules | INFERRED from a cited practitioner source (Full Time Filmmaker, "Top 10 Tips for Cinematic Music Videos"), not yet encoded as rules |
| Named subsystems appearing only in the originating chat (e.g. "Trust Evolution Engine," "Timelessness Gate," "Multi-Layer Intent Lock," "Editorial Resonance Index") | UNVERIFIED — carried over as text, not confirmed to correspond to any real designed component. Do not treat as built or even as scoped until each is independently re-derived and given its own evidence entry |

## Non-goals now

- Do not claim any generated video is production-ready without the stage-6 comprehension gate passing.
- Do not treat the unverified named subsystems above as implemented, or even as agreed scope, until re-derived from first principles with evidence.
- Do not skip the stage-1 maxim gate — every entry into stage 2 must trace back to one stated causal claim.
- Do not solve cross-shot continuity and single-shot quality in the same pass (stage 4 build order above).

## Build order

1. Editorial Intent Card JSON schema (stage 2) — the data contract stage 2 and 3 share.
2. Shot List JSON schema (stage 3), including the coverage-set field.
3. Continuity subsystem prototype (stage 4): SAM 2 + depth-conditioned generation for one tracked object across states.
4. Orchestration for stages 1, 3, 5 (largely glue once 2 and 4 exist).
5. Automated comprehension-proxy gate (stage 6).

## Next 3 + 1

- **next_1:** Write the Editorial Intent Card JSON schema.
- **next_2:** Write the Shot List JSON schema, including the coverage-set (5 angles × 2 takes) field.
- **next_3:** Prototype the stage-4 continuity subsystem for one tracked object across two states.
- **plus_1_control:** No subsystem name may be documented as built until it has a passing evidence entry — no labeled claim without a check behind it.

## Source

Structure derived from a design conversation on 2026-08-02, plus a practitioner shot-coverage breakdown (Full Time Filmmaker, "Top 10 Tips for Shooting Cinematic Music Videos," https://youtu.be/BX86dUlokQY). No prior DreamMusicForge state existed in this repository before this folder.
