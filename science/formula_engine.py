"""
Formula Engine — derives, validates, and explains scientific/mathematical formulas.

Approach:
  1. Identify the domain (mechanics, electromagnetism, thermodynamics, etc.)
  2. Select applicable physical laws and axioms
  3. Perform dimensional analysis to verify consistency
  4. Derive formula step-by-step from first principles
  5. State validity domain and assumptions
  6. Provide numerical examples with SI units
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from typing import Optional

import anthropic


@dataclass
class DerivedFormula:
    name: str
    formula: str                    # symbolic, e.g. "F = ma"
    latex: str                      # LaTeX, e.g. "F = m \\cdot a"
    description: str
    domain: str                     # physics / chemistry / maths / engineering
    subdomain: str                  # e.g. classical mechanics
    variables: dict[str, str]       # {"F": "Force (N)", "m": "mass (kg)", ...}
    derivation_steps: list[str]
    physical_laws_used: list[str]
    assumptions: list[str]
    validity_domain: str
    breakdown_conditions: list[str] # when this formula fails
    numerical_example: str
    related_formulas: list[str]
    dimensional_analysis: str
    confidence: float               # 0.0 – 1.0


_FORMULA_SYSTEM = """You are a mathematical physicist with expertise in deriving and
validating formulas across all branches of science and engineering.

You always:
1. Derive from first principles, not just state the result
2. Perform rigorous dimensional analysis
3. Use consistent SI units throughout
4. State all assumptions explicitly
5. Identify when/where the formula breaks down
6. Provide a worked numerical example

Your derivations are peer-review quality and could appear in a textbook."""

_DERIVE_PROMPT = """Derive the formula for: {query}

Domain hint: {domain}

Return ONLY valid JSON:
{{
  "name": "<formula name>",
  "formula": "<symbolic formula, e.g. E = mc²>",
  "latex": "<LaTeX representation>",
  "description": "<one sentence description>",
  "domain": "<physics|chemistry|mathematics|engineering|biology>",
  "subdomain": "<e.g. thermodynamics, calculus, organic chemistry>",
  "variables": {{
    "<symbol>": "<full name with SI unit>"
  }},
  "derivation_steps": [
    "<step 1: starting point / known law>",
    "<step 2>",
    "..."
  ],
  "physical_laws_used": ["<law or axiom name>"],
  "assumptions": ["<assumption made in derivation>"],
  "validity_domain": "<conditions under which this is valid>",
  "breakdown_conditions": ["<when this formula fails>"],
  "numerical_example": "<worked example with numbers and units>",
  "related_formulas": ["<related formula name and expression>"],
  "dimensional_analysis": "<show dimensional consistency>",
  "confidence": <float 0.0-1.0>
}}"""

_VALIDATE_FORMULA_PROMPT = """Validate the following formula. Check dimensional consistency,
physical plausibility, and mathematical correctness.

Formula: {formula}
Claimed description: {description}

Return ONLY valid JSON:
{{
  "is_valid": <bool>,
  "dimensional_check": "<result of dimensional analysis>",
  "errors": ["<specific error>"],
  "correct_formula": "<corrected formula if invalid>",
  "confidence": <float 0.0-1.0>,
  "notes": "<additional observations>"
}}"""


class FormulaEngine:
    def __init__(self, api_key: str | None = None, model: str = "claude-opus-4-6"):
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key or os.environ["ANTHROPIC_API_KEY"]
        )
        self.model = model

    def derive(self, query: str, domain: str = "auto") -> DerivedFormula:
        return asyncio.run(self.aderive(query, domain))

    async def aderive(self, query: str, domain: str = "auto") -> DerivedFormula:
        prompt = _DERIVE_PROMPT.format(query=query, domain=domain)

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": _FORMULA_SYSTEM,
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
            return DerivedFormula(
                name=query,
                formula="",
                latex="",
                description=raw,
                domain="unknown",
                subdomain="",
                variables={},
                derivation_steps=[],
                physical_laws_used=[],
                assumptions=[],
                validity_domain="",
                breakdown_conditions=[],
                numerical_example="",
                related_formulas=[],
                dimensional_analysis="",
                confidence=0.5,
            )

        return DerivedFormula(
            name=data.get("name", query),
            formula=data.get("formula", ""),
            latex=data.get("latex", ""),
            description=data.get("description", ""),
            domain=data.get("domain", ""),
            subdomain=data.get("subdomain", ""),
            variables=data.get("variables", {}),
            derivation_steps=data.get("derivation_steps", []),
            physical_laws_used=data.get("physical_laws_used", []),
            assumptions=data.get("assumptions", []),
            validity_domain=data.get("validity_domain", ""),
            breakdown_conditions=data.get("breakdown_conditions", []),
            numerical_example=data.get("numerical_example", ""),
            related_formulas=data.get("related_formulas", []),
            dimensional_analysis=data.get("dimensional_analysis", ""),
            confidence=float(data.get("confidence", 0.8)),
        )

    async def validate_formula(self, formula: str, description: str = "") -> dict:
        prompt = _VALIDATE_FORMULA_PROMPT.format(formula=formula, description=description)

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()
        if "```" in raw:
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]

        try:
            return json.loads(raw)
        except Exception:
            return {"is_valid": False, "notes": raw}

    def format_formula(self, f: DerivedFormula) -> str:
        """Human-readable formula sheet."""
        lines = [
            f"{'=' * 60}",
            f"Formula: {f.name}",
            f"{'=' * 60}",
            f"  {f.formula}",
            f"  {f.latex}",
            "",
            f"Description: {f.description}",
            f"Domain: {f.domain} > {f.subdomain}",
            "",
            "Variables:",
        ]
        for sym, desc in f.variables.items():
            lines.append(f"  {sym}: {desc}")

        lines += ["", "Derivation:"]
        for i, step in enumerate(f.derivation_steps, 1):
            lines.append(f"  {i}. {step}")

        lines += ["", f"Laws used: {', '.join(f.physical_laws_used)}"]
        lines += [f"Assumptions: {', '.join(f.assumptions)}"]
        lines += [f"Valid when: {f.validity_domain}"]
        lines += [f"Breaks down when: {'; '.join(f.breakdown_conditions)}"]
        lines += ["", f"Example: {f.numerical_example}"]
        lines += [f"Dimensional analysis: {f.dimensional_analysis}"]
        lines += [f"Confidence: {f.confidence:.0%}"]
        return "\n".join(lines)
