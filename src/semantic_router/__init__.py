# Semantic Router Package
from .router import SemanticRouter, HybridRouter, create_router
from .config import RouterConfig, DEFAULT_CONFIG, FAST_CONFIG, ACCURATE_CONFIG
from .routes import ROUTES, glossary_route, legal_route, financial_route, news_route
from .retriever import SupabaseRetriever, RouterRetrieverPipeline, Document
from .evaluation import evaluate_router, tune_thresholds, EVALUATION_DATASET

__all__ = [
    # Router
    "SemanticRouter",
    "HybridRouter",
    "create_router",
    # Config
    "RouterConfig",
    "DEFAULT_CONFIG",
    "FAST_CONFIG",
    "ACCURATE_CONFIG",
    # Routes
    "ROUTES",
    "glossary_route",
    "legal_route",
    "financial_route",
    "news_route",
    # Retriever
    "SupabaseRetriever",
    "RouterRetrieverPipeline",
    "Document",
    # Evaluation
    "evaluate_router",
    "tune_thresholds",
    "EVALUATION_DATASET",
]
