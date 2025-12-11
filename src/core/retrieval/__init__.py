"""
Retrieval Module - Parallel Vector Search and Result Fusion.

Provides async parallel retrieval from multiple Supabase indices.
"""
from .parallel import ParallelRetriever, RetrievalResult, RetrievedDocument
from .fusion import ResultFusion, FusedContext, FusionStrategy

__all__ = [
    "ParallelRetriever",
    "RetrievalResult",
    "RetrievedDocument",
    "ResultFusion",
    "FusedContext",
    "FusionStrategy",
]
