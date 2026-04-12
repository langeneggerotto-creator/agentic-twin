"""
FastAPI REST server for the Digital Twin.

Endpoints:
  POST /twin/process          — Full Digital Twin pipeline
  POST /twin/validate         — Validate existing AI output
  POST /twin/research         — Research validation
  POST /twin/science/formula  — Derive a formula
  POST /twin/science/test     — Design a hypothesis test
  POST /twin/science/theory   — Build a scientific theory
  POST /twin/image/generate   — Multiplayer image generation
  POST /twin/image/describe   — Generate image descriptions
  POST /twin/image/labels     — Validate image labels
  GET  /twin/health           — Health check

Run:
  uvicorn api.server:app --reload --port 8080
"""

import os
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.digital_twin import DigitalTwin, TwinRequest, TwinResponse
from agents.validator_agent import ValidatorAgent
from agents.researcher_agent import ResearcherAgent
from agents.scientist_agent import ScientistAgent
from agents.architect_agent import ArchitectAgent
from agents.image_orchestrator import ImageOrchestrator
from science.formula_engine import FormulaEngine
from science.hypothesis_tester import HypothesisTester
from science.theory_builder import TheoryBuilder
from image.generation_hub import GenerationHub, GenerationRequest
from image.label_validator import LabelValidator
from image.description_engine import DescriptionEngine


app = FastAPI(
    title="Digital Twin AI Validation Layer",
    description=(
        "An advanced AI validation and enhancement layer that sits on top of any AI. "
        "Provides truth verification, scientific method application, multiplayer image "
        "generation, architectural review, and iterative error correction."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Lazy singletons ──────────────────────────────────────────────────────────

def _twin() -> DigitalTwin:
    return DigitalTwin()

def _validator() -> ValidatorAgent:
    return ValidatorAgent()

def _researcher() -> ResearcherAgent:
    return ResearcherAgent()

def _scientist() -> ScientistAgent:
    return ScientistAgent()

def _architect() -> ArchitectAgent:
    return ArchitectAgent()

def _img_orch() -> ImageOrchestrator:
    return ImageOrchestrator()

def _formula_engine() -> FormulaEngine:
    return FormulaEngine()

def _hypothesis_tester() -> HypothesisTester:
    return HypothesisTester()

def _theory_builder() -> TheoryBuilder:
    return TheoryBuilder()

def _gen_hub() -> GenerationHub:
    return GenerationHub()

def _label_validator() -> LabelValidator:
    return LabelValidator()

def _desc_engine() -> DescriptionEngine:
    return DescriptionEngine()


# ─── Request / Response helpers ───────────────────────────────────────────────

class ValidateRequest(BaseModel):
    query: str
    ai_output: str

class ResearchRequest(BaseModel):
    query: str
    text: str

class FormulaRequest(BaseModel):
    query: str
    domain: str = "auto"

class HypothesisRequest(BaseModel):
    claim: str
    context: str = ""

class TheoryRequest(BaseModel):
    topic: str
    phenomena: str = ""
    existing_theories: str = ""

class ArchitectRequest(BaseModel):
    query: str

class ScienceRequest(BaseModel):
    query: str
    context: str = ""

class ImageGenRequest(BaseModel):
    topic: str
    style_preference: str = "auto"
    accuracy_priority: str = "maximum"
    use_case: str = ""
    target_audience: str = "general"
    num_variants: int = 3

class ImageDescribeRequest(BaseModel):
    topic: str
    style: str = "photorealistic"
    context: str = ""
    domain: str = "general"
    elements: list[str] = Field(default_factory=list)

class LabelValidateRequest(BaseModel):
    labels: dict[str, str]
    topic: str
    content_type: str = "diagram"


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/twin/health")
async def health():
    return {
        "status": "ok",
        "service": "Digital Twin AI Validation Layer",
        "version": "1.0.0",
    }


@app.post("/twin/process", response_model=TwinResponse)
async def process(request: TwinRequest):
    """
    Full Digital Twin pipeline.
    Generates or validates output, runs truth engine, corrects errors,
    and returns a fully validated response with confidence scores.
    """
    try:
        twin = _twin()
        return await twin.aprocess(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/twin/validate")
async def validate_output(request: ValidateRequest):
    """Validate an existing AI output for accuracy."""
    try:
        agent = _validator()
        result = await agent.avalidate(request.query, request.ai_output)
        return {
            "is_accurate": result.is_accurate,
            "quality_grade": result.quality_grade,
            "overall_confidence": result.overall_confidence,
            "corrections": result.corrections,
            "flagged_claims": result.flagged_claims,
            "validated_output": result.validated_output,
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/twin/research")
async def validate_research(request: ResearchRequest):
    """Validate research claims using evidence-based methodology."""
    try:
        agent = _researcher()
        report = await agent.avalidate_research(request.query, request.text)
        return {
            "overall_evidence_quality": report.overall_evidence_quality,
            "consensus_score": report.consensus_score,
            "methodology_rating": report.methodology_rating,
            "statistical_validity": report.statistical_validity,
            "claims": [
                {
                    "claim": c.claim,
                    "evidence_level": c.evidence_level,
                    "consensus_alignment": c.consensus_alignment,
                    "quality_score": c.quality_score,
                    "concerns": c.concerns,
                    "counter_evidence": c.counter_evidence,
                }
                for c in report.claims
            ],
            "recommendations": report.recommendations,
            "validated_summary": report.validated_summary,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/twin/science")
async def science_analysis(request: ScienceRequest):
    """Apply the full scientific method to a query."""
    try:
        agent = _scientist()
        analysis = await agent.aanalyse(request.query, request.context)
        return {
            "hypotheses": [
                {
                    "statement": h.statement,
                    "null_hypothesis": h.null_hypothesis,
                    "prediction": h.prediction,
                    "test_method": h.test_method,
                    "confidence_prior": h.confidence_prior,
                }
                for h in analysis.hypotheses
            ],
            "derived_formulas": [
                {
                    "formula": f.formula,
                    "latex": f.latex,
                    "derivation_steps": f.derivation_steps,
                    "physical_laws_used": f.physical_laws_used,
                    "assumptions": f.assumptions,
                    "validity_domain": f.validity_domain,
                }
                for f in analysis.derived_formulas
            ],
            "experiment_design": analysis.experiment_design,
            "predicted_outcomes": analysis.predicted_outcomes,
            "conclusion": analysis.conclusion,
            "confidence": analysis.confidence,
            "open_questions": analysis.open_questions,
            "theory_basis": analysis.theory_basis,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/twin/science/formula")
async def derive_formula(request: FormulaRequest):
    """Derive a formula from first principles."""
    try:
        engine = _formula_engine()
        formula = await engine.aderive(request.query, request.domain)
        return {
            "name": formula.name,
            "formula": formula.formula,
            "latex": formula.latex,
            "description": formula.description,
            "domain": formula.domain,
            "subdomain": formula.subdomain,
            "variables": formula.variables,
            "derivation_steps": formula.derivation_steps,
            "physical_laws_used": formula.physical_laws_used,
            "assumptions": formula.assumptions,
            "validity_domain": formula.validity_domain,
            "breakdown_conditions": formula.breakdown_conditions,
            "numerical_example": formula.numerical_example,
            "related_formulas": formula.related_formulas,
            "dimensional_analysis": formula.dimensional_analysis,
            "confidence": formula.confidence,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/twin/science/hypothesis")
async def design_hypothesis_test(request: HypothesisRequest):
    """Design a rigorous hypothesis test."""
    try:
        tester = _hypothesis_tester()
        result = await tester.adesign_test(request.claim, request.context)
        return {
            "h0": result.h0,
            "h1": result.h1,
            "test_type": result.test_type,
            "required_sample_size": result.required_sample_size,
            "effect_size_estimate": result.effect_size_estimate,
            "statistical_power": result.statistical_power,
            "alpha_threshold": result.alpha_threshold,
            "confounders": result.confounders,
            "control_strategy": result.control_strategy,
            "experiment_protocol": result.experiment_protocol,
            "outcome_metrics": result.outcome_metrics,
            "interpretation_guide": result.interpretation_guide,
            "replication_design": result.replication_design,
            "confidence": result.confidence,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/twin/science/theory")
async def build_theory(request: TheoryRequest):
    """Build or evaluate a scientific theory."""
    try:
        builder = _theory_builder()
        theory = await builder.abuild(request.topic, request.phenomena, request.existing_theories)
        return {
            "name": theory.name,
            "domain": theory.domain,
            "core_postulates": theory.core_postulates,
            "explanatory_scope": theory.explanatory_scope,
            "predictions": [
                {
                    "prediction": p.prediction,
                    "testable": p.testable,
                    "test_method": p.test_method,
                    "falsification_condition": p.falsification_condition,
                }
                for p in theory.predictions
            ],
            "supporting_evidence": theory.supporting_evidence,
            "contradicting_evidence": theory.contradicting_evidence,
            "mathematical_framework": theory.mathematical_framework,
            "key_equations": theory.key_equations,
            "limitations": theory.limitations,
            "open_problems": theory.open_problems,
            "falsification_test": theory.falsification_test,
            "confidence_level": theory.confidence_level,
            "maturity": theory.maturity,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/twin/architect")
async def architect_review(request: ArchitectRequest):
    """Review and improve system architecture."""
    try:
        agent = _architect()
        review = await agent.areview(request.query)
        return {
            "components": [
                {
                    "name": c.name,
                    "responsibility": c.responsibility,
                    "interfaces": c.interfaces,
                    "dependencies": c.dependencies,
                    "scalability_notes": c.scalability_notes,
                }
                for c in review.components
            ],
            "design_patterns": review.design_patterns,
            "data_flows": review.data_flows,
            "scalability_rating": review.scalability_rating,
            "reliability_rating": review.reliability_rating,
            "security_rating": review.security_rating,
            "issues": review.issues,
            "recommendations": review.recommendations,
            "mermaid_diagram": review.mermaid_diagram,
            "improved_design": review.improved_design,
            "complexity_estimate": review.complexity_estimate,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/twin/image/generate")
async def generate_image(request: ImageGenRequest):
    """Generate multiplayer image prompts with maximum accuracy."""
    try:
        hub = _gen_hub()
        gen_request = GenerationRequest(
            topic=request.topic,
            style_preference=request.style_preference,  # type: ignore[arg-type]
            accuracy_priority=request.accuracy_priority,  # type: ignore[arg-type]
            use_case=request.use_case,
            target_audience=request.target_audience,
            num_variants=request.num_variants,
        )
        result = await hub.agenerate(gen_request)
        return {
            "topic": result.topic,
            "blended_prompt": result.blended_prompt,
            "consensus_best": {
                "expert": result.consensus_best.expert,
                "style": result.consensus_best.style,
                "positive": result.consensus_best.positive,
                "negative": result.consensus_best.negative,
                "accuracy_score": result.consensus_best.accuracy_score,
            },
            "all_variants": [
                {
                    "expert": v.expert,
                    "style": v.style,
                    "positive": v.positive,
                    "negative": v.negative,
                    "accuracy_score": v.accuracy_score,
                    "key_details": v.key_details,
                }
                for v in result.variants
            ],
            "scene_description": result.scene_description,
            "label_map": result.label_map,
            "accessibility_text": result.accessibility_text,
            "generation_notes": result.generation_notes,
            "accuracy_confidence": result.accuracy_confidence,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/twin/image/describe")
async def describe_image(request: ImageDescribeRequest):
    """Generate comprehensive descriptions for an image."""
    try:
        engine = _desc_engine()
        desc = await engine.adescribe(
            topic=request.topic,
            style=request.style,
            context=request.context,
            domain=request.domain,
            elements=request.elements or None,
        )
        return {
            "full_description": desc.full_description,
            "alt_text": desc.alt_text,
            "technical_caption": desc.technical_caption,
            "figure_legend": desc.figure_legend,
            "social_caption": desc.social_caption,
            "key_elements": desc.key_elements,
            "accuracy_notes": desc.accuracy_notes,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/twin/image/labels")
async def validate_labels(request: LabelValidateRequest):
    """Validate image labels for accuracy and correct terminology."""
    try:
        validator = _label_validator()
        report = await validator.avalidate(request.labels, request.topic, request.content_type)
        return {
            "overall_accuracy": report.overall_accuracy,
            "corrections_needed": report.corrections_needed,
            "terminology_standard": report.terminology_standard,
            "labels_checked": [
                {
                    "label": c.label,
                    "is_accurate": c.is_accurate,
                    "issue": c.issue,
                    "correction": c.correction,
                    "confidence": c.confidence,
                }
                for c in report.labels_checked
            ],
            "validated_labels": report.validated_labels,
            "recommendations": report.recommendations,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
