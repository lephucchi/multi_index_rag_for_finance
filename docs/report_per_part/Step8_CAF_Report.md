# STEP 8: CANONICAL ANSWER FRAMEWORK (CAF)
**Report Date**: 19/12/2024  
**System Component**: 2-Pass Generation Pipeline  
**Development Phase**: Answer Quality Enhancement  

---

## EXECUTIVE SUMMARY

This report documents the implementation of the Canonical Answer Framework (CAF), a 2-pass prompting system that improves answer consistency and structure. CAF first extracts structured facts from documents, then synthesizes a unified answer from those facts.

**Key Achievements**:
- 2-pass generation: CFE (Fact Extraction) + CAS (Answer Synthesis)
- Gemini Structured Output for guaranteed valid JSON
- JSON repair fallback for truncated responses
- Extracted 17 canonical facts from 15 documents in test

---

## 1. SYSTEM ARCHITECTURE

### 1.1. Pipeline Flow

```
Query → Route → Decompose → Retrieve → [CFE] → [CAS] → Answer
                                         ↓        ↓
                                   17 Facts   Structured Answer
```

### 1.2. Two Passes

| Pass | Name | Purpose |
|------|------|---------|
| **Pass 1** | CFE (Canonical Fact Extraction) | Extract structured facts from documents |
| **Pass 2** | CAS (Canonical Answer Synthesis) | Synthesize answer from facts |

---

## 2. CANONICAL FACT SCHEMA

```python
@dataclass
class CanonicalFact:
    domain: FactDomain          # LEGAL, FINANCIAL, NEWS, GLOSSARY
    fact_type: FactType         # definition, regulation, trend, etc.
    statement: str              # 1-2 sentence fact
    scope: str                  # Vietnam, Global, Company: X
    relevance: Relevance        # HIGH, MEDIUM, LOW
    source_id: int              # Citation number [1], [2], etc.
    sub_query: str              # Which sub-query this answers
```

---

## 3. GEMINI STRUCTURED OUTPUT

### 3.1. Problem
LLM returns invalid JSON → parsing failures

### 3.2. Solution
Use `response_schema` to force valid JSON:

```python
from google import genai
from google.genai import types

config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=decomposition_schema
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config=config
)
```

---

## 4. CANONICAL ANSWER STRUCTURE

```markdown
## 1. Tổng quan
[2-3 câu tóm tắt quan trọng nhất]

## 2. Chi tiết theo lĩnh vực
### 2.1. Khía cạnh pháp lý (if LEGAL facts)
### 2.2. Khía cạnh tài chính (if FINANCIAL facts)
### 2.3. Thông tin thị trường (if NEWS facts)
### 2.4. Thuật ngữ liên quan (if GLOSSARY facts)

## 3. Hướng dẫn thực hành
[Các bước cụ thể nên làm tiếp theo]

## 4. Lưu ý & Giới hạn
[Những gì dữ liệu KHÔNG bao phủ]
```

---

## 5. FILES CREATED/MODIFIED

| File | Status | Description |
|------|--------|-------------|
| `src/core/generator/canonical_types.py` | NEW | CanonicalFact, FactDomain, FactType |
| `src/core/generator/fact_extractor.py` | NEW | CanonicalFactExtractor class |
| `src/core/generator/answer_synthesizer.py` | NEW | CanonicalAnswerSynthesizer class |
| `src/core/generator/prompts.py` | MODIFIED | CAF prompts added |
| `src/pipeline/caf_nodes.py` | NEW | extract_facts_node, synthesize_answer_node |
| `src/pipeline/graph.py` | MODIFIED | CAF_ENABLED flag, CAF nodes |

---

## 6. TEST RESULTS

| Metric | Value |
|--------|-------|
| Total Time | 68s |
| Decomposition | 2 sub-queries |
| Facts Extracted | 17 |
| Answer Length | 3,249 chars |
| Citations Used | 9 |

---

## 7. CHALLENGES & SOLUTIONS

| Challenge | Solution |
|-----------|----------|
| JSON parsing failures | Gemini Structured Output Schema |
| Truncated JSON | JSON repair fallback |
| Missing sub-query context | Improved decomposition prompt |
| API rate limits (429) | Graceful fallback |

---

## 8. SOLID COMPLIANCE

| Principle | Implementation |
|-----------|----------------|
| **S** | Prompts, types, extractor, synthesizer separated |
| **O** | Extensible via config |
| **L** | CanonicalFact can be extended |
| **I** | Separate interfaces for extract/synthesize |
| **D** | Config from environment, dependency injection |

---

## 9. CONFIGURATION

```python
# Enable/disable CAF
CAF_ENABLED = os.getenv("CAF_ENABLED", "true").lower() == "true"

# Use programmatically
graph = build_rag_graph(use_caf=True)
```

---

## 10. NEXT STEPS

→ Step 9: External Search Fallback (Google Search Grounding)
→ DeepSearch for complex research queries
