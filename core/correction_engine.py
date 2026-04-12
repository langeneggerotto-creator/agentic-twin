"""
Correction Engine — detects errors in AI output and iteratively rewrites them
until the truth score meets the configured threshold.

Strategy
────────
  1. Receive the original output + truth report
  2. Build a targeted correction prompt citing specific issues
  3. Rewrite only the parts that are wrong (surgical correction)
  4. Return the corrected output + diff summary
"""

import json
from dataclasses import dataclass, field
from typing import Optional

import anthropic

from .truth_engine import TruthReport


@dataclass
class CorrectionReport:
    corrected_output: str
    corrections: list[str]
    correction_confidence: float
    unchanged_sections: list[str] = field(default_factory=list)


_CORRECTION_PROMPT = """You are a surgical correction engine. You will receive:
1. The original user query
2. An AI output that contains errors
3. A list of specific issues found

Your job: rewrite the output to fix ONLY the identified errors.
- Keep correct sections exactly as they are
- Do NOT add new content beyond what's needed to fix the errors
- Preserve the format and structure
- After fixing, the output must be fully accurate and consistent

Query:
{query}

Original Output:
\"\"\"
{output}
\"\"\"

Issues to fix:
{issues}

Return ONLY valid JSON:
{{
  "corrected_output": "<the full corrected output text>",
  "corrections": ["<description of change 1>", "<description of change 2>", ...],
  "correction_confidence": <float 0.0-1.0 — how confident you are corrections are right>
}}"""


class CorrectionEngine:
    def __init__(self, client: anthropic.Anthropic, model: str):
        self.client = client
        self.model = model

    async def correct(
        self,
        query: str,
        output: str,
        truth_report: TruthReport,
        mode: str,
    ) -> CorrectionReport:
        import anthropic as _anthropic

        async_client = _anthropic.AsyncAnthropic(api_key=self.client.api_key)

        # Collect all issues
        issues_list: list[str] = []
        for warning in truth_report.warnings:
            issues_list.append(f"Warning: {warning}")
        for claim in truth_report.claims:
            if claim.confidence < 0.7:
                issue = f"Low-confidence claim ({claim.confidence:.0%}): '{claim.text}'"
                if claim.flags:
                    issue += f" — flags: {', '.join(claim.flags)}"
                issues_list.append(issue)

        if not issues_list:
            # Nothing to correct
            return CorrectionReport(
                corrected_output=output,
                corrections=[],
                correction_confidence=1.0,
            )

        issues_text = "\n".join(f"  {i + 1}. {issue}" for i, issue in enumerate(issues_list))

        prompt = _CORRECTION_PROMPT.format(
            query=query,
            output=output[:4000],
            issues=issues_text,
        )

        try:
            response = await async_client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=[
                    {
                        "type": "text",
                        "text": (
                            "You are an expert editor who specialises in factual accuracy. "
                            "You make surgical, minimal corrections and never introduce new errors."
                        ),
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

            data = json.loads(text)
            return CorrectionReport(
                corrected_output=data.get("corrected_output", output),
                corrections=data.get("corrections", []),
                correction_confidence=float(data.get("correction_confidence", 0.8)),
            )

        except Exception as exc:
            return CorrectionReport(
                corrected_output=output,
                corrections=[f"Correction failed: {exc}"],
                correction_confidence=0.0,
            )
