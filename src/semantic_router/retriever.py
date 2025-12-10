"""
Multi-Index Retriever with Supabase Integration.

This module provides retrieval functionality that works with the Semantic Router
to fetch relevant documents from the appropriate vector indices.
"""
import os
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class Document:
    """Retrieved document with metadata."""
    id: str
    content: str
    metadata: Dict[str, Any]
    similarity: float
    source_index: str
    
    def __repr__(self):
        return f"Document(id={self.id[:8]}..., sim={self.similarity:.3f}, source={self.source_index})"


class SupabaseRetriever:
    """
    Retriever for Supabase vector indices.
    
    Supports:
    - Single index retrieval
    - Multi-index parallel retrieval
    - Weighted retrieval based on route confidence
    """
    
    INDEX_MAPPING = {
        "glossary": "glossary_index",
        "legal": "legal_index",
        "financial": "financial_index", 
        "news": "news_index",
    }
    
    def __init__(
        self,
        supabase_url: str = None,
        supabase_key: str = None,
        encoder_model: str = "BAAI/bge-m3"
    ):
        """
        Initialize the Supabase retriever.
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service key
            encoder_model: Embedding model name
        """
        self.supabase_url = supabase_url or os.getenv("supabase_url")
        self.supabase_key = supabase_key or os.getenv("supabase_service_role_key")
        self.encoder_model = encoder_model
        
        self._client = None
        self._encoder = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization of Supabase client and encoder."""
        if not self._initialized:
            from supabase import create_client
            from sentence_transformers import SentenceTransformer
            
            print(f"Initializing Supabase client...")
            self._client = create_client(self.supabase_url, self.supabase_key)
            
            print(f"Loading encoder: {self.encoder_model}...")
            self._encoder = SentenceTransformer(self.encoder_model)
            
            self._initialized = True
            print("Retriever initialized.")
    
    def _encode_query(self, query: str) -> List[float]:
        """Encode query to embedding vector."""
        self._ensure_initialized()
        embedding = self._encoder.encode(
            query,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return embedding.tolist()
    
    async def retrieve_from_index(
        self,
        query: str,
        index_name: str,
        k: int = 10,
        threshold: float = 0.0
    ) -> List[Document]:
        """
        Retrieve documents from a single index.
        
        Args:
            query: Search query
            index_name: Name of the index (e.g., "glossary_index")
            k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of Document objects
        """
        self._ensure_initialized()
        
        # Get query embedding
        query_embedding = self._encode_query(query)
        
        # Call Supabase RPC function for similarity search
        # Assumes function: match_{index_name}(query_embedding, match_count, match_threshold)
        func_name = f"match_{index_name}"
        
        try:
            response = self._client.rpc(
                func_name,
                {
                    "query_embedding": query_embedding,
                    "match_count": k,
                    "match_threshold": threshold
                }
            ).execute()
            
            documents = []
            for item in response.data or []:
                doc = Document(
                    id=str(item.get("id", "")),
                    content=item.get("content", ""),
                    metadata=item.get("metadata", {}),
                    similarity=float(item.get("similarity", 0)),
                    source_index=index_name
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            print(f"Error retrieving from {index_name}: {e}")
            return []
    
    async def retrieve_multi_index(
        self,
        query: str,
        routes: List[str],
        k: int = 10,
        strategy: str = "equal"
    ) -> List[Document]:
        """
        Retrieve from multiple indices in parallel.
        
        Args:
            query: Search query
            routes: List of route names (e.g., ["glossary", "financial"])
            k: Total number of results
            strategy: "equal" or "weighted"
            
        Returns:
            Combined list of Document objects
        """
        if strategy == "equal":
            k_per_index = max(k // len(routes), 2)
        else:
            k_per_index = k  # Will be adjusted in weighted strategy
        
        # Create tasks for parallel retrieval
        tasks = []
        for route in routes:
            index_name = self.INDEX_MAPPING.get(route, f"{route}_index")
            tasks.append(
                self.retrieve_from_index(query, index_name, k=k_per_index)
            )
        
        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine and deduplicate
        all_docs = []
        seen_ids = set()
        
        for result in results:
            if isinstance(result, Exception):
                print(f"Retrieval error: {result}")
                continue
            
            for doc in result:
                if doc.id not in seen_ids:
                    all_docs.append(doc)
                    seen_ids.add(doc.id)
        
        # Sort by similarity
        all_docs.sort(key=lambda x: x.similarity, reverse=True)
        
        return all_docs[:k]
    
    async def retrieve_weighted(
        self,
        query: str,
        routes: List[str],
        scores: Dict[str, float],
        k: int = 10
    ) -> List[Document]:
        """
        Retrieve with weighted distribution based on route confidence.
        
        Args:
            query: Search query
            routes: List of route names
            scores: Dict of {route: confidence_score}
            k: Total number of results
            
        Returns:
            List of Document objects
        """
        # Calculate k per route based on confidence
        total_score = sum(scores.get(r, 0.5) for r in routes)
        
        tasks = []
        for route in routes:
            weight = scores.get(route, 0.5) / total_score
            k_for_route = max(int(k * weight), 2)
            
            index_name = self.INDEX_MAPPING.get(route, f"{route}_index")
            tasks.append(
                self.retrieve_from_index(query, index_name, k=k_for_route)
            )
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine with source tagging
        all_docs = []
        seen_ids = set()
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                continue
            
            route = routes[i]
            for doc in result:
                if doc.id not in seen_ids:
                    doc.metadata["route_confidence"] = scores.get(route, 0.5)
                    all_docs.append(doc)
                    seen_ids.add(doc.id)
        
        # Sort by combined score
        all_docs.sort(
            key=lambda x: x.similarity * x.metadata.get("route_confidence", 0.5),
            reverse=True
        )
        
        return all_docs[:k]


class RouterRetrieverPipeline:
    """
    Combined Router + Retriever pipeline.
    
    Usage:
        pipeline = RouterRetrieverPipeline()
        docs = await pipeline.retrieve("ROE là gì và VNM có ROE bao nhiêu")
    """
    
    def __init__(self, router=None, retriever=None):
        from .router import HybridRouter
        
        self.router = router or HybridRouter()
        self.retriever = retriever or SupabaseRetriever()
    
    async def retrieve(
        self,
        query: str,
        k: int = 10,
        use_weighted: bool = True
    ) -> Dict[str, Any]:
        """
        Route query and retrieve relevant documents.
        
        Args:
            query: User query
            k: Number of documents to retrieve
            use_weighted: Use weighted retrieval based on confidence
            
        Returns:
            Dict with routes, documents, and metadata
        """
        # Step 1: Route the query
        routes, scores = self.router.route(query)
        
        # Step 2: Check if should search all
        if self.router.should_search_all_indices(query, scores):
            routes = list(self.router.routes.keys())
        
        # Step 3: Retrieve
        if use_weighted and len(routes) > 1:
            documents = await self.retriever.retrieve_weighted(
                query, routes, scores, k
            )
        else:
            documents = await self.retriever.retrieve_multi_index(
                query, routes, k
            )
        
        return {
            "query": query,
            "routes": routes,
            "scores": scores,
            "documents": documents,
            "document_count": len(documents)
        }


# Synchronous wrapper for non-async contexts
def retrieve_sync(query: str, k: int = 10) -> Dict[str, Any]:
    """Synchronous wrapper for retrieve."""
    pipeline = RouterRetrieverPipeline()
    return asyncio.run(pipeline.retrieve(query, k))
