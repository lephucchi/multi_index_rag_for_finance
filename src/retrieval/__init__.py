"""
Retrieval Module

Provides parallel retrieval from multiple vector indices and result fusion.

Components:
- ParallelRetriever: Async parallel retrieval from Supabase
- ResultFusion: Merge and rank documents from multiple sources
- RetrieverConfig/FusionConfig: Configuration management

Example:
    >>> from src.retrieval import ParallelRetriever, ResultFusion
    >>> retriever = ParallelRetriever()
    >>> result = retriever.retrieve_all(
    ...     sub_queries=["ROE là gì", "VNM ROE"],
    ...     routes=["glossary", "financial"]
    ... )
    >>> fusion = ResultFusion()
    >>> context = fusion.merge(result.documents)
"""
from .config import RetrieverConfig, FusionConfig, INDEX_TABLE_MAP, get_table_name
from .parallel import (
    ParallelRetriever,
    RetrievalResult,
    RetrievedDocument,
    EncoderProtocol,
    VectorDBProtocol,
)
from .fusion import ResultFusion, FusedContext, FusionStrategy

__all__ = [
    # Config
    "RetrieverConfig",
    "FusionConfig",
    "INDEX_TABLE_MAP",
    "get_table_name",
    # Retrieval
    "ParallelRetriever",
    "RetrievalResult",
    "RetrievedDocument",
    "EncoderProtocol",
    "VectorDBProtocol",
    # Fusion
    "ResultFusion",
    "FusedContext",
    "FusionStrategy",
]
