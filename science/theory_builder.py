"""
Theory Builder — constructs, evaluates, and extends scientific theories.

A scientific theory (in the technical sense) is:
  • Explanatory: accounts for a set of phenomena
  • Predictive: makes testable predictions
  • Falsifiable: can in principle be shown to be wrong
  • Consistent: internally free of contradiction
  • Parsimonious: minimal assumptions (Occam's Razor)
  • Supported: backed by empirical evidence

This module builds new theories, critiques existing ones, and identifies
where existing theory is insufficient (new theory needed).
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from typing import Optional

import anthropic


@dataclass
class TheoreticalPrediction:
    prediction: str
    testable: bool
    test_method: str
    falsification_condition: str


@dataclass
class ScientificTheory:
    name: str
    domain: str
    core_postulates: list[str]          # fundamental assumptions
    explanatory_scope: str              # what phenomena it explains
    predictions: list[TheoreticalPrediction]
    supporting_evidence: list[str]
    contradicting_evidence: list[str]
    mathematical_framework: str
    key_equations: list[str]
    relationship_to_existing_theories: str
    limitations: list[str]
    open_problems: list[str]
    falsification_test: str             # the single most decisive test
    confidence_level: float
    maturity: str                       # speculative / developing / established / paradigm


_THEORY_SYSTEM = """You are a theoretical scientist with expertise in building, evaluating,
and extending scientific theories across all disciplines.

You construct theories that are:
  1. Explanatory — account for observed phenomena
  2. Predictive — make testable, novel predictions
  3. Falsifiable — have clear conditions under which they'd be wrong
  4. Parsimonious — minimal assumptions
  5. Mathematically formulated where possible
  6. Consistent with established physics/chemistry/biology

You also identify when:
  • An existing theory needs extension
  • Multiple theories need unification
  • A genuine theoretical gap exists
  • A proposed theory is unfalsifiable (pseudoscience)
"""

_THEORY_PROMPT = """Build or evaluate a scientific theory for:

Topic: {topic}
Observed phenomena to explain: {phenomena}
Existing related theories: {existing}

Return ONLY valid JSON:
{{
  "name": "<theory name>",
  "domain": "<scientific domain>",
  "core_postulates": ["<fundamental axiom or assumption>"],
  "explanatory_scope": "<what phenomena this theory explains>",
  "predictions": [
    {{
      "prediction": "<specific, measurable prediction>",
      "testable": <bool>,
      "test_method": "<how to test it>",
      "falsification_condition": "<what result would falsify the theory>"
    }}
  ],
  "supporting_evidence": ["<evidence that supports this theory>"],
  "contradicting_evidence": ["<evidence that challenges this theory>"],
  "mathematical_framework": "<mathematical structure or formalism>",
  "key_equations": ["<equation: description>"],
  "relationship_to_existing_theories": "<how this relates to / extends / conflicts with known theories>",
  "limitations": ["<boundary condition or limitation>"],
  "open_problems": ["<unresolved question within the theory>"],
  "falsification_test": "<the single most decisive experiment that would falsify this>",
  "confidence_level": <float 0.0-1.0>,
  "maturity": "<speculative|developing|established|paradigm>"
}}"""


class TheoryBuilder:
    def __init__(self, api_key: str | None = None, model: str = "claude-opus-4-6"):
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key or os.environ["ANTHROPIC_API_KEY"]
        )
        self.model = model

    def build(
        self,
        topic: str,
        phenomena: str = "",
        existing_theories: str = "",
    ) -> ScientificTheory:
        return asyncio.run(self.abuild(topic, phenomena, existing_theories))

    async def abuild(
        self,
        topic: str,
        phenomena: str = "",
        existing_theories: str = "",
    ) -> ScientificTheory:
        prompt = _THEORY_PROMPT.format(
            topic=topic,
            phenomena=phenomena[:1500] or "General phenomena in this domain",
            existing=existing_theories[:1000] or "Standard physics / chemistry / biology",
        )

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": _THEORY_SYSTEM,
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
            return ScientificTheory(
                name=topic,
                domain="",
                core_postulates=[],
                explanatory_scope="",
                predictions=[],
                supporting_evidence=[],
                contradicting_evidence=[],
                mathematical_framework="",
                key_equations=[],
                relationship_to_existing_theories="",
                limitations=[],
                open_problems=[],
                falsification_test="",
                confidence_level=0.5,
                maturity="speculative",
            )

        predictions = [
            TheoreticalPrediction(
                prediction=p.get("prediction", ""),
                testable=bool(p.get("testable", True)),
                test_method=p.get("test_method", ""),
                falsification_condition=p.get("falsification_condition", ""),
            )
            for p in data.get("predictions", [])
        ]

        return ScientificTheory(
            name=data.get("name", topic),
            domain=data.get("domain", ""),
            core_postulates=data.get("core_postulates", []),
            explanatory_scope=data.get("explanatory_scope", ""),
            predictions=predictions,
            supporting_evidence=data.get("supporting_evidence", []),
            contradicting_evidence=data.get("contradicting_evidence", []),
            mathematical_framework=data.get("mathematical_framework", ""),
            key_equations=data.get("key_equations", []),
            relationship_to_existing_theories=data.get("relationship_to_existing_theories", ""),
            limitations=data.get("limitations", []),
            open_problems=data.get("open_problems", []),
            falsification_test=data.get("falsification_test", ""),
            confidence_level=float(data.get("confidence_level", 0.5)),
            maturity=data.get("maturity", "speculative"),
        )
