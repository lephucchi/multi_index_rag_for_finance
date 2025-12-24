# A Semantic-Router Multi-Index Retrieval-Augmented Generation System for Vietnamese Financial Data and the Economic–Regulatory Framework

> **Trạng thái**: Step 8 (CAF) 🔄 | Chuẩn bị Step 9 (External Search)

---

## 1. Mục Tiêu Dự Án

- Xây dựng hệ thống **Retrieval-Augmented Generation đa chỉ mục (Multi-Index RAG)** cho dữ liệu pháp lý – tài chính Việt Nam
- Sử dụng **Semantic Router** để tự động định tuyến truy vấn (đạt 100% accuracy)
- Áp dụng **Query Decomposition** để xử lý truy vấn phức tạp
- Tích hợp **LangGraph** cho pipeline orchestration
- **External Search Fallback** (Google/DeepSearch) cho thông tin real-time
- Tạo nền tảng cho MVP fintech hỗ trợ phân tích thị trường và compliance

---

## 2. Kiến Trúc Hệ Thống

```
                          ┌──────────────────────────────┐
                          │      FRONTEND (Next.js)      │
                          └───────────────┬──────────────┘
                                          │ REST / WebSocket
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       BACKEND (FastAPI + LangGraph)                          │
│                                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐ │
│  │ Semantic   │→ │ Query      │→ │ Parallel   │→ │ Grounded Generation    │ │
│  │ Router     │  │ Decomposer │  │ Retriever  │  │ (CAF, Citations)       │ │
│  └────────────┘  └────────────┘  └─────┬──────┘  └────────────────────────┘ │
│                                        │                                     │
│                             ┌──────────▼──────────┐                          │
│                             │   Coverage Check    │                          │
│                             │  (Confidence < 0.4) │                          │
│                             └──────────┬──────────┘                          │
│                        ┌───────────────┴────────────────┐                    │
│                        │ YES                            │ NO                 │
│                        ▼                                │                    │
│         ┌──────────────────────────────────┐            │                    │
│         │     External Search Fallback      │           │                    │
│         │  ┌──────────────┐ ┌────────────┐ │            │                    │
│         │  │ Google       │ │ DeepSearch │ │            │                    │
│         │  │ Search API   │ │ (Tavily)   │ │            │                    │
│         │  └──────────────┘ └────────────┘ │            │                    │
│         └──────────────────────────────────┘            │                    │
│                        │                                │                    │
│                        └────────────────────────────────┘                    │
│                                        ↓                                     │
│                             ┌────────────────────┐                           │
│                             │ Final Cited Answer │                           │
│                             └────────────────────┘                           │
└────────────────┬───────────────────────┬─────────────────────────────────────┘
                 │                       │
    ┌────────────▼───────┐     ┌─────────▼─────────┐
    │ Supabase/pgvector  │     │  Gemini/OpenAI │
    │   (4 Indices)      │     │     (LLM API)     │
    └────────────────────┘     └───────────────────┘
```

---

## 3. Các Chỉ Mục Vector

| Index | Số lượng | Mô tả |
|-------|----------|-------|
| **Legal Index** | ~15,000 chunks | Luật, Nghị định, Thông tư Việt Nam |
| **News Index** | ~500,000 chunks | Tin tức tài chính – kinh tế |
| **Financial Index** | ~1,000,000 chunks | Dữ liệu 1700+ doanh nghiệp niêm yết |
| **Glossary Index** | ~3,000 terms | Thuật ngữ tài chính – pháp lý |

**Tổng**: 1,518,000+ documents | **Embedding**: BAAI/bge-m3 (1024-dim)

---

## 4. Công Nghệ Sử Dụng

| Layer | Technology | Trạng thái |
|-------|------------|------------|
| **Orchestration** | LangGraph | ✅ Implemented |
| **Backend** | FastAPI | ✅ Ready |
| **Database** | Supabase + pgvector | ✅ Ready |
| **Embeddings** | BAAI/bge-m3 | ✅ Ready |
| **LLM** | Gemini/OpenAI | ✅ Ready |
| **Cache** | Redis | 📋 Planned |
| **Frontend** | Next.js + TailwindCSS | ✅ Ready |
| **External Search** | Google API / Tavily | 📋 Planned |

---

## 5. Tiến Độ

| Step | Tên | Trạng thái |
|------|-----|------------|
| 1 | Data Preprocessing | ✅ Hoàn thành |
| 2 | Embedding & Indexing | ✅ Hoàn thành |
| 3 | Semantic Router | ✅ Hoàn thành (100% accuracy) |
| 4 | Query Decomposition & Parallel Retrieval | ✅ Hoàn thành |
| 5 | Grounded Generation (LangGraph) | ✅ Hoàn thành |
| 6 | FastAPI MVP | ✅ Hoàn thành |
| 7 | Frontend Enhancement | ✅ Hoàn thành |
| **8** | **Canonical Answer Framework (CAF)** | 🔄 Đang triển khai |
| **9** | **External Knowledge Expansion (Google/DeepSearch)** | 📋 Planned |

---

## 6. Tài Liệu Chi Tiết

- **[system.md](./system.md)** - Kiến trúc hệ thống chi tiết
- **[outline.md](./outline.md)** - Đề cương nghiên cứu khoa học
- **[plan.md](./plan.md)** - Kế hoạch triển khai từng bước
