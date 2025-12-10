"""
Query Decomposition Module

Provides functionality to decompose complex queries into atomic sub-queries
for more accurate retrieval in multi-index RAG systems.

Components:
- QueryComplexityClassifier: Fast rule-based complexity detection
- QueryDecomposer: LLM-based decomposition using Gemini
- DecomposerConfig: Configuration management

Example:
    >>> from src.query_decomposition import QueryDecomposer
    >>> decomposer = QueryDecomposer()
    >>> result = decomposer.decompose("ROE là gì và VNM có ROE bao nhiêu")
    >>> print(result.sub_queries)
"""
from .config import DecomposerConfig, ClassifierConfig, QueryType
from .classifier import QueryComplexityClassifier, ClassificationResult
from .decomposer import QueryDecomposer, DecompositionResult, SubQuery

__all__ = [
    # Config
    "DecomposerConfig",
    "ClassifierConfig",
    "QueryType",
    # Classifier
    "QueryComplexityClassifier",
    "ClassificationResult",
    # Decomposer
    "QueryDecomposer",
    "DecompositionResult",
    "SubQuery",
]
