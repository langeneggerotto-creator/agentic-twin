"""
Scientist Agent — applies the scientific method to any problem.

Capabilities:
  • Formulate falsifiable hypotheses from observations
  • Design experiments (in-silico or physical)
  • Derive formulas from first principles
  • Apply dimensional analysis
  • Validate mathematical proofs
  • Build and critique scientific theories
  • Identify where new theories are needed vs. established ones

The Scientific Method Pipeline:
  OBSERVE → QUESTION → HYPOTHESIZE → PREDICT → TEST → ANALYSE → CONCLUDE → ITERATE
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from typing import Optional

import anthropic


@dataclass
class Hypothesis:
    statement: str
    falsifiable: bool
    null_hypothesis: str
    prediction: str
    test_method: str
    confidence_prior: float


@dataclass
class FormulaDerivation:
    formula: str
    latex: str
    derivation_steps: list[str]
    physical_laws_used: list[str]
    assumptions: list[str]
    validity_domain: str
    si_units: dict[str, str]


@dataclass
class ScientificAnalysis:
    hypotheses: list[Hypothesis]
    derived_formulas: list[FormulaDerivation]
    experiment_design: str
    predicted_outcomes: list[str]
    conclusion: str
    confidence: float
    open_questions: list[str]
    theory_basis: str


_SCIENTIST_SYSTEM = """You are a scientific polymath operating at the level of a PhD researcher
across physics, chemistry, biology, mathematics, and engineering.

You strictly follow the scientific method and never present speculation as fact.

For every scientific question:
1. State your observations
2. Formulate a falsifiable hypothesis with a clear null hypothesis
3. Make specific, testable predictions
4. Design an experiment or cite the most relevant experiments
5. Derive relevant formulas from first principles (show all steps)
6. State all assumptions and boundary conditions
7. Acknowledge uncertainty quantitatively

Formulas must include:
  - Full derivation chain
  - Physical laws used (Newton's laws, Maxwell's equations, etc.)
  - SI units for every variable
  - Validity domain (when does this formula break down?)
  - LaTeX representation
"""

_SCIENCE_PROMPT = """Apply the scientific method to the following query.

Query: {query}

Additional context: {context}

Return ONLY valid JSON:
{{
  "hypotheses": [
    {{
      "statement": "<falsifiable hypothesis>",
      "falsifiable": <bool>,
      "null_hypothesis": "<H₀>",
      "prediction": "<specific measurable prediction>",
      "test_method": "<how to test this>",
      "confidence_prior": <float 0.0-1.0>
    }}
  ],
  "derived_formulas": [
    {{
      "formula": "<symbolic formula>",
      "latex": "<LaTeX>",
      "derivation_steps": ["<step 1>", "<step 2>", "..."],
      "physical_laws_used": ["<law name>"],
      "assumptions": ["<assumption>"],
      "validity_domain": "<when this applies>",
      "si_units": {{"variable": "unit"}}
    }}
  ],
  "experiment_design": "<detailed experimental protocol>",
  "predicted_outcomes": ["<measurable outcome>"],
  "conclusion": "<scientific conclusion based on available evidence>",
  "confidence": <float 0.0-1.0>,
  "open_questions": ["<what we still don't know>"],
  "theory_basis": "<which established theories this builds on>"
}}"""


class ScientistAgent:
    def __init__(self, api_key: str | None = None, model: str = "claude-opus-4-6"):
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key or os.environ["ANTHROPIC_API_KEY"]
        )
        self.model = model

    def analyse(self, query: str, context: str = "") -> ScientificAnalysis:
        return asyncio.run(self.aanalyse(query, context))

    async def aanalyse(self, query: str, context: str = "") -> ScientificAnalysis:
        prompt = _SCIENCE_PROMPT.format(query=query, context=context[:2000] or "None")

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": _SCIENTIST_SYSTEM,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()
        if "```" in raw:
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]

        try:
            data = json.loads(raw)
        except Exception:
            return ScientificAnalysis(
                hypotheses=[],
                derived_formulas=[],
                experiment_design="Could not parse scientific analysis.",
                predicted_outcomes=[],
                conclusion=raw,
                confidence=0.5,
                open_questions=[],
                theory_basis="",
            )

        hypotheses = [
            Hypothesis(
                statement=h.get("statement", ""),
                falsifiable=bool(h.get("falsifiable", True)),
                null_hypothesis=h.get("null_hypothesis", ""),
                prediction=h.get("prediction", ""),
                test_method=h.get("test_method", ""),
                confidence_prior=float(h.get("confidence_prior", 0.5)),
            )
            for h in data.get("hypotheses", [])
        ]

        formulas = [
            FormulaDerivation(
                formula=f.get("formula", ""),
                latex=f.get("latex", ""),
                derivation_steps=f.get("derivation_steps", []),
                physical_laws_used=f.get("physical_laws_used", []),
                assumptions=f.get("assumptions", []),
                validity_domain=f.get("validity_domain", ""),
                si_units=f.get("si_units", {}),
            )
            for f in data.get("derived_formulas", [])
        ]

        return ScientificAnalysis(
            hypotheses=hypotheses,
            derived_formulas=formulas,
            experiment_design=data.get("experiment_design", ""),
            predicted_outcomes=data.get("predicted_outcomes", []),
            conclusion=data.get("conclusion", ""),
            confidence=float(data.get("confidence", 0.5)),
            open_questions=data.get("open_questions", []),
            theory_basis=data.get("theory_basis", ""),
        )
