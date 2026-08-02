"""Provider interface.

Every provider module exposes:

    async def run_delegate(contract: dict) -> dict

returning an outcome shaped like:

    {
        "provider": str,
        "gate": dict,             # governance.gatekeeper.enforce_contract's return value
        "rolled_back": bool,
        "changed_files_verified_by_git": list[str],
        "commands_run": list[str],
        "session_id": str | None,      # provider-specific; None if the provider has no notion of one
        "cost_usd": float | None,      # None if the provider can't report a verified figure
        "is_error": bool | None,
    }

This is the whole contract the router (runner/providers/router.py) and the
evidence ledger rely on. Any new provider must match this shape and must
call governance.gatekeeper.enforce_contract itself -- routing to a
different provider must never bypass the gate, or "graceful replacement of
any provider" just means replacing the safety along with the engine.
"""
