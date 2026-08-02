import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import requests

from dream_builder import llm_client


def test_chat_returns_message_content(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"message": {"content": "hello"}}

    monkeypatch.setattr(llm_client.requests, "post", lambda *a, **kw: FakeResponse())

    assert llm_client.chat([{"role": "user", "content": "hi"}]) == "hello"


def test_chat_raises_ollama_error_on_timeout(monkeypatch):
    def fake_post(*a, **kw):
        raise requests.exceptions.ReadTimeout("timed out")

    monkeypatch.setattr(llm_client.requests, "post", fake_post)

    try:
        llm_client.chat([{"role": "user", "content": "hi"}])
        assert False, "expected OllamaError"
    except llm_client.OllamaError as e:
        assert "didn't respond within" in str(e)


def test_chat_raises_ollama_error_on_connection_error(monkeypatch):
    def fake_post(*a, **kw):
        raise requests.exceptions.ConnectionError("refused")

    monkeypatch.setattr(llm_client.requests, "post", fake_post)

    try:
        llm_client.chat([{"role": "user", "content": "hi"}])
        assert False, "expected OllamaError"
    except llm_client.OllamaError as e:
        assert "Could not reach Ollama" in str(e)


def test_chat_raises_ollama_error_on_http_error(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            raise requests.exceptions.HTTPError("500 server error")

    monkeypatch.setattr(llm_client.requests, "post", lambda *a, **kw: FakeResponse())

    try:
        llm_client.chat([{"role": "user", "content": "hi"}])
        assert False, "expected OllamaError"
    except llm_client.OllamaError as e:
        assert "Ollama returned an error" in str(e)
