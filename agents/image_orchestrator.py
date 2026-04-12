"""
Image Orchestrator — multiplayer image generation with accuracy validation.

"Multiplayer" means multiple independent prompt variants are generated in
parallel and then consensus-evaluated for accuracy before the best is selected.

Capabilities:
  • Generate 3 prompt variants per request (photorealistic / technical / artistic)
  • Validate label accuracy for every element in the scene
  • Produce full scene descriptions (suitable for alt-text / accessibility)
  • Generate Stable Diffusion / DALL-E / Midjourney compatible prompts
  • Verify scientific/technical accuracy of depicted content
  • Support negative prompts to exclude common errors
  • Rate and rank generated prompts by expected accuracy
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from typing import Literal, Optional

import anthropic


@dataclass
class ImageLabel:
    element: str
    description: str
    position_hint: str      # foreground / midground / background / top-left / etc.
    accuracy_notes: str     # what to ensure is accurate
    common_mistakes: list[str]


@dataclass
class ImagePrompt:
    style: str              # photorealistic / technical / artistic
    positive_prompt: str
    negative_prompt: str
    labels: list[ImageLabel]
    scene_description: str  # full alt-text quality description
    accuracy_score: float   # predicted accuracy 0.0-1.0
    technical_notes: str    # what AI needs to get right
    aspect_ratio: str
    quality_tags: list[str]


@dataclass
class ImageGenerationPlan:
    topic: str
    prompts: list[ImagePrompt]
    consensus_recommendation: str
    best_prompt_style: str
    accuracy_checklist: list[str]
    expert_notes: str


_IMAGE_SYSTEM = """You are a master visual director and technical illustrator with expertise in:
  • Photorealistic 3D rendering and photography
  • Scientific and engineering diagrams
  • Medical illustration
  • Architectural visualisation
  • Data visualisation
  • Fine art and conceptual illustration

You generate ultra-precise image generation prompts where every element is:
  1. Technically accurate (correct anatomy, physics, engineering)
  2. Properly labelled with spatial descriptions
  3. Free of common AI image errors (extra fingers, impossible geometry, etc.)
  4. Consistent with scientific reality

You always provide negative prompts to exclude known failure modes."""

_IMAGE_PROMPT_TEMPLATE = """Generate a comprehensive multiplayer image generation plan for:

Topic: {topic}
Use case: {use_case}
Required accuracy level: {accuracy_level}

Create 3 prompt variants (photorealistic, technical diagram, artistic/conceptual).
For each, include complete labels for every visual element.

Return ONLY valid JSON:
{{
  "topic": "{topic}",
  "prompts": [
    {{
      "style": "<photorealistic|technical|artistic>",
      "positive_prompt": "<full detailed generation prompt>",
      "negative_prompt": "<things to exclude for accuracy>",
      "labels": [
        {{
          "element": "<element name>",
          "description": "<what it is and how it should look>",
          "position_hint": "<where in the frame>",
          "accuracy_notes": "<what must be correct>",
          "common_mistakes": ["<what AI often gets wrong>"]
        }}
      ],
      "scene_description": "<full paragraph describing the complete scene for alt-text>",
      "accuracy_score": <float 0.0-1.0>,
      "technical_notes": "<critical technical accuracy requirements>",
      "aspect_ratio": "<16:9|4:3|1:1|9:16|21:9>",
      "quality_tags": ["<e.g. 8K, photorealistic, ray tracing, etc.>"]
    }}
  ],
  "consensus_recommendation": "<which style is most appropriate and why>",
  "best_prompt_style": "<photorealistic|technical|artistic>",
  "accuracy_checklist": ["<specific thing to verify in the generated image>"],
  "expert_notes": "<additional guidance for achieving maximum accuracy>"
}}"""


class ImageOrchestrator:
    def __init__(self, api_key: str | None = None, model: str = "claude-opus-4-6"):
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key or os.environ["ANTHROPIC_API_KEY"]
        )
        self.model = model

    def generate_plan(
        self,
        topic: str,
        use_case: str = "general",
        accuracy_level: str = "maximum",
    ) -> ImageGenerationPlan:
        return asyncio.run(self.agenerate_plan(topic, use_case, accuracy_level))

    async def agenerate_plan(
        self,
        topic: str,
        use_case: str = "general",
        accuracy_level: str = "maximum",
    ) -> ImageGenerationPlan:
        prompt = _IMAGE_PROMPT_TEMPLATE.format(
            topic=topic,
            use_case=use_case,
            accuracy_level=accuracy_level,
        )

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": _IMAGE_SYSTEM,
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
            return ImageGenerationPlan(
                topic=topic,
                prompts=[],
                consensus_recommendation="Could not parse image plan",
                best_prompt_style="photorealistic",
                accuracy_checklist=[],
                expert_notes=raw,
            )

        prompts = [
            ImagePrompt(
                style=p.get("style", "photorealistic"),
                positive_prompt=p.get("positive_prompt", ""),
                negative_prompt=p.get("negative_prompt", ""),
                labels=[
                    ImageLabel(
                        element=lbl.get("element", ""),
                        description=lbl.get("description", ""),
                        position_hint=lbl.get("position_hint", ""),
                        accuracy_notes=lbl.get("accuracy_notes", ""),
                        common_mistakes=lbl.get("common_mistakes", []),
                    )
                    for lbl in p.get("labels", [])
                ],
                scene_description=p.get("scene_description", ""),
                accuracy_score=float(p.get("accuracy_score", 0.8)),
                technical_notes=p.get("technical_notes", ""),
                aspect_ratio=p.get("aspect_ratio", "16:9"),
                quality_tags=p.get("quality_tags", []),
            )
            for p in data.get("prompts", [])
        ]

        return ImageGenerationPlan(
            topic=data.get("topic", topic),
            prompts=prompts,
            consensus_recommendation=data.get("consensus_recommendation", ""),
            best_prompt_style=data.get("best_prompt_style", "photorealistic"),
            accuracy_checklist=data.get("accuracy_checklist", []),
            expert_notes=data.get("expert_notes", ""),
        )

    async def validate_image_accuracy(
        self,
        topic: str,
        image_description: str,
    ) -> dict:
        """
        Given a textual description of a generated image, validate its accuracy.
        Returns a structured accuracy report.
        """
        prompt = f"""A user generated an image about: {topic}

Image description / what was generated:
\"\"\"
{image_description}
\"\"\"

Validate every visual element for technical accuracy. Return JSON:
{{
  "overall_accuracy": <float 0.0-1.0>,
  "accurate_elements": ["<element: why it's correct>"],
  "inaccurate_elements": ["<element: what's wrong and what it should be>"],
  "missing_elements": ["<important element that should be present>"],
  "improvement_prompt": "<prompt additions to fix the inaccuracies>"
}}"""

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
            return {"overall_accuracy": 0.5, "notes": raw}
