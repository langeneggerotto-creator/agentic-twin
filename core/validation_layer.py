"""
Validation Layer — multi-layer pipeline that scrutinises AI output across
six independent dimensions before it reaches the user.

Layers
──────
  1. Factual Accuracy   — are stated facts correct?
  2. Logic Consistency  — does the reasoning chain hold?
  3. Source Reliability — are cited sources credible?
  4. Mathematical       — are all calculations correct?
  5. Code Quality       — (if code) is it correct and secure?
  6. Completeness       — does it fully answer the query?
"""

import json
from dataclasses import dataclass, field
from typing import Optional

import anthropic


@dataclass
class LayerResult:
    layer: str
    score: float          # 0.0 – 1.0
    passed: bool
    issues: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class ValidationReport:
    results: list[LayerResult]
    aggregate_score: float
    warnings: list[str]
    passed: bool


_LAYER_PROMPT = """You are a precision validation engine. Evaluate the AI output below on the
dimension: **{layer}**.

Query: {query}

AI Output:
\"\"\"
{output}
\"\"\"

Score it 0.0–1.0 where:
  1.0 = perfect
  0.8 = minor issues
  0.6 = moderate issues
  0.4 = significant issues
  0.2 = major problems
  0.0 = completely wrong / missing

Return ONLY valid JSON with this exact schema:
{{
  "score": <float 0.0-1.0>,
  "passed": <bool>,
  "issues": [<string>, ...],
  "notes": "<one-sentence summary>"
}}"""

_LAYERS = {
    "Factual Accuracy": """Are all factual claims correct and verifiable? Check dates, names,
statistics, scientific facts, and any concrete assertions.""",

    "Logic Consistency": """Does the reasoning chain hold without contradictions or non-sequiturs?
Are all conclusions properly supported by preceding statements?""",

    "Source Reliability": """Are any cited sources real, credible, and relevant? Flag hallucinated
citations, paywalled sources presented as open, or low-quality sources.""",

    "Mathematical Correctness": """Verify every number, formula, unit, and calculation. Re-derive
results from scratch where possible. Flag rounding errors or dimensional inconsistencies.""",

    "Code Quality": """If code is present: check for correctness, security vulnerabilities (OWASP
Top-10), edge cases, and adherence to best practices. If no code, score 1.0.""",

    "Completeness": """Does the response fully address the query? Is nothing important omitted?
Does it satisfy the user's evident intent?""",
}

_LAYER_WEIGHTS = {
    "Factual Accuracy": 0.25,
    "Logic Consistency": 0.20,
    "Source Reliability": 0.15,
    "Mathematical Correctness": 0.20,
    "Code Quality": 0.10,
    "Completeness": 0.10,
}


class ValidationLayer:
    def __init__(self, client: anthropic.Anthropic, model: str):
        self.client = client
        self.model = model

    async def validate(self, query: str, output: str, mode: str) -> ValidationReport:
        import asyncio
        import anthropic as _anthropic

        async_client = _anthropic.AsyncAnthropic(api_key=self.client.api_key)

        # Run all layers concurrently
        tasks = [
            self._check_layer(async_client, layer_name, layer_desc, query, output)
            for layer_name, layer_desc in _LAYERS.items()
        ]
        results: list[LayerResult] = await asyncio.gather(*tasks)

        # Weighted aggregate
        aggregate = sum(
            r.score * _LAYER_WEIGHTS.get(r.layer, 0.1) for r in results
        )
        total_weight = sum(_LAYER_WEIGHTS.values())
        aggregate /= total_weight

        warnings = [
            f"[{r.layer}] {issue}"
            for r in results
            for issue in r.issues
        ]

        passed = aggregate >= 0.75 and all(
            r.score >= 0.5 for r in results
            if r.layer in ("Factual Accuracy", "Mathematical Correctness")
        )

        return ValidationReport(
            results=results,
            aggregate_score=round(aggregate, 4),
            warnings=warnings,
            passed=passed,
        )

    async def _check_layer(
        self,
        client,
        layer_name: str,
        layer_desc: str,
        query: str,
        output: str,
    ) -> LayerResult:
        prompt = _LAYER_PROMPT.format(
            layer=f"{layer_name}\n\n{layer_desc}",
            query=query,
            output=output[:3000],
        )

        try:
            response = await client.messages.create(
                model=self.model,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            # Strip code fences
            if "```" in text:
                parts = text.split("```")
                text = parts[1] if len(parts) > 1 else text
                if text.startswith("json"):
                    text = text[4:]

            data = json.loads(text)
            return LayerResult(
                layer=layer_name,
                score=float(data.get("score", 0.5)),
                passed=bool(data.get("passed", False)),
                issues=data.get("issues", []),
                notes=data.get("notes", ""),
            )
        except Exception as exc:
            return LayerResult(
                layer=layer_name,
                score=0.5,
                passed=False,
                issues=[f"Validation error: {exc}"],
                notes="Could not complete validation",
            )
