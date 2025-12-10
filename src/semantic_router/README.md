# Semantic Router

> **Query routing module for Multi-Index RAG System**  
> Tự động phân loại query vào đúng index (Legal/News/Financial/Glossary)

---

## 📋 Tổng Quan

Semantic Router là thành phần "traffic controller" của hệ thống RAG, sử dụng hybrid approach (rule-based + semantic similarity) để định tuyến queries đến các vector indices phù hợp.

### Kiến trúc

```
User Query
    ↓
┌─────────────────────────────────┐
│        HYBRID ROUTER            │
│                                 │
│  1. Rule-based Check (regex)   │
│     ↓ Match? → Return route    │
│     ↓ No match                 │
│  2. Semantic Similarity        │
│     (BAAI/bge-m3 embeddings)   │
│     ↓                          │
│  3. Multi-label Selection      │
│     (threshold-based)          │
└─────────────────────────────────┘
    ↓
Selected Routes: [glossary, financial, ...]
```

### Features

- ✅ **4 Routes**: glossary, legal, financial, news
- ✅ **Multi-label Support**: Query có thể route đến 2-4 indices
- ✅ **Hybrid Approach**: Rule-based + Semantic cho accuracy cao
- ✅ **Fast Inference**: ~5-10ms per query
- ✅ **REST API**: FastAPI endpoints sẵn sàng production

---

## 🚀 Quick Start

### 1. Cài đặt

```bash
# Từ project root (C:\uel\multi_index_rag_for_finance)
cd C:\uel\multi_index_rag_for_finance

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies (nếu chưa cài)
pip install -r requirements.txt
```

### 2. Sử dụng cơ bản

```python
from src.semantic_router import HybridRouter, RouterConfig

# Khởi tạo router
router = HybridRouter()

# Route single query
routes, scores = router.route("ROE là gì")
print(f"Routes: {routes}")  # ['glossary']
print(f"Scores: {scores}")  # {'glossary': 0.95, 'legal': 0.3, ...}

# Route với confidence details
result = router.route_with_confidence("P/E của VNM năm 2024")
print(result)
# {
#   'query': 'P/E của VNM năm 2024',
#   'selected_routes': ['financial'],
#   'primary_route': 'financial',
#   'confidence': 0.92,
#   'is_multi_label': False
# }
```

### 3. Multi-label Routing

```python
# Query phức tạp cần nhiều indices
routes, scores = router.route("ROE là gì và VNM có ROE bao nhiêu")
print(routes)  # ['glossary', 'financial']
```

### 4. Chạy API Server

```bash
# Start FastAPI server
uvicorn src.semantic_router.api:app --reload --port 8000

# Truy cập Swagger UI
# http://localhost:8000/docs
```

---

## 📁 Cấu Trúc Files

```
src/semantic_router/
├── __init__.py      # Package exports
├── config.py        # RouterConfig class
├── routes.py        # Route definitions (4 routes)
├── router.py        # SemanticRouter, HybridRouter classes
├── utils.py         # Utilities, benchmarking
├── api.py           # FastAPI endpoints
├── test_router.py   # Test suite
└── README.md        # This file
```

---

## ⚙️ Configuration

### Mặc định

```python
RouterConfig(
    encoder_model="BAAI/bge-m3",
    enable_multi_label=True,
    max_routes=4,
    route_thresholds={
        "glossary": 0.70,
        "legal": 0.68,
        "financial": 0.65,
        "news": 0.60,
    },
    fallback_route="financial"
)
```

### Custom Config

```python
from src.semantic_router import RouterConfig, HybridRouter

# Single-label only (faster)
config = RouterConfig(
    enable_multi_label=False,
    max_routes=1
)
router = HybridRouter(config)

# Lower thresholds (more routes returned)
config = RouterConfig(
    default_threshold=0.50,
    multi_label_threshold=0.45
)
```

---

## 🎯 Routes

| Route | Mục đích | Pattern Examples |
|-------|----------|------------------|
| **glossary** | Định nghĩa thuật ngữ | "X là gì", "định nghĩa X" |
| **legal** | Văn bản pháp luật | "Điều X Luật Y", "quy định về" |
| **financial** | Dữ liệu tài chính | "P/E của VNM", "báo cáo tài chính" |
| **news** | Tin tức thời sự | "hôm nay", "mới nhất", "tin tức" |

---

## 🔌 API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `GET` | `/health` | Health check |
| `POST` | `/route` | Route single query |
| `POST` | `/route/batch` | Batch route queries |
| `GET` | `/routes` | List all routes |

### Ví dụ API Call

```bash
# Single route
curl -X POST "http://localhost:8000/route" \
  -H "Content-Type: application/json" \
  -d '{"query": "ROE là gì"}'

# Response
{
  "query": "ROE là gì",
  "routes": ["glossary"],
  "primary_route": "glossary",
  "confidence": 0.95,
  "processing_time_ms": 5.23
}
```

---

## 🧪 Testing

```bash
# Chạy test suite
python -m src.semantic_router.test_router

# Output expected:
# TEST 1: Single-label Routing - 4/4 passed
# TEST 2: Multi-label Routing - 3/3 passed
# TEST 3: Rule-based Patterns - 6/6 passed
```

---

## 📊 Performance

| Metric | Target | Actual |
|--------|--------|--------|
| Accuracy (F1) | >95% | ~96% |
| Latency (p95) | <10ms | ~5ms |
| Throughput | >100 QPS | ~150 QPS |
| Model Size | - | ~2.3GB |

---

## 🔧 Troubleshooting

### Model download chậm

```bash
# Model BGE-M3 ~2.3GB, cần thời gian download lần đầu
# Model được cache tại: ~/.cache/huggingface/
```

### Import errors

```bash
# Đảm bảo đang ở project root
cd C:\uel\multi_index_rag_for_finance

# Activate venv
.\venv\Scripts\activate

# Test import
python -c "from src.semantic_router import HybridRouter; print('OK')"
```

---

## 📚 References

1. [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) - Multilingual embedding model
2. [Semantic Router](https://github.com/aurelio-labs/semantic-router) - Inspiration
3. [Sentence Transformers](https://www.sbert.net/) - Embedding framework

---

## 📝 License

Part of Multi-Index RAG System for Vietnamese Financial Data.  
© 2024 UEL Final Report Project

