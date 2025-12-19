# CAF Pipeline Analysis Report

> **Test Query:** "Muốn thành lập công ty xuất nhập khẩu xây dựng ở Việt Nam cần điều kiện gì, và cho tôi một số doanh nghiệp đi trước để tham khảo?"
> 
> **Test Date:** 2025-12-19 14:19

---

## 📊 Results Summary

| Metric | Value |
|--------|-------|
| Total Time | **68.08s** |
| Documents Retrieved | 39 → 15 (after fusion) |
| Canonical Facts | **17** |
| Answer Length | **3,249 chars** |
| Citations Used | **9** (`[1,4,6,7,8,9,10,11,15]`) |

---

## ⏱️ Time Breakdown

```
Route:          16.4s (24.1%)  ← Cold start, includes model loading
Decompose:       3.5s ( 5.1%)  ✅ Fast with Structured Output
Retrieve:       12.1s (17.8%)  ✅ Parallel retrieval
Extract Facts:  25.8s (38.0%)  ⚠️ Heaviest step
Synthesize:     10.2s (15.0%)  ✅ Reasonable
```

---

## ✅ Điểm Mạnh

### 1. Decomposition Chính Xác
```
Input:  "Muốn thành lập...cần điều kiện gì, và...doanh nghiệp tham khảo?"
Output:
  [1] LEGAL: Điều kiện pháp lý để thành lập công ty xuất nhập khẩu xây dựng
  [2] FINANCIAL: Các doanh nghiệp xuất nhập khẩu xây dựng uy tín để tham khảo
```
- ✅ Giữ đầy đủ context trong mỗi sub-query
- ✅ Route đúng (LEGAL, FINANCIAL)
- ✅ Method: `llm_structured` → 100% JSON hợp lệ

### 2. Multi-Index Retrieval
- 4 queries gửi đến 4 indices (legal, financial, news, glossary)
- Coverage check tự động thêm missing routes
- 39 documents retrieved → 15 sau fusion

### 3. CAF 2-Pass Generation
- **Pass 1 (CFE):** 17 facts (4 LEGAL, 10 FINANCIAL, 3 NEWS)
- **Pass 2 (CAS):** Structured answer với 9 citations
- Answer có cấu trúc rõ ràng (Tổng quan → Chi tiết → Lưu ý)

### 4. Grounded Answer
- Mỗi claim có citation `[n]` trỏ đến document nguồn
- Không hallucination (thông tin từ retrieved docs)

---

## ⚠️ Điểm Yếu

### 1. Latency Cao
- **68s** là quá chậm cho production
- CFE chiếm 38% thời gian (25.8s)
- Route cold start ~16s (có thể cache)

### 2. Router Chọn Tất Cả Indices
- Legal score 0.95, nhưng vẫn query cả news (0.37), financial (0.34)
- Có thể filter indices với score < threshold

### 3. Retrieved Documents Không Hoàn Toàn Liên Quan
- Top docs về "Luật Nhà Ở", "Luật Kinh Doanh BĐS" → không đúng chủ đề XNK
- Database thiếu data về xuất nhập khẩu cụ thể

### 4. CFE Output Size
- 17 facts cho 15 documents → có thể dư thừa
- Cần filter HIGH relevance facts

---

## 💡 Đề Xuất Cải Tiến

### Short-term (Quick Wins)

| Improvement | Expected Impact |
|-------------|-----------------|
| Cache router embeddings | -15s route time |
| Filter indices score < 0.5 | -25% retrieval time |
| Reduce CFE max facts to 10 | -30% CFE time |
| Warm-up API on startup | -3s first request |

### Medium-term

| Improvement | Description |
|-------------|-------------|
| Streaming response | Show partial answer while generating |
| Parallel CFE + CAS | Extract facts while synthesizing |
| GPU acceleration | Move embeddings to GPU |
| Index-specific prompts | Better retrieval per domain |

### Long-term

| Improvement | Description |
|-------------|-------------|
| Fine-tuned embeddings | Domain-specific embeddings |
| Legal/Financial corpus | Add more relevant documents |
| Query rewriting | Better search queries |
| Evaluation metrics | Auto-evaluate answer quality |

---

## 📈 Metrics to Track

1. **Latency P50/P95** - Target < 20s
2. **Fact Precision** - % relevant facts extracted
3. **Citation Accuracy** - % correct citations
4. **User Satisfaction** - Thumbs up/down feedback

---

## Conclusion

Pipeline CAF đã **hoạt động hoàn chỉnh** với khả năng:
- Decompose query phức tạp
- Multi-index retrieval
- Structured fact extraction
- Grounded answer synthesis

**Priority:** Optimize latency (target < 20s) trước khi mở rộng features.
