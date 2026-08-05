#!/usr/bin/env python3
"""Smoke tests for the Kling AI Avatar live-integration client.

Every test here runs fully offline: FakeTransport records requests and
returns scripted responses, so this suite exercises the real request-
building, JWT-signing, retry, and error-handling logic without ever
touching the network or needing a real API key -- same discipline as
every other test in this repo (deterministic, no live calls, no
dependencies beyond the standard library).
"""
import importlib.util
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # dreammusicforge/
REPO_ROOT = ROOT.parent

# providers/ has real internal structure (kling_ai_avatar.py imports from
# .exceptions and .transport), unlike schemas/*.py, which are deliberately
# standalone files. dreammusicforge has no __init__.py, but providers/ does,
# so `dreammusicforge.providers.*` resolves as a regular package nested in
# an implicit PEP 420 namespace package -- no __init__.py needed at the
# dreammusicforge level for this to work.
sys.path.insert(0, str(REPO_ROOT))

from dreammusicforge.providers import exceptions as exceptions_mod  # noqa: E402
from dreammusicforge.providers import kling_ai_avatar as kling_mod  # noqa: E402
from dreammusicforge.providers import transport as transport_mod  # noqa: E402


def load_schema(name, filename):
    # schemas/*.py are deliberately standalone (no cross-file relative
    # imports), so every test in this repo loads them this way rather than
    # through package import machinery.
    spec = importlib.util.spec_from_file_location(name, ROOT / "schemas" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


provider_package = load_schema("provider_specific_production_package", "provider_specific_production_package.py")

Response = transport_mod.Response
KlingCredentials = kling_mod.KlingCredentials
KlingAIAvatarClient = kling_mod.KlingAIAvatarClient
build_jwt = kling_mod.build_jwt


class FakeTransport:
    """Records every call and returns pre-scripted responses in order,
    or a single fixed response if `responses` is not a list of per-call
    entries."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls: list[dict] = []

    def request(self, method, url, headers, body):
        self.calls.append({"method": method, "url": url, "headers": headers, "body": body})
        if not self.responses:
            raise AssertionError("FakeTransport ran out of scripted responses")
        return self.responses.pop(0)


SAMPLE_VIDEO_PROMPT = {
    "shot_id": "shot1",
    "provider": "kling_ai_avatar",
    "prompt_text": "extreme wide shot, static camera movement.",
    "negative_prompt": "no watermark",
    "provider_parameters": {"duration_seconds": 4.5, "aspect_ratio": "16:9"},
    "source_fields_used": ["camera.shot_size"],
}


class KlingCredentialsTests(unittest.TestCase):
    def test_missing_credentials_raise_with_no_secret_in_message(self):
        env = {k: v for k, v in os.environ.items() if k not in ("KLING_ACCESS_KEY", "KLING_SECRET_KEY")}
        old_environ = dict(os.environ)
        os.environ.clear()
        os.environ.update(env)
        try:
            with self.assertRaises(exceptions_mod.MissingCredentialsError) as ctx:
                KlingCredentials.from_env()
            self.assertIn("KLING_ACCESS_KEY", str(ctx.exception))
            self.assertIn("KLING_SECRET_KEY", str(ctx.exception))
        finally:
            os.environ.clear()
            os.environ.update(old_environ)


class BuildJwtTests(unittest.TestCase):
    def setUp(self):
        self.credentials = KlingCredentials(access_key="ak-test", secret_key="sk-test-secret")

    def test_jwt_has_three_segments(self):
        token = build_jwt(self.credentials, now=1_700_000_000)
        self.assertEqual(len(token.split(".")), 3)

    def test_jwt_header_declares_hs256(self):
        import base64
        import json
        token = build_jwt(self.credentials, now=1_700_000_000)
        header_b64 = token.split(".")[0]
        padded = header_b64 + "=" * (-len(header_b64) % 4)
        header = json.loads(base64.urlsafe_b64decode(padded))
        self.assertEqual(header, {"alg": "HS256", "typ": "JWT"})

    def test_jwt_payload_uses_access_key_as_issuer_and_sets_expiry(self):
        import base64
        import json
        now = 1_700_000_000
        token = build_jwt(self.credentials, now=now, ttl_seconds=1800)
        payload_b64 = token.split(".")[1]
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        self.assertEqual(payload["iss"], "ak-test")
        self.assertEqual(payload["exp"], now + 1800)

    def test_jwt_signature_changes_with_secret(self):
        token_a = build_jwt(KlingCredentials("ak", "secret-a"), now=1_700_000_000)
        token_b = build_jwt(KlingCredentials("ak", "secret-b"), now=1_700_000_000)
        self.assertNotEqual(token_a.split(".")[2], token_b.split(".")[2])


class CreateTaskRequestBuildingTests(unittest.TestCase):
    def setUp(self):
        self.credentials = KlingCredentials("ak-test", "sk-test")

    def test_prompt_over_character_limit_is_rejected_before_any_network_call(self):
        transport = FakeTransport([])
        client = KlingAIAvatarClient(transport=transport, credentials=self.credentials)
        oversized = dict(SAMPLE_VIDEO_PROMPT, prompt_text="x" * 2501)
        with self.assertRaises(exceptions_mod.PromptTooLongError):
            client.create_task(oversized)
        self.assertEqual(transport.calls, [], "no request should have been sent")

    def test_create_task_sends_bearer_auth_and_expected_body_shape(self):
        transport = FakeTransport([Response(status=200, body={"task_id": "task-123"})])
        client = KlingAIAvatarClient(transport=transport, credentials=self.credentials, base_url="https://example.invalid")
        handle = client.create_task(SAMPLE_VIDEO_PROMPT)

        self.assertEqual(handle.task_id, "task-123")
        self.assertEqual(handle.shot_id, "shot1")
        self.assertEqual(len(transport.calls), 1)
        call = transport.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://example.invalid/v1/videos/avatar-tasks")
        self.assertTrue(call["headers"]["Authorization"].startswith("Bearer "))
        self.assertEqual(call["body"]["prompt"], SAMPLE_VIDEO_PROMPT["prompt_text"])
        self.assertEqual(call["body"]["negative_prompt"], "no watermark")
        self.assertTrue(call["body"]["sound"], "native audio must be requested -- that's the entire point of this provider")
        self.assertEqual(call["body"]["duration"], 4.5)
        self.assertEqual(call["body"]["aspect_ratio"], "16:9")

    def test_create_task_error_status_raises_provider_api_error(self):
        transport = FakeTransport([Response(status=401, body={"message": "invalid key"})])
        client = KlingAIAvatarClient(transport=transport, credentials=self.credentials)
        with self.assertRaises(exceptions_mod.ProviderAPIError) as ctx:
            client.create_task(SAMPLE_VIDEO_PROMPT)
        self.assertEqual(ctx.exception.status, 401)

    def test_create_task_missing_task_id_raises(self):
        transport = FakeTransport([Response(status=200, body={"unexpected": "shape"})])
        client = KlingAIAvatarClient(transport=transport, credentials=self.credentials)
        with self.assertRaises(exceptions_mod.ProviderAPIError):
            client.create_task(SAMPLE_VIDEO_PROMPT)


class GenerateWithRetriesTests(unittest.TestCase):
    def setUp(self):
        self.credentials = KlingCredentials("ak-test", "sk-test")
        self.sleeps: list[float] = []

    def _fake_sleep(self, seconds):
        self.sleeps.append(seconds)

    def test_succeeds_immediately_when_first_poll_reports_success(self):
        transport = FakeTransport([
            Response(status=200, body={"task_id": "task-1"}),
            Response(status=200, body={"status": "succeed", "asset_url": "https://cdn.example/shot1.mp4"}),
        ])
        client = KlingAIAvatarClient(transport=transport, credentials=self.credentials)
        result = client.generate_with_retries(SAMPLE_VIDEO_PROMPT, max_attempts=5, sleep_fn=self._fake_sleep)
        self.assertEqual(result.status, "succeed")
        self.assertEqual(result.asset_url, "https://cdn.example/shot1.mp4")
        self.assertEqual(result.attempts, 1)
        self.assertEqual(self.sleeps, [], "no sleep should happen once the task has already succeeded")

    def test_polls_through_processing_states_before_succeeding(self):
        transport = FakeTransport([
            Response(status=200, body={"task_id": "task-1"}),
            Response(status=200, body={"status": "processing"}),
            Response(status=200, body={"status": "processing"}),
            Response(status=200, body={"status": "succeed", "asset_url": "https://cdn.example/shot1.mp4"}),
        ])
        client = KlingAIAvatarClient(transport=transport, credentials=self.credentials)
        result = client.generate_with_retries(SAMPLE_VIDEO_PROMPT, max_attempts=5, sleep_fn=self._fake_sleep)
        self.assertEqual(result.attempts, 3)
        self.assertEqual(len(self.sleeps), 2, "should sleep between polls, not after the final success")

    def test_terminal_failure_status_raises_immediately_not_treated_as_success(self):
        transport = FakeTransport([
            Response(status=200, body={"task_id": "task-1"}),
            Response(status=200, body={"status": "failed", "reason": "content policy"}),
        ])
        client = KlingAIAvatarClient(transport=transport, credentials=self.credentials)
        with self.assertRaises(exceptions_mod.ProviderAPIError):
            client.generate_with_retries(SAMPLE_VIDEO_PROMPT, max_attempts=5, sleep_fn=self._fake_sleep)

    def test_exhausting_budget_raises_rather_than_fabricating_a_result(self):
        transport = FakeTransport([
            Response(status=200, body={"task_id": "task-1"}),
            Response(status=200, body={"status": "processing"}),
            Response(status=200, body={"status": "processing"}),
        ])
        client = KlingAIAvatarClient(transport=transport, credentials=self.credentials)
        with self.assertRaises(exceptions_mod.GenerationBudgetExceededError):
            client.generate_with_retries(SAMPLE_VIDEO_PROMPT, max_attempts=2, sleep_fn=self._fake_sleep)


class EndToEndWithRealPipelineDataTests(unittest.TestCase):
    """Proves the live client actually connects to the existing,
    already-validated pipeline: a real video_prompts[] entry from the
    Provider-Specific Production Package's worked example, run through
    the client with a scripted success, using the real
    generation_risk_estimate.budget_max_total_attempts as the retry
    ceiling -- not a separately made-up number."""

    def test_real_shot1_prompt_through_a_scripted_success(self):
        real_prompt = provider_package.EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE["video_prompts"][0]
        budget = provider_package.EXAMPLE_PROVIDER_SPECIFIC_PRODUCTION_PACKAGE["generation_risk_estimate"]["budget_max_total_attempts"]
        self.assertEqual(real_prompt["provider"], "kling_ai_avatar")

        transport = FakeTransport([
            Response(status=200, body={"task_id": "task-shot1"}),
            Response(status=200, body={"status": "succeed", "asset_url": "https://cdn.example/shot1.mp4"}),
        ])
        client = KlingAIAvatarClient(transport=transport, credentials=KlingCredentials("ak", "sk"))
        result = client.generate_with_retries(real_prompt, max_attempts=budget, sleep_fn=lambda s: None)

        self.assertEqual(result.shot_id, "shot1")
        self.assertEqual(result.status, "succeed")
        self.assertLessEqual(result.attempts, budget)


if __name__ == "__main__":
    unittest.main()
