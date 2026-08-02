"""Dream Builder integration boundary for OCode.

STATUS: PLACEHOLDER_ACTIVE / AUTHORITATIVE_INTERFACE_UNRESOLVED

A Pass 1 implementation-reality extraction run against APEX Dream Builder's
actual source artifacts (2026-08-02) found that real implementations exist
-- a browser-only "Dream Intelligence Engine" (v0.5.0-dev.21), a "v0.1
Dream Capture & Clarity" package, and a FastAPI/SQLite "V3 Full App"
(v3.1) reported built and locally tested -- but none of their source was
reachable from this session: no authoritative repository root, route
definitions, or request/response schemas were established. Calling a
"real" Dream Builder without that source on hand would be exactly the kind
of invented interface this project's own truth-boundary rule exists to
prevent (see CORE_OS_INHERITANCE.md).

DreamBuilderAdapter is the integration boundary that will call the real
implementation once its contract is established (routes/schemas/source
location). Until then it raises DreamBuilderUnresolvedError rather than
silently behaving like a working integration.

RuleBasedDreamPathwayPlaceholder is the deterministic fallback previously
(and misleadingly) exposed as this module's only entry point, build_dream().
It still works and is still useful for producing an inspectable OCode
contract, but it is not Dream Builder and every contract it produces is
now tagged with its true provenance (dream_builder.dream_source) so
nothing downstream -- including the evidence ledger -- can mistake its
output for the real thing.

Scope (allowed_paths/allowed_commands) is always supplied explicitly by a
human in both paths, never inferred from the description -- inferring the
security-critical fields from free text would be exactly the kind of guess
this whole system exists to avoid.
"""
import json

DEFAULT_MAX_BUDGET_USD = 2.00
DEFAULT_MAX_TURNS = 30

# If the dream's own description mentions one of these, the matching
# approval tag is added automatically -- a dream that says "deploy" or
# "actuator" can't skip human review just because a human forgot to name
# the tag by hand.
APPROVAL_TRIGGER_KEYWORDS = {
    "production_deployment": ["deploy", "production", "release", "publish"],
    "hardware_control": ["gpio", "actuator", "servo", "motor", "robot", "hardware"],
}

ALWAYS_FORBIDDEN_ACTIONS = ["modify_credentials", "elevated_privileges"]


class DreamBuilderUnresolvedError(RuntimeError):
    """Raised by DreamBuilderAdapter until a real Dream Builder contract has
    been established and wired in. Callers should treat this as an expected
    signal to fall back, not a bug -- see plan_dream()."""


class DreamBuilderAdapter:
    """Integration boundary awaiting an authoritative Dream Builder contract.

    STATUS: AUTHORITATIVE_INTERFACE_UNRESOLVED

    Once the real Dream Builder's source is available (its FastAPI routes,
    request/response models, and repository location), replace build()
    below with an actual call into it -- do not hand-wave a schema in the
    meantime.
    """

    def build(self, description: str, allowed_paths: list, allowed_commands: list, **kwargs) -> dict:
        raise DreamBuilderUnresolvedError(
            "No authoritative Dream Builder interface is wired in yet -- see "
            "agents/dream_builder.py's module docstring for what was found and "
            "what's still missing. Use plan_dream(), which falls back to "
            "RuleBasedDreamPathwayPlaceholder automatically."
        )


def load_canon(canon_path: str = "vault/canon.json") -> dict:
    with open(canon_path) as f:
        return json.load(f)


def infer_approval_tags(description: str) -> list:
    lowered = description.lower()
    return sorted({
        tag for tag, keywords in APPROVAL_TRIGGER_KEYWORDS.items()
        if any(keyword in lowered for keyword in keywords)
    })


class RuleBasedDreamPathwayPlaceholder:
    """Deterministic, keyword-based fallback. Not Dream Builder -- only a
    stand-in, used because AUTHORITATIVE_INTERFACE_UNRESOLVED."""

    PROVENANCE = "RuleBasedDreamPathwayPlaceholder"

    def build(
        self,
        description: str,
        allowed_paths: list,
        allowed_commands: list,
        acceptance_criteria: list = None,
        forbidden_actions: list = None,
        provider: str = "claude_code",
        max_budget_usd: float = DEFAULT_MAX_BUDGET_USD,
        canon_path: str = "vault/canon.json",
    ) -> dict:
        canon = load_canon(canon_path)
        forbidden = sorted(set(ALWAYS_FORBIDDEN_ACTIONS) | set(forbidden_actions or []))

        return {
            "goal": description,
            "provider": provider,
            "allowed_paths": list(allowed_paths),
            "allowed_commands": list(allowed_commands),
            "forbidden_actions": forbidden,
            "acceptance_criteria": acceptance_criteria or [f"Complies with canon: {r}" for r in canon.get("rules", [])],
            "requires_human_approval": infer_approval_tags(description),
            "max_budget_usd": max_budget_usd,
            "max_turns": DEFAULT_MAX_TURNS,
            "dream_builder": {
                "source_description": description,
                "canon_rules_applied": canon.get("rules", []),
                "dream_source": RuleBasedDreamPathwayPlaceholder.PROVENANCE,
                "truth_status": "PLACEHOLDER_ACTIVE",
            },
        }


def plan_dream(
    description: str,
    allowed_paths: list,
    allowed_commands: list,
    acceptance_criteria: list = None,
    forbidden_actions: list = None,
    provider: str = "claude_code",
    max_budget_usd: float = DEFAULT_MAX_BUDGET_USD,
    canon_path: str = "vault/canon.json",
    adapter: DreamBuilderAdapter = None,
) -> dict:
    """Turn a raw goal into a governed OCode contract. Tries the real
    DreamBuilderAdapter first; falls back to RuleBasedDreamPathwayPlaceholder
    only because the adapter is currently unresolved. Every contract this
    returns carries dream_builder.dream_source naming whichever one actually
    built it -- check that field rather than assuming."""
    adapter = adapter or DreamBuilderAdapter()
    kwargs = dict(
        acceptance_criteria=acceptance_criteria, forbidden_actions=forbidden_actions,
        provider=provider, max_budget_usd=max_budget_usd, canon_path=canon_path,
    )
    try:
        return adapter.build(description, allowed_paths, allowed_commands, **kwargs)
    except DreamBuilderUnresolvedError:
        return RuleBasedDreamPathwayPlaceholder().build(description, allowed_paths, allowed_commands, **kwargs)
