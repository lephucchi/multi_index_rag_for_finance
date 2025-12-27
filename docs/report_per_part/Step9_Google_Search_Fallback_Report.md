# STEP 9: GOOGLE SEARCH FALLBACK IMPLEMENTATION
**Report Date**: 27/12/2025  
**System Component**: External Search Fallback  
**Development Phase**: Real-time Data Integration  

---

## EXECUTIVE SUMMARY

This report documents the implementation of a Google Search Grounding fallback mechanism for the Multi-Index RAG system. The fallback triggers when internal vector DB has insufficient coverage for real-time or temporal queries (e.g., "VN-Index hôm nay").

**Key Achievements**:
- Implemented automatic fallback detection for temporal queries
- Integrated Google Search via Gemini's `google_search` tool binding
- Added FAST PATH for simple queries (skip CAF, ~20s faster)
- Returned real-time data: "VN-Index 1.729,80 điểm (-0.75%)"

---

## 1. SYSTEM ARCHITECTURE

### 1.1. Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Search Provider** | Google Search Grounding | Real-time web data |
| **LLM** | Gemini 2.5 Flash | Search execution + summarization |
| **Integration** | langchain-google-genai | Tool binding for google_search |
| **Pipeline** | LangGraph | Conditional edge routing |

### 1.2. Pipeline Flow

```
┌──────────┐     ┌───────────┐     ┌────────────────┐
│ Retrieve │ ──▶ │ Fallback  │ ──▶ │ Should         │
│          │     │ Check     │     │ Fallback?      │
└──────────┘     └───────────┘     └───────┬────────┘
                                           │
                    ┌──────────────────────┴───────────────────────┐
                    │                                              │
                    ▼ YES                                          ▼ NO
          ┌─────────────────┐                            ┌─────────────────┐
          │ Google Search   │                            │ CAF Generation  │
          │ Grounding       │                            │ (Standard)      │
          └────────┬────────┘                            └─────────────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ FAST PATH       │
          │ (Direct Answer) │
          └─────────────────┘
```

---

## 2. FALLBACK DECISION LOGIC

### 2.1. Decision Priority

| Priority | Condition | Action |
|----------|-----------|--------|
| 1 | **STRONG temporal** ("hôm nay", "today") | ALWAYS fallback |
| 2 | No documents retrieved | Fallback |
| 3 | Low relevance score (< 0.45) | Fallback |
| 4 | **WEAK temporal** without news | Fallback |
| 5 | Sufficient coverage | Skip fallback |

### 2.2. Temporal Keywords

**STRONG (always trigger fallback):**
```python
STRONG_TEMPORAL_KEYWORDS = (
    "hôm nay", "hôm qua", "sáng nay", "chiều nay", "tối nay",
    "lúc này", "bây giờ", "ngay bây giờ", "hiện tại", "hiện nay",
    "today", "yesterday", "right now", "currently", "now",
)
```

**WEAK (trigger if no news coverage):**
```python
WEAK_TEMPORAL_KEYWORDS = (
    "tuần này", "tháng này", "năm nay", "mới nhất", "gần đây",
    "vừa rồi", "vừa qua", "latest", "recent", "recently",
)
```

---

## 3. GOOGLE SEARCH GROUNDING

### 3.1. Implementation

```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)
llm_with_search = llm.bind_tools([{"google_search": {}}])
response = llm_with_search.invoke([HumanMessage(content=search_prompt)])
```

### 3.2. Search Prompt

```
Bạn là trợ lý nghiên cứu tài chính và pháp lý Việt Nam.
Hãy tìm kiếm thông tin mới nhất về các câu hỏi sau:
- VN-Index hôm nay

Yêu cầu:
1. Sử dụng Google Search để tìm thông tin chính xác
2. Ưu tiên nguồn uy tín: CafeF, VnExpress, công ty chứng khoán
3. Trích dẫn URL nguồn cho mỗi thông tin

Trả về kết quả dưới dạng JSON:
{
    "findings": [...],
    "summary": "..."
}
```

### 3.3. Sample Response

```json
{
    "findings": [
        {
            "fact": "VN-Index đóng cửa ngày 26/12/2025 ở mức 1.729,80 điểm, giảm 13,05 điểm (-0,75%)",
            "source_url": "https://cafef.vn/...",
            "source_title": "CafeF.vn"
        },
        {
            "fact": "Thanh khoản HOSE đạt 32.500 tỷ đồng, tăng 23% so với phiên trước",
            "source_url": "https://vnexpress.net/...",
            "source_title": "VnExpress"
        }
    ],
    "summary": "VN-Index giảm 0.75%, thanh khoản cao nhất từ đầu tháng 11"
}
```

---

## 4. FAST PATH OPTIMIZATION

### 4.1. Problem
CAF 2-pass (Extract Facts → Synthesize Answer) adds ~20s for simple queries with good web data.

### 4.2. Solution
Skip CAF when:
- Query is simple (not complex)
- Fallback was used
- Web contexts have good data

### 4.3. Implementation

```python
if is_simple and has_web_data:
    logger.info("[FAST PATH] Simple query with web data - using direct answer")
    web_answer = _format_web_answer(state)
    state["answer"] = web_answer
    return state
```

---

## 5. STATE SCHEMA ADDITIONS

```python
class RAGState(TypedDict):
    # NEW: Fallback (Step 9)
    fallback_decision: Optional[Dict[str, Any]]  # FallbackDecision dict
    web_contexts: List[Dict[str, Any]]           # Results from Google Search
    fallback_used: bool
    fallback_error: Optional[str]
```

---

## 6. FILES CREATED/MODIFIED

| File | Status | Description |
|------|--------|-------------|
| `src/config/fallback_config.py` | NEW | FallbackConfig dataclass |
| `src/core/fallback/__init__.py` | NEW | Module exports |
| `src/core/fallback/decider.py` | NEW | FallbackDecider, FallbackDecision |
| `src/core/fallback/google_search.py` | NEW | GoogleSearchGrounding class |
| `src/pipeline/state.py` | MODIFIED | Added fallback state fields |
| `src/pipeline/nodes.py` | MODIFIED | Added fallback_check_node, google_search_node |
| `src/pipeline/graph.py` | MODIFIED | FALLBACK_ENABLED, conditional edges |
| `src/pipeline/caf_nodes.py` | MODIFIED | FAST PATH logic |
| `src/core/generator/prompts.py` | MODIFIED | Simplified synthesis prompt |

---

## 7. CONFIGURATION

### 7.1. Environment Variables

```env
# Feature Flag
FALLBACK_ENABLED=true

# Thresholds
FALLBACK_RELEVANCE_THRESHOLD=0.45
FALLBACK_MIN_DOCS=1

# Search Settings
FALLBACK_SEARCH_TEMPERATURE=0.0
FALLBACK_MAX_RESULTS=5
FALLBACK_TIMEOUT=15.0
```

### 7.2. Runtime Override

```python
from src.pipeline.graph import build_rag_graph

# Programmatic override
graph = build_rag_graph(use_fallback=True)
```

---

## 8. VERIFICATION RESULTS

### 8.1. Test Query: "VN-Index hôm nay"

| Step | Result |
|------|--------|
| Fallback Check | ✅ TEMPORAL_QUERY detected (matched: 'hôm nay') |
| Google Search | ✅ 5 web contexts returned |
| FAST PATH | ✅ Direct answer used |
| Answer | VN-Index 1.729,80 điểm (-0.75%) |
| Total Time | ~35s (vs ~55s without FAST PATH) |

### 8.2. Pipeline Logs

```
[FALLBACK CHECK] Strong temporal keyword 'hôm nay' detected - forcing fallback
[GOOGLE SEARCH] Web Contexts: 5
[FAST PATH] Simple query with web data - using direct answer
[OUTPUT] Answer Length: 450 chars
```

---

## 9. KNOWN ISSUES & MITIGATIONS

| Issue | Status | Mitigation |
|-------|--------|------------|
| Google Search cost | ⚠️ | Free tier limit; add usage tracking |
| Server restart after pip install | ✅ Fixed | Document in README |
| CAF complexity for simple queries | ✅ Fixed | FAST PATH bypass |

---

## 10. NEXT STEPS

1. **DeepSearch** - Iterative research for complex queries
2. **Tavily/Serper** - Backup search providers
3. **Caching** - Cache repeated searches
4. **Metrics** - Track fallback_rate, latency_p95
