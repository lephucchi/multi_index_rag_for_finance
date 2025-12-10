# DEV JOURNEY: STEP 2 - VECTOR DATABASE SETUP
**Project**: Semantic-Router Multi-Index RAG System  
**Phase**: Infrastructure Setup  
**Date**: 01/12/2025  

---

## 1. Goal Definition
The objective of Step 2 was to provision a vector database capable of storing and querying the processed data from Step 1.
- **Platform**: Supabase (PostgreSQL).
- **Requirement**: Support for high-dimensional vectors (1536 dims) and complex metadata filtering.

---

## 2. Technical Implementation Journey

### 2.1. Extension Activation
- **Action**: Ran `create extension if not exists vector;`.
- **Why**: This enables the `vector` data type in Postgres, which is essential for storing embeddings. Without this, we'd have to store vectors as arrays, which are incredibly slow for similarity search.

### 2.2. Schema Design Strategy
I decided to create three separate tables instead of one giant table with a `type` column.
- **Decision**: **Multi-Table Strategy** (`finance_index`, `legal_index`, `news_index`).
- **Reasoning**: 
    - **Index Efficiency**: Each table has its own HNSW index. Searching for a law doesn't need to traverse the graph of news articles. This significantly speeds up domain-specific queries.
    - **Metadata Divergence**: Finance data has `ticker` and `ratios`, while News has `publish_date`. A single table would result in a sparse JSON structure or many NULL columns.

### 2.3. Indexing Strategy (The Performance Booster)
- **HNSW Index**: `create index on ... using hnsw (embedding vector_cosine_ops);`
    - *Insight*: IVFFlat is faster to build but has lower recall. HNSW is slower to build but offers much better query performance (recall vs. latency trade-off). Since our dataset is static-heavy (laws don't change often, past news is static), HNSW is the superior choice.
- **GIN Index**: `create index on ... using gin (metadata);`
    - *Insight*: This is crucial for the "Hybrid Search". When a user filters by `year=2025`, the GIN index quickly narrows down the candidate set before the vector search even begins (or combined via bitmap scan).

### 2.4. RPC Functions (Server-Side Logic)
I wrote PL/pgSQL functions (`match_finance_documents`, etc.) to encapsulate the search logic.
- **Code Snippet**:
  ```sql
  where 1 - (embedding <=> query_embedding) > match_threshold
  ```
- **Why**: 
    - Security: We can expose these functions via Supabase API without exposing the raw table access.
    - Simplicity: The backend code just calls `rpc('match_finance', { query_embedding: ... })` instead of constructing complex SQL queries string-by-string.

---

## 3. Challenges & Fixes

| Challenge | Root Cause | Fix |
|-----------|------------|-----|
| **Function Overloading** | Supabase RPC can get confused if multiple functions have similar signatures. | Used distinct names (`match_finance_documents`, `match_legal_documents`) instead of a generic `match_documents` with a type parameter. |
| **JSONB Performance** | Querying deep inside JSON objects can be slow. | Ensured GIN indexing on the top-level `metadata` column. For extremely frequent filters (like `ticker`), we promoted them to top-level columns. |

---

## 4. Final Output Status
- **SQL Script**: `supabasePgvector_setup/setup_database.sql` created and verified.
- **Database State**: Tables created, indexes built, functions ready.

**Next Step**: Proceed to Step 2 (Continued) - Embedding Generation & Upload.

---
*Documented by Antigravity*

