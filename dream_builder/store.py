import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

DREAMS_PATH = Path(__file__).resolve().parent.parent / "vault" / "dreams.json"
BUCKET_PATH = Path(__file__).resolve().parent.parent / "vault" / "action_bucket.json"


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


def load_bucket():
    if not BUCKET_PATH.exists():
        return []
    with open(BUCKET_PATH) as f:
        return json.load(f)


def save_bucket(items):
    BUCKET_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BUCKET_PATH, "w") as f:
        json.dump(items, f, indent=2)


def add_to_bucket(label, detail, url=None, source_dream_id=None, source_dream_title=None):
    """Save a resource or hint (from any dream) into a persistent, cross-dream
    collection the user can later combine into a new dream — independent of
    that dream's own resources list, which gets overwritten whenever
    resources are re-searched."""
    items = load_bucket()
    item = {
        "id": uuid.uuid4().hex[:8],
        "label": label,
        "detail": detail,
        "url": url,
        "source_dream_id": source_dream_id,
        "source_dream_title": source_dream_title,
        "added_at": now(),
    }
    items.append(item)
    save_bucket(items)
    return item


def remove_from_bucket(item_id):
    items = [i for i in load_bucket() if i["id"] != item_id]
    save_bucket(items)


def get_bucket_item(item_id):
    for i in load_bucket():
        if i["id"] == item_id:
            return i
    return None
