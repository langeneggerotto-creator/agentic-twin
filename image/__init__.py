"""
Image module — multiplayer image generation, label validation, description engine.
"""
from .generation_hub import GenerationHub, GenerationRequest, GenerationResult
from .label_validator import LabelValidator, LabelReport
from .description_engine import DescriptionEngine, SceneDescription

__all__ = [
    "GenerationHub",
    "GenerationRequest",
    "GenerationResult",
    "LabelValidator",
    "LabelReport",
    "DescriptionEngine",
    "SceneDescription",
]
