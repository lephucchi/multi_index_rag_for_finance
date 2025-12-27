# STEP 4: QUERY DECOMPOSITION & PARALLEL RETRIEVAL
**Report Date**: 11/12/2024  
**System Component**: Query Processing & Multi-Index Retrieval  
**Development Phase**: Query Intelligence  

---

## EXECUTIVE SUMMARY

This report documents the implementation of query decomposition and parallel retrieval for the Multi-Index RAG system. The system automatically detects complex queries and breaks them into sub-queries, then retrieves from multiple indices in parallel.

**Key Achievements**:
- Two-stage complexity classification (rule-based + LLM)
- Async parallel retrieval (3.75x faster than sequential)
- Multiple fusion strategies (weighted, round-robin, top-k)
- 100% accuracy on complexity classification tests

---

## 1. SYSTEM ARCHITECTURE

### 1.1. Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Complexity Classifier** | Rule-based + Regex | Fast query analysis (<5ms) |
| **Query Decomposer** | Gemini 2.0 Flash | LLM-powered decomposition |
| **Parallel Retriever** | asyncio.gather | Concurrent index queries |
| **Result Fusion** | Custom strategies | Merge multi-source results |

### 1.2. Pipeline Flow

```
Query → [Complexity Check] → Simple? → Direct Retrieve
                │
                └── Complex? → [Decompose] → [Parallel Retrieve] → [Fusion]
```

---

## 2. QUERY COMPLEXITY CLASSIFICATION

### 2.1. Two-Stage Approach

**Stage 1: Rule-based (Fast, <5ms)**
- Regex patterns for composite queries ("và", "với", "so với")
- Word count threshold
- Keyword detection

**Stage 2: LLM Decomposition (when needed, ~300ms)**
- Gemini 2.0 Flash with few-shot prompts
- Graceful fallback if LLM unavailable

### 2.2. Classification Rules

```python
COMPOSITE_PATTERNS = [
    r"\b(và|với|cùng|hoặc|hay)\b",   # Vietnamese conjunctions
    r"\bso sánh\b",                    # Comparison requests
    r"\b(giữa|với nhau)\b",            # Between/comparison
]
```

---

## 3. PARALLEL RETRIEVAL

### 3.1. Performance Comparison

| Mode | Time (4 indices) | Speedup |
|------|-----------------|---------|
| Sequential | ~3,000ms | 1x |
| Parallel | ~800ms | **3.75x** |

### 3.2. Implementation

```python
async def retrieve_parallel(queries_with_routes):
    tasks = [
        retrieve_async(query, route) 
        for query, route in queries_with_routes
    ]
    results = await asyncio.gather(*tasks)
    return results
```

---

## 4. RESULT FUSION STRATEGIES

| Strategy | Description | Use Case |
|----------|-------------|----------|
| **Weighted** | Boost glossary results | Definition queries |
| **Round-robin** | Interleave sources | Diversity needed |
| **Top-k** | Simple similarity ranking | General queries |

---

## 5. FILES CREATED

```
src/config/
├── decomposition_config.py    # DecompositionConfig dataclass
└── retrieval_config.py        # RetrievalConfig settings

src/core/decomposition/
├── classifier.py              # QueryComplexityClassifier
├── decomposer.py              # QueryDecomposer + GeminiClient
└── prompts.py                 # Few-shot decomposition prompts

src/core/retrieval/
├── parallel.py                # ParallelRetriever
└── fusion.py                  # ResultFusion + FusionStrategy
```

---

## 6. SOLID COMPLIANCE

| Principle | Implementation |
|-----------|----------------|
| **S** | Classifier classifies, Decomposer decomposes |
| **O** | Config injection, no core logic modification |
| **L** | Protocol-based abstractions |
| **I** | Compact protocols (EncoderProtocol, VectorDBProtocol) |
| **D** | DI for encoder, vector_db, llm_client |

---

## 7. TEST RESULTS

```
✓ Classifier: 9/9 queries classified correctly
✓ Decomposer: LLM integration working (with fallback)
✓ Parallel Retrieval: Async working
✓ Fusion: All 3 strategies tested
```

---

## 8. NEXT STEPS

→ Step 5: Grounded Generation with LangGraph pipeline
