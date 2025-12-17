"""
LangGraph Node Functions for RAG Pipeline.

Each node transforms the state and returns the updated state.
With comprehensive logging for debugging and pipeline analysis.
"""
import time
import logging
from typing import Dict, Any

from .state import RAGState

# Configure detailed logger
logger = logging.getLogger(__name__)

# Cached instances (lazy loaded)
_router = None
_decomposer = None
_retriever = None
_fusion = None
_generator = None


def _log_separator(title: str = "", char: str = "=", length: int = 60):
    """Log a visual separator."""
    if title:
        padding = (length - len(title) - 2) // 2
        logger.info(f"{char * padding} {title} {char * padding}")
    else:
        logger.info(char * length)


def _truncate(text: str, max_len: int = 150) -> str:
    """Truncate text for logging."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


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
    _log_separator("STEP 1: ROUTING")
    router = _get_router()
    start = time.time()
    
    query = state["query"]
    logger.info(f"[INPUT] Query: {_truncate(query)}")
    
    routes, scores = router.route(query)
    
    state["routes"] = routes
    state["route_scores"] = scores
    state["step_times"]["route"] = (time.time() - start) * 1000
    
    # Detailed logging
    logger.info(f"[OUTPUT] Selected Routes: {routes}")
    logger.info("[OUTPUT] All Scores:")
    for index, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        bar = "#" * int(score * 20)
        logger.info(f"  - {index:12s}: {score:.3f} {bar}")
    logger.info(f"[TIME] Route: {state['step_times']['route']:.2f}ms")
    
    return state


def decompose_node(state: RAGState) -> RAGState:
    """Decompose complex query into sub-queries."""
    _log_separator("STEP 2: DECOMPOSITION")
    decomposer = _get_decomposer()
    start = time.time()
    
    query = state["query"]
    logger.info(f"[INPUT] Query: {_truncate(query)}")
    
    result = decomposer.decompose(query)
    
    state["is_complex"] = result.is_decomposed
    state["sub_queries"] = [sq.query for sq in result.sub_queries]
    state["sub_query_types"] = [sq.query_type for sq in result.sub_queries]
    state["step_times"]["decompose"] = (time.time() - start) * 1000
    
    # Detailed logging
    logger.info(f"[OUTPUT] Is Decomposed: {result.is_decomposed}")
    logger.info(f"[OUTPUT] Method: {result.method}")
    logger.info(f"[OUTPUT] Sub-queries ({len(result.sub_queries)}):")
    for i, sq in enumerate(result.sub_queries, 1):
        logger.info(f"  [{i}] Type: {sq.query_type}")
        logger.info(f"      Query: {_truncate(sq.query, 100)}")
    if result.reasoning:
        logger.info(f"[OUTPUT] Reasoning: {_truncate(result.reasoning, 200)}")
    logger.info(f"[TIME] Decompose: {state['step_times']['decompose']:.2f}ms")
    
    return state


async def retrieve_node(state: RAGState) -> RAGState:
    """Retrieve documents for sub-queries (async version)."""
    _log_separator("STEP 3: RETRIEVAL")
    retriever = _get_retriever()
    fusion = _get_fusion()
    start = time.time()
    
    # Import translator for cross-lingual retrieval
    from src.core.retrieval import get_translator
    translator = get_translator()
    
    # Map sub-queries to routes
    sub_queries = state["sub_queries"] or [state["query"]]
    sub_query_types = state.get("sub_query_types", [])
    
    # Check if decomposition failed (single query with UNKNOWN type)
    decomposition_failed = (
        len(sub_queries) == 1 and
        len(sub_query_types) >= 1 and
        sub_query_types[0] == "UNKNOWN"
    )
    
    if decomposition_failed:
        # When decomposition fails, query ALL routes selected by router
        # This ensures we don't miss relevant documents from other indices
        all_routes = state["routes"]
        logger.info(f"[FALLBACK] Decomposition failed, querying ALL routes: {all_routes}")
        
        # Replicate the query for each route
        sub_queries = [sub_queries[0]] * len(all_routes)
        routes = all_routes
    else:
        # Normal case: map sub-queries to their respective routes
        routes = []
        for i, sq_type in enumerate(sub_query_types):
            if sq_type and sq_type != "UNKNOWN":
                routes.append(sq_type.lower())
            elif i < len(state["routes"]):
                routes.append(state["routes"][i])
            else:
                routes.append(state["routes"][0] if state["routes"] else "financial")
        
        # Ensure routes matches sub_queries length
        while len(routes) < len(sub_queries):
            routes.append(routes[0] if routes else "financial")
    
    # Translate queries for glossary index (Vietnamese -> English)
    translated_queries = []
    for sq, route in zip(sub_queries, routes[:len(sub_queries)]):
        if route == "glossary" and translator.is_available:
            translated = translator.translate_for_index(sq, "glossary")
            translated_queries.append(translated)
            if translated != sq:
                logger.info(f"[TRANSLATE] '{sq}' -> '{translated}'")
        else:
            translated_queries.append(sq)
    
    # Log retrieval plan
    logger.info("[INPUT] Retrieval Plan:")
    for i, (sq, tq, route) in enumerate(zip(sub_queries, translated_queries, routes[:len(sub_queries)]), 1):
        logger.info(f"  [{i}] Query: {_truncate(sq, 80)}")
        if tq != sq:
            logger.info(f"      Translated: {_truncate(tq, 80)}")
        logger.info(f"      -> Index: {route}")
    
    # Retrieve with translated queries
    result = await retriever.retrieve_all_async(translated_queries, routes[:len(translated_queries)])
    
    logger.info(f"[OUTPUT] Documents Retrieved: {len(result.documents)}")
    logger.info(f"[OUTPUT] Retrieval Time: {result.total_time_ms:.2f}ms")
    
    # Log top documents
    logger.info("[OUTPUT] Top Documents Preview:")
    for i, doc in enumerate(result.documents[:5], 1):
        logger.info(f"  [{i}] Source: {doc.source_index} | Score: {doc.similarity:.3f}")
        logger.info(f"      Content: {_truncate(doc.content, 120)}")
    if len(result.documents) > 5:
        logger.info(f"  ... and {len(result.documents) - 5} more documents")
    
    # Fuse
    fused = fusion.merge(result.documents)
    
    logger.info(f"[OUTPUT] After Fusion: {len(fused.documents)} documents")
    logger.info(f"[OUTPUT] Context Length: {len(fused.formatted_context)} chars")
    logger.info(f"[OUTPUT] Citations: {len(fused.citations)} entries")
    
    state["contexts"] = [doc.to_dict() for doc in fused.documents]
    state["formatted_context"] = fused.formatted_context
    state["citations_map"] = fused.citations
    state["step_times"]["retrieve"] = (time.time() - start) * 1000
    
    logger.info(f"[TIME] Retrieve + Fusion: {state['step_times']['retrieve']:.2f}ms")
    
    return state


def generate_node(state: RAGState) -> RAGState:
    """Generate grounded answer with citations."""
    _log_separator("STEP 4: GENERATION")
    generator = _get_generator()
    start = time.time()
    
    query = state["query"]
    context_len = len(state["formatted_context"])
    citations_count = len(state["citations_map"])
    
    logger.info(f"[INPUT] Query: {_truncate(query)}")
    logger.info(f"[INPUT] Context Length: {context_len} chars")
    logger.info(f"[INPUT] Available Citations: {citations_count}")
    
    result = generator.generate(
        query=query,
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
    
    # Detailed logging
    logger.info(f"[OUTPUT] Is Grounded: {result.is_grounded}")
    logger.info(f"[OUTPUT] Citations Used: {result.citations_used}")
    logger.info(f"[OUTPUT] Answer Preview: {_truncate(result.answer, 300)}")
    logger.info(f"[TIME] Generate: {state['step_times']['generate']:.2f}ms")
    
    # Final summary
    _log_separator("PIPELINE SUMMARY")
    logger.info(f"Total Time: {state['total_time_ms']:.2f}ms")
    logger.info("Time Breakdown:")
    for step, time_ms in state["step_times"].items():
        pct = (time_ms / state["total_time_ms"] * 100) if state["total_time_ms"] > 0 else 0
        logger.info(f"  - {step:12s}: {time_ms:8.2f}ms ({pct:5.1f}%)")
    
    return state


def should_decompose(state: RAGState) -> bool:
    """Determine if query needs decomposition."""
    from src.core.decomposition import QueryComplexityClassifier
    classifier = QueryComplexityClassifier()
    result = classifier.classify(state["query"])
    
    logger.info(f"[CLASSIFY] Query: {_truncate(state['query'], 80)}")
    logger.info(f"[CLASSIFY] Is Complex: {result.is_complex}")
    logger.info(f"[CLASSIFY] Score: {result.complexity_score:.2f}")
    logger.info(f"[CLASSIFY] Reason: {result.reason}")
    
    return result.is_complex


