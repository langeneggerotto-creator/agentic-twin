import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dream_builder import (
    executor,
    planner,
    projections,
    reflector,
    resources,
    scaling,
    service,
    store,
)
from dream_builder.util import extract_json_array, extract_json_object


def test_extract_json_array_parses_embedded_array():
    text = 'Sure, here you go:\n```json\n[{"a": 1}]\n```\nHope that helps.'
    assert extract_json_array(text) == [{"a": 1}]


def test_extract_json_array_raises_without_array():
    try:
        extract_json_array("no json here")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_extract_json_object_parses_embedded_object():
    text = 'Sure, here you go:\n```json\n{"a": 1}\n```\nHope that helps.'
    assert extract_json_object(text) == {"a": 1}


def test_extract_json_object_raises_without_object():
    try:
        extract_json_object("no json here")
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


def test_suggest_resources_stores_hints_without_touching_resources(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DREAMS_PATH", tmp_path / "dreams.json")
    dream = store.create_dream("Learn guitar", "Play basic songs within 3 months")

    hints_response = json.dumps(
        [
            {"pitch": "This could be handy for your dream: a cheap starter guitar."},
            {"pitch": "Worth peeking at: local community music classes."},
        ]
    )
    monkeypatch.setattr(resources, "chat", lambda messages, **kw: hints_response)

    pitches = resources.suggest_resources(dream)

    assert pitches == [
        "This could be handy for your dream: a cheap starter guitar.",
        "Worth peeking at: local community music classes.",
    ]
    assert dream["resources"] == []
    fetched = store.get_dream(dream["id"])
    assert fetched["resource_hints"] == pitches
    assert fetched["resources"] == []


def test_suggest_resources_includes_plan_context(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DREAMS_PATH", tmp_path / "dreams.json")
    dream = store.create_dream("Learn guitar", "Play basic songs within 3 months")
    dream["plan"] = [{"step": "Buy a cheap acoustic guitar", "needs_internet": True, "done": False, "notes": ""}]

    captured = {}

    def fake_chat(messages, **kw):
        captured["messages"] = messages
        return json.dumps([{"pitch": "This could be handy: a tuner app."}])

    monkeypatch.setattr(resources, "chat", fake_chat)

    resources.suggest_resources(dream)

    user_message = captured["messages"][1]["content"]
    assert "Buy a cheap acoustic guitar" in user_message


def test_service_create_dream_with_hints_calls_both(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DREAMS_PATH", tmp_path / "dreams.json")
    monkeypatch.setattr(
        resources, "chat", lambda messages, **kw: json.dumps([{"pitch": "Could be handy: X."}])
    )

    dream = service.create_dream_with_hints("Run a 5k", "Finish under 30 minutes")

    assert dream["title"] == "Run a 5k"
    assert dream["resource_hints"] == ["Could be handy: X."]
    assert store.get_dream(dream["id"])["resource_hints"] == ["Could be handy: X."]


def test_service_plan_dream_calls_both(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DREAMS_PATH", tmp_path / "dreams.json")
    dream = store.create_dream("Run a 5k", "Finish under 30 minutes")

    plan_response = json.dumps([{"step": "Start a couch-to-5k program", "needs_internet": False}])
    hints_response = json.dumps([{"pitch": "Could be handy: a running app."}])
    monkeypatch.setattr(planner, "chat", lambda messages, **kw: plan_response)
    monkeypatch.setattr(resources, "chat", lambda messages, **kw: hints_response)

    service.plan_dream(dream)

    assert dream["status"] == "in_progress"
    assert len(dream["plan"]) == 1
    assert dream["resource_hints"] == ["Could be handy: a running app."]


def test_reflect_appends_reflection(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DREAMS_PATH", tmp_path / "dreams.json")
    dream = store.create_dream("Write a book", "Finish a first draft")
    dream["plan"] = [{"step": "Outline chapters", "needs_internet": False, "done": True, "notes": ""}]
    store.update_dream(dream)

    monkeypatch.setattr(reflector, "chat", lambda messages, **kw: "Good start — keep drafting daily.")

    text = reflector.reflect(dream)

    assert text == "Good start — keep drafting daily."
    assert store.get_dream(dream["id"])["reflections"][0]["text"] == text


def test_project_dream_stores_projection(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DREAMS_PATH", tmp_path / "dreams.json")
    dream = store.create_dream("Run a marathon", "Finish under 5 hours")
    dream["plan"] = [{"step": "Follow a couch-to-marathon plan", "needs_internet": False, "done": False, "notes": ""}]
    store.update_dream(dream)

    projection_response = json.dumps(
        {
            "time_estimate": "4-6 months at 4 runs/week",
            "cost_estimate": "$50-150 for shoes and a race entry fee",
            "lead_measures": ["Runs completed per week", "Weekly mileage logged"],
            "lag_measures": ["5k time trial result", "Longest training run distance"],
        }
    )
    monkeypatch.setattr(projections, "chat", lambda messages, **kw: projection_response)

    result = projections.project_dream(dream)

    assert result["time_estimate"] == "4-6 months at 4 runs/week"
    assert result["cost_estimate"] == "$50-150 for shoes and a race entry fee"
    assert result["lead_measures"] == ["Runs completed per week", "Weekly mileage logged"]
    assert result["lag_measures"] == ["5k time trial result", "Longest training run distance"]
    assert "generated_at" in result

    fetched = store.get_dream(dream["id"])
    assert fetched["projection"]["time_estimate"] == "4-6 months at 4 runs/week"


def test_project_dream_retries_once_on_malformed_json(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DREAMS_PATH", tmp_path / "dreams.json")
    dream = store.create_dream("Run a marathon", "Finish under 5 hours")

    valid_response = json.dumps(
        {"time_estimate": "5 months", "cost_estimate": "$100", "lead_measures": [], "lag_measures": []}
    )
    calls = {"n": 0}

    def flaky_chat(messages, **kw):
        calls["n"] += 1
        return "{not valid json" if calls["n"] == 1 else valid_response

    monkeypatch.setattr(projections, "chat", flaky_chat)

    result = projections.project_dream(dream)

    assert calls["n"] == 2
    assert result["time_estimate"] == "5 months"


def test_project_dream_flattens_non_string_estimates(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DREAMS_PATH", tmp_path / "dreams.json")
    dream = store.create_dream("Build a side hustle", "Make extra income")

    projection_response = json.dumps(
        {
            "time_estimate": {"research phase": "40 hours", "launch phase": "80 hours"},
            "cost_estimate": {"tools": "$500/year"},
            "lead_measures": [{"weekly hours": "10 hours/week"}],
            "lag_measures": ["Monthly revenue"],
        }
    )
    monkeypatch.setattr(projections, "chat", lambda messages, **kw: projection_response)

    result = projections.project_dream(dream)

    assert result["time_estimate"] == "research phase: 40 hours; launch phase: 80 hours"
    assert result["cost_estimate"] == "tools: $500/year"
    assert result["lead_measures"] == ["weekly hours: 10 hours/week"]
    assert result["lag_measures"] == ["Monthly revenue"]


def test_project_dream_includes_plan_and_resources_context(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DREAMS_PATH", tmp_path / "dreams.json")
    dream = store.create_dream("Run a marathon", "Finish under 5 hours")
    dream["plan"] = [{"step": "Buy running shoes", "needs_internet": True, "done": False, "notes": ""}]
    dream["resources"] = [{"resource": "Running shoes", "why": "comfort", "recommendation": "Get Brooks Ghost, ~$130."}]
    store.update_dream(dream)

    captured = {}

    def fake_chat(messages, **kw):
        captured["messages"] = messages
        return json.dumps(
            {"time_estimate": "x", "cost_estimate": "y", "lead_measures": [], "lag_measures": []}
        )

    monkeypatch.setattr(projections, "chat", fake_chat)

    projections.project_dream(dream)

    user_message = captured["messages"][1]["content"]
    assert "Buy running shoes" in user_message
    assert "Brooks Ghost" in user_message


def test_plan_scaling_stores_funding_and_scaling_plan(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DREAMS_PATH", tmp_path / "dreams.json")
    dream = store.create_dream("Build a niche micro-SaaS", "Solve one problem for a paying niche")

    scaling_response = json.dumps(
        {
            "funding_strategy": "Bootstrap with pre-sales to 5 committed customers before writing code.",
            "scaling_strategy": "Grow through the niche's existing communities, then add a second channel once retention is proven.",
            "funding_milestones": ["$0-500: validate with pre-sales", "$500-2000: cover hosting + tools for 6 months"],
            "scaling_lead_measures": ["Number of validation conversations per week"],
            "scaling_lag_measures": ["Paying customers", "Monthly recurring revenue"],
        }
    )
    monkeypatch.setattr(scaling, "chat", lambda messages, **kw: scaling_response)

    result = scaling.plan_scaling(dream)

    assert result["funding_strategy"].startswith("Bootstrap with pre-sales")
    assert result["funding_milestones"] == [
        "$0-500: validate with pre-sales",
        "$500-2000: cover hosting + tools for 6 months",
    ]
    assert result["scaling_lead_measures"] == ["Number of validation conversations per week"]
    assert result["scaling_lag_measures"] == ["Paying customers", "Monthly recurring revenue"]
    assert "generated_at" in result

    fetched = store.get_dream(dream["id"])
    assert fetched["scaling"]["scaling_strategy"].startswith("Grow through the niche's")


def test_plan_scaling_retries_once_on_malformed_json(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DREAMS_PATH", tmp_path / "dreams.json")
    dream = store.create_dream("Build a niche micro-SaaS", "Solve one problem for a paying niche")

    valid_response = json.dumps(
        {
            "funding_strategy": "x",
            "scaling_strategy": "y",
            "funding_milestones": [],
            "scaling_lead_measures": [],
            "scaling_lag_measures": [],
        }
    )
    calls = {"n": 0}

    def flaky_chat(messages, **kw):
        calls["n"] += 1
        return "{not valid json" if calls["n"] == 1 else valid_response

    monkeypatch.setattr(scaling, "chat", flaky_chat)

    result = scaling.plan_scaling(dream)

    assert calls["n"] == 2
    assert result["funding_strategy"] == "x"


def test_plan_scaling_flattens_non_string_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DREAMS_PATH", tmp_path / "dreams.json")
    dream = store.create_dream("Build a niche micro-SaaS", "Solve one problem for a paying niche")

    scaling_response = json.dumps(
        {
            "funding_strategy": {"phase 1": "bootstrap", "phase 2": "reinvest revenue"},
            "scaling_strategy": "y",
            "funding_milestones": [],
            "scaling_lead_measures": [],
            "scaling_lag_measures": [],
        }
    )
    monkeypatch.setattr(scaling, "chat", lambda messages, **kw: scaling_response)

    result = scaling.plan_scaling(dream)

    assert result["funding_strategy"] == "phase 1: bootstrap; phase 2: reinvest revenue"


def test_plan_scaling_opts_out_for_personal_goals(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DREAMS_PATH", tmp_path / "dreams.json")
    dream = store.create_dream("Learn Spanish", "Be conversational within 6 months")

    scaling_response = json.dumps(
        {
            "funding_strategy": "This is a personal skill goal — no funding is needed.",
            "scaling_strategy": "Scaling doesn't apply here; consider tutoring others once fluent, if desired.",
            "funding_milestones": [],
            "scaling_lead_measures": [],
            "scaling_lag_measures": [],
        }
    )
    monkeypatch.setattr(scaling, "chat", lambda messages, **kw: scaling_response)

    result = scaling.plan_scaling(dream)

    assert "no funding is needed" in result["funding_strategy"]


def test_build_with_claude_code_raises_without_binary(tmp_path, monkeypatch):
    dream = {"title": "x", "description": "y", "plan": [], "resources": []}
    monkeypatch.setattr(executor.shutil, "which", lambda name: None)

    try:
        executor.build_with_claude_code(dream, tmp_path / "out")
        assert False, "expected ClaudeCodeError"
    except executor.ClaudeCodeError as e:
        assert "isn't on your PATH" in str(e)


def test_build_with_claude_code_invokes_claude(tmp_path, monkeypatch):
    dream = {
        "title": "Build a thing",
        "description": "A useful thing",
        "plan": [{"step": "Do X", "needs_internet": False, "done": False, "notes": ""}],
        "resources": [{"resource": "A tool", "recommendation": "Use tool Y"}],
    }
    monkeypatch.setattr(executor.shutil, "which", lambda name: "/usr/bin/claude")

    captured = {}

    class FakeResult:
        returncode = 0

    def fake_run(cmd, cwd, check):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        return FakeResult()

    monkeypatch.setattr(executor.subprocess, "run", fake_run)

    target = tmp_path / "out"
    result = executor.build_with_claude_code(dream, target, permission_mode="acceptEdits")

    assert result == target
    assert target.exists()
    assert captured["cmd"][0] == "claude"
    assert "--permission-mode" in captured["cmd"]
    assert "acceptEdits" in captured["cmd"]
    assert "Build a thing" in captured["cmd"][2]
    assert "Do X" in captured["cmd"][2]
    assert "Use tool Y" in captured["cmd"][2]
    assert captured["cwd"] == target


def test_build_with_claude_code_raises_on_nonzero_exit(tmp_path, monkeypatch):
    dream = {"title": "x", "description": "y", "plan": [], "resources": []}
    monkeypatch.setattr(executor.shutil, "which", lambda name: "/usr/bin/claude")

    class FakeResult:
        returncode = 1

    monkeypatch.setattr(executor.subprocess, "run", lambda cmd, cwd, check: FakeResult())

    try:
        executor.build_with_claude_code(dream, tmp_path / "out")
        assert False, "expected ClaudeCodeError"
    except executor.ClaudeCodeError as e:
        assert "exited with code 1" in str(e)


def test_build_with_claude_code_writes_log_when_log_path_given(tmp_path, monkeypatch):
    dream = {"title": "Build a thing", "description": "y", "plan": [], "resources": []}
    monkeypatch.setattr(executor.shutil, "which", lambda name: "/usr/bin/claude")

    class FakeResult:
        returncode = 0

    def fake_run(cmd, cwd, check, stdout=None, stderr=None):
        stdout.write("scaffolding project...\ndone.\n")
        return FakeResult()

    monkeypatch.setattr(executor.subprocess, "run", fake_run)

    log_path = tmp_path / "out" / ".dream_builder_build.log"
    result = executor.build_with_claude_code(dream, tmp_path / "out", log_path=log_path)

    assert result == tmp_path / "out"
    assert log_path.read_text() == "scaffolding project...\ndone.\n"
