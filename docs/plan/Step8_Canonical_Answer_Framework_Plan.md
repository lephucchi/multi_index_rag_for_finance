# Step 8: Canonical Answer Framework (CAF) Implementation

> **Objective**: Implement 2-pass prompting architecture for consistent multi-index RAG answers
> **Status**: 📋 Planning → Implementation
> **Estimated Time**: 3-4 days

---

## I. Problem Statement

### Current Issues

| Issue | Impact | Root Cause |
|-------|--------|------------|
| LLM tự mâu thuẫn khi tổng hợp nhiều nguồn | Answer quality ↓ | Single-pass prompt không control |
| Đổi giọng giữa LEGAL vs NEWS vs FINANCIAL | User confusion | Không có answer structure chuẩn |
| Khó debug lỗi ở đâu | Dev productivity ↓ | Extraction + synthesis mixed |
| Khó scale khi thêm index mới | Maintenance ↑ | Prompt phải rewrite |

### Why CAF?

> **Canonical Answer Framework** là phương pháp được dùng trong:
> - Enterprise RAG systems
> - Compliance QA platforms
> - Financial/Legal copilots

**Nguyên tắc cốt lõi:**
> LLM không được "tự do trả lời" mà phải **đổ mọi thông tin về một khung chuẩn hóa trước**.

---

## II. Architecture Overview

### 2.1. High-Level Flow

```
User Query
   ↓
Query Decomposition (existing)
   ↓
Index Routing (existing)
   ↓
Per-Index Retrieval (existing)
   ↓
┌─────────────────────────────────────────────────────────────┐
│                 CANONICAL ANSWER FRAMEWORK                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ PASS 1: Canonical Fact Extraction (CFE)               │   │
│  │                                                       │   │
│  │ Input:  Per-sub-query contexts with citations        │   │
│  │ Output: List[CanonicalFact] - structured JSON        │   │
│  │                                                       │   │
│  │ Rules:                                                │   │
│  │ - Extract ONLY, no interpretation                    │   │
│  │ - Map each fact to FACT_SCHEMA                       │   │
│  │ - Preserve source_id for citations                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ PASS 2: Canonical Answer Synthesis (CAS)              │   │
│  │                                                       │   │
│  │ Input:  List[CanonicalFact] + original query         │   │
│  │ Output: Structured answer with inline citations      │   │
│  │                                                       │   │
│  │ Rules:                                                │   │
│  │ - Follow ANSWER_STRUCTURE exactly                    │   │
│  │ - Prioritize HIGH relevance facts                    │   │
│  │ - No facts outside provided canonical facts          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
   ↓
Final User Answer
```

### 2.2. Updated LangGraph Pipeline

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   route     │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │ is_complex │            │ simple
              ▼            │            ▼
       ┌─────────────┐     │     ┌─────────────┐
       │  decompose  │     │     │   retrieve  │
       └──────┬──────┘     │     └──────┬──────┘
              │            │            │
              ▼            │            │
       ┌─────────────┐     │            │
       │  retrieve   │     │            │
       │  (parallel) │     │            │
       └──────┬──────┘     │            │
              │            │            │
              └────────────┼────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ extract_facts   │  ← NEW (Pass 1)
                  │     (CFE)       │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ synthesize      │  ← NEW (Pass 2)
                  │    (CAS)        │
                  └────────┬────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    END      │
                    └─────────────┘
```

---

## III. Canonical Fact Schema

### 3.1. Schema Definition

```python
@dataclass
class CanonicalFact:
    """A single structured fact extracted from documents."""
    
    domain: Literal["LEGAL", "FINANCIAL", "NEWS", "GLOSSARY"]
    fact_type: Literal["definition", "regulation", "trend", "example", "requirement", "metric"]
    statement: str          # Concise factual statement (1-2 sentences)
    scope: str              # "Vietnam" | "Global" | "Company: XYZ"
    relevance: Literal["HIGH", "MEDIUM", "LOW"]
    source_id: int          # Citation number [1], [2], ...
    sub_query: str          # Which sub-query this fact answers
```

### 3.2. Fact Type Definitions

| Fact Type | Description | Example |
|-----------|-------------|---------|
| `definition` | Định nghĩa thuật ngữ | "ROE là tỷ suất sinh lời trên vốn chủ sở hữu" |
| `regulation` | Quy định pháp lý | "Theo Luật Doanh nghiệp 2020, công ty phải..." |
| `requirement` | Điều kiện, yêu cầu | "Doanh nghiệp XNK phải có giấy phép..." |
| `metric` | Số liệu, chỉ số | "VNM có ROE 25.3% năm 2024" |
| `trend` | Xu hướng thị trường | "Thị trường BĐS phục hồi nhờ FDI" |
| `example` | Ví dụ minh họa | "VCG là doanh nghiệp XNK xây dựng tiêu biểu" |

### 3.3. Example Output

```json
[
  {
    "domain": "LEGAL",
    "fact_type": "requirement",
    "statement": "Doanh nghiệp xuất nhập khẩu phải đăng ký kinh doanh theo Luật Doanh nghiệp 2020, Điều 7",
    "scope": "Vietnam",
    "relevance": "HIGH",
    "source_id": 3,
    "sub_query": "Điều kiện thành lập công ty xuất nhập khẩu xây dựng"
  },
  {
    "domain": "LEGAL",
    "fact_type": "requirement",
    "statement": "Công ty xây dựng phải có chứng chỉ năng lực hoạt động xây dựng theo Nghị định 15/2021",
    "scope": "Vietnam",
    "relevance": "HIGH",
    "source_id": 5,
    "sub_query": "Điều kiện thành lập công ty xuất nhập khẩu xây dựng"
  },
  {
    "domain": "NEWS",
    "fact_type": "example",
    "statement": "VCG (Vinaconex) là Tổng Công ty Cổ phần Xuất nhập khẩu và Xây dựng Việt Nam, niêm yết trên HOSE",
    "scope": "Company: VCG",
    "relevance": "HIGH",
    "source_id": 7,
    "sub_query": "Các doanh nghiệp xuất nhập khẩu xây dựng tiêu biểu"
  }
]
```

---

## IV. Canonical Answer Structure

### 4.1. Fixed Structure

```markdown
## 1. Tổng quan
[2-3 câu tóm tắt quan trọng nhất, trả lời trực tiếp câu hỏi]

## 2. Chi tiết theo lĩnh vực

### 2.1. Khía cạnh pháp lý
[Các quy định, điều kiện, nghĩa vụ - nếu có facts từ LEGAL domain]

### 2.2. Khía cạnh tài chính
[Số liệu, chỉ số, phân tích - nếu có facts từ FINANCIAL domain]

### 2.3. Thông tin thị trường
[Xu hướng, doanh nghiệp tiêu biểu - nếu có facts từ NEWS domain]

### 2.4. Thuật ngữ liên quan
[Định nghĩa - nếu có facts từ GLOSSARY domain]

## 3. Hướng dẫn thực hành
[Các bước cụ thể nên làm tiếp theo]

## 4. Lưu ý & Giới hạn
[Những gì dữ liệu KHÔNG bao phủ, cần tham khảo thêm]
```

### 4.2. Omission Rules

- Nếu không có facts từ domain nào → Bỏ section đó
- Nếu chỉ có 1-2 facts → Có thể gộp vào Tổng quan
- Section "Lưu ý & Giới hạn" luôn bắt buộc

---

## V. Prompts

### 5.1. Pass 1: Extraction Prompt

```
SYSTEM:
Bạn là agent trích xuất thông tin (Fact Extraction Agent).

NHIỆM VỤ: Trích xuất các facts từ documents vào Canonical Fact Schema.

QUY TẮC BẮT BUỘC:
1. CHỈ trích xuất, KHÔNG giải thích hoặc tư vấn
2. KHÔNG merge hoặc diễn giải thông tin across domains
3. Mỗi fact PHẢI có source_id tương ứng với citation trong document
4. Chỉ trích xuất thông tin CÓ TRONG documents
5. Nếu relevance không rõ ràng, đặt MEDIUM

CANONICAL FACT SCHEMA:
- domain: LEGAL | FINANCIAL | NEWS | GLOSSARY
- fact_type: definition | regulation | trend | example | requirement | metric
- statement: Câu khẳng định ngắn gọn (1-2 câu)
- scope: Vietnam | Global | Company: <tên công ty>
- relevance: HIGH | MEDIUM | LOW
- source_id: Số citation [1], [2], ...
- sub_query: Sub-query mà fact này trả lời

---

USER:
SUB-QUERIES VÀ DOCUMENTS:

{sub_query_contexts}

---

OUTPUT: Trả về JSON array các CanonicalFact. Không có text khác.
```

### 5.2. Pass 2: Synthesis Prompt

```
SYSTEM:
Bạn là agent tổng hợp câu trả lời (Answer Synthesis Agent).

NHIỆM VỤ: Tạo MỘT câu trả lời nhất quán từ danh sách Canonical Facts.

QUY TẮC BẮT BUỘC:
1. TUÂN THEO CANONICAL ANSWER STRUCTURE chính xác
2. ƯU TIÊN facts có relevance = HIGH
3. TRÍCH DẪN sources inline [1], [2], ... sau mỗi khẳng định
4. KHÔNG thêm facts ngoài những gì được cung cấp
5. KHÔNG lặp lại thông tin
6. Viết bằng tiếng Việt, rõ ràng, chuyên nghiệp

CANONICAL ANSWER STRUCTURE:
## 1. Tổng quan
[2-3 câu tóm tắt trực tiếp]

## 2. Chi tiết theo lĩnh vực
### 2.1. Khía cạnh pháp lý (nếu có)
### 2.2. Khía cạnh tài chính (nếu có)
### 2.3. Thông tin thị trường (nếu có)
### 2.4. Thuật ngữ liên quan (nếu có)

## 3. Hướng dẫn thực hành
[Các bước cụ thể tiếp theo]

## 4. Lưu ý & Giới hạn
[Luôn bắt buộc]

---

USER:
CÂU HỎI GỐC: {original_query}

CANONICAL FACTS:
{facts_json}

---

Hãy tạo câu trả lời theo CANONICAL ANSWER STRUCTURE:
```

---

## VI. Implementation Plan

### Phase 1: Data Classes (Day 1)
- [ ] Tạo `src/core/generator/canonical_types.py`
  - CanonicalFact dataclass
  - FactDomain, FactType, Relevance enums
- [ ] Update `src/pipeline/state.py`
  - Thêm `sub_query_contexts: Dict[str, str]`
  - Thêm `canonical_facts: List[Dict]`

### Phase 2: Fact Extraction (Day 1-2)
- [ ] Tạo `src/core/generator/fact_extractor.py`
  - CanonicalFactExtractor class
  - EXTRACTION_PROMPT
  - JSON parsing với fallback
- [ ] Update `src/core/retrieval/fusion.py`
  - Thêm `format_by_sub_query()` method

### Phase 3: Answer Synthesis (Day 2-3)
- [ ] Tạo `src/core/generator/answer_synthesizer.py`
  - CanonicalAnswerSynthesizer class
  - SYNTHESIS_PROMPT
  - Answer validation

### Phase 4: Pipeline Integration (Day 3)
- [ ] Update `src/pipeline/nodes.py`
  - Thêm `extract_facts_node()`
  - Thêm `synthesize_answer_node()`
- [ ] Update `src/pipeline/graph.py`
  - Thêm 2 nodes mới vào graph

### Phase 5: Testing (Day 4)
- [ ] Test với complex queries
- [ ] Verify canonical facts output
- [ ] Verify answer structure
- [ ] Benchmark latency

---

## VII. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Answer Structure Compliance | 100% | Automated check cho sections |
| Citation Accuracy | >95% | Manual review 50 queries |
| Cross-domain Consistency | No contradictions | Human eval |
| Latency Increase | <50% | Benchmark before/after |
| User Satisfaction | ↑ from baseline | A/B test nếu có |

---

## VIII. Comparison: Before vs After

### Before (Single-pass)
```
Query → Retrieve → Merge Context → Generate Answer
                                        ↑
                                   1 LLM call
                                   Uncontrolled output
```

### After (CAF Two-pass)
```
Query → Retrieve → Format by Sub-query → Extract Facts → Synthesize Answer
                                              ↑                ↑
                                         Pass 1           Pass 2
                                      Structured JSON    Fixed Structure
```

---

## IX. Future Extensibility

### Adding New Index (e.g., "RESEARCH")

1. **Fact Schema**: Không thay đổi, RESEARCH sẽ map vào domain mới
2. **Extraction Prompt**: Thêm RESEARCH vào domain list
3. **Answer Structure**: Thêm "### 2.5. Nghiên cứu học thuật" section
4. **Routing**: Chỉ cần update router

> **Effort estimate**: ~2 hours instead of rewriting entire prompt logic.

---

## X. References

- Enterprise RAG best practices
- Canonical Answer patterns in Legal/Financial AI
- LangGraph multi-step workflows
- Vietnamese financial regulations (Luật Doanh nghiệp 2020, etc.)
