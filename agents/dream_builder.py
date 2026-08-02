"""Dream Builder: turns a raw human "dream" (a goal description) into a
governed OCode delegation contract, instead of a hand-written JSON file.

This is the piece APEX's own mission statement names but nothing
implemented: "convert ideas, dreams, code... into tested artifacts,
executable systems, and continuous improvement loops" (APEX/README.md).
It also finally gives vault/vision.json and vault/canon.json a real job --
previously they were only read by the hardcoded agents/planner.py stub.

Deliberately deterministic and rule-based, not model-driven: a dream only
ever becomes an inspectable contract, never an immediate action. Whether it
actually runs is still entirely gated by everything already built
(governance.gatekeeper.enforce_contract, governance.approvals,
max_budget_usd) -- Dream Builder does not bypass any of that, it only
produces the contract those systems then enforce.

Scope (allowed_paths/allowed_commands) is always supplied explicitly by a
human, never inferred from the description -- inferring the
security-critical fields from free text would be exactly the kind of
guess this whole system exists to avoid.
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


def load_canon(canon_path: str = "vault/canon.json") -> dict:
    with open(canon_path) as f:
        return json.load(f)


def infer_approval_tags(description: str) -> list:
    lowered = description.lower()
    return sorted({
        tag for tag, keywords in APPROVAL_TRIGGER_KEYWORDS.items()
        if any(keyword in lowered for keyword in keywords)
    })


def build_dream(
    description: str,
    allowed_paths: list,
    allowed_commands: list,
    acceptance_criteria: list = None,
    forbidden_actions: list = None,
    provider: str = "claude_code",
    max_budget_usd: float = DEFAULT_MAX_BUDGET_USD,
    canon_path: str = "vault/canon.json",
) -> dict:
    """Turn a raw goal into a full OCode delegation contract, ready to pass
    straight to runner.providers.router.route_delegate (after any
    approval-gated actions it names have actually been granted)."""
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
            "truth_status": "DESIGNED_NOT_PROVEN",
        },
    }
