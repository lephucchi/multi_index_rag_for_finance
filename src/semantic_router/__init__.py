"""
Semantic Router Module

Provides intelligent query routing to appropriate vector indices
using a hybrid rule-based + semantic similarity approach.

Components:
- SemanticRouter: Pure semantic similarity routing
- HybridRouter: Rule-based + semantic hybrid (recommended)
- RouterConfig: Configuration management

Example:
    >>> from src.semantic_router import HybridRouter
    >>> router = HybridRouter()
    >>> routes, scores = router.route("ROE là gì và VNM có ROE bao nhiêu")
    >>> print(routes)
    ['glossary', 'financial']
"""
from .config import RouterConfig, DEFAULT_CONFIG, FAST_CONFIG, ACCURATE_CONFIG
from .router import SemanticRouter, HybridRouter, create_router
from .routes import Route, ROUTES

__all__ = [
    # Config
    "RouterConfig",
    "DEFAULT_CONFIG",
    "FAST_CONFIG",
    "ACCURATE_CONFIG",
    # Router
    "SemanticRouter",
    "HybridRouter",
    "create_router",
    # Routes
    "Route",
    "ROUTES",
]
