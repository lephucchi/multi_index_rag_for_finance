# Step 4: Query Decomposition & Parallel Retrieval - Development Journey

> **Hoàn thành**: 11/12/2024  
> **Tác giả**: Development Team

## Tổng Quan

Step 4 implement hai module quan trọng:
1. **Query Decomposition**: Phân tách truy vấn phức tạp thành các sub-queries
2. **Parallel Retrieval**: Truy xuất song song từ nhiều vector indices

## Thách Thức & Giải Pháp

### 1. Phát Hiện Query Phức Tạp

**Vấn đề**: Làm sao xác định query cần decomposition?

**Giải pháp**: Two-stage approach
```
Stage 1: Rule-based classifier (fast, < 5ms)
  - Regex patterns cho composite queries ("và", "với", ...)
  - Word count threshold
  
Stage 2: LLM decomposition (khi cần, ~300ms)
  - Gemini 2.0 Flash với few-shot prompts
  - Fallback nếu LLM không available
```

### 2. Parallel vs Sequential Retrieval

**Vấn đề**: Retrieve từ nhiều indices sao cho nhanh?

**Giải pháp**: Async parallel với asyncio
```python
tasks = [retrieve_async(sq, route) for sq, route in zip(...)]
results = await asyncio.gather(*tasks)  # Song song!
```

**Kết quả**: 
- Sequential: ~3s cho 4 indices
- Parallel: ~800ms cho 4 indices (3.75x faster)

### 3. Result Fusion

**Vấn đề**: Merge results từ nhiều sources như thế nào?

**Giải pháp**: 3 strategies
1. **Weighted**: Boost glossary (định nghĩa trước)
2. **Round-robin**: Interleave để đảm bảo diversity
3. **Top-k**: Simple similarity ranking

## SOLID Principles Applied

| Principle | Implementation |
|-----------|----------------|
| **S**ingle Responsibility | Classifier chỉ classify, Decomposer chỉ decompose |
| **O**pen/Closed | Config injection, không sửa core logic |
| **L**iskov | Protocol-based abstractions |
| **I**nterface Segregation | Nhỏ gọn protocols (EncoderProtocol, VectorDBProtocol) |
| **D**ependency Inversion | DI cho encoder, vector_db, llm_client |

## Files Đã Tạo

```
src/
├── config/
│   ├── __init__.py           # Settings + re-export configs
│   ├── router_config.py
│   ├── decomposition_config.py
│   └── retrieval_config.py
│
├── core/
│   ├── decomposition/
│   │   ├── classifier.py     # QueryComplexityClassifier
│   │   ├── decomposer.py     # QueryDecomposer + GeminiClient
│   │   └── prompts.py        # Few-shot prompts
│   └── retrieval/
│       ├── parallel.py       # ParallelRetriever
│       └── fusion.py         # ResultFusion + FusionStrategy
```

## Kết Quả Test

```
✓ Classifier: 9/9 queries classified correctly
✓ Decomposer: LLM integration working (with fallback)
✓ Parallel Retrieval: Async working
✓ Fusion: All 3 strategies tested
```

## Lessons Learned

1. **Lazy loading** giúp startup nhanh hơn
2. **Protocol-based DI** làm testing dễ hơn
3. **Graceful fallback** quan trọng khi external services fail

## Next Steps

→ Step 5: Grounded Generation với LangGraph pipeline
