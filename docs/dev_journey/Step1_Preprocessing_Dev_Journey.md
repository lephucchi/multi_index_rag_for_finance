# DEV JOURNEY: STEP 1 - DATA PREPROCESSING
**Project**: Semantic-Router Multi-Index RAG System  
**Phase**: Data Engineering & Preprocessing  
**Date**: 01/12/2025  

---

## 1. Goal Definition
The objective of Step 1 was to transform raw, heterogeneous datasets into a unified, clean, and chunked format suitable for vector embedding and RAG retrieval.
- **Input**: Raw CSV files (Finance, Legal, News).
- **Output**: Cleaned CSVs with `content` (for embedding) and `metadata` (for filtering) columns.
- **Constraint**: Must handle Vietnamese language nuances and specific domain structures.

---

## 2. Technical Implementation Journey

### 2.1. Setting up the Environment
- **Tools**: Python 3.x, Pandas, VS Code.
- **Workspace**: `C:\uel\multi_index_rag_for_finance`.
- **Initial Check**: Created helper scripts (`check_columns.py`, `check_structure.py`) to inspect the schema of input CSVs. This was crucial to understand the data before writing any processing logic.

### 2.2. Processing Finance Data (`preprocess_finance.py`)
- **Challenge**: The finance data had 27 columns. Simply concatenating them would create messy text.
- **Solution**: 
    - Selected key columns for the `content` block: Ticker, Company Name, Overview, Profile, Shareholders, Financial Ratios.
    - Used a template approach: `Field Name: Value`.
    - Implemented a `clean_text` function to remove HTML tags and excessive whitespace.
- **Chunking**: Implemented a sliding window approach.
    - *Logic*: If text length > 1000 chars, split by paragraph `\n\n`.
    - *Refinement*: Added an overlap of 50 tokens to ensure continuity.

### 2.3. Processing Legal Data (`preprocess_legal.py`)
- **Challenge**: Legal documents are hierarchical. A chunk cannot just be "Clause 2" without knowing it belongs to "Article 5" of "Law on Enterprises".
- **Solution**:
    - **Context Injection**: Every chunk includes the Law Title and Article Title in its header.
    - **ID Strategy**: Used `Law Name` as the `law_id` to ensure human readability.
    - **Smart Chunking**: 
        - Short articles (< 500 tokens) are kept as single chunks to preserve integrity.
        - Long articles are split, but header info is repeated for every chunk.
- **Validation**: Verified that no "orphan chunks" (chunks without context) were created.

### 2.4. Processing News Data (`preprocess_news.py`)
- **Challenge**: News is time-sensitive. A RAG system needs to know *when* an event happened.
- **Solution**:
    - **Temporal Parsing**: Wrote a regex-based `parse_date` function to extract `Year`, `Month`, `Day` from the `date` string.
    - **Metadata Enrichment**: Added `year`, `month`, `day` fields to the JSON metadata. This enables future SQL-like filtering (e.g., `WHERE year = 2025`).
    - **Volume Handling**: The news dataset was large (12,685 articles). Optimized the script to use Pandas vectorization where possible, though chunking required row-by-row processing.

---

## 3. Key Algorithms Used

### 3.1. Smart Chunking (The "Secret Sauce")
Instead of using standard libraries like LangChain's `RecursiveCharacterTextSplitter` blindly, we wrote a custom splitter optimized for Vietnamese:
```python
def smart_chunk_text(text, target_tokens=800, overlap_tokens=50):
    # 1. Estimate tokens (1 token ≈ 4 chars for VN)
    # 2. Split by double newline (\n\n) -> Paragraphs
    # 3. Accumulate paragraphs into a chunk
    # 4. If a paragraph is too huge, split by sentence delimiters (. ! ?)
    # 5. When chunk limit reached, save and backtrack by 'overlap_tokens'
```
*Why?* Standard splitters often cut in the middle of Vietnamese words or lose semantic context. Our approach prioritizes semantic boundaries.

### 3.2. Metadata Serialization
We used JSON serialization for the `metadata` column.
- **Format**: `{"key": "value", ...}` stringified.
- **Benefit**: This allows the vector database (pgvector/Supabase) to index these fields as JSONB, enabling high-performance filtering.

---

## 4. Challenges & Fixes

| Challenge | Root Cause | Fix |
|-----------|------------|-----|
| **Encoding Errors** | Windows default encoding (cp1252) vs Vietnamese characters. | Enforced `encoding='utf-8-sig'` (UTF-8 with BOM) for all file I/O. |
| **Missing Data** | Some finance rows had `NaN` for critical fields. | Implemented `.fillna("N/A")` and conditional formatting to avoid printing "None" in the final text. |
| **Large Output Size** | News data generated ~1.5M chunks. | Accepted as necessary for high granularity. Future optimization: Batch processing for embeddings. |

---

## 5. Final Output Status
- **Finance**: Clean, rich company profiles. Ready for embedding.
- **Legal**: Hierarchical, context-aware legal clauses. Ready for embedding.
- **News**: Time-stamped, topic-tagged news segments. Ready for embedding.

**Next Step**: Proceed to Step 2 - Embedding Generation & Vector Database Construction.

---
*Documented by Antigravity*

