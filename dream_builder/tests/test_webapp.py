import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from fastapi.testclient import TestClient

from dream_builder import executor, planner, projections, reflector, resources, store
from dream_builder.webapp import jobs, main


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DREAMS_PATH", tmp_path / "dreams.json")
    monkeypatch.setattr(jobs, "_jobs", {})
    return TestClient(main.app)


def _make_dream(monkeypatch, title="Learn Spanish", description="Be conversational"):
    monkeypatch.setattr(
        resources, "chat", lambda messages, **kw: json.dumps([{"pitch": "Could be handy: X."}])
    )
    dream = store.create_dream(title, description)
    return dream


def test_create_dream_returns_hints(client, monkeypatch):
    monkeypatch.setattr(
        resources, "chat", lambda messages, **kw: json.dumps([{"pitch": "Could be handy: X."}])
    )
    resp = client.post("/api/dreams", json={"title": "Learn Spanish", "description": "Be conversational"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Learn Spanish"
    assert body["resource_hints"] == ["Could be handy: X."]


def test_list_and_get_dream(client, monkeypatch):
    dream = _make_dream(monkeypatch)
    resp = client.get("/api/dreams")
    assert resp.status_code == 200
    listed = resp.json()
    assert len(listed) == 1
    assert listed[0]["id"] == dream["id"]
    assert listed[0]["steps_total"] == 0

    resp = client.get(f"/api/dreams/{dream['id']}")
    assert resp.status_code == 200
    assert resp.json()["title"] == dream["title"]


def test_get_unknown_dream_returns_404(client):
    resp = client.get("/api/dreams/doesnotexist")
    assert resp.status_code == 404


def test_plan_endpoint_generates_plan_and_hints(client, monkeypatch):
    dream = _make_dream(monkeypatch)
    plan_response = json.dumps([{"step": "Download Duolingo", "needs_internet": True}])
    hints_response = json.dumps([{"pitch": "Could be handy: a phrasebook."}])
    monkeypatch.setattr(planner, "chat", lambda messages, **kw: plan_response)
    monkeypatch.setattr(resources, "chat", lambda messages, **kw: hints_response)

    resp = client.post(f"/api/dreams/{dream['id']}/plan")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "in_progress"
    assert body["plan"][0]["step"] == "Download Duolingo"
    assert body["resource_hints"] == ["Could be handy: a phrasebook."]


def test_resources_endpoint_full_search(client, monkeypatch):
    dream = _make_dream(monkeypatch)
    need_response = json.dumps(
        [{"resource": "App", "why": "practice", "search_query": "best spanish app"}]
    )
    fake_options = [{"title": "Duolingo", "url": "https://example.com", "snippet": "free app"}]
    calls = {"n": 0}

    def fake_chat(messages, **kw):
        calls["n"] += 1
        return need_response if calls["n"] == 1 else "Use Duolingo — it's free."

    monkeypatch.setattr(resources, "chat", fake_chat)
    monkeypatch.setattr(resources, "search", lambda query, max_results=5: fake_options)

    resp = client.post(f"/api/dreams/{dream['id']}/resources")
    assert resp.status_code == 200
    body = resp.json()["resources"]
    assert body[0]["resource"] == "App"
    assert body[0]["options"] == fake_options


def test_patch_step_marks_done_and_updates_status(client, monkeypatch):
    dream = _make_dream(monkeypatch)
    dream["plan"] = [{"step": "Do X", "needs_internet": False, "done": False, "notes": ""}]
    store.update_dream(dream)

    resp = client.patch(f"/api/dreams/{dream['id']}/steps/1", json={"done": True})
    assert resp.status_code == 200
    body = resp.json()
    assert body["plan"][0]["done"] is True
    assert body["status"] == "done"

    resp = client.patch(f"/api/dreams/{dream['id']}/steps/1", json={"done": False})
    assert resp.status_code == 200
    body = resp.json()
    assert body["plan"][0]["done"] is False
    assert body["status"] == "in_progress"


def test_patch_step_out_of_range_returns_400(client, monkeypatch):
    dream = _make_dream(monkeypatch)
    resp = client.patch(f"/api/dreams/{dream['id']}/steps/1", json={"done": True})
    assert resp.status_code == 400


def test_reflect_endpoint(client, monkeypatch):
    dream = _make_dream(monkeypatch)
    monkeypatch.setattr(reflector, "chat", lambda messages, **kw: "Keep going, you're on track.")

    resp = client.post(f"/api/dreams/{dream['id']}/reflect")
    assert resp.status_code == 200
    body = resp.json()
    assert body["text"] == "Keep going, you're on track."
    assert body["dream"]["reflections"][-1]["text"] == "Keep going, you're on track."


def test_projection_endpoint(client, monkeypatch):
    dream = _make_dream(monkeypatch)
    projection_response = json.dumps(
        {
            "time_estimate": "2-3 months",
            "cost_estimate": "$20-40",
            "lead_measures": ["Minutes practiced per day"],
            "lag_measures": ["Conversation fluency check-in"],
        }
    )
    monkeypatch.setattr(projections, "chat", lambda messages, **kw: projection_response)

    resp = client.post(f"/api/dreams/{dream['id']}/projection")
    assert resp.status_code == 200
    body = resp.json()["projection"]
    assert body["time_estimate"] == "2-3 months"
    assert body["lead_measures"] == ["Minutes practiced per day"]

    fetched = client.get(f"/api/dreams/{dream['id']}").json()
    assert fetched["projection"]["cost_estimate"] == "$20-40"


def test_projection_endpoint_unknown_dream_returns_404(client):
    resp = client.post("/api/dreams/doesnotexist/projection")
    assert resp.status_code == 404


def test_build_endpoint_starts_job_then_polling_reports_done(client, monkeypatch, tmp_path):
    dream = _make_dream(monkeypatch)
    monkeypatch.setattr(executor.shutil, "which", lambda name: "/usr/bin/claude")

    class FakeResult:
        returncode = 0

    def fake_run(cmd, cwd, check, stdout=None, stderr=None):
        stdout.write("done building\n")
        return FakeResult()

    monkeypatch.setattr(executor.subprocess, "run", fake_run)

    target_dir = tmp_path / "built"
    resp = client.post(f"/api/dreams/{dream['id']}/build", json={"dir": str(target_dir)})
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    for _ in range(50):
        status = client.get(f"/api/builds/{job_id}").json()
        if status["status"] != "running":
            break
        time.sleep(0.05)

    assert status["status"] == "done"
    assert "done building" in status["log"]


def test_build_endpoint_reports_error_status(client, monkeypatch, tmp_path):
    dream = _make_dream(monkeypatch)
    monkeypatch.setattr(executor.shutil, "which", lambda name: None)

    target_dir = tmp_path / "built"
    resp = client.post(f"/api/dreams/{dream['id']}/build", json={"dir": str(target_dir)})
    job_id = resp.json()["job_id"]

    for _ in range(50):
        status = client.get(f"/api/builds/{job_id}").json()
        if status["status"] != "running":
            break
        time.sleep(0.05)

    assert status["status"] == "error"
    assert "isn't on your PATH" in status["error"]


def test_unknown_build_job_returns_404(client):
    resp = client.get("/api/builds/doesnotexist")
    assert resp.status_code == 404
