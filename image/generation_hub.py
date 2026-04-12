"""
Generation Hub — the central coordinator for multiplayer image generation.

"Multiplayer" architecture:
  1. Generate N independent prompt variants in parallel (the "players")
  2. Each variant uses a different expert perspective:
       • Photorealism expert
       • Technical diagram expert
       • Scientific illustrator
       • Fine art director
  3. Run consensus scoring across all variants
  4. Select the highest-accuracy prompt
  5. Optionally blend the best elements from multiple prompts

This hub generates the prompts — it is model-agnostic and works with
Stable Diffusion, DALL-E, Midjourney, or any image generation backend.
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from typing import Literal, Optional

import anthropic


@dataclass
class GenerationRequest:
    topic: str
    style_preference: Literal["photorealistic", "technical", "artistic", "scientific", "auto"] = "auto"
    accuracy_priority: Literal["maximum", "high", "standard"] = "maximum"
    use_case: str = ""
    target_audience: str = "general"
    image_size: str = "1024x1024"
    num_variants: int = 3
    include_labels: bool = True
    include_accessibility_text: bool = True


@dataclass
class VariantPrompt:
    expert: str             # which expert persona generated this
    style: str
    positive: str           # full positive prompt
    negative: str           # negative prompt
    accuracy_score: float   # predicted accuracy 0.0–1.0
    rationale: str          # why this prompt achieves accuracy
    key_details: list[str]  # critical details included


@dataclass
class GenerationResult:
    topic: str
    variants: list[VariantPrompt]
    consensus_best: VariantPrompt
    blended_prompt: str             # best elements merged
    scene_description: str
    label_map: dict[str, str]       # element → description
    accessibility_text: str
    generation_notes: str
    accuracy_confidence: float


_EXPERT_PERSONAS = {
    "photorealism": (
        "master photorealistic photographer and 3D rendering artist. "
        "You specify exact lighting rigs, camera settings (lens mm, f-stop, ISO), "
        "material properties, and environmental details."
    ),
    "technical": (
        "precision technical illustrator with engineering drawing expertise. "
        "You create clear, labeled diagrams with ISO standards, proper line weights, "
        "accurate dimensions, and unambiguous callouts."
    ),
    "scientific": (
        "scientific illustrator for Nature and Science journals. "
        "You ensure biological, chemical, and physical accuracy. "
        "Every structure, molecule, and phenomenon is depicted correctly."
    ),
    "artistic": (
        "conceptual art director with a background in fine arts and design. "
        "You create visually striking compositions that communicate complex ideas "
        "clearly while maintaining aesthetic excellence."
    ),
}

_HUB_SYSTEM = """You are an expert image generation coordinator managing a team of
specialist prompt engineers. Each specialist uses their unique expertise to generate
the most accurate possible image prompt for the given topic.

Critical accuracy requirements:
  • Anatomically correct (if biological)
  • Physically plausible (correct shadows, reflections, proportions)
  • Technically accurate (correct components, labels, configurations)
  • Historically accurate (correct period, style, materials if historical)
  • Geographically accurate (correct flora, fauna, architecture if location-specific)
"""

_VARIANT_PROMPT = """You are a {expert_description}

Generate the most accurate possible image prompt for:
Topic: {topic}
Use case: {use_case}
Accuracy priority: {accuracy}

Return ONLY valid JSON:
{{
  "expert": "{expert_name}",
  "style": "<style name>",
  "positive": "<full detailed positive prompt — be specific, use comma-separated tags>",
  "negative": "<comma-separated negative prompt — things to exclude for accuracy>",
  "accuracy_score": <float 0.0-1.0>,
  "rationale": "<why this achieves maximum accuracy>",
  "key_details": ["<important detail you included for accuracy>"]
}}"""

_CONSENSUS_PROMPT = """Given these {n} image generation prompt variants for "{topic}",
perform consensus analysis and create a blended optimal prompt.

Variants:
{variants_json}

Return ONLY valid JSON:
{{
  "best_variant_index": <0-based index of the best single prompt>,
  "consensus_rationale": "<why this is best>",
  "blended_prompt": "<merged positive prompt combining best elements from all variants>",
  "scene_description": "<full, detailed scene description for accessibility — 2-3 paragraphs>",
  "label_map": {{
    "<element name>": "<precise description of that element in the image>"
  }},
  "accessibility_text": "<alt text for the image — complete and descriptive>",
  "generation_notes": "<tips for the image generator to maximise accuracy>",
  "accuracy_confidence": <float 0.0-1.0>
}}"""


class GenerationHub:
    def __init__(self, api_key: str | None = None, model: str = "claude-opus-4-6"):
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key or os.environ["ANTHROPIC_API_KEY"]
        )
        self.model = model

    def generate(self, request: GenerationRequest) -> GenerationResult:
        return asyncio.run(self.agenerate(request))

    async def agenerate(self, request: GenerationRequest) -> GenerationResult:
        # Select which experts to use
        experts = list(_EXPERT_PERSONAS.items())[: request.num_variants]

        # Generate all variants in parallel
        tasks = [
            self._generate_variant(
                expert_name=name,
                expert_description=desc,
                topic=request.topic,
                use_case=request.use_case,
                accuracy=request.accuracy_priority,
            )
            for name, desc in experts
        ]
        variants: list[VariantPrompt] = await asyncio.gather(*tasks)

        # Consensus pass
        consensus = await self._consensus(request.topic, variants)

        best_idx = consensus.get("best_variant_index", 0)
        best_idx = min(best_idx, len(variants) - 1)

        return GenerationResult(
            topic=request.topic,
            variants=variants,
            consensus_best=variants[best_idx],
            blended_prompt=consensus.get("blended_prompt", variants[0].positive),
            scene_description=consensus.get("scene_description", ""),
            label_map=consensus.get("label_map", {}),
            accessibility_text=consensus.get("accessibility_text", ""),
            generation_notes=consensus.get("generation_notes", ""),
            accuracy_confidence=float(consensus.get("accuracy_confidence", 0.8)),
        )

    async def _generate_variant(
        self,
        expert_name: str,
        expert_description: str,
        topic: str,
        use_case: str,
        accuracy: str,
    ) -> VariantPrompt:
        prompt = _VARIANT_PROMPT.format(
            expert_description=expert_description,
            topic=topic,
            use_case=use_case or "general purpose",
            accuracy=accuracy,
            expert_name=expert_name,
        )

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=[{"type": "text", "text": _HUB_SYSTEM, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            if "```" in raw:
                parts = raw.split("```")
                raw = parts[1] if len(parts) > 1 else raw
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)
            return VariantPrompt(
                expert=data.get("expert", expert_name),
                style=data.get("style", expert_name),
                positive=data.get("positive", ""),
                negative=data.get("negative", ""),
                accuracy_score=float(data.get("accuracy_score", 0.8)),
                rationale=data.get("rationale", ""),
                key_details=data.get("key_details", []),
            )
        except Exception as exc:
            return VariantPrompt(
                expert=expert_name,
                style=expert_name,
                positive=f"High quality {topic}, {expert_name} style",
                negative="blurry, low quality, inaccurate",
                accuracy_score=0.5,
                rationale=f"Fallback prompt due to: {exc}",
                key_details=[],
            )

    async def _consensus(self, topic: str, variants: list[VariantPrompt]) -> dict:
        variants_json = json.dumps(
            [
                {
                    "expert": v.expert,
                    "positive": v.positive,
                    "accuracy_score": v.accuracy_score,
                    "key_details": v.key_details,
                }
                for v in variants
            ],
            indent=2,
        )

        prompt = _CONSENSUS_PROMPT.format(
            n=len(variants),
            topic=topic,
            variants_json=variants_json,
        )

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            if "```" in raw:
                parts = raw.split("```")
                raw = parts[1] if len(parts) > 1 else raw
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw)
        except Exception:
            return {
                "best_variant_index": 0,
                "blended_prompt": variants[0].positive if variants else "",
                "scene_description": f"Image of {topic}",
                "label_map": {},
                "accessibility_text": f"Image depicting {topic}",
                "generation_notes": "",
                "accuracy_confidence": 0.6,
            }
