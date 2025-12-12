"""
Generator Module - Grounded Answer Generation with Citations.

Provides LLM-based answer generation strictly grounded in retrieved context.
"""
from .config import GeneratorConfig
from .grounded import GroundedGenerator, GenerationResult
from .prompts import GROUNDED_GENERATION_SYSTEM, build_generation_prompt

__all__ = [
    "GeneratorConfig",
    "GroundedGenerator",
    "GenerationResult",
    "GROUNDED_GENERATION_SYSTEM",
    "build_generation_prompt",
]
