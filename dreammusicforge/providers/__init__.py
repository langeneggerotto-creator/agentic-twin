"""Live provider integration layer.

This is the first part of DreamMusicForge that makes (or is designed to
make) real network calls with real credentials -- everything under
schemas/ is pure validation logic with zero network dependency, by design.

Currently implemented: kling_ai_avatar.py. See its module docstring for
exactly what has and hasn't been verified against a real endpoint (nothing
has -- there is no API key available in this environment).
"""
from __future__ import annotations

from .exceptions import (
    GenerationBudgetExceededError, MissingCredentialsError, ProviderAPIError, PromptTooLongError,
)
from .kling_ai_avatar import (
    GenerationResult, KlingAIAvatarClient, KlingCredentials, KlingTaskHandle, build_jwt,
)
from .transport import Response, Transport, TransportError, UrllibTransport

__all__ = [
    "GenerationBudgetExceededError", "GenerationResult", "KlingAIAvatarClient", "KlingCredentials",
    "KlingTaskHandle", "MissingCredentialsError", "ProviderAPIError", "PromptTooLongError",
    "Response", "Transport", "TransportError", "UrllibTransport", "build_jwt",
]
