"""APEX Agentic AAI Kernel v0.1 bounded authority guard."""
from dataclasses import dataclass
from enum import IntEnum


class Authority(IntEnum):
    A0_DEFINE = 0
    A1_BUILD = 1
    A2_TEST = 2
    A3_DRAFT_DELIVERY = 3


MINIMUM_AUTHORITY = {
    "read_context": Authority.A0_DEFINE,
    "build_artifacts": Authority.A1_BUILD,
    "run_tests": Authority.A2_TEST,
    "write_ledgers": Authority.A2_TEST,
    "package_outputs": Authority.A2_TEST,
    "create_branch": Authority.A3_DRAFT_DELIVERY,
    "create_draft_pr": Authority.A3_DRAFT_DELIVERY,
}

ALWAYS_DENIED = {
    "merge_pr",
    "publish_release",
    "production_deploy",
    "store_credentials",
    "physical_connect",
    "physical_command",
    "self_escalate",
}


@dataclass(frozen=True)
class Decision:
    allowed: bool
    code: str
    reason: str


class PolicyGuard:
    def __init__(self, ceiling: Authority = Authority.A3_DRAFT_DELIVERY):
        self.ceiling = ceiling

    def authorize(self, action: str) -> Decision:
        if action in ALWAYS_DENIED:
            return Decision(False, "BLOCK_HUMAN_GATE", f"{action} is outside v0.1 autonomous authority.")
        if action not in MINIMUM_AUTHORITY:
            return Decision(False, "BLOCK_UNKNOWN", "Unknown action denied by default.")
        if MINIMUM_AUTHORITY[action] > self.ceiling:
            return Decision(False, "BLOCK_CEILING", "Action exceeds current authority ceiling.")
        return Decision(True, "ALLOW_BOUNDED", f"{action} is within bounded authority.")
