"""
Digital Twin - The central orchestrator that sits on top of any AI and provides
a validation, correction, and enhancement layer for all outputs.

Architecture:
  User Query → [DigitalTwin] → route to specialist agents → validate → correct → respond

The twin ensures:
  - All outputs are factually accurate
  - Research is validated against scientific consensus
  - Code is correct and secure
  - Images are generated with accurate labels and descriptions
  - All answers are backed by scientific method where applicable
"""

import asyncio
import json
import os
import time
from typing import Literal, Optional

import anthropic
from pydantic import BaseModel, Field

from .validation_layer import ValidationLayer, ValidationResult
from .truth_engine import TruthEngine, TruthReport
from .correction_engine import CorrectionEngine, CorrectionReport


# ─── Request / Response Models ────────────────────────────────────────────────

class TwinRequest(BaseModel):
    """Input to the Digital Twin."""

    query: str = Field(..., description="The user's query or task")
    context: Optional[str] = Field(None, description="Additional context")
    mode: Literal["auto", "validate", "research", "science", "image", "architect", "code"] = Field(
        "auto", description="Processing mode"
    )
    target_ai_output: Optional[str] = Field(
        None, description="Existing AI output to validate/correct"
    )
    confidence_threshold: float = Field(
        0.85, ge=0.0, le=1.0, description="Minimum acceptable confidence"
    )
    max_correction_rounds: int = Field(3, ge=1, le=5)
    include_scientific_basis: bool = Field(True)
    include_image_prompts: bool = Field(False)


class LayerScore(BaseModel):
    layer: str
    score: float
    passed: bool
    notes: str


class TwinResponse(BaseModel):
    """Full output from the Digital Twin, with all validation metadata."""

    original_query: str
    final_output: str
    corrections_made: list[str] = Field(default_factory=list)
    overall_confidence: float
    truth_score: float
    accuracy_score: float
    layer_scores: list[LayerScore] = Field(default_factory=list)
    scientific_basis: Optional[str] = None
    derived_formulas: list[str] = Field(default_factory=list)
    image_prompts: list[str] = Field(default_factory=list)
    sources_verified: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    processing_rounds: int = 1
    mode_used: str = "auto"
    latency_ms: float = 0.0
    metadata: dict = Field(default_factory=dict)


# ─── Mode Detection ────────────────────────────────────────────────────────────

_MODE_KEYWORDS = {
    "science": [
        "formula", "equation", "theorem", "hypothesis", "derive", "prove",
        "physics", "chemistry", "biology", "calculus", "quantum", "thermodynamic",
        "scientific", "experiment", "theory", "law of", "constant",
    ],
    "research": [
        "research", "study", "paper", "citation", "evidence", "literature",
        "published", "journal", "peer-reviewed", "meta-analysis", "systematic",
    ],
    "image": [
        "image", "picture", "photo", "illustration", "render", "generate image",
        "visualize", "draw", "diagram", "scene", "portrait", "landscape",
    ],
    "architect": [
        "design", "architecture", "system", "diagram", "infrastructure",
        "scalable", "microservice", "database schema", "api design", "pattern",
    ],
    "code": [
        "code", "implement", "function", "class", "algorithm", "script",
        "program", "debug", "fix", "refactor", "test", "unit test",
    ],
}


def detect_mode(query: str) -> str:
    query_lower = query.lower()
    scores = {mode: 0 for mode in _MODE_KEYWORDS}
    for mode, keywords in _MODE_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                scores[mode] += 1
    best = max(scores, key=lambda m: scores[m])
    return best if scores[best] > 0 else "validate"


# ─── System Prompts ────────────────────────────────────────────────────────────

_BASE_SYSTEM = """You are an elite AI Digital Twin — an advanced validation and enhancement
layer operating above any base AI. Your purpose is absolute accuracy, scientific rigor,
and truthful output.

Core principles:
1. TRUTH FIRST: Never output unverified claims. Flag uncertainty explicitly.
2. SCIENTIFIC METHOD: Use observation → hypothesis → prediction → test → conclusion.
3. PRECISION: Every claim must be as specific and measurable as possible.
4. CORRECTION: Actively identify and fix errors in reasoning or fact.
5. TRANSPARENCY: Always show your work and reasoning chain.
6. ENGINEERING EXCELLENCE: Apply best-practice architecture and design patterns.
"""

_MODE_ADDENDUM = {
    "validate": """
You are validating AI output. For every claim:
- Assign a truth confidence (0–100%)
- Identify logical fallacies or factual errors
- Provide corrections with citations where possible
- Give an overall accuracy score
""",
    "research": """
You are a research validation specialist. For every research claim:
- Verify it aligns with peer-reviewed consensus
- Identify methodology weaknesses
- Rate evidence quality (anecdotal / correlational / causal / meta-analytic)
- Flag replication concerns or conflicting studies
""",
    "science": """
You are a scientific derivation engine. When working with science:
- Show full dimensional analysis for any formula
- Cite the physical laws or mathematical axioms used
- Derive step-by-step from first principles when possible
- Identify all assumptions and boundary conditions
- Provide SI units for every quantity
""",
    "image": """
You are an image generation orchestrator. For image requests:
- Generate ultra-detailed, technically accurate prompts
- Specify: lighting, camera angle, color palette, texture, style, composition
- Include accurate labels and annotations
- Provide scene description suitable for alt-text
- Generate 3 prompt variants (photorealistic / artistic / technical diagram)
""",
    "architect": """
You are a system architecture expert. For design tasks:
- Apply SOLID principles, 12-factor app, CAP theorem as appropriate
- Identify single points of failure
- Recommend proven patterns (CQRS, Event Sourcing, Saga, etc.)
- Estimate complexity and scalability implications
- Produce structured outputs: components, interfaces, data flows
""",
    "code": """
You are a senior software engineer and security auditor. For code:
- Apply OWASP Top-10 security checks
- Enforce clean code principles (SRP, DRY, YAGNI)
- Include type annotations, docstrings, error handling
- Write testable, modular code
- Flag any potential bugs or edge cases
""",
}


# ─── Digital Twin ──────────────────────────────────────────────────────────────

class DigitalTwin:
    """
    The central AI Digital Twin.

    It wraps any AI interaction with a multi-layer validation pipeline:
      1. Mode detection
      2. Primary generation (or intake of existing output)
      3. Truth layer validation
      4. Correction loop (up to N rounds)
      5. Final validation scoring
      6. Response assembly
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-opus-4-6"):
        self.client = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
        self.async_client = anthropic.AsyncAnthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
        self.model = model
        self.validation_layer = ValidationLayer(self.client, model)
        self.truth_engine = TruthEngine(self.client, model)
        self.correction_engine = CorrectionEngine(self.client, model)

    # ── public API ──────────────────────────────────────────────────────────

    def process(self, request: TwinRequest) -> TwinResponse:
        """Synchronous entry point."""
        return asyncio.run(self.aprocess(request))

    async def aprocess(self, request: TwinRequest) -> TwinResponse:
        """Async entry point — primary processing pipeline."""
        t0 = time.monotonic()

        mode = request.mode if request.mode != "auto" else detect_mode(request.query)

        # Step 1 — generate or receive base output
        if request.target_ai_output:
            base_output = request.target_ai_output
        else:
            base_output = await self._generate(request, mode)

        # Step 2 — run truth engine
        truth_report = await self.truth_engine.analyze(request.query, base_output, mode)

        # Step 3 — correction loop
        current_output = base_output
        all_corrections: list[str] = []
        rounds = 1

        for _ in range(request.max_correction_rounds):
            if truth_report.overall_truth_score >= request.confidence_threshold:
                break
            correction = await self.correction_engine.correct(
                request.query, current_output, truth_report, mode
            )
            if correction.corrections:
                current_output = correction.corrected_output
                all_corrections.extend(correction.corrections)
                rounds += 1
                truth_report = await self.truth_engine.analyze(request.query, current_output, mode)
            else:
                break

        # Step 4 — full validation scoring
        validation = await self.validation_layer.validate(request.query, current_output, mode)

        # Step 5 — optional enrichments
        scientific_basis = None
        derived_formulas: list[str] = []
        if request.include_scientific_basis and mode in ("science", "research", "architect"):
            sci = await self._derive_scientific_basis(request.query, current_output, mode)
            scientific_basis = sci.get("basis")
            derived_formulas = sci.get("formulas", [])

        image_prompts: list[str] = []
        if request.include_image_prompts or mode == "image":
            image_prompts = await self._generate_image_prompts(request.query, current_output)

        latency_ms = (time.monotonic() - t0) * 1000

        layer_scores = [
            LayerScore(
                layer=r.layer,
                score=r.score,
                passed=r.passed,
                notes=r.notes,
            )
            for r in validation.results
        ]

        overall_confidence = _harmonic_mean(
            [truth_report.overall_truth_score, validation.aggregate_score]
        )

        return TwinResponse(
            original_query=request.query,
            final_output=current_output,
            corrections_made=all_corrections,
            overall_confidence=overall_confidence,
            truth_score=truth_report.overall_truth_score,
            accuracy_score=validation.aggregate_score,
            layer_scores=layer_scores,
            scientific_basis=scientific_basis,
            derived_formulas=derived_formulas,
            image_prompts=image_prompts,
            sources_verified=truth_report.sources_verified,
            warnings=truth_report.warnings + validation.warnings,
            processing_rounds=rounds,
            mode_used=mode,
            latency_ms=round(latency_ms, 1),
            metadata={
                "model": self.model,
                "truth_details": truth_report.model_dump(),
            },
        )

    # ── private helpers ──────────────────────────────────────────────────────

    async def _generate(self, request: TwinRequest, mode: str) -> str:
        system = _BASE_SYSTEM + _MODE_ADDENDUM.get(mode, "")
        user_msg = request.query
        if request.context:
            user_msg = f"Context:\n{request.context}\n\nQuery:\n{request.query}"

        response = await self.async_client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=[
                {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
            ],
            messages=[{"role": "user", "content": user_msg}],
        )
        return response.content[0].text

    async def _derive_scientific_basis(self, query: str, output: str, mode: str) -> dict:
        prompt = f"""Given this output, derive or state the scientific/mathematical basis that supports it.
Include any relevant formulas, laws, or theorems. Be precise.

Output to analyse:
{output}

Return JSON with keys: "basis" (string), "formulas" (list of strings).
Only return valid JSON."""

        response = await self.async_client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        try:
            text = response.content[0].text.strip()
            # strip markdown code fences if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text)
        except Exception:
            return {"basis": response.content[0].text, "formulas": []}

    async def _generate_image_prompts(self, query: str, context: str) -> list[str]:
        prompt = f"""Generate 3 highly accurate image generation prompts for the following:

Topic: {query}
Context: {context[:500]}

Each prompt should be:
1. Photorealistic version — maximum detail, real-world accuracy
2. Technical diagram version — labeled components, clean vector-style
3. Artistic/conceptual version — evocative, stylized

Return as JSON array of 3 strings. Only return valid JSON."""

        response = await self.async_client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        try:
            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text)
        except Exception:
            return [response.content[0].text]


# ─── Utilities ─────────────────────────────────────────────────────────────────

def _harmonic_mean(values: list[float]) -> float:
    if not values or any(v == 0 for v in values):
        return 0.0
    return len(values) / sum(1 / v for v in values)
