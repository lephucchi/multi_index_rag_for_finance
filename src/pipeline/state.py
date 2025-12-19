"""
LangGraph State Definition for RAG Pipeline.

Updated for Canonical Answer Framework (CAF) - Step 8.
"""
from typing import TypedDict, List, Optional, Dict, Any


class RAGState(TypedDict):
    """
    State schema for the RAG pipeline.
    
    This state flows through all nodes in the graph.
    Updated to support Canonical Answer Framework (CAF).
    """
    # Input
    query: str
    
    # Routing
    routes: List[str]
    route_scores: Dict[str, float]
    
    # Decomposition  
    is_complex: bool
    sub_queries: List[str]
    sub_query_types: List[str]
    
    # Retrieval
    contexts: List[Dict[str, Any]]
    formatted_context: str
    citations_map: List[Dict[str, Any]]
    
    # NEW: Sub-query organized contexts for CAF
    sub_query_contexts: Dict[str, str]  # {sub_query: formatted_context}
    
    # NEW: Canonical Facts (CAF Pass 1 output)
    canonical_facts: List[Dict[str, Any]]  # List of CanonicalFact dicts
    
    # Generation (CAF Pass 2 output)
    answer: str
    citations: List[Dict[str, Any]]
    is_grounded: bool
    
    # Metadata
    total_time_ms: float
    step_times: Dict[str, float]
    error: Optional[str]


def create_initial_state(query: str) -> RAGState:
    """Create initial state from query."""
    return RAGState(
        query=query,
        routes=[],
        route_scores={},
        is_complex=False,
        sub_queries=[],
        sub_query_types=[],
        contexts=[],
        formatted_context="",
        citations_map=[],
        sub_query_contexts={},  # NEW for CAF
        canonical_facts=[],      # NEW for CAF
        answer="",
        citations=[],
        is_grounded=False,
        total_time_ms=0.0,
        step_times={},
        error=None
    )
