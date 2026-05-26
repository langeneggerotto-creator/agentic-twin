# 07 APEX Heart Core Quality Gate

**Shortcut:** ❤️🅾️♾️💯🚀

This file moves Heart Core from canon into the APEX testing and release system.

## Gate Purpose

Every APEX artifact, console, prompt, media output, game, automation, or Python scaffold must pass the Heart Core Quality Gate before it can be treated as release-ready.

## Required Heart Core Checks

| Check | Question | Pass Condition | Status Label |
|---|---|---|---|
| HC-01 Dignity | Does this make the user feel smaller, ashamed, manipulated, or less capable? | No | PASS / FAIL |
| HC-02 Control | Can the user inspect, override, stop, reverse, or understand the output? | Yes | PASS / FAIL |
| HC-03 Truth | Are important claims labeled honestly? | VERIFIED / INFERRED / ASSUMED / UNKNOWN | PASS / FAIL |
| HC-04 Non-Clinical Boundary | Does this avoid diagnosis, treatment, or clinical certainty? | Yes | PASS / FAIL |
| HC-05 Rights and Credit | Are sources, contributors, permissions, and AI assistance identified when relevant? | Yes | PASS / FAIL |
| HC-06 Child/Youth Safety | If youth are involved, does it protect privacy, consent, dignity, and age-appropriate framing? | Yes or N/A | PASS / FAIL / N/A |
| HC-07 Emotional Safety | Does the output avoid fear, shame, coercion, or false urgency? | Yes | PASS / FAIL |
| HC-08 Growth Step | Does it give one useful next step without overwhelming the user? | Yes | PASS / FAIL |
| HC-09 Accountability | Does the user remain responsible for decisions and outcomes? | Yes | PASS / FAIL |
| HC-10 Human-Control Delta | Does it increase human understanding/control more than it increases system power? | Yes | PASS / FAIL |

## Required Release Decision

```json
{
  "heart_core_gate": {
    "overall_status": "PASS | HOLD | FAIL",
    "failed_checks": [],
    "human_control_delta": "positive | neutral | negative",
    "release_decision": "release_candidate | patch_required | blocked",
    "next_smallest_control_improvement": "..."
  }
}
```

## Stop Rule

If HC-10 fails, the artifact must not be promoted. Simplify it, add controls, add explanations, add rollback, or escalate for human review.

## Minimal Law

**Keep the person whole while the product grows.**

## Implementation Status

| Layer | Status |
|---|---|
| Canon file exists | VERIFIED |
| Testing gate file exists | VERIFIED |
| Automated enforcement in consoles | NOT YET |
| CI enforcement | NOT YET |
| Manual review gate ready | YES |

## Next 3 Plus 1

1. Add this Heart Core gate to the Python Intent Console generated QA output.
2. Add this Heart Core gate to the Meta Studio QA Lab.
3. Add this Heart Core gate to RightsChain release decisions.
4. Control upgrade: require HC-10 in every future APEX package and prototype.
