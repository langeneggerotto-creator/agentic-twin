"""
Researcher Agent — validates research claims against scientific consensus.

Capabilities:
  • Evaluate study quality (RCT > cohort > case study > anecdotal)
  • Detect common statistical fallacies (correlation ≠ causation, p-hacking, etc.)
  • Flag retracted or contested studies
  • Synthesise evidence level rating
  • Provide counter-evidence where relevant
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from typing import Optional

import anthropic


@dataclass
class ResearchClaim:
    claim: str
    evidence_level: str     # Ia / Ib / IIa / IIb / III / IV (Oxford EBM scale)
    consensus_alignment: float  # 0.0 – 1.0
    quality_score: float    # 0.0 – 1.0
    concerns: list[str]
    counter_evidence: list[str]


@dataclass
class ResearchReport:
    claims: list[ResearchClaim]
    overall_evidence_quality: str
    consensus_score: float
    methodology_rating: float
    statistical_validity: float
    recommendations: list[str]
    validated_summary: str


_RESEARCHER_SYSTEM = """You are a senior research methodologist and systematic review specialist
with expertise in evidence-based medicine, statistics, and scientific methodology.

You evaluate research claims using the Oxford Centre for Evidence-Based Medicine (OCEBM) levels:
  Ia  — Systematic review / meta-analysis of RCTs
  Ib  — Randomised controlled trial
  IIa — Controlled trial without randomisation
  IIb — Quasi-experimental study
  III — Observational (cohort, case-control, cross-sectional)
  IV  — Case reports, expert opinion, anecdotal

You rigorously check for:
  • P-hacking and HARKing (Hypothesising After Results are Known)
  • Underpowered studies
  • Confounding variables
  • Publication bias
  • Replication failures
  • Conflict of interest
"""

_RESEARCH_PROMPT = """Evaluate the research claims in this text.

Query: {query}

Text to evaluate:
\"\"\"
{text}
\"\"\"

Return ONLY valid JSON:
{{
  "claims": [
    {{
      "claim": "<the research claim>",
      "evidence_level": "<Ia|Ib|IIa|IIb|III|IV>",
      "consensus_alignment": <float 0.0-1.0>,
      "quality_score": <float 0.0-1.0>,
      "concerns": ["<methodological concern>"],
      "counter_evidence": ["<contrary finding or study>"]
    }}
  ],
  "overall_evidence_quality": "<strong|moderate|weak|insufficient>",
  "consensus_score": <float 0.0-1.0>,
  "methodology_rating": <float 0.0-1.0>,
  "statistical_validity": <float 0.0-1.0>,
  "recommendations": ["<what additional evidence is needed>"],
  "validated_summary": "<corrected, evidence-graded summary of the research>"
}}"""


class ResearcherAgent:
    def __init__(self, api_key: str | None = None, model: str = "claude-opus-4-6"):
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key or os.environ["ANTHROPIC_API_KEY"]
        )
        self.model = model

    def validate_research(self, query: str, text: str) -> ResearchReport:
        return asyncio.run(self.avalidate_research(query, text))

    async def avalidate_research(self, query: str, text: str) -> ResearchReport:
        prompt = _RESEARCH_PROMPT.format(query=query, text=text[:4000])

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=[
                {
                    "type": "text",
                    "text": _RESEARCHER_SYSTEM,
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
            return ResearchReport(
                claims=[],
                overall_evidence_quality="insufficient",
                consensus_score=0.5,
                methodology_rating=0.5,
                statistical_validity=0.5,
                recommendations=["Could not parse research validation response."],
                validated_summary=text,
            )

        claims = [
            ResearchClaim(
                claim=c.get("claim", ""),
                evidence_level=c.get("evidence_level", "IV"),
                consensus_alignment=float(c.get("consensus_alignment", 0.5)),
                quality_score=float(c.get("quality_score", 0.5)),
                concerns=c.get("concerns", []),
                counter_evidence=c.get("counter_evidence", []),
            )
            for c in data.get("claims", [])
        ]

        return ResearchReport(
            claims=claims,
            overall_evidence_quality=data.get("overall_evidence_quality", "moderate"),
            consensus_score=float(data.get("consensus_score", 0.5)),
            methodology_rating=float(data.get("methodology_rating", 0.5)),
            statistical_validity=float(data.get("statistical_validity", 0.5)),
            recommendations=data.get("recommendations", []),
            validated_summary=data.get("validated_summary", text),
        )
