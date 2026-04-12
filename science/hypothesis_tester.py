"""
Hypothesis Tester — applies formal hypothesis testing methodology.

Implements:
  • Null hypothesis formulation (H₀)
  • Alternative hypothesis (H₁)
  • Test design (parametric / non-parametric)
  • Statistical power analysis
  • Effect size estimation (Cohen's d, η², r)
  • p-value interpretation with Bayesian supplement
  • Type I / Type II error analysis
  • Replication assessment
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from typing import Optional

import anthropic


@dataclass
class HypothesisTestResult:
    h0: str                     # null hypothesis
    h1: str                     # alternative hypothesis
    test_type: str              # t-test / chi-squared / ANOVA / Bayesian / etc.
    required_sample_size: int
    effect_size_estimate: float
    statistical_power: float    # 0.0 – 1.0
    alpha_threshold: float      # significance level (e.g. 0.05)
    expected_p_value_range: str
    type_i_error_risk: str
    type_ii_error_risk: str
    confounders: list[str]
    control_strategy: str
    experiment_protocol: str
    outcome_metrics: list[str]
    interpretation_guide: str
    bayesian_prior: str
    replication_design: str
    confidence: float


_HYPOTHESIS_SYSTEM = """You are a biostatistician and experimental methodologist with
expertise in null hypothesis significance testing (NHST), Bayesian inference, and
meta-scientific methodology.

You design rigorous hypothesis tests that:
1. Have clear, falsifiable null and alternative hypotheses
2. Are properly powered (≥80% power at α=0.05 unless justified otherwise)
3. Control for confounders
4. Use appropriate statistical tests
5. Account for multiple comparisons
6. Include a pre-registered analysis plan
7. Are reproducible and transparent
"""

_HYPOTHESIS_PROMPT = """Design a formal hypothesis test for:

Claim / Question: {claim}
Context: {context}

Return ONLY valid JSON:
{{
  "h0": "<null hypothesis: specific, measurable, falsifiable>",
  "h1": "<alternative hypothesis>",
  "test_type": "<statistical test to use and why>",
  "required_sample_size": <integer>,
  "effect_size_estimate": <float — Cohen's d or equivalent>,
  "statistical_power": <float 0.0-1.0>,
  "alpha_threshold": <float — e.g. 0.05>,
  "expected_p_value_range": "<e.g. 0.01–0.05 if H1 is true>",
  "type_i_error_risk": "<description>",
  "type_ii_error_risk": "<description>",
  "confounders": ["<potential confounding variable>"],
  "control_strategy": "<how to control for confounders>",
  "experiment_protocol": "<step-by-step procedure>",
  "outcome_metrics": ["<primary outcome>", "<secondary outcome>"],
  "interpretation_guide": "<how to interpret each possible result>",
  "bayesian_prior": "<reasonable prior belief and Bayes factor interpretation>",
  "replication_design": "<how to design a replication study>",
  "confidence": <float 0.0-1.0>
}}"""


class HypothesisTester:
    def __init__(self, api_key: str | None = None, model: str = "claude-opus-4-6"):
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key or os.environ["ANTHROPIC_API_KEY"]
        )
        self.model = model

    def design_test(self, claim: str, context: str = "") -> HypothesisTestResult:
        return asyncio.run(self.adesign_test(claim, context))

    async def adesign_test(self, claim: str, context: str = "") -> HypothesisTestResult:
        prompt = _HYPOTHESIS_PROMPT.format(claim=claim, context=context[:2000] or "None")

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=[
                {
                    "type": "text",
                    "text": _HYPOTHESIS_SYSTEM,
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
            return HypothesisTestResult(
                h0="Could not formulate null hypothesis",
                h1="Could not formulate alternative hypothesis",
                test_type="",
                required_sample_size=0,
                effect_size_estimate=0.0,
                statistical_power=0.0,
                alpha_threshold=0.05,
                expected_p_value_range="",
                type_i_error_risk="",
                type_ii_error_risk="",
                confounders=[],
                control_strategy="",
                experiment_protocol=raw,
                outcome_metrics=[],
                interpretation_guide="",
                bayesian_prior="",
                replication_design="",
                confidence=0.0,
            )

        return HypothesisTestResult(
            h0=data.get("h0", ""),
            h1=data.get("h1", ""),
            test_type=data.get("test_type", ""),
            required_sample_size=int(data.get("required_sample_size", 0)),
            effect_size_estimate=float(data.get("effect_size_estimate", 0.0)),
            statistical_power=float(data.get("statistical_power", 0.8)),
            alpha_threshold=float(data.get("alpha_threshold", 0.05)),
            expected_p_value_range=data.get("expected_p_value_range", ""),
            type_i_error_risk=data.get("type_i_error_risk", ""),
            type_ii_error_risk=data.get("type_ii_error_risk", ""),
            confounders=data.get("confounders", []),
            control_strategy=data.get("control_strategy", ""),
            experiment_protocol=data.get("experiment_protocol", ""),
            outcome_metrics=data.get("outcome_metrics", []),
            interpretation_guide=data.get("interpretation_guide", ""),
            bayesian_prior=data.get("bayesian_prior", ""),
            replication_design=data.get("replication_design", ""),
            confidence=float(data.get("confidence", 0.8)),
        )
