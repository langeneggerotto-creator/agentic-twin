#!/usr/bin/env python3
"""Smoke tests for runner.providers.router's dispatch logic. Uses stub
providers so no real API calls (Claude or OpenAI) happen here."""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.providers import router


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


async def _stub_provider(name):
    async def run_delegate(contract):
        return {"provider": name, "gate": {"passed": True}, "contract_goal": contract.get("goal")}
    return run_delegate


def test_defaults_to_claude_code_when_provider_is_unspecified():
    original = dict(router.PROVIDERS)
    try:
        called = {}

        async def stub(contract):
            called["ran"] = True
            return {"provider": "claude_code", "gate": {"passed": True}}

        router.PROVIDERS["claude_code"] = stub
        result = asyncio.run(router.route_delegate({"goal": "no-op"}))
        assert_true(called.get("ran"), "the default provider must actually be invoked")
        assert_true(result["provider"] == "claude_code", "default provider must be claude_code")
    finally:
        router.PROVIDERS.clear()
        router.PROVIDERS.update(original)


def test_routes_to_the_named_provider():
    original = dict(router.PROVIDERS)
    try:
        async def stub(contract):
            return {"provider": "openai", "gate": {"passed": True}}

        router.PROVIDERS["openai"] = stub
        result = asyncio.run(router.route_delegate({"goal": "no-op", "provider": "openai"}))
        assert_true(result["provider"] == "openai", "an explicit provider field must be honored")
    finally:
        router.PROVIDERS.clear()
        router.PROVIDERS.update(original)


def test_unknown_provider_raises_instead_of_silently_falling_back():
    threw = False
    try:
        asyncio.run(router.route_delegate({"goal": "no-op", "provider": "does_not_exist"}))
    except ValueError as e:
        threw = True
        assert_true("does_not_exist" in str(e), "error must name the unrecognized provider")
    assert_true(threw, "an unknown provider must raise, never silently pick a default")


def test_both_real_providers_are_registered():
    assert_true("claude_code" in router.PROVIDERS, "claude_code must be a registered provider")
    assert_true("openai" in router.PROVIDERS, "openai must be a registered provider")


if __name__ == "__main__":
    test_defaults_to_claude_code_when_provider_is_unspecified()
    test_routes_to_the_named_provider()
    test_unknown_provider_raises_instead_of_silently_falling_back()
    test_both_real_providers_are_registered()
    print("PASS: provider router smoke tests")
