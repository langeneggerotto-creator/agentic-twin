# agentic-twin
My self-learning Agentic AI Digital Twin system.

## Dream Builder

A local-first personal goal/project planner. It runs on an LLM on your own
PC (via [Ollama](https://ollama.com)) and only reaches out to the internet
for the specific lookups a plan needs — finding real, current, low-cost/
high-value resources (courses, tools, equipment, communities, funding) for
whatever you're trying to achieve.

### Setup

```bash
# 1. Install Ollama and pull a model that fits an 8GB+ GPU well
ollama pull llama3.1:8b

# 2. Install Python deps
pip install -r requirements.txt

# 3. Make sure Ollama is running
ollama serve
```

Override the model or host with env vars if needed:

```bash
export DREAM_BUILDER_MODEL=qwen2.5:7b-instruct
export OLLAMA_HOST=http://localhost:11434
```

### Usage

```bash
# Add a goal (immediately prints a few light, suggestive
# resource hints to help narrow down the goal's scope)
python -m dream_builder.cli add "Learn Spanish" "Be conversational within 6 months"

# List your dreams (note the id it prints)
python -m dream_builder.cli list

# Generate a concrete action plan
python -m dream_builder.cli plan <id>

# Find real resources for it (lowest cost, highest value)
python -m dream_builder.cli resources <id>

# Project how long it might take and what it might cost, plus lead/lag
# measures to track progress (lead = behaviors you control that predict
# progress, lag = outcomes that confirm you're getting there)
python -m dream_builder.cli project <id>

# Mark a step done, check overall status, get an honest reflection
python -m dream_builder.cli done <id> 1
python -m dream_builder.cli show <id>
python -m dream_builder.cli reflect <id>

# One-off web search
python -m dream_builder.cli lookup "beginner acoustic guitar under $100"

# Have Claude Code actually implement the plan as a real project
python -m dream_builder.cli build <id>

# Run the local web UI instead of the CLI
python -m dream_builder.cli serve
# -> open http://127.0.0.1:8000
```

### Web UI

`serve` runs a local FastAPI app (`dream_builder/webapp/`) that's a thin
layer over the same store/planner/resources/reflector/executor code the
CLI uses — no separate logic, no account, no auth (single local user). It
lets you add dreams, see resource hints, generate plans, mark steps done,
run the full resource search, get time/cost projections and lead/lag
measures, get reflections, and trigger `build` (with its output streamed
to a log you can watch from the page) all from the browser instead of the
terminal.

Goals are stored locally in `vault/dreams.json`. Nothing leaves your
machine except the specific web searches a plan or resource lookup needs —
**except `build`**, which is a deliberate exception: it hands your plan and
resources to a separate `claude` CLI (Claude Code) to actually scaffold and
write the project, which does call Anthropic's API. Requires Claude Code
installed and logged in (https://claude.com/code) separately from Ollama.
It defaults to `--permission-mode acceptEdits` (file writes auto-accepted,
everything else still gated) rather than bypassing permissions, since this
runs against your real machine. Output goes to `builds/<id>-<slug>/` unless
you pass `--dir`.

Run the test suite (no Ollama or network required — the LLM and search
calls are mocked):

```bash
python -m pytest dream_builder/tests
```
