"""
LangGraph State Definition for RAG Pipeline.
"""
from typing import TypedDict, List, Optional, Dict, Any


class RAGState(TypedDict):
    """
    State schema for the RAG pipeline.
    
    This state flows through all nodes in the graph.
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
    
    # Generation (Step 5)
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
        answer="",
        citations=[],
        is_grounded=False,
        total_time_ms=0.0,
        step_times={},
        error=None
    )
