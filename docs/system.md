# Kiến Trúc Hệ Thống RAG Đa Chỉ Mục

> **Semantic-Router Multi-Index RAG System**  
> Hệ thống Retrieval-Augmented Generation cho dữ liệu Tài chính-Pháp lý Việt Nam

---

## 1. Tổng Quan Kiến Trúc

### 1.1. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            FRONTEND LAYER                                 │
│                         (React/Next.js + TailwindCSS)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ Chat UI     │  │ Citation    │  │ Index       │  │ Response        │  │
│  │             │  │ Display     │  │ Selector    │  │ Streaming       │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘  │
└───────────────────────────────┬──────────────────────────────────────────┘
                                │ WebSocket / REST API
                                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                           BACKEND API LAYER                               │
│                              (FastAPI)                                    │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                    LangGraph Orchestration                          │  │
│  │                                                                     │  │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────┐  │  │
│  │  │ Semantic │ →  │ Query    │ →  │ Parallel │ →  │ Grounded     │  │  │
│  │  │ Router   │    │ Decomp.  │    │ Retrieval│    │ Generation   │  │  │
│  │  └──────────┘    └──────────┘    └──────────┘    └──────────────┘  │  │
│  │       ↓               ↓               ↓               ↓            │  │
│  │  [Route Decision] [Sub-queries] [Context Fusion] [Cited Answer]    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────┬────────────────────┬──────────────────────────────┘
                       │                    │
       ┌───────────────┼────────────────────┼───────────────┐
       ▼               ▼                    ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────────┐ ┌─────────────┐
│  Supabase   │ │   Gemini    │ │     Redis       │ │  LangSmith  │
│  (pgvector) │ │   2.0 Flash │ │    (Cache)      │ │ (Logging)   │
│             │ │             │ │                 │ │             │
│ 4 Indices:  │ │ - Decompose │ │ - Query cache   │ │ - Tracing   │
│ - Legal     │ │ - Generate  │ │ - Rate limit    │ │ - Metrics   │
│ - News      │ │ - Cite      │ │ - Session       │ │ - Debug     │
│ - Financial │ │             │ │                 │ │             │
│ - Glossary  │ │             │ │                 │ │             │
└─────────────┘ └─────────────┘ └─────────────────┘ └─────────────┘
```

### 1.2. Data Flow

```
User Query
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. SEMANTIC ROUTING (HybridRouter)                          │
│    - Rule-based pattern matching                            │
│    - Semantic similarity with route prototypes              │
│    - Multi-label support (1-4 indices)                      │
│    Output: routes=["glossary", "financial"], scores={...}   │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. QUERY DECOMPOSITION (Gemini 2.0 Flash)                   │
│    - Detect composite queries                               │
│    - Split into atomic sub-queries                          │
│    - Maintain dependencies                                  │
│    Output: ["ROE là gì", "VNM có ROE bao nhiêu"]           │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. PARALLEL RETRIEVAL (Async + Supabase)                    │
│    - Route each sub-query to selected indices               │
│    - Execute searches in parallel (asyncio.gather)          │
│    - Weighted result fusion                                 │
│    Output: [Document1, Document2, ...] with similarities    │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. GROUNDED GENERATION (Gemini + Citation)                  │
│    - Construct grounded prompt with contexts                │
│    - Enforce citation format [1], [2], ...                  │
│    - Validate claims against sources                        │
│    Output: Answer with inline citations                     │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
Response to User
```

---

## 2. LangGraph Pipeline

### 2.1. State Definition

```python
from typing import TypedDict, List, Optional, Annotated
from langgraph.graph import StateGraph, END
import operator

class RAGState(TypedDict):
    # Input
    query: str
    
    # Routing
    routes: List[str]
    route_scores: dict
    
    # Decomposition
    sub_queries: List[str]
    is_composite: bool
    
    # Retrieval
    contexts: Annotated[List[dict], operator.add]
    
    # Generation
    answer: str
    citations: List[dict]
    
    # Metadata
    processing_time_ms: float
    error: Optional[str]
```

### 2.2. Graph Structure

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   route     │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │ is_complex │            │ simple
              ▼            │            ▼
       ┌─────────────┐     │     ┌─────────────┐
       │  decompose  │     │     │   retrieve  │
       └──────┬──────┘     │     └──────┬──────┘
              │            │            │
              ▼            │            │
       ┌─────────────┐     │            │
       │  retrieve   │     │            │
       │  (parallel) │     │            │
       └──────┬──────┘     │            │
              │            │            │
              └────────────┼────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  generate   │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    END      │
                    └─────────────┘
```

### 2.3. Node Implementation

```python
from langgraph.graph import StateGraph, END

def build_rag_graph():
    graph = StateGraph(RAGState)
    
    # Add nodes
    graph.add_node("route", route_node)
    graph.add_node("decompose", decompose_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    
    # Entry point
    graph.set_entry_point("route")
    
    # Conditional edges
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

## 3. Component Details

### 3.1. Semantic Router

| Thuộc tính | Giá trị |
|------------|---------|
| **Approach** | Hybrid (Rule-based + Semantic) |
| **Model** | BAAI/bge-m3 (1024-dim) |
| **Routes** | glossary, legal, financial, news |
| **Accuracy** | 100% on 120 test queries |
| **Latency** | ~5-10ms per query |

**File**: `src/semantic_router/router.py`

### 3.2. Query Decomposition

| Thuộc tính | Giá trị |
|------------|---------|
| **Model** | Gemini 2.0 Flash |
| **Approach** | Least-to-Most Prompting |
| **Max sub-queries** | 5 |
| **Fallback** | Original query if decomposition fails |

### 3.3. Vector Indices

| Index | Records | Embedding Model | Dimension |
|-------|---------|-----------------|-----------|
| `legal_index` | ~15,000 | BAAI/bge-m3 | 1024 |
| `news_index` | ~500,000 | BAAI/bge-m3 | 1024 |
| `financial_index` | ~1,000,000 | BAAI/bge-m3 | 1024 |
| `glossary_index` | ~3,000 | BAAI/bge-m3 | 1024 |

**Database**: Supabase PostgreSQL + pgvector

### 3.4. Grounded Generation

| Thuộc tính | Giá trị |
|------------|---------|
| **Model** | Gemini 2.0 Flash |
| **Context Window** | 1M tokens |
| **Citation Format** | Inline [1], [2], ... |
| **Grounding Threshold** | All claims must have source |

---

## 4. Tech Stack

### 4.1. Core Technologies

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Orchestration** | LangGraph | 0.2.x | Pipeline management |
| **Backend** | FastAPI | 0.100+ | REST/WebSocket API |
| **Database** | Supabase | - | Vector storage |
| **Cache** | Redis | 7.x | Query caching |
| **LLM** | Gemini 2.0 Flash | - | Generation, Decomposition |
| **Embeddings** | BAAI/bge-m3 | - | Query & Document encoding |

### 4.2. Python Dependencies

```
langgraph>=0.2.0
langchain-google-genai>=1.0.0
sentence-transformers>=2.2.0
supabase>=2.0.0
fastapi>=0.100.0
uvicorn>=0.23.0
redis>=5.0.0
python-dotenv>=1.0.0
pydantic>=2.0.0
```

### 4.3. Frontend (Planned)

| Technology | Purpose |
|------------|---------|
| Next.js 14 | React framework |
| TailwindCSS | Styling |
| shadcn/ui | UI components |
| React Query | Data fetching |

---

## 5. API Design

### 5.1. Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/query` | Process RAG query |
| `POST` | `/api/v1/query/stream` | Streaming response |
| `GET` | `/api/v1/routes` | List available routes |
| `POST` | `/api/v1/route` | Route a query (debug) |
| `GET` | `/health` | Health check |

### 5.2. Request/Response

```python
# Request
class QueryRequest(BaseModel):
    query: str
    indices: Optional[List[str]] = None  # Override routing
    k: int = 10
    stream: bool = False

# Response
class QueryResponse(BaseModel):
    query: str
    answer: str
    citations: List[Citation]
    routes_used: List[str]
    sub_queries: List[str]
    processing_time_ms: float
```

---

## 6. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Production Environment                       │
│                                                                       │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │   Frontend      │    │   Backend       │    │   Workers       │  │
│  │   (Vercel)      │───▶│   (Railway/     │───▶│   (Railway)     │  │
│  │                 │    │    Render)      │    │                 │  │
│  └─────────────────┘    └────────┬────────┘    └─────────────────┘  │
│                                  │                                   │
│         ┌────────────────────────┼────────────────────────┐         │
│         ▼                        ▼                        ▼         │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │   Supabase      │    │   Redis Cloud   │    │   Google AI     │  │
│  │   (Database)    │    │   (Upstash)     │    │   (Gemini API)  │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7. Cấu Trúc Thư Mục

```
multi_index_rag_for_finance/
├── src/
│   ├── semantic_router/      # ✅ Implemented
│   │   ├── router.py
│   │   ├── routes.py
│   │   ├── config.py
│   │   ├── retriever.py
│   │   └── evaluation.py
│   ├── query_decomposition/  # 🔄 Step 4
│   │   ├── decomposer.py
│   │   └── prompts.py
│   ├── retrieval/            # 🔄 Step 4
│   │   ├── parallel.py
│   │   └── fusion.py
│   ├── generator/            # 📋 Step 5
│   │   ├── grounded.py
│   │   └── citation.py
│   ├── pipeline/             # 📋 Step 5
│   │   ├── graph.py          # LangGraph definition
│   │   └── state.py
│   └── api/                  # 📋 Step 5
│       ├── main.py
│       └── routes.py
├── docs/                     # Documentation
├── data/
│   ├── processed/
│   └── raw/
├── models/
├── notebooks/
├── tests/
└── requirements.txt
```

---

## 8. Legend

| Icon | Meaning |
|------|---------|
| ✅ | Completed |
| 🔄 | In Progress |
| 📋 | Planned |

