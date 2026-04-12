"""
Architect Agent — reviews and improves system design, architecture, and engineering.

Capabilities:
  • Analyse system architecture for scalability, reliability, and security
  • Apply SOLID, 12-Factor App, CAP theorem, and other principles
  • Recommend design patterns (CQRS, Event Sourcing, Saga, Circuit Breaker, etc.)
  • Produce component diagrams (textual Mermaid format)
  • Identify single points of failure, bottlenecks, and security gaps
  • Calculate complexity estimates (Big-O, request throughput, data volume)
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from typing import Optional

import anthropic


@dataclass
class ArchitectureComponent:
    name: str
    responsibility: str
    interfaces: list[str]
    dependencies: list[str]
    scalability_notes: str


@dataclass
class ArchitectureReview:
    components: list[ArchitectureComponent]
    design_patterns: list[str]
    data_flows: list[str]
    scalability_rating: float
    reliability_rating: float
    security_rating: float
    issues: list[str]
    recommendations: list[str]
    mermaid_diagram: str
    improved_design: str
    complexity_estimate: str


_ARCHITECT_SYSTEM = """You are a principal systems architect with 20+ years of experience
designing large-scale distributed systems at companies like Google, Amazon, and Netflix.

You apply:
  • SOLID principles (SRP, OCP, LSP, ISP, DIP)
  • 12-Factor App methodology
  • CAP theorem for distributed systems
  • Domain-Driven Design (DDD)
  • Event-driven architecture patterns
  • Security-by-design (zero-trust, least privilege)
  • Observability: logs, metrics, traces (the three pillars)

For every design review you:
  1. Map all components and their responsibilities
  2. Identify all interfaces and contracts
  3. Trace data flows end-to-end
  4. Calculate failure modes and mitigations
  5. Apply relevant design patterns
  6. Produce a Mermaid diagram of the architecture
  7. Rate scalability, reliability, and security (0–1)
"""

_ARCHITECT_PROMPT = """Review and improve the following system design.

Query / Design:
\"\"\"
{query}
\"\"\"

Return ONLY valid JSON:
{{
  "components": [
    {{
      "name": "<component name>",
      "responsibility": "<single clear responsibility>",
      "interfaces": ["<API or contract>"],
      "dependencies": ["<other component names>"],
      "scalability_notes": "<horizontal/vertical scaling strategy>"
    }}
  ],
  "design_patterns": ["<pattern name: rationale>"],
  "data_flows": ["<source → transform → destination>"],
  "scalability_rating": <float 0.0-1.0>,
  "reliability_rating": <float 0.0-1.0>,
  "security_rating": <float 0.0-1.0>,
  "issues": ["<architectural problem>"],
  "recommendations": ["<concrete improvement>"],
  "mermaid_diagram": "<full Mermaid graph LR diagram as a string>",
  "improved_design": "<prose description of the improved architecture>",
  "complexity_estimate": "<time complexity, space complexity, throughput estimate>"
}}"""


class ArchitectAgent:
    def __init__(self, api_key: str | None = None, model: str = "claude-opus-4-6"):
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key or os.environ["ANTHROPIC_API_KEY"]
        )
        self.model = model

    def review(self, query: str) -> ArchitectureReview:
        return asyncio.run(self.areview(query))

    async def areview(self, query: str) -> ArchitectureReview:
        prompt = _ARCHITECT_PROMPT.format(query=query[:4000])

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": _ARCHITECT_SYSTEM,
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
            return ArchitectureReview(
                components=[],
                design_patterns=[],
                data_flows=[],
                scalability_rating=0.5,
                reliability_rating=0.5,
                security_rating=0.5,
                issues=["Could not parse architect response"],
                recommendations=[],
                mermaid_diagram="",
                improved_design=raw,
                complexity_estimate="",
            )

        components = [
            ArchitectureComponent(
                name=c.get("name", ""),
                responsibility=c.get("responsibility", ""),
                interfaces=c.get("interfaces", []),
                dependencies=c.get("dependencies", []),
                scalability_notes=c.get("scalability_notes", ""),
            )
            for c in data.get("components", [])
        ]

        return ArchitectureReview(
            components=components,
            design_patterns=data.get("design_patterns", []),
            data_flows=data.get("data_flows", []),
            scalability_rating=float(data.get("scalability_rating", 0.5)),
            reliability_rating=float(data.get("reliability_rating", 0.5)),
            security_rating=float(data.get("security_rating", 0.5)),
            issues=data.get("issues", []),
            recommendations=data.get("recommendations", []),
            mermaid_diagram=data.get("mermaid_diagram", ""),
            improved_design=data.get("improved_design", ""),
            complexity_estimate=data.get("complexity_estimate", ""),
        )
