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
