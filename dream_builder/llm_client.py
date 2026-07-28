import requests

from .config import OLLAMA_HOST, OLLAMA_MODEL


class OllamaError(RuntimeError):
    """Raised when the local Ollama server can't be reached or errors out."""


def chat(messages, model=None, temperature=0.4):
    model = model or OLLAMA_MODEL
    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": temperature},
            },
            timeout=180,
        )
        resp.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        raise OllamaError(
            f"Could not reach Ollama at {OLLAMA_HOST}. Is it running? "
            f"Start it with `ollama serve` and make sure the model is "
            f"pulled: `ollama pull {model}`."
        ) from e
    except requests.exceptions.HTTPError as e:
        raise OllamaError(f"Ollama returned an error: {e}") from e
    return resp.json()["message"]["content"]
