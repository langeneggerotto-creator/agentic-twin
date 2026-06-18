# TASTE_CONSOLE_INTEGRATION_PLAN

## Goal

Add Purpose Gate scoring into the T.A.S.T.E. Console.

## Added Dimensions

- purpose fit
- human benefit
- whole-system usefulness
- evidence awareness
- scope control
- approval boundary clarity

## Adapter Flow

`Purpose Gate Result → T.A.S.T.E. Purpose Score → T.A.S.T.E. Verdict`

## Blocking Rule

If Purpose Gate decision is `BLOCK`, T.A.S.T.E. verdict cannot be `PROMOTE`.

## Output

`TASTE_PURPOSE_GATE_SCORE.json`
