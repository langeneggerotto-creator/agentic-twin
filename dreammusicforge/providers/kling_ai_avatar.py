"""Live integration client for Kling AI Avatar -- the native audio-driven
(video + vocal audio + lip sync in one call) provider this pipeline has
used throughout the Provider-Specific Production Package and Assembly
Package worked examples.

Grounded in what's publicly documented about Kling's API as of this
writing: access-key/secret-key credentials used to sign a short-lived JWT
sent as a Bearer token, an async create-task-then-poll pattern (POST
returns a task_id immediately, GET polls for status), a sound flag to
control whether generated audio is included, and a combined 2500-character
limit on prompt/negative_prompt. None of that has been exercised against a
real Kling endpoint from this repository -- there is no API key available
in this environment to test with.

Two things a real user MUST confirm before the first live call, because
they were not independently verifiable here:

1. BASE_URL. Kling has both a first-party API and third-party resellers
   (e.g. PiAPI) that wrap it under their own paths. DEFAULT_BASE_URL below
   is a placeholder, not a confirmed live endpoint -- pass the real one
   your account actually uses via KlingAIAvatarClient(base_url=...) or the
   KLING_API_BASE_URL environment variable.
2. Exact request/response field names beyond what's covered in this
   module's tests. This client's JSON shape is a best-effort reading of
   published documentation, not a first-party confirmed contract.

Fixing either of those, if they're wrong, means editing this file only --
the rest of the pipeline (schemas, validators, Assembly Package) never
needs to know a provider's wire format.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass

from .exceptions import (
    GenerationBudgetExceededError, MissingCredentialsError, ProviderAPIError, PromptTooLongError,
)
from .transport import Response, Transport, UrllibTransport

PROVIDER_NAME = "kling_ai_avatar"

# Placeholder -- see module docstring point 1. Confirm against your actual
# Kling access (first-party or reseller) before any live call.
DEFAULT_BASE_URL = "https://api.klingai.com"

MAX_PROMPT_CHARS = 2500
DEFAULT_JWT_TTL_SECONDS = 1800
DEFAULT_JWT_NOT_BEFORE_SKEW_SECONDS = 5

TERMINAL_SUCCESS_STATUSES = {"succeed", "succeeded", "completed"}
TERMINAL_FAILURE_STATUSES = {"failed", "error", "cancelled"}


@dataclass(frozen=True)
class KlingCredentials:
    access_key: str
    secret_key: str

    @staticmethod
    def from_env() -> "KlingCredentials":
        access_key = os.environ.get("KLING_ACCESS_KEY")
        secret_key = os.environ.get("KLING_SECRET_KEY")
        missing = [name for name, value in [("KLING_ACCESS_KEY", access_key), ("KLING_SECRET_KEY", secret_key)] if not value]
        if missing:
            raise MissingCredentialsError(
                f"Missing required environment variable(s): {', '.join(missing)}. "
                f"Set them before constructing a KlingAIAvatarClient -- credentials are never read from "
                f"anywhere else (not from code, not from a committed file)."
            )
        return KlingCredentials(access_key=access_key, secret_key=secret_key)


def _base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def build_jwt(
    credentials: KlingCredentials,
    *,
    now: float | None = None,
    ttl_seconds: float = DEFAULT_JWT_TTL_SECONDS,
    not_before_skew_seconds: float = DEFAULT_JWT_NOT_BEFORE_SKEW_SECONDS,
) -> str:
    """HS256 JWT signed with the secret key, issued by the access key --
    stdlib-only (hmac + hashlib + base64), no PyJWT dependency. `now` is
    injectable so tests are deterministic; defaults to time.time()."""
    issued_at = now if now is not None else time.time()
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "iss": credentials.access_key,
        "exp": int(issued_at + ttl_seconds),
        "nbf": int(issued_at - not_before_skew_seconds),
    }
    signing_input = f"{_base64url(json.dumps(header, separators=(',', ':')).encode())}." \
                     f"{_base64url(json.dumps(payload, separators=(',', ':')).encode())}"
    signature = hmac.new(credentials.secret_key.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_base64url(signature)}"


@dataclass(frozen=True)
class KlingTaskHandle:
    task_id: str
    shot_id: str


@dataclass(frozen=True)
class GenerationResult:
    shot_id: str
    task_id: str
    status: str
    asset_url: str | None
    attempts: int
    raw_response: dict


def _require_prompt_within_limit(prompt_text: str, field_name: str) -> None:
    if len(prompt_text) > MAX_PROMPT_CHARS:
        raise PromptTooLongError(
            f"{field_name} is {len(prompt_text)} characters, exceeding Kling's {MAX_PROMPT_CHARS}-character limit"
        )


class KlingAIAvatarClient:
    def __init__(
        self,
        transport: Transport | None = None,
        credentials: KlingCredentials | None = None,
        base_url: str | None = None,
        now_fn=time.time,
    ):
        self.transport = transport or UrllibTransport()
        self.credentials = credentials or KlingCredentials.from_env()
        self.base_url = (base_url or os.environ.get("KLING_API_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.now_fn = now_fn

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {build_jwt(self.credentials, now=self.now_fn())}"}

    def create_task(self, video_prompt: dict) -> KlingTaskHandle:
        """video_prompt is one entry from a Provider-Specific Production
        Package's video_prompts[] -- the exact shape
        provider_specific_production_package.translate_shot_to_video_prompt()
        already produces. required_reference_ids (from an Assembly Package
        CompiledClip, if available) can be passed in via
        video_prompt['provider_parameters']['reference_asset_ids']."""
        prompt_text = video_prompt["prompt_text"]
        negative_prompt = video_prompt.get("negative_prompt", "")
        _require_prompt_within_limit(prompt_text, "prompt_text")
        _require_prompt_within_limit(negative_prompt, "negative_prompt")

        params = video_prompt.get("provider_parameters", {})
        body = {
            "prompt": prompt_text,
            "negative_prompt": negative_prompt,
            "sound": True,  # native audio-driven generation is the whole point of using this provider
            "duration": params.get("duration_seconds"),
            "aspect_ratio": params.get("aspect_ratio"),
            "reference_asset_ids": params.get("reference_asset_ids", []),
        }

        response = self.transport.request(
            "POST", f"{self.base_url}/v1/videos/avatar-tasks", self._auth_headers(), body,
        )
        if response.status >= 400:
            raise ProviderAPIError(
                f"create_task for shot '{video_prompt.get('shot_id')}' failed with status {response.status}",
                status=response.status, body=response.body,
            )
        task_id = response.body.get("task_id") or response.body.get("data", {}).get("task_id")
        if not task_id:
            raise ProviderAPIError(
                f"create_task response for shot '{video_prompt.get('shot_id')}' did not include a task_id",
                status=response.status, body=response.body,
            )
        return KlingTaskHandle(task_id=task_id, shot_id=video_prompt.get("shot_id", ""))

    def poll_task(self, handle: KlingTaskHandle) -> Response:
        return self.transport.request(
            "GET", f"{self.base_url}/v1/videos/avatar-tasks/{handle.task_id}", self._auth_headers(), None,
        )

    def generate_with_retries(
        self,
        video_prompt: dict,
        *,
        max_attempts: int,
        sleep_fn=time.sleep,
        poll_interval_seconds: float = 5.0,
    ) -> GenerationResult:
        """Creates the task once, then polls up to max_attempts times.
        max_attempts should come from the paired Provider-Specific
        Production Package's generation_risk_estimate.budget_max_total_attempts
        -- the retry ceiling this function enforces is the same one the
        Monte Carlo model already estimated risk against, not a separate
        made-up number. Raises GenerationBudgetExceededError rather than
        returning a partial/fabricated result if the budget runs out."""
        handle = self.create_task(video_prompt)
        attempts = 0
        last_response: Response | None = None

        while attempts < max_attempts:
            attempts += 1
            last_response = self.poll_task(handle)
            if last_response.status >= 400:
                raise ProviderAPIError(
                    f"poll_task for shot '{handle.shot_id}' failed with status {last_response.status}",
                    status=last_response.status, body=last_response.body,
                )
            status = str(last_response.body.get("status", "")).lower()
            if status in TERMINAL_SUCCESS_STATUSES:
                asset_url = last_response.body.get("asset_url") or last_response.body.get("data", {}).get("asset_url")
                return GenerationResult(
                    shot_id=handle.shot_id, task_id=handle.task_id, status=status,
                    asset_url=asset_url, attempts=attempts, raw_response=last_response.body,
                )
            if status in TERMINAL_FAILURE_STATUSES:
                raise ProviderAPIError(
                    f"shot '{handle.shot_id}' task {handle.task_id} reported terminal status '{status}'",
                    status=last_response.status, body=last_response.body,
                )
            if attempts < max_attempts:
                sleep_fn(poll_interval_seconds)

        raise GenerationBudgetExceededError(
            f"shot '{handle.shot_id}' task {handle.task_id} did not reach a terminal state within "
            f"{max_attempts} attempts (last status: {last_response.body.get('status') if last_response else 'unknown'})"
        )
