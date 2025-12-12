# Step 6: FastAPI Backend & MVP Development

> **Target**: API layer cho RAG pipeline  
> **Timeline**: 3-4 ngày

---

## I. Tổng Quan

### Mục Tiêu
Xây dựng FastAPI backend expose RAG pipeline qua REST API, sẵn sàng cho frontend integration.

### Phạm Vi
- REST endpoints cho query processing
- Streaming responses (SSE)
- Health check & monitoring
- CORS configuration
- Error handling

---

## II. Kiến Trúc API

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                          │
│                                                              │
│   POST /api/query          → run_rag_pipeline()             │
│   POST /api/query/stream   → SSE streaming response         │
│   GET  /api/health         → Health check                   │
│   GET  /api/routes         → Available indices              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    LangGraph Pipeline
```

---

## III. API Endpoints

### 1. POST `/api/query`

**Request:**
```json
{
  "query": "ROE là gì và VNM có ROE bao nhiêu?",
  "options": {
    "max_docs": 10,
    "include_sources": true
  }
}
```

**Response:**
```json
{
  "answer": "ROE là tỷ suất sinh lời... [1]. VNM có ROE 25% [2].",
  "is_grounded": true,
  "citations": [
    {"number": 1, "source": "glossary", "preview": "..."},
    {"number": 2, "source": "financial", "preview": "..."}
  ],
  "metadata": {
    "routes": ["glossary", "financial"],
    "is_complex": true,
    "sub_queries": ["ROE là gì?", "VNM có ROE bao nhiêu?"],
    "total_time_ms": 2500
  }
}
```

### 2. POST `/api/query/stream`

SSE streaming cho real-time response.

### 3. GET `/api/health`

```json
{
  "status": "healthy",
  "components": {
    "supabase": "connected",
    "gemini": "available",
    "router": "initialized"
  }
}
```

---

## IV. File Structure

```
src/api/
├── __init__.py
├── main.py           # FastAPI app entry
├── routes/
│   ├── __init__.py
│   ├── query.py      # Query endpoints
│   └── health.py     # Health checks
├── schemas/
│   ├── __init__.py
│   ├── request.py    # Pydantic request models
│   └── response.py   # Pydantic response models
├── middleware/
│   ├── __init__.py
│   ├── cors.py       # CORS setup
│   └── logging.py    # Request logging
└── utils/
    ├── __init__.py
    └── streaming.py  # SSE helpers
```

---

## V. Implementation Plan

### Phase 1: Core API (Day 1-2)

#### 1.1 Schemas (request.py, response.py)
```python
# request.py
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    options: Optional[QueryOptions] = None

# response.py
class QueryResponse(BaseModel):
    answer: str
    is_grounded: bool
    citations: List[Citation]
    metadata: ResponseMetadata
```

#### 1.2 Main App (main.py)
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Multi-Index RAG API",
    version="1.0.0",
    docs_url="/docs"
)

# CORS
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)

# Routes
app.include_router(query_router, prefix="/api")
app.include_router(health_router, prefix="/api")
```

#### 1.3 Query Endpoint (query.py)
```python
@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    result = run_rag_pipeline(request.query)
    return QueryResponse(
        answer=result["answer"],
        is_grounded=result["is_grounded"],
        citations=result["citations_map"],
        metadata=ResponseMetadata(...)
    )
```

### Phase 2: Streaming (Day 2-3)

#### 2.1 SSE Streaming
```python
from sse_starlette.sse import EventSourceResponse

@router.post("/query/stream")
async def query_stream(request: QueryRequest):
    async def generate():
        # Stream each step
        yield {"event": "route", "data": ...}
        yield {"event": "retrieve", "data": ...}
        yield {"event": "generate", "data": ...}
    
    return EventSourceResponse(generate())
```

### Phase 3: Polish (Day 3-4)

- Error handling middleware
- Rate limiting (optional)
- Request logging
- API documentation

---

## VI. Dependencies

```txt
# requirements.txt - thêm
sse-starlette>=1.6.0
python-multipart>=0.0.6
```

---

## VII. Environment Variables

```bash
# .env
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1
CORS_ORIGINS=http://localhost:3000
```

---

## VIII. Verification Plan

### Unit Tests
```python
# tests/test_api.py
def test_query_endpoint():
    response = client.post("/api/query", json={"query": "ROE là gì?"})
    assert response.status_code == 200
    assert "answer" in response.json()
```

### Integration Tests
```bash
# Test với curl
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "ROE là gì?"}'
```

### Manual Testing
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## IX. Checklist

### Day 1
- [ ] Tạo folder structure (`src/api/`)
- [ ] Pydantic schemas
- [ ] Main FastAPI app

### Day 2
- [ ] Query endpoint
- [ ] Health endpoint
- [ ] CORS middleware

### Day 3
- [ ] SSE streaming
- [ ] Error handling
- [ ] Request logging

### Day 4
- [ ] Testing
- [ ] Documentation
- [ ] Polish

---

## X. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Long response time | UX kém | Streaming response |
| Gemini rate limit | 429 errors | Retry với backoff |
| CORS issues | Frontend blocked | Proper CORS config |
| Memory leak | Server crash | Lazy loading, cleanup |
