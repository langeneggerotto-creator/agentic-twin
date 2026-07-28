import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dream_builder import planner, reflector, resources, store
from dream_builder.util import extract_json_array


def test_extract_json_array_parses_embedded_array():
    text = 'Sure, here you go:\n```json\n[{"a": 1}]\n```\nHope that helps.'
    assert extract_json_array(text) == [{"a": 1}]


def test_extract_json_array_raises_without_array():
    try:
        extract_json_array("no json here")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_store_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DREAMS_PATH", tmp_path / "dreams.json")

    dream = store.create_dream("Learn Spanish", "Be conversational in 6 months")
    assert dream["status"] == "planning"
    assert dream["plan"] == []
    assert dream["resources"] == []

    fetched = store.get_dream(dream["id"])
    assert fetched["title"] == "Learn Spanish"

    fetched["status"] = "in_progress"
    store.update_dream(fetched)
    assert store.get_dream(dream["id"])["status"] == "in_progress"


def test_build_plan_uses_llm_output(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DREAMS_PATH", tmp_path / "dreams.json")
    dream = store.create_dream("Run a marathon", "Finish a marathon in under 5 hours")

    fake_response = json.dumps(
        [
            {"step": "Get a couch-to-10k training plan", "needs_internet": False},
            {"step": "Find a local marathon to register for", "needs_internet": True},
        ]
    )
    monkeypatch.setattr(planner, "chat", lambda messages, **kw: fake_response)

    planner.build_plan(dream)

    assert dream["status"] == "in_progress"
    assert len(dream["plan"]) == 2
    assert dream["plan"][1]["needs_internet"] is True
    assert store.get_dream(dream["id"])["plan"][0]["step"].startswith("Get a couch")


def test_find_resources_ranks_search_results(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DREAMS_PATH", tmp_path / "dreams.json")
    dream = store.create_dream("Learn guitar", "Play basic songs within 3 months")

    need_response = json.dumps(
        [{"resource": "Beginner guitar", "why": "Need an instrument", "search_query": "cheap beginner acoustic guitar"}]
    )
    fake_options = [
        {"title": "Budget Guitar Co", "url": "https://example.com/a", "snippet": "$60 starter pack"},
    ]

    calls = {"chat": 0}

    def fake_chat(messages, **kw):
        calls["chat"] += 1
        if calls["chat"] == 1:
            return need_response
        return "Get the Budget Guitar Co starter pack — best value under $100."

    monkeypatch.setattr(resources, "chat", fake_chat)
    monkeypatch.setattr(resources, "search", lambda query, max_results=5: fake_options)

    result = resources.find_resources(dream)

    assert len(result) == 1
    assert result[0]["options"] == fake_options
    assert "Budget Guitar Co" in result[0]["recommendation"]
    assert store.get_dream(dream["id"])["resources"][0]["resource"] == "Beginner guitar"


def test_reflect_appends_reflection(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DREAMS_PATH", tmp_path / "dreams.json")
    dream = store.create_dream("Write a book", "Finish a first draft")
    dream["plan"] = [{"step": "Outline chapters", "needs_internet": False, "done": True, "notes": ""}]
    store.update_dream(dream)

    monkeypatch.setattr(reflector, "chat", lambda messages, **kw: "Good start — keep drafting daily.")

    text = reflector.reflect(dream)

    assert text == "Good start — keep drafting daily."
    assert store.get_dream(dream["id"])["reflections"][0]["text"] == text
