# 04 APEX Heart Core Implementation Bridge

This file moves Heart Core into the engineering layer.

## Goal

Each APEX app should include a visible Heart Core section before any output is promoted.

## Required fields

- status
- truth labels
- user controls
- next step
- review needed

## Apps to patch next

- APEX Meta Studio Console
- APEX Python Intent Console v0.2
- APEX RightsChain Builder
- APEX Mobile Python Console

## Engineering rule

A serious APEX output should not be promoted until its Heart Core section is present and reviewed.

## Next 3 Plus 1

1. Add Heart Core output to Python Intent Console.
2. Add Heart Core output to Meta Studio QA.
3. Add Heart Core output to RightsChain release decision.
4. Add automated checking later after the manual version is stable.
