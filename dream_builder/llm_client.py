import requests

from .config import OLLAMA_HOST, OLLAMA_MODEL


class OllamaError(RuntimeError):
    """Raised when the local Ollama server can't be reached or errors out."""


def chat(messages, model=None, temperature=0.4):
    model = model or OLLAMA_MODEL
    timeout = 300
    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": temperature},
            },
            timeout=timeout,
        )
        resp.raise_for_status()
    except requests.exceptions.Timeout as e:
        # A distinct exception hierarchy from ConnectionError in `requests` —
        # easy to miss, and doing so left this uncaught until a real request
        # (generating 3 full plans at once, under concurrent load from
        # multiple browser tabs/CLI calls hitting the same local Ollama
        # instance) actually exceeded the limit and crashed as a raw 500.
        raise OllamaError(
            f"Ollama didn't respond within {timeout}s. This usually means "
            f"it's busy with another request — Ollama serves one at a time "
            f"by default — or this request (e.g. generating multiple full "
            f"plans at once) is just bigger than usual. Wait for any other "
            f"request to finish and try again."
        ) from e
    except requests.exceptions.ConnectionError as e:
        raise OllamaError(
            f"Could not reach Ollama at {OLLAMA_HOST}. Is it running? "
            f"Start it with `ollama serve` and make sure the model is "
            f"pulled: `ollama pull {model}`."
        ) from e
    except requests.exceptions.HTTPError as e:
        raise OllamaError(f"Ollama returned an error: {e}") from e
    return resp.json()["message"]["content"]
