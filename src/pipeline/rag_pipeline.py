"""
Unified RAG Pipeline integrating all components.

Combines:
- SemanticRouter: Query routing
- QueryDecomposer: Complex query breakdown
- ParallelRetriever: Multi-index retrieval
- ResultFusion: Context merging

This module prepares the system for LangGraph integration in Step 5.
"""
import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """
    Result from the RAG pipeline.
    
    Attributes:
        query: Original user query
        routes: Selected indices
        sub_queries: Decomposed queries (if any)
        contexts: Retrieved and fused documents
        total_time_ms: Total processing time
        metadata: Additional pipeline metadata
    """
    query: str
    routes: List[str]
    sub_queries: List[str]
    contexts: List[dict]
    formatted_context: str = ""
    total_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_decomposed(self) -> bool:
        return len(self.sub_queries) > 1
    
    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "routes": self.routes,
            "sub_queries": self.sub_queries,
            "is_decomposed": self.is_decomposed,
            "context_count": len(self.contexts),
            "total_time_ms": round(self.total_time_ms, 2),
            "metadata": self.metadata,
        }


class RAGPipeline:
    """
    Unified RAG Pipeline for query processing.
    
    Orchestrates the flow:
    Query → Route → Decompose → Retrieve → Fuse → Return Context
    
    Example:
        >>> from src.pipeline import RAGPipeline
        >>> pipeline = RAGPipeline()
        >>> result = pipeline.process("ROE là gì và VNM có ROE bao nhiêu")
        >>> print(result.formatted_context)
    """
    
    def __init__(
        self,
        router=None,
        decomposer=None,
        retriever=None,
        fusion=None,
        use_decomposition: bool = True
    ):
        """
        Initialize pipeline with optional dependency injection.
        
        Args:
            router: SemanticRouter/HybridRouter instance
            decomposer: QueryDecomposer instance
            retriever: ParallelRetriever instance
            fusion: ResultFusion instance
            use_decomposition: Whether to use query decomposition
        """
        self._router = router
        self._decomposer = decomposer
        self._retriever = retriever
        self._fusion = fusion
        self.use_decomposition = use_decomposition
    
    @property
    def router(self):
        """Lazy load router."""
        if self._router is None:
            from src.semantic_router import HybridRouter
            self._router = HybridRouter()
        return self._router
    
    @property
    def decomposer(self):
        """Lazy load decomposer."""
        if self._decomposer is None:
            from src.query_decomposition import QueryDecomposer
            self._decomposer = QueryDecomposer()
        return self._decomposer
    
    @property
    def retriever(self):
        """Lazy load retriever."""
        if self._retriever is None:
            from src.retrieval import ParallelRetriever
            self._retriever = ParallelRetriever()
        return self._retriever
    
    @property
    def fusion(self):
        """Lazy load fusion."""
        if self._fusion is None:
            from src.retrieval import ResultFusion
            self._fusion = ResultFusion()
        return self._fusion
    
    def process(self, query: str, k: int = 10) -> PipelineResult:
        """
        Process a query through the full pipeline.
        
        Args:
            query: User query string
            k: Number of documents to retrieve
            
        Returns:
            PipelineResult with contexts and metadata
        """
        start = time.time()
        metadata = {}
        
        # Step 1: Route the query
        routes, route_scores = self.router.route(query)
        metadata["route_scores"] = route_scores
        
        # Step 2: Decompose if enabled
        if self.use_decomposition:
            decomp_result = self.decomposer.decompose(query)
            sub_queries = [sq.query for sq in decomp_result.sub_queries]
            sub_query_types = [sq.query_type for sq in decomp_result.sub_queries]
            metadata["decomposition_method"] = decomp_result.method
            metadata["decomposition_reasoning"] = decomp_result.reasoning
        else:
            sub_queries = [query]
            sub_query_types = ["UNKNOWN"]
        
        # Step 3: Map sub-queries to routes
        # If decomposed, use query types to refine routing
        query_routes = []
        for i, (sq, sq_type) in enumerate(zip(sub_queries, sub_query_types)):
            if sq_type != "UNKNOWN":
                query_routes.append(sq_type.lower())
            elif i < len(routes):
                query_routes.append(routes[i])
            else:
                query_routes.append(routes[0])
        
        # Step 4: Retrieve from all relevant indices
        retrieval_result = self.retriever.retrieve_all(
            sub_queries=sub_queries,
            routes=query_routes,
            k_per_index=max(k // len(sub_queries), 3)
        )
        metadata["retrieval_time_ms"] = retrieval_result.total_time_ms
        metadata["per_index_time_ms"] = retrieval_result.per_index_time_ms
        
        # Step 5: Fuse results
        fused = self.fusion.merge(retrieval_result.documents, max_docs=k)
        metadata["source_distribution"] = fused.source_distribution
        
        total_time = (time.time() - start) * 1000
        
        return PipelineResult(
            query=query,
            routes=routes,
            sub_queries=sub_queries,
            contexts=[doc.to_dict() for doc in fused.documents],
            formatted_context=fused.formatted_context,
            total_time_ms=total_time,
            metadata=metadata
        )
    
    async def process_async(self, query: str, k: int = 10) -> PipelineResult:
        """Async version of process."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.process(query, k))


# Factory function
def create_pipeline(
    use_decomposition: bool = True,
    fast_mode: bool = False
) -> RAGPipeline:
    """
    Create a configured pipeline.
    
    Args:
        use_decomposition: Enable query decomposition
        fast_mode: Use faster but less accurate settings
        
    Returns:
        Configured RAGPipeline instance
    """
    if fast_mode:
        from src.semantic_router import HybridRouter, FAST_CONFIG
        router = HybridRouter(config=FAST_CONFIG)
    else:
        router = None  # Use defaults
    
    return RAGPipeline(
        router=router,
        use_decomposition=use_decomposition
    )
