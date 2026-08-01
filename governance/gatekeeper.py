def enforce_canon(code: str, canon_path: str) -> list[str]:
    import json
    with open(canon_path) as f:
        canon = json.load(f)
    violations = []
    if "def " not in code:
        violations.append("Missing functions.")
    if "assert" not in code:
        violations.append("No tests found.")
    return violations


BANNED_FINANCIAL_CLAIM_PHRASES = [
    "guaranteed income",
    "guaranteed money",
    "guaranteed profit",
    "risk-free",
    "risk free",
    "get rich quick",
    "100% guaranteed",
    "no risk",
]


def enforce_claims_safety(text: str) -> list[str]:
    """Reject overpromising financial language, per the Core OS truth boundary:
    forecasts must not be represented as guaranteed real-world outcomes."""
    lowered = text.lower()
    return [phrase for phrase in BANNED_FINANCIAL_CLAIM_PHRASES if phrase in lowered]
