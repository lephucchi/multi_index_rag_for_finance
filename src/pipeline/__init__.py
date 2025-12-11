"""
Pipeline Module - LangGraph RAG Orchestration.

Provides the unified RAG pipeline integrating all components via LangGraph.

Components:
- RAGState: Pipeline state schema
- Nodes: route, decompose, retrieve, generate
- Graph: StateGraph with conditional edges

Example:
    >>> from src.pipeline import run_rag_pipeline
    >>> result = run_rag_pipeline("ROE là gì và VNM có ROE bao nhiêu")
    >>> print(result["answer"])
"""
from .state import RAGState, create_initial_state
from .nodes import route_node, decompose_node, retrieve_node
from .graph import build_rag_graph, get_rag_graph, run_rag_pipeline

__all__ = [
    # State
    "RAGState",
    "create_initial_state",
    # Nodes
    "route_node",
    "decompose_node",
    "retrieve_node",
    # Graph
    "build_rag_graph",
    "get_rag_graph",
    "run_rag_pipeline",
]
