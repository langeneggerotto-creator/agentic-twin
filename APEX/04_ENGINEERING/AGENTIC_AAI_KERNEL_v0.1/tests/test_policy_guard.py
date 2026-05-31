import sys
import unittest
from pathlib import Path

RUNTIME = Path(__file__).parents[1] / "runtime"
sys.path.insert(0, str(RUNTIME))

from policy_guard import PolicyGuard


class AuthorityBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.guard = PolicyGuard()

    def test_bounded_build_and_draft_delivery_allowed(self):
        self.assertTrue(self.guard.authorize("build_artifacts").allowed)
        self.assertTrue(self.guard.authorize("run_tests").allowed)
        self.assertTrue(self.guard.authorize("create_draft_pr").allowed)

    def test_merge_release_and_production_are_blocked(self):
        self.assertFalse(self.guard.authorize("merge_pr").allowed)
        self.assertFalse(self.guard.authorize("publish_release").allowed)
        self.assertFalse(self.guard.authorize("production_deploy").allowed)

    def test_physical_action_and_self_escalation_are_blocked(self):
        self.assertFalse(self.guard.authorize("physical_connect").allowed)
        self.assertFalse(self.guard.authorize("physical_command").allowed)
        self.assertFalse(self.guard.authorize("self_escalate").allowed)

    def test_unknown_action_is_denied(self):
        self.assertFalse(self.guard.authorize("invent_new_authority").allowed)


if __name__ == "__main__":
    unittest.main()
