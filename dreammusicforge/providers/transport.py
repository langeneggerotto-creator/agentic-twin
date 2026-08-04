"""Minimal, dependency-free HTTP transport seam.

The whole point of this file: every provider client in this package takes a
Transport as a constructor argument instead of calling `urllib.request`
directly inline. That seam is what makes generate_with_retries() and every
request-building code path fully testable offline (see
tests/test_kling_ai_avatar_client.py's FakeTransport) -- no real network
call happens anywhere in this repo's test suite, consistent with every
other module here.

UrllibTransport is the one that actually talks to the network, using only
the standard library (no `requests` dependency). It has not been exercised
against any real provider in this repository -- see providers/kling_ai_avatar.py
for what that would take.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class Response:
    status: int
    body: dict
    headers: dict[str, str] = field(default_factory=dict)


class TransportError(Exception):
    """Raised when the transport itself fails (network error, non-JSON body,
    connection refused, timeout) -- distinct from the provider returning a
    well-formed error response, which callers inspect via Response.status."""


class Transport(Protocol):
    def request(self, method: str, url: str, headers: dict[str, str], body: dict | None) -> Response: ...


class UrllibTransport:
    """Real network transport. Stdlib-only by design -- this repo has never
    depended on anything beyond the Python standard library, and a live
    integration layer is not the place to start."""

    def __init__(self, timeout_seconds: float = 30.0):
        self.timeout_seconds = timeout_seconds

    def request(self, method: str, url: str, headers: dict[str, str], body: dict | None) -> Response:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request_headers = dict(headers)
        if data is not None:
            request_headers.setdefault("Content-Type", "application/json")
        req = urllib.request.Request(url, data=data, headers=request_headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw = response.read()
                status = response.status
                response_headers = dict(response.headers.items())
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            status = exc.code
            response_headers = dict(exc.headers.items()) if exc.headers else {}
        except urllib.error.URLError as exc:
            raise TransportError(f"{method} {url} failed: {exc.reason}") from exc

        try:
            parsed = json.loads(raw.decode("utf-8")) if raw else {}
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise TransportError(f"{method} {url} returned a non-JSON body: {exc}") from exc

        return Response(status=status, body=parsed, headers=response_headers)
