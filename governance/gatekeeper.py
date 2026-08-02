import fnmatch
import re


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


# Heuristics mapping observed shell commands to forbidden-action tags. This is a
# defense-in-depth backstop, not a substitute for declared_actions -- an executor
# can always declare an action explicitly, but should not be trusted to declare
# every dangerous command it ran.
_COMMAND_ACTION_HEURISTICS = [
    (re.compile(r"\b(apt-get|apt|yum|dnf|brew)\s+install\b"), "install_system_packages"),
    (re.compile(r"\bpip3?\s+install\b"), "install_system_packages"),
    (re.compile(r"\bsudo\b"), "elevated_privileges"),
    (re.compile(r"\brm\s+-rf\b"), "destructive_delete"),
    (re.compile(r"\bgit\s+push\b.*--force\b"), "force_push"),
    (re.compile(r"\bgit\s+reset\s+--hard\b"), "hard_reset"),
    (re.compile(r"\bcurl\b.*\|\s*(bash|sh)\b"), "remote_code_execution"),
    (re.compile(r"\b(kubectl\s+apply|terraform\s+apply|docker\s+push|npm\s+publish|helm\s+upgrade|aws\s+deploy|systemctl\s+restart)\b"),
     "production_deployment"),
    (re.compile(r"\b(gpio|pwm|servo|actuator|motor_control)\b", re.IGNORECASE), "hardware_control"),
]


def _detect_actions_from_commands(commands_run: list) -> set:
    detected = set()
    for cmd in commands_run:
        for pattern, action in _COMMAND_ACTION_HEURISTICS:
            if pattern.search(cmd):
                detected.add(action)
    return detected


def _path_allowed(path: str, allowed_patterns: list) -> bool:
    if not allowed_patterns:
        return False
    return any(fnmatch.fnmatch(path, pattern) for pattern in allowed_patterns)


def _command_allowed(command: str, allowed_commands: list) -> bool:
    return any(command == c or command.startswith(c + " ") for c in allowed_commands)


def enforce_contract(
    contract: dict,
    changed_files: list,
    commands_run: list = None,
    test_results: str = "",
    declared_actions: list = None,
    approved_actions: list = None,
    cost_usd: float = None,
) -> dict:
    """Mechanically enforce a delegation contract against what an executor actually did.

    Path and command scope are verified directly against changed_files/commands_run --
    they are never taken on trust. Forbidden actions are checked against both an
    explicit declared_actions list and a heuristic scan of commands_run, since an
    executor should not be relied on to self-report every dangerous command.

    requires_human_approval is not just echoed back for display -- any of those
    action tags that were actually observed (declared or heuristically detected)
    fail the gate unless present in approved_actions, per "preserve human control
    over consequential actions." Pass approved_actions from a real, out-of-band
    human decision (see governance.approvals) -- never from the executor's own output.

    cost_usd, if given, is checked against contract["max_budget_usd"] independently
    of whatever client-side budget stop the executor itself was configured with --
    "cap commitment according to evidence strength" means the actual spend is
    verified here too, not just requested as a soft stop upstream.
    """
    commands_run = commands_run or []
    declared_actions = declared_actions or []
    approved_actions = set(approved_actions or [])
    violations = []

    allowed_paths = contract.get("allowed_paths", [])
    for path in changed_files:
        if not _path_allowed(path, allowed_paths):
            violations.append(f"file outside allowed_paths: {path}")

    allowed_commands = contract.get("allowed_commands", [])
    for command in commands_run:
        if allowed_commands and not _command_allowed(command, allowed_commands):
            violations.append(f"command outside allowed_commands: {command}")

    observed_actions = set(declared_actions) | _detect_actions_from_commands(commands_run)

    forbidden_actions = set(contract.get("forbidden_actions", []))
    tripped = sorted(forbidden_actions & observed_actions)
    if tripped:
        violations.append(f"forbidden actions detected: {tripped}")

    requires_human_approval = set(contract.get("requires_human_approval", []))
    pending_approval = sorted((requires_human_approval & observed_actions) - approved_actions)
    if pending_approval:
        violations.append(f"actions require human approval before proceeding: {pending_approval}")

    test_commands_ran = any("test" in c or "pytest" in c for c in commands_run)
    if test_commands_ran and "FAIL" in test_results:
        violations.append("acceptance criteria failed: tests did not all pass")

    max_budget_usd = contract.get("max_budget_usd")
    if max_budget_usd is not None and cost_usd is not None and cost_usd > max_budget_usd:
        violations.append(f"cost exceeded budget: ${cost_usd:.4f} > ${max_budget_usd:.4f} cap")

    return {
        "passed": not violations,
        "violations": violations,
        "requires_human_approval": sorted(requires_human_approval),
        "pending_approval": pending_approval,
    }
