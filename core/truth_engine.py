"""
Truth Engine — the arbiter of factual accuracy inside the Digital Twin.

Responsibilities
────────────────
  • Extract every verifiable claim from an AI output
  • Score each claim for truth confidence (0–1)
  • Detect hallucinations, outdated facts, or unsupported assertions
  • Identify what sources would be needed to verify uncertain claims
  • Emit a structured TruthReport with an overall truth score
"""

import json
from dataclasses import dataclass, field
from typing import Optional

import anthropic


@dataclass
class Claim:
    text: str
    confidence: float       # 0.0 – 1.0
    category: str           # factual / scientific / statistical / logical / opinion
    verifiable: bool
    evidence_needed: str
    flags: list[str] = field(default_factory=list)


@dataclass
class TruthReport:
    claims: list[Claim]
    overall_truth_score: float
    sources_verified: list[str]
    warnings: list[str]
    hallucination_risk: str     # low / medium / high
    summary: str


_EXTRACTION_PROMPT = """You are a truth-analysis engine. Given the AI output below,
extract every verifiable claim and score its truth confidence.

Query: {query}
Mode: {mode}

AI Output:
\"\"\"
{output}
\"\"\"

Return ONLY valid JSON with this schema:
{{
  "claims": [
    {{
      "text": "<the exact claim>",
      "confidence": <float 0.0-1.0>,
      "category": "<factual|scientific|statistical|logical|opinion>",
      "verifiable": <bool>,
      "evidence_needed": "<what source/method would verify this>",
      "flags": ["<hallucination_risk>", "<outdated>", "<unsupported>", ...]
    }}
  ],
  "overall_truth_score": <float 0.0-1.0>,
  "sources_verified": ["<source name if mentioned and credible>"],
  "warnings": ["<specific concern>"],
  "hallucination_risk": "<low|medium|high>",
  "summary": "<two-sentence plain-English summary of truth assessment>"
}}

Be strict. A claim is only high-confidence (>0.9) if it is a well-established fact
that you are certain is correct. Flag anything you are less than 80% confident about."""


class TruthEngine:
    def __init__(self, client: anthropic.Anthropic, model: str):
        self.client = client
        self.model = model

    async def analyze(self, query: str, output: str, mode: str) -> TruthReport:
        import anthropic as _anthropic

        async_client = _anthropic.AsyncAnthropic(api_key=self.client.api_key)

        prompt = _EXTRACTION_PROMPT.format(
            query=query,
            mode=mode,
            output=output[:4000],
        )

        try:
            response = await async_client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=[
                    {
                        "type": "text",
                        "text": (
                            "You are an expert fact-checker with deep knowledge across all "
                            "scientific disciplines, history, mathematics, and technology. "
                            "You are rigorous, precise, and never guess."
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

            claims = [
                Claim(
                    text=c.get("text", ""),
                    confidence=float(c.get("confidence", 0.5)),
                    category=c.get("category", "factual"),
                    verifiable=bool(c.get("verifiable", True)),
                    evidence_needed=c.get("evidence_needed", ""),
                    flags=c.get("flags", []),
                )
                for c in data.get("claims", [])
            ]

            return TruthReport(
                claims=claims,
                overall_truth_score=float(data.get("overall_truth_score", 0.5)),
                sources_verified=data.get("sources_verified", []),
                warnings=data.get("warnings", []),
                hallucination_risk=data.get("hallucination_risk", "medium"),
                summary=data.get("summary", ""),
            )

        except Exception as exc:
            return TruthReport(
                claims=[],
                overall_truth_score=0.5,
                sources_verified=[],
                warnings=[f"Truth analysis error: {exc}"],
                hallucination_risk="medium",
                summary="Truth analysis could not be completed.",
            )

    def format_report(self, report: TruthReport) -> str:
        """Human-readable truth report."""
        lines = [
            f"Truth Score: {report.overall_truth_score:.0%}",
            f"Hallucination Risk: {report.hallucination_risk.upper()}",
            f"Summary: {report.summary}",
            "",
        ]
        if report.warnings:
            lines.append("Warnings:")
            for w in report.warnings:
                lines.append(f"  ⚠ {w}")
            lines.append("")

        high_risk = [c for c in report.claims if c.confidence < 0.7]
        if high_risk:
            lines.append("Low-confidence claims requiring verification:")
            for c in high_risk:
                lines.append(f"  [{c.confidence:.0%}] {c.text}")
                if c.flags:
                    lines.append(f"         Flags: {', '.join(c.flags)}")

        return "\n".join(lines)
