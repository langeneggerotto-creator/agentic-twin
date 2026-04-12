"""
Description Engine — generates rich, accurate textual descriptions of images.

Outputs:
  • Full scene description (paragraph form)
  • Accessibility alt-text (WCAG compliant)
  • Technical caption
  • Social media caption
  • Scientific figure legend (journal-quality)
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from typing import Optional

import anthropic


@dataclass
class SceneDescription:
    full_description: str           # 2-4 paragraph detailed description
    alt_text: str                   # WCAG-compliant, ≤125 words
    technical_caption: str          # precise, jargon-appropriate
    figure_legend: str              # journal-quality figure legend
    social_caption: str             # engaging, accurate, ≤280 chars
    key_elements: list[str]         # bullet list of main visual elements
    accuracy_notes: str             # what accuracy considerations apply


_DESCRIPTION_SYSTEM = """You are a professional image describer and caption writer with
expertise in accessibility, scientific communication, and creative writing.

Your descriptions are:
  1. Accurate — every element described correctly
  2. Complete — nothing important is omitted
  3. Ordered — described logically (general to specific, or spatially)
  4. Accessible — WCAG 2.1 Level AA compliant for alt text
  5. Contextual — appropriate for the intended use case
"""

_DESCRIPTION_PROMPT = """Generate comprehensive descriptions for an image about:

Topic: {topic}
Style: {style}
Context/Use case: {context}
Technical domain: {domain}

Key visual elements present: {elements}

Return ONLY valid JSON:
{{
  "full_description": "<2-4 paragraph detailed description of the scene>",
  "alt_text": "<WCAG-compliant alt text, ≤125 words, describes the essential content>",
  "technical_caption": "<precise, domain-appropriate caption with terminology>",
  "figure_legend": "<journal-quality figure legend: 'Figure N. [Title]. [Description.] [Scale/units if applicable.]'>",
  "social_caption": "<engaging, accurate social media caption ≤280 chars>",
  "key_elements": ["<element 1>", "<element 2>", "..."],
  "accuracy_notes": "<what viewers should know about the accuracy of this depiction>"
}}"""


class DescriptionEngine:
    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-6"):
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key or os.environ["ANTHROPIC_API_KEY"]
        )
        self.model = model

    def describe(
        self,
        topic: str,
        style: str = "photorealistic",
        context: str = "",
        domain: str = "general",
        elements: list[str] | None = None,
    ) -> SceneDescription:
        return asyncio.run(self.adescribe(topic, style, context, domain, elements))

    async def adescribe(
        self,
        topic: str,
        style: str = "photorealistic",
        context: str = "",
        domain: str = "general",
        elements: list[str] | None = None,
    ) -> SceneDescription:
        prompt = _DESCRIPTION_PROMPT.format(
            topic=topic,
            style=style,
            context=context or "General purpose",
            domain=domain,
            elements=", ".join(elements) if elements else "Not specified",
        )

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=[
                {
                    "type": "text",
                    "text": _DESCRIPTION_SYSTEM,
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
            return SceneDescription(
                full_description=raw,
                alt_text=f"Image depicting {topic}",
                technical_caption=topic,
                figure_legend=f"Figure 1. {topic}.",
                social_caption=topic,
                key_elements=[],
                accuracy_notes="",
            )

        return SceneDescription(
            full_description=data.get("full_description", ""),
            alt_text=data.get("alt_text", ""),
            technical_caption=data.get("technical_caption", ""),
            figure_legend=data.get("figure_legend", ""),
            social_caption=data.get("social_caption", ""),
            key_elements=data.get("key_elements", []),
            accuracy_notes=data.get("accuracy_notes", ""),
        )
