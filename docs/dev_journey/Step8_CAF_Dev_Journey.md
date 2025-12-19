# Step 8: Canonical Answer Framework (CAF) Development Journey

> **Date:** 2025-12-19
> **Status:** ✅ Completed

---

## 1. Objective

Implement a 2-pass prompting framework to improve answer consistency and structure for complex multi-index queries.

---

## 2. Architecture

```
Query → Route → Decompose → Retrieve → [CFE] → [CAS] → Answer
                                         ↓        ↓
                                   17 Facts   Structured Answer
```

### Two Passes:
1. **CFE (Canonical Fact Extraction):** Extract structured facts from documents
2. **CAS (Canonical Answer Synthesis):** Synthesize answer from facts

---

## 3. Key Implementations

### 3.1 Gemini Structured Output
**Problem:** LLM returns invalid JSON → parsing failures

**Solution:** Use `response_schema` to force valid JSON:
```python
config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=decomposition_schema
)
```

### 3.2 Decomposer with Schema
- Guaranteed valid JSON output
- Context-aware sub-queries
- Proper query_type routing (LEGAL, FINANCIAL, NEWS, GLOSSARY)

### 3.3 Fact Extraction
- Schema-based extraction
- JSON repair fallback for truncated responses
- 17 facts extracted from 15 documents

---

## 4. Files Created/Modified

| File | Change |
|------|--------|
| `decomposer.py` | Gemini Structured Output |
| `fact_extractor.py` | CFE with JSON repair |
| `answer_synthesizer.py` | CAS Pass 2 |
| `caf_nodes.py` | Pipeline nodes |
| `graph.py` | CAF_ENABLED flag |
| `prompts.py` | All prompts centralized |

---

## 5. Test Results

| Metric | Value |
|--------|-------|
| Total Time | 68s |
| Decomposition | 2 sub-queries |
| Facts Extracted | 17 |
| Answer Length | 3,249 chars |
| Citations | 9 |

---

## 6. Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| JSON parsing failures | Gemini Structured Output Schema |
| Truncated JSON | JSON repair fallback |
| Missing sub-query context | Improved decomposition prompt |
| API rate limits (429) | Graceful fallback |

---

## 7. SOLID Compliance

- **S:** Prompts, types, extractor, synthesizer separated
- **O:** Extensible via config
- **D:** Config from environment, dependency injection

---

## 8. Next Steps

1. Optimize latency (target < 20s)
2. Add streaming response
3. Cache router embeddings
4. Expand legal/financial corpus
