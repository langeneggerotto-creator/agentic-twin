import os

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("DREAM_BUILDER_MODEL", "llama3.1:8b")
