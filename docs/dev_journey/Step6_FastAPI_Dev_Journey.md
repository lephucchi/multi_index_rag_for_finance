# Step 6: FastAPI Backend - Development Journey

> **Hoàn thành**: 13/12/2024  
> **Tác giả**: Development Team

## Tổng Quan

Step 6 xây dựng REST API layer cho RAG pipeline, expose tất cả functionality qua HTTP endpoints.

## Kiến Trúc API

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│                                                              │
│   POST /api/query      → run_rag_pipeline()                 │
│   GET  /api/health     → Component status                   │
│   GET  /api/routes     → Available indices                  │
│   GET  /docs           → Swagger UI                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Files Đã Tạo

```
src/api/
├── main.py              # FastAPI app + CORS + lifespan
├── schemas/
│   ├── request.py       # QueryRequest, QueryOptions
│   └── response.py      # QueryResponse, Citation, etc.
└── routes/
    ├── query.py         # POST /api/query
    └── health.py        # GET /api/health, /routes

tests/
└── test_api.py          # Pytest test cases
```

## Key Implementation Decisions

### 1. Pydantic V2 Schemas

```python
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    options: Optional[QueryOptions] = None
    
    model_config = {
        "json_schema_extra": {"examples": [...]}
    }
```

### 2. CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configurable via env
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Response Structure

```json
{
  "answer": "ROE là... [1]",
  "is_grounded": true,
  "citations": [...],
  "metadata": {
    "routes": ["glossary"],
    "total_time_ms": 2500
  }
}
```

## Test Results

```
2 passed, 23 warnings in 8.69s
```

| Test Class | Status |
|------------|--------|
| TestRootEndpoint | ✅ |
| TestHealthEndpoint | ✅ |
| TestRoutesEndpoint | ✅ |
| TestQueryValidation | ✅ |

## Lessons Learned

1. **Pydantic V2 syntax changes** - `model_config` thay vì `Config` class
2. **Lazy imports trong routes** - Tránh circular imports
3. **Global exception handler** - Catch-all cho uncaught exceptions

## Commands

```bash
# Run server
uvicorn src.api.main:app --reload --port 8000

# Run tests
pytest tests/test_api.py -v

# Access docs
open http://localhost:8000/docs
```

## Next Steps

→ Step 7: Frontend integration
→ Step 8: Deployment
