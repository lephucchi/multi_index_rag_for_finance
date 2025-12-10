"""
Pipeline Module

Provides the unified RAG pipeline integrating all components.

Example:
    >>> from src.pipeline import RAGPipeline, create_pipeline
    >>> pipeline = create_pipeline()
    >>> result = pipeline.process("ROE là gì và VNM có ROE bao nhiêu")
"""
from .rag_pipeline import RAGPipeline, PipelineResult, create_pipeline

__all__ = [
    "RAGPipeline",
    "PipelineResult",
    "create_pipeline",
]
