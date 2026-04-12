"""
Label Validator — verifies that image labels are accurate and unambiguous.

For any image with labels (diagrams, charts, anatomical drawings, etc.):
  • Checks label-element correspondence
  • Verifies spelling and terminology
  • Validates scientific nomenclature
  • Ensures labels are spatially correct (label points to right element)
  • Suggests corrections for inaccurate labels
"""

import asyncio
import json
import os
from dataclasses import dataclass, field

import anthropic


@dataclass
class LabelCheck:
    label: str
    is_accurate: bool
    issue: str
    correction: str
    confidence: float


@dataclass
class LabelReport:
    labels_checked: list[LabelCheck]
    overall_accuracy: float
    terminology_standard: str
    corrections_needed: int
    validated_labels: dict[str, str]    # corrected label → description
    recommendations: list[str]


_VALIDATOR_PROMPT = """Validate these labels for a {content_type} image about "{topic}".

Labels to validate:
{labels_json}

For each label:
1. Check if the term is correct (spelling, scientific nomenclature, technical term)
2. Check if it would point to the right element in context
3. Verify the description is accurate
4. Suggest corrections

Return ONLY valid JSON:
{{
  "labels_checked": [
    {{
      "label": "<original label>",
      "is_accurate": <bool>,
      "issue": "<what's wrong, or 'none'>",
      "correction": "<corrected label, or same if accurate>",
      "confidence": <float 0.0-1.0>
    }}
  ],
  "overall_accuracy": <float 0.0-1.0>,
  "terminology_standard": "<what standard/convention labels should follow>",
  "corrections_needed": <integer>,
  "validated_labels": {{"<corrected label>": "<precise element description>"}},
  "recommendations": ["<recommendation for label quality>"]
}}"""


class LabelValidator:
    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-6"):
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key or os.environ["ANTHROPIC_API_KEY"]
        )
        self.model = model

    def validate(
        self,
        labels: dict[str, str],
        topic: str,
        content_type: str = "diagram",
    ) -> LabelReport:
        return asyncio.run(self.avalidate(labels, topic, content_type))

    async def avalidate(
        self,
        labels: dict[str, str],
        topic: str,
        content_type: str = "diagram",
    ) -> LabelReport:
        prompt = _VALIDATOR_PROMPT.format(
            content_type=content_type,
            topic=topic,
            labels_json=json.dumps(labels, indent=2),
        )

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

        try:
            data = json.loads(raw)
        except Exception:
            return LabelReport(
                labels_checked=[],
                overall_accuracy=0.5,
                terminology_standard="",
                corrections_needed=0,
                validated_labels=labels,
                recommendations=[],
            )

        checks = [
            LabelCheck(
                label=c.get("label", ""),
                is_accurate=bool(c.get("is_accurate", True)),
                issue=c.get("issue", "none"),
                correction=c.get("correction", ""),
                confidence=float(c.get("confidence", 0.8)),
            )
            for c in data.get("labels_checked", [])
        ]

        return LabelReport(
            labels_checked=checks,
            overall_accuracy=float(data.get("overall_accuracy", 0.8)),
            terminology_standard=data.get("terminology_standard", ""),
            corrections_needed=int(data.get("corrections_needed", 0)),
            validated_labels=data.get("validated_labels", labels),
            recommendations=data.get("recommendations", []),
        )
