"""
LangGraph Node Functions for RAG Pipeline.

Each node transforms the state and returns the updated state.
"""
import time
import logging
from typing import Dict, Any

from .state import RAGState

logger = logging.getLogger(__name__)

# Cached instances (lazy loaded)
_router = None
_decomposer = None
_retriever = None
_fusion = None
_generator = None


def _get_router():
    global _router
    if _router is None:
        from src.core.router import HybridRouter
        _router = HybridRouter()
    return _router


def _get_decomposer():
    global _decomposer
    if _decomposer is None:
        from src.core.decomposition import QueryDecomposer
        _decomposer = QueryDecomposer()
    return _decomposer


def _get_retriever():
    global _retriever
    if _retriever is None:
        from src.core.retrieval import ParallelRetriever
        _retriever = ParallelRetriever()
    return _retriever


def _get_fusion():
    global _fusion
    if _fusion is None:
        from src.core.retrieval import ResultFusion
        _fusion = ResultFusion()
    return _fusion


def _get_generator():
    global _generator
    if _generator is None:
        from src.core.generator import GroundedGenerator
        _generator = GroundedGenerator()
    return _generator


def route_node(state: RAGState) -> RAGState:
    """Route the query to appropriate indices."""
    router = _get_router()
    start = time.time()
    
    routes, scores = router.route(state["query"])
    
    state["routes"] = routes
    state["route_scores"] = scores
    state["step_times"]["route"] = (time.time() - start) * 1000
    
    logger.info(f"Routed to: {routes}")
    return state


def decompose_node(state: RAGState) -> RAGState:
    """Decompose complex query into sub-queries."""
    decomposer = _get_decomposer()
    start = time.time()
    
    result = decomposer.decompose(state["query"])
    
    state["is_complex"] = result.is_decomposed
    state["sub_queries"] = [sq.query for sq in result.sub_queries]
    state["sub_query_types"] = [sq.query_type for sq in result.sub_queries]
    state["step_times"]["decompose"] = (time.time() - start) * 1000
    
    logger.info(f"Decomposed into {len(state['sub_queries'])} sub-queries")
    return state


def retrieve_node(state: RAGState) -> RAGState:
    """Retrieve documents for sub-queries."""
    retriever = _get_retriever()
    fusion = _get_fusion()
    start = time.time()
    
    # Map sub-queries to routes
    sub_queries = state["sub_queries"] or [state["query"]]
    routes = []
    
    for i, sq_type in enumerate(state.get("sub_query_types", [])):
        if sq_type and sq_type != "UNKNOWN":
            routes.append(sq_type.lower())
        elif i < len(state["routes"]):
            routes.append(state["routes"][i])
        else:
            routes.append(state["routes"][0] if state["routes"] else "financial")
    
    # Ensure routes matches sub_queries length
    while len(routes) < len(sub_queries):
        routes.append(routes[0] if routes else "financial")
    
    # Retrieve
    result = retriever.retrieve_all(sub_queries, routes[:len(sub_queries)])
    
    # Fuse
    fused = fusion.merge(result.documents)
    
    state["contexts"] = [doc.to_dict() for doc in fused.documents]
    state["formatted_context"] = fused.formatted_context
    state["citations_map"] = fused.citations
    state["step_times"]["retrieve"] = (time.time() - start) * 1000
    
    logger.info(f"Retrieved {len(state['contexts'])} documents")
    return state


def generate_node(state: RAGState) -> RAGState:
    """Generate grounded answer with citations."""
    generator = _get_generator()
    start = time.time()
    
    result = generator.generate(
        query=state["query"],
        context=state["formatted_context"],
        citations_map=state["citations_map"]
    )
    
    state["answer"] = result.answer
    state["citations"] = [
        {"number": n, "used": True}
        for n in result.citations_used
    ]
    state["is_grounded"] = result.is_grounded
    state["step_times"]["generate"] = (time.time() - start) * 1000
    
    # Calculate total time
    state["total_time_ms"] = sum(state["step_times"].values())
    
    logger.info(f"Generated answer with {len(result.citations_used)} citations, grounded={result.is_grounded}")
    return state


def should_decompose(state: RAGState) -> bool:
    """Determine if query needs decomposition."""
    from src.core.decomposition import QueryComplexityClassifier
    classifier = QueryComplexityClassifier()
    result = classifier.classify(state["query"])
    return result.is_complex

