# Agentic AAI Integration Plan

The Agentic AAI Kernel must call the purpose gate before module promotion.

## Required Hook

`pre_promotion_check(module_contract)`

## Required Stop

If result decision is `BLOCK`, the Agentic AAI Kernel must not continue promotion work.

## Approval Boundary

Agentic AAI may prepare draft-review artifacts, but it may not merge, release, deploy, or authorize physical action.
