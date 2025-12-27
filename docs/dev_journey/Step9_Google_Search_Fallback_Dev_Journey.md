# Step 9: Google Search Fallback Development Journey

> **Date:** 2025-12-27
> **Status:** ✅ Completed

---

## 1. Objective

Implement an external search fallback mechanism using Google Search Grounding when internal vector DB has insufficient coverage for real-time/temporal queries.

---

## 2. Architecture

```
Query → Route → Decompose → Retrieve → [Fallback Check] → Generate → Answer
                                            ↓
                                 [TEMPORAL_QUERY?]
                                            ↓
                                  [Google Search]
                                            ↓
                                    [Web Contexts]
                                            ↓
                                 [FAST PATH Answer]
```

### Flow:
1. **FallbackDecider:** Analyze if query needs real-time data
2. **GoogleSearchGrounding:** Execute search via Gemini + Google Search tool
3. **FAST PATH:** For simple queries, use web data directly (skip CAF)

---

## 3. Key Implementations

### 3.1 Temporal Keyword Detection
**Problem:** Query "VN-Index hôm nay" returns old news from DB

**Solution:** Split temporal keywords into STRONG vs WEAK:
```python
STRONG_TEMPORAL = ("hôm nay", "today", "now", "hiện tại")  # ALWAYS fallback
WEAK_TEMPORAL = ("tuần này", "mới nhất", "latest")  # Fallback if no news
```

### 3.2 Google Search Grounding
- Uses `langchain-google-genai` with `ChatGoogleGenerativeAI`
- Binds `google_search` tool for grounded search
- Parses JSON response with findings and summary

### 3.3 FAST PATH for Simple Queries
**Problem:** CAF 2-pass (extract → synthesize) too complex for web data

**Solution:** When `is_simple AND has_web_data`:
- Skip fact extraction and synthesis
- Use web contexts directly as answer
- Save ~20 seconds + reduce token usage

---

## 4. Files Created/Modified

| File | Change |
|------|--------|
| `src/config/fallback_config.py` | **NEW** - Config with thresholds |
| `src/core/fallback/__init__.py` | **NEW** - Module init |
| `src/core/fallback/decider.py` | **NEW** - FallbackDecider class |
| `src/core/fallback/google_search.py` | **NEW** - GoogleSearchGrounding |
| `src/pipeline/state.py` | Added fallback state fields |
| `src/pipeline/nodes.py` | Added fallback_check_node, google_search_node |
| `src/pipeline/graph.py` | Added FALLBACK_ENABLED, conditional edges |
| `src/pipeline/caf_nodes.py` | Added FAST PATH logic |
| `src/core/generator/prompts.py` | Simplified synthesis prompt |

---

## 5. Test Results

| Metric | Before | After |
|--------|--------|-------|
| "VN-Index hôm nay" | ❌ No real-time data | ✅ 1.729,80 điểm (-0.75%) |
| Fallback Trigger | N/A | ✅ TEMPORAL_QUERY detected |
| Web Contexts | N/A | 5 results from Google |
| Answer Time (FAST PATH) | ~60s | ~35s |

---

## 6. Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| Temporal query not triggering fallback | Split keywords: STRONG (always) vs WEAK |
| Web data not used in answer | Fixed: Add web contexts to CAF extraction |
| Answer too complex for simple query | Added FAST PATH: skip CAF, use web directly |
| Import error after pip install | Restart server to reload modules |

---

## 7. SOLID Compliance

- **S:** Separate decider, search, and config modules
- **O:** Extensible via `FallbackConfig` dataclass
- **L:** `FallbackDecision` can be extended with new reasons
- **I:** Clear interfaces for decider and search
- **D:** Config from environment, dependency injection

---

## 8. Configuration

```python
# Environment Variables
FALLBACK_ENABLED=true  # Feature flag
FALLBACK_RELEVANCE_THRESHOLD=0.45
FALLBACK_SEARCH_TEMPERATURE=0.0
```

---

## 9. Next Steps

1. Add DeepSearch for complex research queries
2. Implement caching for repeated searches
3. Add Tavily/Serper as backup search providers
4. Track fallback metrics (rate, latency)
