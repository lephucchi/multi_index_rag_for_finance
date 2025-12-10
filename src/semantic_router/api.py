"""
FastAPI endpoints for Semantic Router.

Usage:
    cd C:\\uel\\multi_index_rag_for_finance
    .\\venv\\Scripts\\activate
    uvicorn src.semantic_router.api:app --reload --port 8000
    
Then access: http://localhost:8000/docs for Swagger UI
"""
import os
import sys
import time
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.semantic_router.router import HybridRouter
from src.semantic_router.config import RouterConfig

# Load environment variables
load_dotenv()


# =============================================================================
# Pydantic Models
# =============================================================================

class RouteRequest(BaseModel):
    """Request model for routing a query."""
    query: str = Field(..., description="User query to route", min_length=1)
    enable_multi_label: bool = Field(True, description="Allow multiple routes")
    max_routes: int = Field(4, description="Maximum routes to return", ge=1, le=4)


class RouteResponse(BaseModel):
    """Response model for routing result."""
    query: str
    routes: List[str]
    primary_route: str
    scores: dict
    confidence: float
    is_multi_label: bool
    processing_time_ms: float


class BatchRouteRequest(BaseModel):
    """Request model for batch routing."""
    queries: List[str] = Field(..., min_items=1, max_items=100)
    enable_multi_label: bool = True


class BatchRouteResponse(BaseModel):
    """Response model for batch routing."""
    results: List[RouteResponse]
    total_queries: int
    total_time_ms: float


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    routes: List[str]
    model: str
    multi_label_enabled: bool


# =============================================================================
# App Setup
# =============================================================================

# Global router instance
router_instance: Optional[HybridRouter] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize router on startup."""
    global router_instance
    print("Initializing Semantic Router...")
    router_instance = HybridRouter(RouterConfig())
    # Force initialization
    router_instance._ensure_initialized()
    print("Router ready!")
    yield
    print("Shutting down...")


app = FastAPI(
    title="Semantic Router API",
    description="Query routing for Multi-Index RAG System",
    version="1.0.0",
    lifespan=lifespan
)


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health and router status."""
    global router_instance
    
    if router_instance is None:
        raise HTTPException(status_code=503, detail="Router not initialized")
    
    return HealthResponse(
        status="healthy",
        routes=list(router_instance.routes.keys()),
        model=router_instance.config.encoder_model,
        multi_label_enabled=router_instance.config.enable_multi_label
    )


@app.post("/route", response_model=RouteResponse)
async def route_query(request: RouteRequest):
    """
    Route a single query to appropriate index(es).
    
    Returns the selected routes with confidence scores.
    """
    global router_instance
    
    if router_instance is None:
        raise HTTPException(status_code=503, detail="Router not initialized")
    
    # Update config if needed
    if request.enable_multi_label != router_instance.config.enable_multi_label:
        router_instance.config.enable_multi_label = request.enable_multi_label
    if request.max_routes != router_instance.config.max_routes:
        router_instance.config.max_routes = request.max_routes
    
    start_time = time.perf_counter()
    
    try:
        result = router_instance.route_with_confidence(request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Routing error: {str(e)}")
    
    processing_time = (time.perf_counter() - start_time) * 1000
    
    return RouteResponse(
        query=result["query"],
        routes=result["selected_routes"],
        primary_route=result["primary_route"],
        scores=result["scores"],
        confidence=result["confidence"],
        is_multi_label=result["is_multi_label"],
        processing_time_ms=round(processing_time, 2)
    )


@app.post("/route/batch", response_model=BatchRouteResponse)
async def batch_route_queries(request: BatchRouteRequest):
    """
    Route multiple queries in a batch.
    
    More efficient than calling /route multiple times.
    """
    global router_instance
    
    if router_instance is None:
        raise HTTPException(status_code=503, detail="Router not initialized")
    
    router_instance.config.enable_multi_label = request.enable_multi_label
    
    start_time = time.perf_counter()
    
    results = []
    batch_results = router_instance.batch_route(request.queries)
    
    for query, (routes, scores) in zip(request.queries, batch_results):
        results.append(RouteResponse(
            query=query,
            routes=routes,
            primary_route=routes[0],
            scores=scores,
            confidence=scores[routes[0]],
            is_multi_label=len(routes) > 1,
            processing_time_ms=0  # Individual times not tracked in batch
        ))
    
    total_time = (time.perf_counter() - start_time) * 1000
    
    return BatchRouteResponse(
        results=results,
        total_queries=len(request.queries),
        total_time_ms=round(total_time, 2)
    )


@app.get("/routes")
async def list_routes():
    """List all available routes with their descriptions."""
    global router_instance
    
    if router_instance is None:
        raise HTTPException(status_code=503, detail="Router not initialized")
    
    return {
        route.name: {
            "description": route.description,
            "example_count": len(route.utterances),
            "threshold": router_instance.config.route_thresholds.get(route.name, 0.65)
        }
        for route in router_instance.routes.values()
    }


# =============================================================================
# Run directly
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
