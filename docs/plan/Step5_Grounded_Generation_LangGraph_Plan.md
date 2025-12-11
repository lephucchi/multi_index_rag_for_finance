# BƯỚC 5: Grounded Generation & LangGraph Pipeline - Implementation Plan

> **Mục tiêu**: Tích hợp LangGraph để orchestrate toàn bộ pipeline RAG với Grounded Generation  
> **Thời gian dự kiến**: 1 tuần  
> **Dependencies**: Step 3 (Semantic Router) ✅, Step 4 (Decomposition & Retrieval) ✅

---

## PHẦN I: TỔNG QUAN LANGGRAPH

### 1.1. Tại Sao LangGraph?

| Tiêu chí | LangChain | LangGraph | Custom |
|----------|-----------|-----------|--------|
| **Conditional Flow** | Limited | Native support | Manual |
| **State Management** | Basic | TypedDict + Annotations | Manual |
| **Debugging** | Basic | LangSmith integration | Custom |
| **Academic Value** | Low | High (citable) | Low |

**Kết luận**: LangGraph phù hợp cho:
- Quản lý flow phức tạp (route → decompose → retrieve → generate)
- State tracking xuyên suốt pipeline
- Dễ debug với LangSmith
- Có giá trị học thuật (citable trong paper)

### 1.2. LangGraph Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     LangGraph StateGraph                         │
│                                                                   │
│  ┌─────────┐    ┌───────────┐    ┌──────────┐    ┌───────────┐  │
│  │  START  │───▶│   route   │───▶│decompose │───▶│ retrieve  │  │
│  └─────────┘    └───────────┘    └──────────┘    └──────────┘   │
│                       │                               │          │
│                       │ (simple query)                │          │
│                       └───────────────────────────────┤          │
│                                                       ▼          │
│                                               ┌───────────┐      │
│                                               │ generate  │      │
│                                               └─────┬─────┘      │
│                                                     │            │
│                                                     ▼            │
│                                               ┌───────────┐      │
│                                               │    END    │      │
│                                               └───────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## PHẦN II: YÊU CẦU CHỨC NĂNG

### 2.1. Grounded Generation Module

| Requirement | Description | Priority |
|-------------|-------------|----------|
| **REQ-5.1** | Generate answer grounded in retrieved context | P0 |
| **REQ-5.2** | Inline citations [1], [2], ... | P0 |
| **REQ-5.3** | Validate all claims have sources | P0 |
| **REQ-5.4** | Handle Vietnamese language properly | P0 |
| **REQ-5.5** | Streaming response support | P1 |
| **REQ-5.6** | Confidence score per claim | P2 |

### 2.2. LangGraph Pipeline

| Requirement | Description | Priority |
|-------------|-------------|----------|
| **REQ-5.7** | Define RAGState TypedDict | P0 |
| **REQ-5.8** | Implement all nodes (route, decompose, retrieve, generate) | P0 |
| **REQ-5.9** | Conditional edge for simple vs complex queries | P0 |
| **REQ-5.10** | Error handling and fallback states | P1 |
| **REQ-5.11** | LangSmith tracing integration | P2 |

### 2.3. Performance Requirements

| Metric | Target |
|--------|--------|
| End-to-end latency | < 3s (non-streaming) |
| Generation quality | Grounded, no hallucination |
| Citation accuracy | 100% claims cited |

---

## PHẦN III: KIẾN TRÚC VÀ THIẾT KẾ

### 3.1. Module Structure

```
src/
├── generator/                    # NEW - Grounded Generation
│   ├── __init__.py
│   ├── config.py                 # GeneratorConfig
│   ├── grounded.py               # GroundedGenerator class
│   ├── prompts.py                # Generation prompts
│   └── citation.py               # Citation extraction/validation
│
├── pipeline/                     # EXTEND - LangGraph integration
│   ├── __init__.py
│   ├── state.py                  # RAGState TypedDict
│   ├── nodes.py                  # Node functions
│   ├── graph.py                  # StateGraph definition
│   └── rag_pipeline.py           # Existing (will be updated)
│
└── api/                          # NEW - FastAPI endpoints
    ├── __init__.py
    ├── main.py                   # FastAPI app
    ├── routes.py                 # API routes
    └── schemas.py                # Pydantic models
```

### 3.2. RAGState Definition

```python
from typing import TypedDict, List, Optional, Annotated
from langgraph.graph import add_messages
import operator

class RAGState(TypedDict):
    # Input
    query: str
    
    # Routing
    routes: List[str]
    route_scores: dict
    
    # Decomposition
    is_complex: bool
    sub_queries: List[str]
    
    # Retrieval
    contexts: Annotated[List[dict], operator.add]
    formatted_context: str
    
    # Generation
    answer: str
    citations: List[dict]
    
    # Metadata
    total_time_ms: float
    error: Optional[str]
    
    # For streaming
    messages: Annotated[list, add_messages]
```

### 3.3. LangGraph Flow

```python
from langgraph.graph import StateGraph, END

def build_rag_graph() -> StateGraph:
    graph = StateGraph(RAGState)
    
    # Add nodes
    graph.add_node("route", route_node)
    graph.add_node("decompose", decompose_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    
    # Set entry point
    graph.set_entry_point("route")
    
    # Conditional routing
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
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    
    return graph.compile()
```

---

## PHẦN IV: IMPLEMENTATION PLAN

### Phase 1: Generator Module (Day 1-2)

#### 4.1.1. File: `src/generator/config.py`

```python
from dataclasses import dataclass
import os

@dataclass(frozen=True)
class GeneratorConfig:
    """Configuration for Grounded Generator."""
    model_name: str = "models/gemini-2.0-flash"
    temperature: float = 0.3
    max_tokens: int = 2048
    citation_format: str = "[{n}]"  # [1], [2], ...
    require_grounding: bool = True
    language: str = "vi"
    
    @classmethod
    def from_env(cls) -> "GeneratorConfig":
        return cls(
            model_name=os.getenv("GEMINI_MODEL", "models/gemini-2.0-flash"),
            temperature=float(os.getenv("GEN_TEMPERATURE", "0.3")),
        )
```

#### 4.1.2. File: `src/generator/prompts.py`

```python
GROUNDED_GENERATION_SYSTEM = """Bạn là trợ lý AI chuyên về tài chính và pháp lý Việt Nam.

NHIỆM VỤ: Trả lời câu hỏi DỰA TRÊN các tài liệu được cung cấp.

QUY TẮC BẮT BUỘC:
1. CHỈ sử dụng thông tin từ CONTEXT được cung cấp
2. PHẢI trích dẫn nguồn bằng [1], [2], ... sau mỗi claim
3. Nếu không tìm thấy thông tin, nói rõ "Không tìm thấy trong tài liệu"
4. KHÔNG bịa đặt thông tin không có trong context
5. Trả lời bằng tiếng Việt, rõ ràng và chuyên nghiệp

ĐỊNH DẠNG CITATION:
- Mỗi câu khẳng định cần có citation: "ROE là tỷ suất sinh lời trên vốn chủ sở hữu [1]."
- Có thể dùng nhiều citations: "VNM có ROE 25% [2], cao hơn trung bình ngành [3]."
"""

GROUNDED_GENERATION_USER = """CONTEXT:
{context}

---

CÂU HỎI: {query}

Trả lời với citations:"""
```

#### 4.1.3. File: `src/generator/grounded.py`

```python
"""
Grounded Generator using Gemini.

Generates answers strictly grounded in retrieved context with citations.
"""
import json
import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

from .config import GeneratorConfig
from .prompts import GROUNDED_GENERATION_SYSTEM, GROUNDED_GENERATION_USER

logger = logging.getLogger(__name__)

@dataclass
class GenerationResult:
    """Result of grounded generation."""
    answer: str
    citations: List[dict]
    is_grounded: bool
    raw_response: str
    latency_ms: float

class GroundedGenerator:
    """Generate grounded answers with citations."""
    
    def __init__(self, config: GeneratorConfig = None):
        self.config = config or GeneratorConfig.from_env()
        self._model = None
    
    @property
    def model(self):
        if self._model is None:
            import google.generativeai as genai
            import os
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            self._model = genai.GenerativeModel(self.config.model_name)
        return self._model
    
    def generate(
        self,
        query: str,
        context: str,
        citations_map: List[dict]
    ) -> GenerationResult:
        """
        Generate grounded answer.
        
        Args:
            query: User question
            context: Formatted context with [1], [2], ... markers
            citations_map: List of citation references
        """
        import time
        start = time.time()
        
        prompt = f"{GROUNDED_GENERATION_SYSTEM}\n\n{GROUNDED_GENERATION_USER.format(
            context=context,
            query=query
        )}"
        
        response = self.model.generate_content(
            prompt,
            generation_config={
                "temperature": self.config.temperature,
                "max_output_tokens": self.config.max_tokens
            }
        )
        
        answer = response.text
        
        # Extract used citations
        used_citations = self._extract_citations(answer, citations_map)
        
        # Validate grounding
        is_grounded = self._validate_grounding(answer)
        
        return GenerationResult(
            answer=answer,
            citations=used_citations,
            is_grounded=is_grounded,
            raw_response=response.text,
            latency_ms=(time.time() - start) * 1000
        )
    
    def _extract_citations(self, text: str, citations_map: List[dict]) -> List[dict]:
        """Extract citations used in the answer."""
        pattern = r'\[(\d+)\]'
        matches = re.findall(pattern, text)
        used_indices = set(int(m) for m in matches)
        
        return [c for c in citations_map if c.get("number") in used_indices]
    
    def _validate_grounding(self, answer: str) -> bool:
        """Check if answer is properly grounded."""
        # Must have at least one citation
        if not re.search(r'\[\d+\]', answer):
            return False
        
        # Check for hedging phrases that indicate ungrounded claims
        ungrounded_phrases = [
            "tôi nghĩ", "có thể", "thường thì", 
            "theo tôi biết", "không chắc chắn"
        ]
        for phrase in ungrounded_phrases:
            if phrase in answer.lower():
                logger.warning(f"Potential ungrounded claim: {phrase}")
        
        return True
```

### Phase 2: LangGraph Pipeline (Day 3-4)

#### 4.2.1. File: `src/pipeline/state.py`

```python
"""
LangGraph State Definition for RAG Pipeline.
"""
from typing import TypedDict, List, Optional, Annotated, Any
import operator


class RAGState(TypedDict):
    """
    State schema for the RAG pipeline.
    
    This state flows through all nodes in the graph.
    """
    # Input
    query: str
    
    # Routing
    routes: List[str]
    route_scores: dict
    
    # Decomposition  
    is_complex: bool
    sub_queries: List[str]
    sub_query_types: List[str]
    
    # Retrieval
    contexts: List[dict]
    formatted_context: str
    citations_map: List[dict]
    
    # Generation
    answer: str
    citations: List[dict]
    is_grounded: bool
    
    # Metadata
    total_time_ms: float
    step_times: dict
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
```

#### 4.2.2. File: `src/pipeline/nodes.py`

```python
"""
LangGraph Node Functions for RAG Pipeline.

Each node transforms the state and returns the updated state.
"""
import time
import logging
from typing import Dict, Any

from .state import RAGState

logger = logging.getLogger(__name__)

# Lazy imports to avoid circular dependencies
def _get_router():
    from src.semantic_router import HybridRouter
    return HybridRouter()

def _get_decomposer():
    from src.query_decomposition import QueryDecomposer
    return QueryDecomposer()

def _get_retriever():
    from src.retrieval import ParallelRetriever
    return ParallelRetriever()

def _get_fusion():
    from src.retrieval import ResultFusion
    return ResultFusion()

def _get_generator():
    from src.generator import GroundedGenerator
    return GroundedGenerator()

# Cached instances
_router = None
_decomposer = None
_retriever = None
_fusion = None
_generator = None


def route_node(state: RAGState) -> RAGState:
    """Route the query to appropriate indices."""
    global _router
    if _router is None:
        _router = _get_router()
    
    start = time.time()
    
    routes, scores = _router.route(state["query"])
    
    state["routes"] = routes
    state["route_scores"] = scores
    state["step_times"]["route"] = (time.time() - start) * 1000
    
    logger.info(f"Routed to: {routes}")
    return state


def decompose_node(state: RAGState) -> RAGState:
    """Decompose complex query into sub-queries."""
    global _decomposer
    if _decomposer is None:
        _decomposer = _get_decomposer()
    
    start = time.time()
    
    result = _decomposer.decompose(state["query"])
    
    state["is_complex"] = result.is_decomposed
    state["sub_queries"] = [sq.query for sq in result.sub_queries]
    state["sub_query_types"] = [sq.query_type for sq in result.sub_queries]
    state["step_times"]["decompose"] = (time.time() - start) * 1000
    
    logger.info(f"Decomposed into {len(state['sub_queries'])} sub-queries")
    return state


def retrieve_node(state: RAGState) -> RAGState:
    """Retrieve documents for sub-queries."""
    global _retriever, _fusion
    if _retriever is None:
        _retriever = _get_retriever()
    if _fusion is None:
        _fusion = _get_fusion()
    
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
    result = _retriever.retrieve_all(sub_queries, routes[:len(sub_queries)])
    
    # Fuse
    fused = _fusion.merge(result.documents)
    
    state["contexts"] = [doc.to_dict() for doc in fused.documents]
    state["formatted_context"] = fused.formatted_context
    state["citations_map"] = fused.citations
    state["step_times"]["retrieve"] = (time.time() - start) * 1000
    
    logger.info(f"Retrieved {len(state['contexts'])} documents")
    return state


def generate_node(state: RAGState) -> RAGState:
    """Generate grounded answer."""
    global _generator
    if _generator is None:
        _generator = _get_generator()
    
    start = time.time()
    
    result = _generator.generate(
        query=state["query"],
        context=state["formatted_context"],
        citations_map=state["citations_map"]
    )
    
    state["answer"] = result.answer
    state["citations"] = result.citations
    state["is_grounded"] = result.is_grounded
    state["step_times"]["generate"] = (time.time() - start) * 1000
    
    # Calculate total time
    state["total_time_ms"] = sum(state["step_times"].values())
    
    logger.info(f"Generated answer with {len(state['citations'])} citations")
    return state


# Conditional function
def should_decompose(state: RAGState) -> bool:
    """Determine if query needs decomposition."""
    from src.query_decomposition import QueryComplexityClassifier
    classifier = QueryComplexityClassifier()
    result = classifier.classify(state["query"])
    return result.is_complex
```

#### 4.2.3. File: `src/pipeline/graph.py`

```python
"""
LangGraph State Graph Definition.

This is the main entry point for the RAG pipeline.
"""
import logging
from langgraph.graph import StateGraph, END

from .state import RAGState, create_initial_state
from .nodes import route_node, decompose_node, retrieve_node, generate_node, should_decompose

logger = logging.getLogger(__name__)


def build_rag_graph() -> StateGraph:
    """
    Build the RAG pipeline graph.
    
    Returns:
        Compiled StateGraph ready for invocation.
    """
    # Create graph with state schema
    graph = StateGraph(RAGState)
    
    # Add nodes
    graph.add_node("route", route_node)
    graph.add_node("decompose", decompose_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    
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
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    
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


def run_rag_pipeline(query: str) -> dict:
    """
    Run a query through the RAG pipeline.
    
    Args:
        query: User question
        
    Returns:
        Final state with answer and citations
    """
    graph = get_rag_graph()
    initial_state = create_initial_state(query)
    
    result = graph.invoke(initial_state)
    
    return {
        "query": result["query"],
        "answer": result["answer"],
        "citations": result["citations"],
        "is_grounded": result["is_grounded"],
        "routes": result["routes"],
        "sub_queries": result["sub_queries"],
        "total_time_ms": result["total_time_ms"],
        "step_times": result["step_times"]
    }
```

### Phase 3: API Layer (Day 5-6)

#### 4.3.1. File: `src/api/schemas.py`

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000)
    k: int = Field(default=10, ge=1, le=50)
    stream: bool = Field(default=False)

class Citation(BaseModel):
    number: int
    source: str
    preview: str

class QueryResponse(BaseModel):
    query: str
    answer: str
    citations: List[Citation]
    is_grounded: bool
    routes: List[str]
    sub_queries: List[str]
    total_time_ms: float
```

#### 4.3.2. File: `src/api/main.py`

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import QueryRequest, QueryResponse
from src.pipeline.graph import run_rag_pipeline

app = FastAPI(
    title="Multi-Index RAG API",
    description="RAG system for Vietnamese financial & legal data",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/v1/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    try:
        result = run_rag_pipeline(request.query)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

---

## PHẦN V: DEPENDENCIES

### 5.1. New Requirements

```txt
# Add to requirements.txt
langgraph>=0.2.0
langchain-google-genai>=1.0.0
langsmith>=0.1.0  # Optional: tracing
```

### 5.2. Environment Variables

```bash
# Add to .env
GEMINI_API_KEY=your-key
LANGCHAIN_TRACING_V2=true  # Optional
LANGCHAIN_API_KEY=your-langsmith-key  # Optional
```

---

## PHẦN VI: VERIFICATION PLAN

### 6.1. Unit Tests

| Test | Description |
|------|-------------|
| `test_generator_grounding` | Verify citations in output |
| `test_langgraph_flow` | Test graph compilation |
| `test_node_functions` | Test each node independently |

### 6.2. Integration Tests

```bash
# Test full pipeline
python -c "from src.pipeline.graph import run_rag_pipeline; print(run_rag_pipeline('ROE là gì'))"

# Test API
uvicorn src.api.main:app --reload
curl -X POST http://localhost:8000/api/v1/query -d '{"query":"ROE là gì"}'
```

---

## PHẦN VII: CHECKLIST

### Day 1-2: Generator
- [ ] Create `src/generator/` folder
- [ ] Implement `config.py`, `prompts.py`
- [ ] Implement `grounded.py` with citation extraction
- [ ] Test generation với Gemini API

### Day 3-4: LangGraph
- [ ] Install langgraph
- [ ] Create `state.py` với RAGState
- [ ] Implement `nodes.py` với 4 node functions
- [ ] Build `graph.py` với StateGraph
- [ ] Test end-to-end pipeline

### Day 5-6: API
- [ ] Create `src/api/` folder
- [ ] Implement FastAPI endpoints
- [ ] Test API với Swagger UI

### Day 7: Polish
- [ ] Documentation update
- [ ] Error handling improvement
- [ ] Git commit & push

---

*Tạo: 11/12/2024*
