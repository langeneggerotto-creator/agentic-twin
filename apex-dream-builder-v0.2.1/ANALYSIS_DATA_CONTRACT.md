# Dream Analysis Data Contract — v0.2.1

Defines the input and output shape of `DreamAnalysis.buildAnalysis()` in `analysis.js`. This is the first sub-increment of **v0.2 — Dream Analysis & Intelligence Core** per the APEX Dream Builder Genesis Seed. It is deterministic and local: no AI API call, no external research.

## Input

| Field | Type | Source | Required |
|---|---|---|---|
| `card` | object | the v0.1 Dream Card (`DreamCore.buildDreamCard()` output) | yes |
| `timeAvailable` | free text | new v0.2.1 question | no (skippable; becomes an unknown) |
| `resources` | free text | new v0.2.1 question | no |
| `skillsReadiness` | `"yes" \| "partial" \| "no"` | new v0.2.1 question | no |
| `ownershipPlan` | free text | new v0.2.1 question | no |
| `biggestRisk` | free text | new v0.2.1 question | no |

## Output

| Field | Type | Meaning |
|---|---|---|
| `purpose` | string | pass-through of `card.statement` |
| `beneficiary` | string | pass-through of `card.audience` |
| `impact` | string | pass-through of `card.outcome` |
| `dimensions` | object | `feasibility`, `readiness`, `resources`, `time`, `ownership`, `risk`, each `{ score: 0-10, basis: string }` |
| `barrierMap` | array | `{ dimension, severity: BLOCKING\|HIGH\|MODERATE, description }` for every dimension scoring ≤ 6 |
| `evidenceRequired` | array of strings | one deterministic evidence request per dimension scoring below 8 |
| `unknowns` | array of strings | human-readable names of any input field left blank |
| `dreamScore` | number 0-10 | mean of all `dimensions[*].score` |
| `scoreBasis` | string | plain-language explanation of the Dream Score formula |
| `recommendedNextStep` | string | addresses the single worst barrier, or a forward action if none exist |
| `truthLabels` | object | `{ method: "LOCAL · DETERMINISTIC · USER-GROUNDED", aiApiUsed: false, externalResearchUsed: false, validated: "NOT_YET_PROVEN" }` |
| `createdAt` | ISO timestamp | generation time |
| `version` | string | `"0.2.1"` |

## Scoring method (transparent, deterministic)

- A free-text answer is scored 0 if blank, 2 if it contains explicit uncertainty language ("not sure", "don't know", "none", etc.), otherwise 3-10 scaled by answer length/specificity, capped per-dimension.
- `skillsReadiness` maps directly: `yes` → 9, `partial` → 5, `no` → 2, unanswered → 0.
- `feasibility` is derived as the average of `time`, `resources`, and `readiness` — it is not asked directly.
- `dreamScore` is the mean of all six dimension scores.
- Every score carries a `basis` string that quotes or explains exactly what produced it, so the score is never a black box.

## Compatibility

`buildAnalysis()` only reads `card` fields already produced by v0.1's `DreamCore.buildDreamCard()`; it adds no required fields to the Dream Card itself. A Dream Card created in v0.1 works unmodified as analysis input.
