"""
Validator Agent — the primary quality-gate agent.

Takes any AI-generated output and runs it through:
  1. Claim extraction + truth scoring
  2. Logical consistency check
  3. Correction loop
  4. Final confidence report

Usage:
  agent = ValidatorAgent()
  result = agent.validate(query="...", ai_output="...")
"""

import asyncio
import os
from dataclasses import dataclass, field

import anthropic


@dataclass
class ValidationResult:
    original_output: str
    validated_output: str
    is_accurate: bool
    overall_confidence: float
    corrections: list[str]
    flagged_claims: list[dict]
    quality_grade: str          # A / B / C / D / F
    explanation: str


_VALIDATOR_SYSTEM = """You are an elite AI output validator with expertise spanning
science, mathematics, technology, history, and critical reasoning.

Your job is to perform a comprehensive validation of any text I give you.

For each validation:
1. Extract every factual, logical, and mathematical claim
2. Score each for accuracy (0–100%)
3. Identify errors, hallucinations, or unsupported assertions
4. Produce a corrected version if needed
5. Assign an overall quality grade (A/B/C/D/F)

Be rigorous. Be specific. Never guess — if uncertain, say so."""

_VALIDATE_PROMPT = """Validate the following AI output for the given query.

Query: {query}

AI Output:
\"\"\"
{output}
\"\"\"

Return a JSON object with:
{{
  "is_accurate": <bool>,
  "overall_confidence": <float 0.0-1.0>,
  "flagged_claims": [
    {{"claim": "<text>", "issue": "<what's wrong>", "confidence": <float>}}
  ],
  "corrections": ["<what was changed and why>"],
  "corrected_output": "<the fixed version of the output, or original if no changes needed>",
  "quality_grade": "<A|B|C|D|F>",
  "explanation": "<2-3 sentence summary of overall quality>"
}}"""


class ValidatorAgent:
    def __init__(self, api_key: str | None = None, model: str = "claude-opus-4-6"):
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key or os.environ["ANTHROPIC_API_KEY"]
        )
        self.model = model

    def validate(self, query: str, ai_output: str) -> ValidationResult:
        return asyncio.run(self.avalidate(query, ai_output))

    async def avalidate(self, query: str, ai_output: str) -> ValidationResult:
        import json

        prompt = _VALIDATE_PROMPT.format(query=query, output=ai_output[:4000])

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=[
                {
                    "type": "text",
                    "text": _VALIDATOR_SYSTEM,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        if "```" in text:
            parts = text.split("```")
            text = parts[1] if len(parts) > 1 else text
            if text.startswith("json"):
                text = text[4:]

        try:
            data = json.loads(text)
        except Exception:
            data = {
                "is_accurate": False,
                "overall_confidence": 0.5,
                "flagged_claims": [],
                "corrections": ["Parse error — could not decode validator response"],
                "corrected_output": ai_output,
                "quality_grade": "C",
                "explanation": "Validation response could not be parsed.",
            }

        return ValidationResult(
            original_output=ai_output,
            validated_output=data.get("corrected_output", ai_output),
            is_accurate=data.get("is_accurate", False),
            overall_confidence=float(data.get("overall_confidence", 0.5)),
            corrections=data.get("corrections", []),
            flagged_claims=data.get("flagged_claims", []),
            quality_grade=data.get("quality_grade", "C"),
            explanation=data.get("explanation", ""),
        )
