"""
LangGraph State Graph Definition.

This is the main entry point for the RAG pipeline.
"""
import logging
from typing import Dict, Any

from .state import RAGState, create_initial_state
from .nodes import route_node, decompose_node, retrieve_node, should_decompose

logger = logging.getLogger(__name__)

# Check if langgraph is installed
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("langgraph not installed. Install with: pip install langgraph")


def build_rag_graph():
    """
    Build the RAG pipeline graph.
    
    Returns:
        Compiled StateGraph ready for invocation.
    """
    if not LANGGRAPH_AVAILABLE:
        raise ImportError("langgraph not installed")
    
    # Create graph with state schema
    graph = StateGraph(RAGState)
    
    # Add nodes
    graph.add_node("route", route_node)
    graph.add_node("decompose", decompose_node)
    graph.add_node("retrieve", retrieve_node)
    # graph.add_node("generate", generate_node)  # Step 5
    
    # Set entry point
    graph.set_entry_point("route")
    
    # Conditional edges: route → decompose OR retrieve
    graph.add_conditional_edges(
        "route",
        should_decompose,
        {
            True: "decompose",
            False: "retrieve"
        }
    )
    
    # Linear edges
    graph.add_edge("decompose", "retrieve")
    graph.add_edge("retrieve", END)  # Will be → generate in Step 5
    
    # Compile
    return graph.compile()


# Singleton instance
_compiled_graph = None


def get_rag_graph():
    """Get or create the compiled RAG graph."""
    global _compiled_graph
    if _compiled_graph is None:
        logger.info("Building RAG graph...")
        _compiled_graph = build_rag_graph()
        logger.info("RAG graph ready.")
    return _compiled_graph


def run_rag_pipeline(query: str) -> Dict[str, Any]:
    """
    Run a query through the RAG pipeline.
    
    Args:
        query: User question
        
    Returns:
        Final state with contexts (and answer in Step 5)
    """
    graph = get_rag_graph()
    initial_state = create_initial_state(query)
    
    result = graph.invoke(initial_state)
    
    return {
        "query": result["query"],
        "routes": result["routes"],
        "sub_queries": result["sub_queries"],
        "is_complex": result["is_complex"],
        "contexts": result["contexts"],
        "formatted_context": result["formatted_context"],
        "citations_map": result["citations_map"],
        "step_times": result["step_times"],
        # Generation fields (Step 5)
        "answer": result.get("answer", ""),
        "is_grounded": result.get("is_grounded", False),
    }


# Fallback for when langgraph is not installed
def run_rag_pipeline_fallback(query: str) -> Dict[str, Any]:
    """Fallback pipeline without LangGraph."""
    state = create_initial_state(query)
    
    # Manual pipeline execution
    state = route_node(state)
    if should_decompose(state):
        state = decompose_node(state)
    state = retrieve_node(state)
    
    return {
        "query": state["query"],
        "routes": state["routes"],
        "sub_queries": state["sub_queries"],
        "is_complex": state["is_complex"],
        "contexts": state["contexts"],
        "formatted_context": state["formatted_context"],
        "citations_map": state["citations_map"],
        "step_times": state["step_times"],
        "answer": "",
        "is_grounded": False,
    }
