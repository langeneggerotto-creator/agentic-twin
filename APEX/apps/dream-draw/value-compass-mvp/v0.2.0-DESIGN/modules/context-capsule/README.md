# APEX Context Capsule Engine — Truth-Preserving Token Economy Layer
## Dream Draw / 🅾️♾️ Value Compass Integration — v0.2.0-DESIGN

| Field | Entry |
|---|---|
| Module ID | `DD-CONTEXT-CAPSULE-001` |
| Parent Application | `Dream Draw / 🅾️♾️ Value Compass` |
| Capability Type | Context compression, retrieval routing and prompt optimization subsystem |
| Status | `DESIGNED / PROMPT + SCHEMA CREATED / NOT YET CODED INTO UI` |
| Evidence Maturity | `E2 — DESIGN ARTIFACT` |
| Purpose | Reduce AI processing tokens and repeated context without reducing truth, safety, evidence or user control. |
| Truth Boundary | Token reduction and cost savings are hypotheses until measured with a tokenizer/model on representative Dream Draw sessions. |

## 1. Core Principle

```text
Do not minimize meaning.
Minimize repeated payload.
Preserve truth, decisions, gates and reconstruction paths.
```

A shorter prompt is not automatically better. A valid Context Capsule is smaller **and** capable of reproducing the same materially correct recommendation, proof boundary and safety decision as the full context.

## 2. Why It Belongs in Dream Draw

Dream Draw may eventually maintain dreams, pathways, guide preferences, prior recommendations, evidence records, avatar state and APEX Mirror status. Sending all history to an AI on every interaction would be costly, slow and noisy.

The Context Capsule Engine supplies only what the next decision needs:

```text
Long user/app history
→ Stable kernel extracted once
→ Current delta captured per action
→ Relevant evidence retrieved by pointer
→ Small AI-ready capsule assembled
→ Recommendation generated
→ Outcome/evidence appended
```

## 3. Three-Layer Context Model

| Layer | Content | Token Rule |
|---|---|---|
| `KERNEL` | Purpose, user-chosen dream, hard boundaries, truth rules, active constraints and fixed definitions | Keep compact; reuse by ID/version; include only when necessary or changed. |
| `DELTA` | What changed this turn: new input, feedback, request, conflict or decision needed | Always include; this is the active reason for processing. |
| `RETRIEVAL` | Only evidence, records or prior decisions materially relevant to the current action | Load by pointer/selective extract; do not resend full archive. |

## 4. Mandatory Preservation Fields

Compression must never silently remove:

- user-selected dream or desired outcome;
- current task and decision required;
- truth/evidence status;
- unresolved blockers and approval gates;
- privacy, consent, safety and human-control boundaries;
- locked decisions that constrain the recommendation;
- source/provenance pointers needed to reconstruct the output;
- uncertainty that could materially change the result.

## 5. Token-Reduction Tactics

| Tactic | Rule |
|---|---|
| Canon by pointer | Replace repeated doctrine with `rule_id`, version and short operational effect. |
| Delta-only turns | Send only what changed plus required active state. |
| Evidence retrieval | Retrieve/load only records that can change the decision. |
| Structured fields | Prefer compact JSON/schema fields to repeated narrative. |
| Duplicate collapse | Merge identical or near-identical instructions; retain strongest governing wording once. |
| Optional context quarantine | Exclude decorative history, unused examples and unrelated module content unless requested. |
| Progressive disclosure | Start with minimum capsule; retrieve extra evidence only when uncertainty/gate requires it. |
| Output constraints | Ask for the minimum decision-bearing response first; expand only on demand. |

## 6. Quality Gate

A capsule may be promoted only when comparison testing shows:

1. no loss of user intent;
2. no loss of truth labels or evidence boundary;
3. no safety/privacy/governance omission;
4. no material change in recommended next step unless omitted context was irrelevant or the compressed output is demonstrably more accurate;
5. measurable reduction in tokens or a clearly labelled character-count proxy when exact tokens are unavailable.

## 7. Dream Draw Integration Position

```text
Dream Intake + History + Evidence
        ↓
Context Capsule Engine — 🪙🧿🧬
Kernel • Delta • Retrieval • Exclusions • Reconstruction Map
        ↓
Value Compass Recommendation Engine
        ↓
Best Move • Why Now • Watch Out • Guide Mode • Card Spec
        ↓
Feedback / Evidence Export / APEX Mirror
```

## 8. App Build Plan

| Build Stage | Addition | Evidence Gate |
|---|---|---|
| `v0.2 DESIGN` | Prompt generator, capsule schema and testing protocol | Created in this module |
| `v0.2 PROTOTYPE` | Add “Optimize Context” panel and downloadable capsule JSON to local app | Source validation and demo test |
| `v0.3 TEST` | Compare full prompt vs. capsule prompt outputs for real Dream Draw records | Token count + equivalence review |
| `v0.4 GATED AI` | Send capsule to a live AI recommendation endpoint only after tests | Human approval and privacy controls |

## 9. Current Status

| Capability | Status |
|---|---|
| Token economy concept | `DEFINED` |
| Meta-prompt | `CREATED AS DESIGN ARTIFACT` |
| Context Capsule schema | `CREATED AS DESIGN ARTIFACT` |
| Token measurement | `NOT YET EXECUTED` |
| UI implementation | `NOT YET CODED` |
| Real savings / quality equivalence | `NOT YET VALIDATED` |

## Next Proof Gate

Implement a local “Context Capsule” panel in the Dream Draw MVP, then compare one full pilot intake with one compressed capsule using exact token counts when a tokenizer is available, or a clearly labelled text-length proxy until then.

🔮🅾️💲🪙🧿♾️🌟💯🧬🚀
