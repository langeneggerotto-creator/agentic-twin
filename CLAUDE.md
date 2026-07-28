# agentic-twin

Self-learning agentic AI digital twin. Python.

## Active project: dream_builder

A local-first LLM goal planner (see `README.md` for setup/usage). It runs
on a model on the user's own machine via Ollama and only calls the internet
through `dream_builder/web_lookup.py` for resource lookups.

**IMPORTANT: keep it local-first.** No component outside `web_lookup.py`
should make network calls. `llm_client.py` only talks to `OLLAMA_HOST`
(default `http://localhost:11434`), never a cloud API. `executor.py` is a
deliberate, explicit exception: `dream_builder.cli build` shells out to a
separate `claude` CLI (Claude Code) to actually implement a plan as a real
project — that's an opt-in cloud step the user invokes directly, not
something the local planning/resources/reflect path does implicitly.

Commands:
- Test: `python -m pytest dream_builder/tests -q`
- Lint: `ruff check dream_builder`
- Run: `python -m dream_builder.cli <add|list|plan|resources|show|done|reflect|lookup>`

A PostToolUse hook (`.claude/settings.json`) auto-runs the test suite after
edits to `dream_builder/*.py` and reports pass/fail back into the session.

## Everything else in this repo

`agents/`, `runner/`, `governance/`, `APEX/`, and the `apex-*` consoles are
earlier/parallel experiments, mostly hardcoded scaffolds rather than live
LLM-backed systems. Don't assume conventions from one part of the repo
apply to another — check the specific directory before extending it.
