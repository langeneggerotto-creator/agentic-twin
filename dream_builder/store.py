import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

DREAMS_PATH = Path(__file__).resolve().parent.parent / "vault" / "dreams.json"


def now():
    return datetime.now(timezone.utc).isoformat()


def load_dreams():
    if not DREAMS_PATH.exists():
        return []
    with open(DREAMS_PATH) as f:
        return json.load(f)


def save_dreams(dreams):
    DREAMS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DREAMS_PATH, "w") as f:
        json.dump(dreams, f, indent=2)


def create_dream(title, description):
    dreams = load_dreams()
    dream = {
        "id": uuid.uuid4().hex[:8],
        "title": title,
        "description": description,
        "created_at": now(),
        "status": "planning",
        "plan": [],
        "resources": [],
        "resource_hints": [],
        "reflections": [],
        "projection": None,
        "scaling": None,
    }
    dreams.append(dream)
    save_dreams(dreams)
    return dream


def get_dream(dream_id):
    for d in load_dreams():
        if d["id"] == dream_id:
            return d
    return None


def update_dream(dream):
    dreams = load_dreams()
    for i, d in enumerate(dreams):
        if d["id"] == dream["id"]:
            dreams[i] = dream
            break
    save_dreams(dreams)
