# Step 7: System Optimization Phase 1

## Overview

This phase focuses on **Quick Wins** and **Latency Optimization** to improve answer quality and system performance based on production testing feedback.

### Current State Analysis

| Metric | Current | Target |
|--------|---------|--------|
| Routes selected | 4 (all) | 2-3 (smart) |
| Documents retrieved | 16 | 15-20 |
| Answer style | Academic/Legal | Consulting/Actionable |
| Total latency | ~56s | <20s |
| Retrieval quality score | 6.5/10 | 8/10 |

---

## Phase 1A: Answer Synthesis Layer (1-2 days)

### Objective
Transform grounded answers from "document excerpts" to "consulting advice" while maintaining citations.

### Implementation

#### 1. Create Persona Rewriter Module

**File**: `src/core/generator/persona_  rewriter.py`

```python
class PersonaRewriter:
    """Rewrite grounded answers for specific user personas."""
    
    PERSONAS = {
        "startup_founder": {
            "style": "actionable, strategic, risk-aware",
            "sections": ["Key Takeaways", "Action Items", "Risks to Avoid"]
        },
        "investor": {
            "style": "analytical, data-driven, comparative", 
            "sections": ["Investment Thesis", "Risk Analysis", "Recommendations"]
        },
        "legal_professional": {
            "style": "precise, citation-heavy, comprehensive",
            "sections": ["Legal Framework", "Compliance Requirements", "Precedents"]
        }
    }
    
    def rewrite(self, answer: str, persona: str, citations: List[int]) -> str:
        """Rewrite answer for target persona while preserving citations."""
        pass
```

#### 2. Integrate into Pipeline

**File**: `src/pipeline/nodes.py`

Add new step after `generate_node`:

```python
async def synthesize_node(state: RAGState) -> RAGState:
    """Synthesize answer for user persona."""
    if state.get("persona"):
        rewriter = PersonaRewriter()
        state["answer"] = rewriter.rewrite(
            answer=state["answer"],
            persona=state["persona"],
            citations=state["citations_used"]
        )
    return state
```

---

## Phase 1B: Smart News Routing (0.5 days)

### Objective
Only route to `news` index when query contains temporal/market keywords.

### Implementation

**File**: `src/core/router/router.py`

```python
TEMPORAL_KEYWORDS = [
    "xu hướng", "thị trường", "2024", "2025", "mới nhất", 
    "gần đây", "hiện nay", "triển vọng", "dự báo"
]

def should_include_news(query: str) -> bool:
    """Check if query needs news index."""
    query_lower = query.lower()
    return any(kw in query_lower for kw in TEMPORAL_KEYWORDS)

# In SemanticRouter._select_routes():
if "news" in selected and not should_include_news(query):
    selected.remove("news")
```

---

## Phase 1C: Latency Optimization (2-3 days)

### Objective
Reduce total latency from ~56s to <20s.

### 1. True Parallel Retrieval

**Current**: Sequential retrieval per sub-query
**Target**: Parallel retrieval across all indices

**File**: `src/core/retrieval/parallel.py`

```python
async def retrieve_all_async(self, sub_queries, routes):
    # Create ALL tasks upfront
    all_tasks = []
    for sq, route in zip(sub_queries, routes):
        all_tasks.append(self.retrieve_async(sq, route))
    
    # Execute ALL in parallel
    results = await asyncio.gather(*all_tasks, return_exceptions=True)
    return self._merge_results(results)
```

### 2. Query Embedding Cache

**File**: `src/core/retrieval/cache.py`

```python
from functools import lru_cache
import hashlib

class EmbeddingCache:
    """LRU cache for query embeddings."""
    
    def __init__(self, maxsize: int = 1000):
        self._cache = {}
        self.maxsize = maxsize
    
    def get_or_compute(self, query: str, encoder) -> np.ndarray:
        key = hashlib.md5(query.encode()).hexdigest()
        if key not in self._cache:
            if len(self._cache) >= self.maxsize:
                # Remove oldest entry
                oldest = next(iter(self._cache))
                del self._cache[oldest]
            self._cache[key] = encoder.encode(query)
        return self._cache[key]
```

### 3. Fast/Deep Mode Split

**File**: `src/config/retrieval_config.py`

```python
class RetrievalMode(Enum):
    FAST = "fast"      # glossary + legal only, target <10s
    DEEP = "deep"      # all indices, target <30s

@dataclass
class ModeConfig:
    FAST_INDICES = ["glossary", "legal"]
    DEEP_INDICES = ["glossary", "legal", "financial", "news"]
    
    FAST_K_PER_INDEX = 5
    DEEP_K_PER_INDEX = 10
```

---

## Phase 1D: Model Pre-warming (0.5 days)

### Objective
Eliminate "cold start" latency on first query.

### Implementation

**File**: `src/api/main.py`

```python
@app.on_event("startup")
async def startup_event():
    """Pre-warm models on API startup."""
    logger.info("Pre-warming models...")
    
    # Warm up encoder
    from src.core.retrieval import ParallelRetriever
    retriever = ParallelRetriever()
    _ = retriever.retrieve("warmup", "glossary", k=1)
    
    # Warm up router
    from src.core.router import HybridRouter
    router = HybridRouter()
    _ = router.route("warmup query")
    
    logger.info("Models ready!")
```

---

## Verification Plan

### Test Queries

```python
TEST_QUERIES = [
    # Consulting query (should use persona rewriter)
    "Tôi là startup founder, tư vấn cho tôi về BĐS",
    
    # Temporal query (should include news)
    "Xu hướng thị trường BĐS 2025",
    
    # Definition query (fast mode)
    "ROE là gì?",
    
    # Complex analysis (deep mode)
    "So sánh VIC, NVL, KDH về chiến lược phát triển"
]
```

### Success Metrics

| Metric | Before | After Phase 1 |
|--------|--------|---------------|
| Latency (simple query) | ~30s | <10s |
| Latency (complex query) | ~56s | <25s |
| Answer actionability | Low | High |
| News false positives | High | Low |

---

## File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `src/core/generator/persona_rewriter.py` | NEW | Persona-based answer rewriting |
| `src/core/retrieval/cache.py` | NEW | Embedding cache |
| `src/core/router/router.py` | MODIFY | Smart news routing |
| `src/core/retrieval/parallel.py` | MODIFY | True parallel retrieval |
| `src/config/retrieval_config.py` | MODIFY | Add RetrievalMode |
| `src/pipeline/nodes.py` | MODIFY | Add synthesize_node |
| `src/pipeline/graph.py` | MODIFY | Add synthesize to graph |
| `src/api/main.py` | MODIFY | Add model pre-warming |

---

## Estimated Timeline

```
Day 1: Phase 1A (Persona Rewriter)
  ├── Create persona_rewriter.py
  ├── Integrate into pipeline
  └── Test with consulting queries

Day 2: Phase 1B + 1D
  ├── Smart news routing
  ├── Model pre-warming
  └── Basic latency tests

Day 3-4: Phase 1C (Latency)
  ├── True parallel retrieval
  ├── Embedding cache
  ├── Fast/Deep mode
  └── End-to-end latency testing

Day 5: Integration & Testing
  ├── Full pipeline tests
  ├── A/B comparison
  └── Documentation
```

---

## Next Steps (Phase 2 Preview)

After Phase 1 completion:

1. **Expand Finance Index** - Add VIC, NVL, KDH, DXG company profiles
2. **Smart Sub-query Generation** - Add "lessons learned" templates
3. **Structured Answer Templates** - Domain-specific output formats
4. **Intent Classification Enhancement** - Better complexity scoring
