# SDK Migration: google-generativeai → google-genai

> **Ngày thực hiện**: 14/12/2024  
> **Phiên bản mới**: google-genai>=1.0.0

---

## Tóm Tắt

Migration từ SDK `google-generativeai` (deprecated) sang SDK `google-genai` mới nhất. SDK cũ sẽ ngừng hỗ trợ vào 31/08/2025.

---

## Lý Do Migration

- **Deprecation**: SDK `google-generativeai` sẽ ngừng hỗ trợ vào 31/08/2025
- **Unified Interface**: SDK mới cung cấp interface thống nhất cho cả Gemini Developer API và Vertex AI
- **Simpler API**: Client-based API đơn giản và dễ sử dụng hơn
- **New Features**: Tiếp cận các tính năng mới và cải thiện hiệu năng

---

## Files Đã Thay Đổi

### Requirements
- `requirements.txt`: `google-generativeai>=0.3.0` → `google-genai>=1.0.0`

### Source Code
| File | Changes |
|------|---------|
| `src/core/retrieval/translator.py` | Import + Client API |
| `src/core/generator/persona_rewriter.py` | Import + Client API |
| `src/core/generator/grounded.py` | Import + Client API |
| `src/core/decomposition/decomposer.py` | Import + Client API |

### Documentation
| File | Changes |
|------|---------|
| `docs/plan/Step4_Query_Decomposition_Parallel_Retrieval_Plan.md` | Updated examples |
| `docs/plan/Step5_Grounded_Generation_LangGraph_Plan.md` | Updated examples |

---

## API Changes Reference

| Trước (google-generativeai) | Sau (google-genai) |
|----------------------------|---------------------|
| `import google.generativeai as genai` | `from google import genai` |
| `genai.configure(api_key=key)` | `client = genai.Client(api_key=key)` |
| `genai.GenerativeModel(name)` | N/A (use client directly) |
| `model.generate_content(prompt, generation_config=cfg)` | `client.models.generate_content(model=name, contents=prompt, config=cfg)` |
| `genai.GenerationConfig(...)` | `types.GenerateContentConfig(...)` |

---

## Code Example

### Trước (google-generativeai)
```python
import google.generativeai as genai

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash-exp")
config = genai.GenerationConfig(temperature=0.3, max_output_tokens=2048)
response = model.generate_content(prompt, generation_config=config)
```

### Sau (google-genai)
```python
from google import genai
from google.genai import types

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
config = types.GenerateContentConfig(temperature=0.3, max_output_tokens=2048)
response = client.models.generate_content(
    model="gemini-2.0-flash-exp",
    contents=prompt,
    config=config
)
```

---

## Verification

```bash
# Install new package
pip install google-genai

# Verify import
python -c "from google import genai; print('OK')"

# Verify modules
python -c "from src.core.decomposition.decomposer import GEMINI_AVAILABLE; print(f'GEMINI_AVAILABLE: {GEMINI_AVAILABLE}')"
```

**Kết quả**: ✅ Tất cả modules import thành công với `GEMINI_AVAILABLE = True`

---

*Migration thực hiện bởi Antigravity AI Assistant*
