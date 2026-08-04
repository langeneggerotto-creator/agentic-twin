"""Fail-closed error types for the live provider integration layer.

Every one of these is raised before or in place of a real network call
where possible, rather than letting a bad request go out and fail
opaquely -- consistent with this repo's "fail closed" discipline
elsewhere (schema validators, Monte Carlo reproducibility checks, the
rights-review gate)."""
from __future__ import annotations


class MissingCredentialsError(Exception):
    """Raised when a required credential environment variable is unset.
    Never raised with the credential value in the message -- there isn't
    one to leak, by construction."""


class PromptTooLongError(Exception):
    """Raised before any network call when a prompt/negative_prompt exceeds
    the provider's documented character limit."""


class ProviderAPIError(Exception):
    """Raised when the provider returns a well-formed error response
    (non-2xx status, or a body indicating task failure)."""

    def __init__(self, message: str, *, status: int | None = None, body: dict | None = None):
        super().__init__(message)
        self.status = status
        self.body = body or {}


class GenerationBudgetExceededError(Exception):
    """Raised when polling exhausts the retry/attempt budget without the
    task reaching a terminal success state. Never silently returns a
    fabricated success."""
