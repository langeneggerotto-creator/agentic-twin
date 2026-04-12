# Agentic Twin — AI Validation Layer

An advanced **Digital Twin** that sits on top of any AI and operates as a
validation, correction, and enhancement layer. Every output is fact-checked,
scientifically grounded, architecturally sound, and iteratively corrected until
it meets a configurable confidence threshold.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DIGITAL TWIN                             │
│                                                                 │
│  User Query ──► Mode Detection ──► Primary Generation           │
│                        │                                        │
│                        ▼                                        │
│              ┌─────────────────┐                                │
│              │  TRUTH ENGINE   │ ◄── claim extraction           │
│              │  truth scoring  │     hallucination detection     │
│              └────────┬────────┘                                │
│                       │                                         │
│                       ▼                                         │
│           ┌──────────────────────┐                              │
│           │  CORRECTION ENGINE   │ ◄── surgical rewrites        │
│           │  (up to N rounds)    │     error fixing             │
│           └──────────┬───────────┘                              │
│                      │                                          │
│                      ▼                                          │
│         ┌────────────────────────┐                              │
│         │   VALIDATION LAYER     │                              │
│         │  6 independent layers: │                              │
│         │  • Factual Accuracy    │                              │
│         │  • Logic Consistency   │                              │
│         │  • Source Reliability  │                              │
│         │  • Mathematical Check  │                              │
│         │  • Code Quality        │                              │
│         │  • Completeness        │                              │
│         └────────────┬───────────┘                              │
│                      │                                          │
│                      ▼                                          │
│         Validated Response + Confidence Scores                  │
└─────────────────────────────────────────────────────────────────┘
```

### Specialist Agents

| Agent | Role |
|-------|------|
| `ValidatorAgent` | Validates any AI output, grades it A–F |
| `ResearcherAgent` | Evidence-based research validation (OCEBM levels) |
| `ScientistAgent` | Full scientific method: hypotheses → formulas → experiments |
| `ArchitectAgent` | System design review with SOLID, CAP, 12-factor |
| `ImageOrchestrator` | Multiplayer image generation with label accuracy |

### Science Module

| Module | Capability |
|--------|-----------|
| `FormulaEngine` | First-principles derivation with dimensional analysis |
| `HypothesisTester` | Rigorous H₀/H₁ design, power analysis, confounders |
| `TheoryBuilder` | Construct and evaluate scientific theories |

### Image Module

| Module | Capability |
|--------|-----------|
| `GenerationHub` | Multiplayer prompts from 4 expert personas → consensus |
| `LabelValidator` | Validates terminology and spatial accuracy of labels |
| `DescriptionEngine` | Alt-text, figure legends, technical captions |

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set API key

```bash
export ANTHROPIC_API_KEY=your_key_here
```

### 3. CLI usage

```bash
# Auto-mode: Twin detects the best mode
python runner/twin_runner.py "Explain how black holes evaporate via Hawking radiation"

# Science mode: Derive formula from first principles
python runner/twin_runner.py --mode science "Derive the relativistic kinetic energy formula"

# Image mode: Multiplayer image generation
python runner/twin_runner.py --mode image "A human heart with all four chambers labelled"

# Architecture mode: System design review
python runner/twin_runner.py --mode architect "Design a real-time chat system for 10 million users"

# Validate existing AI output
python runner/twin_runner.py --validate "The speed of light is approximately 300,000 km/s"

# Start the REST API server
python runner/twin_runner.py --server
```

### 4. REST API

```bash
# Start server
uvicorn api.server:app --reload --port 8080

# Open interactive docs
open http://localhost:8080/docs
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/twin/health` | Health check |
| `POST` | `/twin/process` | Full Digital Twin pipeline |
| `POST` | `/twin/validate` | Validate existing AI output |
| `POST` | `/twin/research` | Research validation (OCEBM) |
| `POST` | `/twin/science` | Full scientific method |
| `POST` | `/twin/science/formula` | Derive formula from first principles |
| `POST` | `/twin/science/hypothesis` | Design hypothesis test |
| `POST` | `/twin/science/theory` | Build/evaluate scientific theory |
| `POST` | `/twin/architect` | Architecture review |
| `POST` | `/twin/image/generate` | Multiplayer image generation |
| `POST` | `/twin/image/describe` | Scene description + alt-text |
| `POST` | `/twin/image/labels` | Validate image labels |

---

## Response Structure

Every `/twin/process` response includes:

```json
{
  "original_query": "...",
  "final_output": "...",
  "corrections_made": ["..."],
  "overall_confidence": 0.92,
  "truth_score": 0.95,
  "accuracy_score": 0.89,
  "layer_scores": [
    {"layer": "Factual Accuracy", "score": 0.95, "passed": true, "notes": "..."},
    {"layer": "Mathematical Correctness", "score": 0.98, "passed": true, "notes": "..."}
  ],
  "scientific_basis": "...",
  "derived_formulas": ["E = mc²", "..."],
  "image_prompts": ["..."],
  "warnings": [],
  "processing_rounds": 1,
  "mode_used": "science",
  "latency_ms": 3421.0
}
```

---

## Configuration

### `vault/truth_charter.json`
Governs truth validation rules — confidence thresholds, hallucination flags,
and the 8 truth rules (TR-001 through TR-008).

### `vault/scientific_canon.json`
Scientific method requirements — evidence hierarchy, formula standards,
domain authorities, and statistical minimums.

### `vault/canon.json`
Code quality and governance rules (existing).

### `vault/vision.json`
Project vision and constraints (existing).

---

## Project Structure

```
agentic-twin/
├── core/                      # Digital Twin heart
│   ├── digital_twin.py        # Main orchestrator
│   ├── validation_layer.py    # 6-layer validation pipeline
│   ├── truth_engine.py        # Claim extraction + truth scoring
│   └── correction_engine.py   # Surgical error correction
├── agents/                    # Specialist agents
│   ├── validator_agent.py     # Output quality validator
│   ├── researcher_agent.py    # Research validation (OCEBM)
│   ├── scientist_agent.py     # Scientific method engine
│   ├── architect_agent.py     # Architecture reviewer
│   └── image_orchestrator.py # Multiplayer image generation
├── science/                   # Science module
│   ├── formula_engine.py      # First-principles derivation
│   ├── hypothesis_tester.py   # Hypothesis test design
│   └── theory_builder.py      # Theory construction
├── image/                     # Image module
│   ├── generation_hub.py      # Multiplayer generation coordinator
│   ├── label_validator.py     # Label accuracy validation
│   └── description_engine.py  # Scene descriptions + alt-text
├── api/
│   └── server.py              # FastAPI REST server
├── governance/
│   └── gatekeeper.py          # Code compliance enforcement
├── runner/
│   ├── controller.py          # Original pipeline runner
│   └── twin_runner.py         # Digital Twin CLI runner
├── vault/
│   ├── vision.json            # Project vision
│   ├── canon.json             # Code quality rules
│   ├── truth_charter.json     # Truth validation rules
│   └── scientific_canon.json  # Scientific method rules
└── outputs/                   # Generated artefacts
```

---

## Design Principles

1. **Truth First** — No claim passes without a confidence score. Uncertain claims are flagged, not suppressed.
2. **Scientific Method** — Every answer involving facts or formulas goes through observe → hypothesize → test → conclude.
3. **Iterative Correction** — The Twin loops up to N times, correcting errors on each pass, until the confidence threshold is met.
4. **Multiplayer Consensus** — Image generation uses multiple expert personas in parallel; the highest-accuracy prompt wins.
5. **Transparent Scoring** — Every response includes layer-by-layer scores so users know exactly why a confidence level was assigned.
6. **Prompt Caching** — All system prompts use Anthropic's prompt caching for efficiency.
