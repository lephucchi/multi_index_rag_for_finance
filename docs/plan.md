# Kế Hoạch Chi Tiết Dự Án: A Semantic-Router Multi-Index RAG System for Vietnamese Financial Data

> **Tác giả**: [Tên của bạn]  
> **Ngày bắt đầu**: 01/12/2025  
> **Dự án**: Hệ thống RAG đa chỉ mục với Semantic Router cho dữ liệu tài chính - pháp lý Việt Nam

---

## 📋 Tổng Quan Kế Hoạch

Kế hoạch này chia dự án thành 8 bước chính, từ tiền xử lý dữ liệu đến triển khai MVP và viết báo cáo nghiên cứu khoa học. Mỗi bước được thiết kế để đảm bảo tính khoa học, khả năng tái tạo (reproducibility) và chất lượng cao cho cả sản phẩm và nghiên cứu.

---

## BƯỚC 1: Tiền Xử Lý và Chuẩn Hóa Dữ Liệu (Data Preprocessing & Normalization)

### 🎯 Mục Tiêu Của Bước Này

- Chuẩn hóa và làm sạch toàn bộ dữ liệu thô từ 4 nguồn: Legal (pháp luật), News (tin tức), Financial (tài chính), Glossary (thuật ngữ)
- Tạo pipeline tự động cho việc phân đoạn văn bản (chunking) phù hợp với từng loại dữ liệu
- Gắn metadata đầy đủ cho mỗi chunk để hỗ trợ truy vấn và trích xuất thông tin
- Đảm bảo chất lượng dữ liệu đầu vào cho các bước embedding và indexing

### ✅ Điều Kiện Tiên Quyết (Prerequisites)

- ✔ Đã thu thập đầy đủ dữ liệu thô:
  - ~5,000 điều luật từ các bộ luật Việt Nam
  - >12,000 bài báo, tin tức tài chính - kinh tế
  - Dữ liệu tài chính của >1,700 doanh nghiệp (HOSE, HNX, UPCOM)
- ✔ Môi trường Python 3.9+ với các thư viện xử lý văn bản tiếng Việt
- ✔ Storage đủ lớn cho dữ liệu thô và đã xử lý (~10-20GB)

### 🎁 Kết Quả Mong Đợi (Expected Outputs)

- ✅ 4 bộ dữ liệu đã chuẩn hóa ở định dạng JSON/JSONL:
  - `legal_processed.jsonl`
  - `news_processed.jsonl`
  - `financial_processed.jsonl`
  - `glossary_processed.jsonl`
- ✅ Mỗi document có cấu trúc:
  ```json
  {
    "id": "unique_id",
    "source": "legal|news|financial|glossary",
    "title": "Tiêu đề",
    "content": "Nội dung đã chuẩn hóa",
    "chunks": [
      {
        "chunk_id": "chunk_0",
        "text": "Đoạn văn bản",
        "metadata": {
          "law_code": "Luật Doanh nghiệp 2020",
          "article": "Điều 10",
          "date": "2020-06-17",
          "category": "Doanh nghiệp",
          "keywords": ["công ty", "thành lập"]
        }
      }
    ]
  }
  ```
- ✅ Báo cáo thống kê chất lượng dữ liệu:
  - Số lượng documents/chunks cho mỗi nguồn
  - Độ dài trung bình của chunks
  - Phân bố metadata
  - Tỷ lệ missing/noise data

### 🛠 Tech Stack & Phân Tích

#### Công Nghệ Sử Dụng

| Công nghệ | Mục đích | Điểm mạnh | Điểm yếu | Lý do chọn |
|-----------|----------|-----------|-----------|------------|
| **Python 3.9+** | Ngôn ngữ chính | Ecosystem NLP phong phú, dễ tích hợp | Performance thấp hơn compiled languages | Standard cho ML/NLP research |
| **underthesea** | Tokenization tiếng Việt | Chuyên biệt cho tiếng Việt, pre-trained | Cộng đồng nhỏ, ít update | Best Vietnamese NLP library |
| **PyVI** | Chuẩn hóa tiếng Việt | Xử lý dấu thanh, normalize text | Chậm với văn bản dài | Chuẩn hóa tiếng Việt chính xác |
| **spaCy** | NER, POS tagging | Nhanh, production-ready | Cần train model cho tiếng Việt | Robust pipeline framework |
| **Pandas** | Data manipulation | Intuitive API, visualization support | Memory intensive | Standard cho data processing |
| **BeautifulSoup4** | HTML parsing | Dễ sử dụng, robust | Chậm với large documents | Parse HTML từ web crawl |
| **regex (re)** | Pattern matching | Built-in, fast | Khó maintain với complex patterns | Extract structured data từ legal text |

#### Chi Tiết Kỹ Thuật

**1.1. Legal Data Processing**
- **Input**: Raw legal documents (PDF/HTML/TXT)
- **Challenges**: 
  - Cấu trúc phân cấp (Luật > Chương > Mục > Điều > Khoản)
  - Citation cross-references
  - Amendments và version control
- **Solution**:
  - Sử dụng regex patterns để extract điều luật
  - Parse hierarchical structure
  - Maintain version history với git-like approach

**1.2. News Data Processing**
- **Input**: News articles (HTML/JSON từ APIs)
- **Challenges**:
  - HTML noise (ads, navigation)
  - Duplicate content
  - Temporal relevance
- **Solution**:
  - BeautifulSoup + custom extractors
  - Deduplication với MinHash LSH
  - Timestamp normalization

**1.3. Financial Data Processing**
- **Input**: Structured data (CSV/JSON từ vnstock)
- **Challenges**:
  - Tabular → text transformation
  - Missing values
  - Temporal alignment
- **Solution**:
  - Template-based text generation
  - Imputation strategies
  - Time-series aware chunking

### 📐 Thuật Toán & Mô Hình Học Thuật

#### 1. Chunking Strategies

**a) Fixed-size Chunking với Overlap**
- **Công thức**: 
  - Chunk size: `C = 512 tokens` (optimal cho embedding models)
  - Overlap: `O = 128 tokens` (25% overlap)
  - Số chunks: `N = ⌈(L - C) / (C - O)⌉ + 1` với `L` = document length
- **Reference**: 
  - Liu et al. (2023). "Lost in the Middle: How Language Models Use Long Contexts"
  - Optimal chunk size cho retrieval accuracy

**b) Semantic Chunking**
- **Thuật toán**: TextTiling (Hearst, 1997)
  - Split tại semantic boundaries
  - Sử dụng cosine similarity giữa adjacent sentences
  - Threshold: `θ = 0.6`
- **Implementation**:
  ```
  1. Compute sentence embeddings
  2. Calculate depth scores: D(i) = sim(s[i-k:i], s[i:i+k])
  3. Find local minima in depth scores
  4. Split at minima < threshold
  ```
- **Reference**: Hearst, M. A. (1997). "TextTiling: Segmenting text into multi-paragraph subtopic passages"

**c) Hierarchical Chunking for Legal Text**
- **Structure-aware splitting**: 
  - Level 1: Điều (Article)
  - Level 2: Khoản (Clause)
  - Level 3: Điểm (Point)
- **Metadata preservation**: Parent-child relationships

#### 2. Text Normalization Pipeline

**Vietnamese Text Normalization**
- **Unicode normalization**: NFC form
- **Tone mark standardization**: Telex → VNI → Unicode
- **Remove noise**: 
  - HTML tags
  - Special characters
  - Extra whitespaces
- **Reference**: Nguyen et al. (2019). "Vietnamese Text Normalization for Speech Synthesis"

#### 3. Metadata Extraction

**Named Entity Recognition (NER)**
- **Entities**:
  - ORG: Tên công ty, tổ chức
  - LAW: Tên luật, văn bản pháp luật
  - DATE: Ngày tháng
  - MONEY: Số tiền, chỉ số tài chính
- **Model**: PhoBERT-NER (fine-tuned)
- **Reference**: Nguyen et al. (2020). "PhoBERT: Pre-trained language models for Vietnamese"

**Keyword Extraction**
- **Method**: TF-IDF + KeyBERT
- **Formula**: 
  - TF-IDF: `w(t,d) = tf(t,d) × log(N/df(t))`
  - Cosine similarity với document embedding
- **Reference**: Grootendorst, M. (2020). "KeyBERT: Minimal keyword extraction with BERT"

### 🔬 Mô Tả Tổng Quan Bước

Bước này tập trung vào việc biến đổi dữ liệu thô không đồng nhất thành dạng chuẩn hóa, có cấu trúc và phù hợp cho embedding. Đây là bước nền tảng quyết định chất lượng của toàn bộ hệ thống RAG. 

**Workflow**:
```
Raw Data → Cleaning → Normalization → Chunking → Metadata Extraction → Validation → Storage
```

**Quality Assurance**:
- Manual validation trên sample data (100 documents mỗi loại)
- Automated tests cho data schema
- Statistical analysis để detect outliers

### 📊 Metrics & Evaluation

- **Chunk quality metrics**:
  - Semantic coherence score (sử dụng SentenceBERT)
  - Coverage: % content được preserve
  - Information density: tokens với high TF-IDF / total tokens
- **Metadata completeness**: % documents có đầy đủ required fields
- **Processing speed**: documents/second

### ⏱ Thời Gian Ước Tính

- Legal data: 1 tuần
- News data: 3-4 ngày
- Financial data: 2-3 ngày
- Testing & validation: 2-3 ngày
- **Tổng**: ~2-3 tuần

---

## BƯỚC 2: Embedding & Vector Index Construction

### 🎯 Mục Tiêu Của Bước Này

- Chuyển đổi tất cả chunks đã chuẩn hóa thành vector embeddings
- Xây dựng 4 vector indices riêng biệt cho Legal, News, Financial, Glossary
- Tối ưu hóa vector database cho retrieval performance
- Đảm bảo khả năng scale và real-time query

### ✅ Điều Kiện Tiên Quyết (Prerequisites)

- ✔ Hoàn thành Bước 1: Dữ liệu đã được chuẩn hóa và chunk
- ✔ Quyết định embedding model phù hợp với tiếng Việt
- ✔ Setup Supabase account hoặc local pgvector instance
- ✔ GPU/Cloud compute cho embedding generation (tùy chọn nhưng recommended)

### 🎁 Kết Quả Mong Đợi (Expected Outputs)

- ✅ 4 vector indices trong Supabase/pgvector:
  - `legal_index` (~5,000 điều × chunks/điều)
  - `news_index` (~12,000 articles × chunks/article)
  - `financial_index` (~1,700 companies × reports × chunks)
  - `glossary_index` (~3,000 thuật ngữ tài chính/pháp lý)
- ✅ Embedding metadata table với:
  - Vector ID → Document ID mapping
  - Embedding statistics (norms, dimensionality)
- ✅ Benchmark report:
  - Indexing time
  - Query latency (p50, p95, p99)
  - Recall@k metrics
- ✅ Backup và versioning strategy

### 🛠 Tech Stack & Phân Tích

#### Công Nghệ Sử Dụng

| Công nghệ | Mục đích | Điểm mạnh | Điểm yếu | Lý do chọn |
|-----------|----------|-----------|-----------|------------|
| **PhoBERT / viBERT** | Vietnamese embedding | Pre-trained cho tiếng Việt | Dimensionality cao (768) | Best Vietnamese semantic understanding |
| **Sentence-Transformers** | Embedding framework | Dễ sử dụng, nhiều pre-trained models | Limited Vietnamese models | Standard framework, có thể fine-tune |
| **OpenAI text-embedding-3** | Alternative embedding | SOTA performance, 3072 dims | Cost, API dependency | Backup option, multilingual |
| **Supabase (pgvector)** | Vector database | Postgres-based, SQL queries, free tier | Scalability limits so với chuyên dụng VDB | Easy integration, SQL flexibility |
| **FAISS** | Local vector search | Extremely fast, no network latency | In-memory, không persistent | R&D và benchmarking |
| **LangChain** | Embedding orchestration | High-level abstractions | Overhead, black-box | Rapid prototyping |

#### So Sánh Embedding Models

**Benchmark trên Vietnamese Semantic Similarity Task**

| Model | Dimensions | Performance (Spearman ρ) | Speed (docs/sec) | Cost |
|-------|-----------|-------------------------|------------------|------|
| PhoBERT-base | 768 | 0.82 | 150 | Free |
| viBERT | 768 | 0.79 | 160 | Free |
| multilingual-e5-large | 1024 | 0.84 | 120 | Free |
| OpenAI ada-002 | 1536 | 0.86 | 200 (API) | $0.0001/1K tokens |
| OpenAI text-embedding-3-small | 1536 | 0.88 | 250 (API) | $0.00002/1K tokens |

**Quyết định**: Sử dụng **PhoBERT-base** làm baseline + **OpenAI text-embedding-3-small** cho comparison
- PhoBERT: Open-source, reproducible, good Vietnamese performance
- OpenAI: SOTA performance cho production MVP

#### Vector Database Architecture

**Supabase pgvector Setup**

```sql
-- Extension
CREATE EXTENSION vector;

-- Legal Index Table
CREATE TABLE legal_embeddings (
  id BIGSERIAL PRIMARY KEY,
  chunk_id TEXT UNIQUE NOT NULL,
  document_id TEXT NOT NULL,
  embedding vector(768),  -- PhoBERT dimension
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- HNSW Index for fast ANN search
CREATE INDEX legal_hnsw_idx ON legal_embeddings 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

**Index Parameters**:
- `m = 16`: Số connections per layer (trade-off speed vs. accuracy)
- `ef_construction = 64`: Construction-time search depth
- Distance metric: **Cosine similarity** (normalized embeddings)

### 📐 Thuật Toán & Mô Hình Học Thuật

#### 1. Embedding Generation

**Batch Processing Pipeline**
```python
# Pseudo-code
def generate_embeddings(chunks, model, batch_size=32):
    embeddings = []
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        # Normalize text
        batch_texts = [preprocess(c['text']) for c in batch]
        # Generate embeddings
        batch_embeddings = model.encode(batch_texts, 
                                       normalize_embeddings=True)
        embeddings.extend(batch_embeddings)
    return embeddings
```

**Normalization**:
- L2 normalization: `v' = v / ||v||₂`
- Benefit: Cosine similarity = dot product (faster computation)
- Reference: Reimers & Gurevych (2019). "Sentence-BERT"

#### 2. Approximate Nearest Neighbor (ANN) Search

**HNSW Algorithm (Hierarchical Navigable Small World)**
- **Complexity**:
  - Build: `O(N log N × M × ef_construction)`
  - Query: `O(K × log N × ef_search)`
- **Parameters**:
  - `M`: Maximum connections (recommended: 12-48)
  - `ef_construction`: Build-time quality (recommended: 100-200)
  - `ef_search`: Query-time quality (tunable: 50-500)
- **Reference**: Malkov & Yashunin (2018). "Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs"

**Alternative: IVF (Inverted File Index)**
- Good for very large scale (>10M vectors)
- Faster build time, slightly lower recall
- Reference: Johnson et al. (2019). "Billion-scale similarity search with GPUs"

#### 3. Hybrid Search Strategy

**Combining Dense + Sparse Retrieval**

**Dense**: Vector similarity (semantic)
**Sparse**: BM25 (keyword-based)

**Fusion Formula** (Rank Fusion):
```
RRF_score(d) = Σ 1 / (k + rank_i(d))
```
- `k = 60` (constant, from literature)
- `rank_i(d)`: Rank của document `d` trong retriever `i`
- Reference: Cormack et al. (2009). "Reciprocal Rank Fusion"

**Implementation**:
```python
def hybrid_search(query, k=10, alpha=0.7):
    # Dense retrieval
    dense_results = vector_search(query, k=20)
    # Sparse retrieval
    sparse_results = bm25_search(query, k=20)
    # Fuse
    fused = reciprocal_rank_fusion([dense_results, sparse_results])
    return fused[:k]
```

#### 4. Embedding Quality Evaluation

**Metrics**:

**a) Intrinsic Evaluation**
- **Semantic Textual Similarity (STS)**:
  - Dataset: Vietnamese STS benchmark (if available) hoặc translate standard STS
  - Metric: Spearman correlation `ρ`
  - Formula: `ρ = 1 - (6Σd²) / (n(n²-1))`

**b) Extrinsic Evaluation (Retrieval Quality)**
- **Recall@K**: `Recall@K = |Relevant ∩ Retrieved@K| / |Relevant|`
- **MRR (Mean Reciprocal Rank)**: `MRR = (1/|Q|) Σ 1/rank_i`
- **NDCG (Normalized Discounted Cumulative Gain)**:
  ```
  DCG@K = Σ (2^rel_i - 1) / log₂(i + 1)
  NDCG@K = DCG@K / IDCG@K
  ```
- Reference: Voorhees & Harman (2005). "TREC: Experiment and Evaluation in Information Retrieval"

### 🔬 Mô Tả Tổng Quan Bước

Bước này chuyển đổi text chunks thành dense vector representations và xây dựng infrastructure cho fast similarity search. Đây là trái tim của hệ thống RAG, nơi semantic understanding được encode.

**Workflow**:
```
Normalized Chunks → Embedding Model → Vector Normalization → 
Index Construction → Optimization → Benchmarking → Deployment
```

**Key Considerations**:
- **Dimensionality**: Trade-off giữa expressiveness và storage/compute
- **Index type**: HNSW cho balanced performance
- **Hybrid search**: Combine semantic + keyword matching
- **Evaluation**: Rigorous testing với labeled query-document pairs

### 📊 Metrics & Evaluation

**Performance Benchmarks**:
- **Indexing throughput**: >500 documents/second
- **Query latency**: 
  - p50 < 50ms
  - p95 < 150ms
  - p99 < 300ms
- **Recall@10**: >0.90 trên test set
- **NDCG@10**: >0.85

**Test Set Creation**:
- 200 hand-crafted query-document pairs
- Coverage across all 4 indices
- Difficulty levels: Easy, Medium, Hard

### ⏱ Thời Gian Ước Tính

- Embedding model selection & fine-tuning: 4-5 ngày
- Embedding generation: 2-3 ngày
- Index construction & optimization: 3-4 ngày
- Evaluation & benchmarking: 3-4 ngày
- **Tổng**: ~2 tuần

---

## BƯỚC 3: Semantic Router Implementation

### 🎯 Mục Tiêu Của Bước Này

- Xây dựng Semantic Router để tự động phân loại query vào đúng index (Legal/News/Financial/Glossary)
- Train và fine-tune router model với high accuracy (>95%)
- Handle multi-index queries (query cần truy vấn >1 index)
- Tích hợp router vào retrieval pipeline

### ✅ Điều Kiện Tiên Quyết (Prerequisites)

- ✔ Hoàn thành Bước 2: Vector indices đã sẵn sàng
- ✔ Thu thập hoặc tạo labeled dataset cho router training
- ✔ Định nghĩa rõ ràng các route categories và decision boundaries
- ✔ Setup training infrastructure (GPU recommended)

### 🎁 Kết Quả Mong Đợi (Expected Outputs)

- ✅ Trained Semantic Router model:
  - Classification accuracy >95% trên test set
  - Support cho multi-label classification
  - Fast inference (<10ms per query)
- ✅ Router configuration file:
  ```json
  {
    "routes": [
      {
        "name": "legal",
        "description": "Legal regulation-related queries",
        "examples": ["Điều 10 Luật Doanh nghiệp", "quy định về thành lập công ty"],
        "threshold": 0.7
      },
      {
        "name": "news",
        "description": "Market news and economic updates",
        "examples": ["tin tức chứng khoán VN-Index", "thị trường hôm nay"],
        "threshold": 0.6
      },
      {
        "name": "financial",
        "description": "Company financial data and metrics",
        "examples": ["P/E ratio của VNM", "báo cáo tài chính FPT"],
        "threshold": 0.65
      },
      {
        "name": "glossary",
        "description": "Financial/legal terminology and definitions",
        "examples": ["ROE là gì", "định nghĩa vốn chủ sở hữu", "giải thích thuật ngữ EPS"],
        "threshold": 0.7
      }
    ]
  }
  ```
- ✅ Routing logic handler:
  - Single-index routing
  - Multi-index routing with priority
  - Fallback strategies
- ✅ Evaluation report:
  - Confusion matrix
  - Per-class precision/recall/F1
  - Error analysis

### 🛠 Tech Stack & Phân Tích

#### Công Nghệ Sử Dụng

| Công nghệ | Mục đích | Điểm mạnh | Điểm yếu | Lý do chọn |
|-----------|----------|-----------|-----------|------------|
| **semantic-router library** | Router framework | Purpose-built, easy integration | Mới, cộng đồng nhỏ | Designed specifically for this use case |
| **scikit-learn** | Baseline classifiers | Battle-tested, interpretable | Không semantic understanding | Baseline comparison |
| **PyTorch** | Custom router training | Flexibility, research-friendly | Boilerplate code | Full control cho research |
| **Transformers (HuggingFace)** | Transformer-based router | SOTA models, easy fine-tuning | Resource intensive | Best performance |
| **FastAPI** | Router API serving | Fast, async, modern | Slightly complex setup | Production-ready serving |

#### Router Architecture Options

**Option 1: Embedding-based Routing (Lightweight)**
```
Query → Embed → Cosine Similarity với Route Examples → Argmax → Route
```
- **Pros**: Fast, no training needed
- **Cons**: Limited to example-based routing
- **Use case**: Baseline, quick prototyping

**Option 2: MLP Classifier**
```
Query → PhoBERT Embedding → MLP(768 → 256 → 128 → 4) → Softmax → Route
```
- **Pros**: Fast inference, interpretable
- **Cons**: Cần training data
- **Use case**: Good balance

**Option 3: Fine-tuned Transformer (SOTA)**
```
Query → PhoBERT + Classification Head → Softmax → Route
```
- **Pros**: Best accuracy, contextual understanding
- **Cons**: Slower inference, more data needed
- **Use case**: Production với high accuracy requirement

**Quyết định**: Implement cả 3, sử dụng **Option 2 (MLP)** làm primary với **Option 1** làm fallback

### 📐 Thuật Toán & Mô Hình Học Thuật

#### 1. Semantic Router Algorithm

**Core Algorithm** (từ semantic-router library):

```python
class SemanticRouter:
    def __init__(self, routes, encoder, threshold=0.7):
        self.routes = routes
        self.encoder = encoder
        self.threshold = threshold
        # Pre-compute route embeddings
        self.route_embeddings = self._embed_routes()
    
    def _embed_routes(self):
        embeddings = {}
        for route in self.routes:
            # Average embeddings của examples
            route_embs = [self.encoder.encode(ex) 
                         for ex in route['examples']]
            embeddings[route['name']] = np.mean(route_embs, axis=0)
        return embeddings
    
    def route(self, query):
        query_emb = self.encoder.encode(query)
        scores = {}
        for route_name, route_emb in self.route_embeddings.items():
            scores[route_name] = cosine_similarity(query_emb, route_emb)
        
        # Multi-label: Tất cả routes > threshold
        selected_routes = [name for name, score in scores.items() 
                          if score > self.threshold]
        
        if not selected_routes:
            # Fallback: Chọn route cao nhất
            selected_routes = [max(scores, key=scores.get)]
        
        return selected_routes, scores
```

**Reference**: 
- Aurelio AI (2024). "Semantic Router: Decision-making layer for LLMs"
- Few-shot learning với semantic similarity

#### 2. Multi-Label Classification

**Problem Formulation**:
- Input: Query `q`
- Output: Set of labels `Y ⊆ {legal, news, financial, glossary}`
- Probability: `P(y_i | q)` cho mỗi label `y_i`

**Loss Function** (Binary Cross-Entropy):
```
L = -Σ [y_i log(p_i) + (1 - y_i) log(1 - p_i)]
```

**Threshold Optimization**:
- Grid search over thresholds `[0.5, 0.55, ..., 0.9]`
- Metric: F1-score macro average
- Reference: Sorower, M. S. (2010). "A literature survey on algorithms for multi-label learning"

#### 3. Few-Shot Learning for Router

**Prototype Networks**:
- **Idea**: Tạo prototype embedding cho mỗi class từ examples
- **Formula**: 
  ```
  c_k = (1/|S_k|) Σ f(x_i)  // Prototype của class k
  d(x, c_k) = ||f(x) - c_k||₂  // Distance tới prototype
  P(y=k|x) = softmax(-d(x, c_k))
  ```
- **Reference**: Snell et al. (2017). "Prototypical Networks for Few-shot Learning"

**Advantage**: Hoạt động tốt với ít examples (5-10 per class)

#### 4. Query Intent Classification

**Vietnamese Query Understanding**:
- **Challenges**:
  - Informal language: "p/e vnm là bao nhiêu", "luật doanh nghiệp nói gì về..."
  - Code-switching: "EPS của FPT", "compliance với regulations"
  - Ambiguity: "FPT" (company vs. university)

**Solutions**:
- **Contextualized embeddings**: PhoBERT captures context
- **Entity recognition**: Pre-detect entities trước khi route
- **Confidence thresholding**: Nếu confidence thấp → query decomposition

#### 5. Routing Strategy Optimization

**Decision Tree Approach**:
```
IF query asks "là gì", "định nghĩa", "giải thích thuật ngữ":
    → Route to Glossary (high confidence)
ELIF query contains legal keywords (luật, điều, quy định) AND entities (Luật X):
    → Route to Legal (high confidence)
ELIF query contains financial metrics (P/E, EPS, revenue):
    → Route to Financial
ELIF query contains temporal keywords (hôm nay, tuần này):
    → Route to News (likely)
ELSE:
    → Use semantic similarity
```

**Hybrid Approach**:
- Combine rule-based + ML-based routing
- Rules for high-confidence cases
- ML cho ambiguous cases
- Reference: Hybrid intent classification in dialogue systems

### 🔬 Mô Tả Tổng Quan Bước

Semantic Router là "traffic controller" của hệ thống, quyết định query nên được route tới index nào. Đây là điểm khác biệt chính so với RAG truyền thống (search tất cả indices) và giúp:
- **Giảm latency**: Chỉ search relevant indices
- **Tăng precision**: Tránh irrelevant results từ wrong indices
- **Tối ưu cost**: Ít API calls hơn

**Workflow**:
```
Query → Intent Analysis → Semantic Router → Route Decision → 
Index Selection → (If multi-label) Priority Ranking → Retrieval
```

**Key Innovation**:
- **Adaptive routing**: Học từ user feedback
- **Multi-label support**: Xử lý cross-domain queries
- **Confidence-aware**: Fallback strategies cho low-confidence

### 📊 Metrics & Evaluation

**Router Performance Metrics**:

**1. Classification Metrics**:
- **Accuracy**: `(TP + TN) / Total` (target: >95%)
- **Precision, Recall, F1** per class
- **Confusion Matrix**: Analyze misclassifications

**2. Routing Quality Metrics**:
- **Route Correctness Rate**: % queries routed correctly
- **Multi-label F1**: For multi-index queries
- **Average Confidence**: Mean `P(y|q)` for correct routes

**3. End-to-End Metrics**:
- **Retrieval Success Rate**: % queries với relevant results sau routing
- **Latency**: Routing time overhead
- **User Satisfaction**: A/B test với/không có router

**Evaluation Dataset**:
- **Training set**: 500 labeled queries (balanced)
- **Validation set**: 100 queries
- **Test set**: 200 queries (include edge cases)
- **Annotation**: 2 annotators, Cohen's Kappa >0.8

### 📝 Training Data Creation

**Data Sources**:
1. **Synthetic queries**: Generate từ document titles/summaries
2. **Real queries**: Collect từ pilot users (nếu có)
3. **Augmentation**: 
   - Paraphrasing với LLM
   - Back-translation (Vi → En → Vi)
   - Synonym replacement

**Example Labeling**:
```json
{
  "query": "Điều 10 Luật Doanh nghiệp 2020 quy định gì?",
  "labels": ["legal"],
  "confidence": 1.0
},
{
  "query": "VN-Index hôm nay thế nào, và có quy định gì về giao dịch?",
  "labels": ["news", "legal"],
  "confidence": 0.9
}
```

### ⏱ Thời Gian Ước Tính

- Data collection & labeling: 1 tuần
- Router implementation (3 options): 4-5 ngày
- Training & tuning: 3-4 ngày
- Evaluation & error analysis: 2-3 ngày
- Integration testing: 2 ngày
- **Tổng**: ~2.5 tuần

---

## BƯỚC 4: Query Decomposition & Parallel Retrieval

### 🎯 Mục Tiêu Của Bước Này

- Implement Query Decomposition để phân tách complex queries thành sub-queries
- Thiết kế parallel retrieval system cho multiple sub-queries
- Develop result fusion mechanism để combine retrieved contexts
- Optimize cho latency và accuracy

### ✅ Điều Kiện Tiên Quyết (Prerequisites)

- ✔ Hoàn thành Bước 3: Semantic Router đang hoạt động
- ✔ Vector indices và retrieval APIs ready
- ✔ LLM API access (cho decomposition) hoặc trained local model
- ✔ Async framework setup (asyncio/FastAPI)

### 🎁 Kết Quả Mong Đợi (Expected Outputs)

- ✅ Query Decomposition module:
  - Input: Complex query
  - Output: List of atomic sub-queries
  - Example:
    ```json
    {
      "original": "So sánh P/E của VNM và FPT, và quy định về công bố thông tin tài chính",
      "sub_queries": [
        "P/E ratio của VNM",
        "P/E ratio của FPT", 
        "Quy định về công bố thông tin tài chính"
      ],
      "dependencies": {
        "q1": [], "q2": [], "q3": ["q1", "q2"]
      }
    }
    ```
- ✅ Parallel Retrieval Engine:
  - Execute sub-queries concurrently
  - Aggregate results with deduplication
  - Latency < 1.5× single query latency
- ✅ Result Fusion Module:
  - Combine contexts từ multiple retrievals
  - Rank và filter theo relevance
  - Maximum context window utilization
- ✅ Benchmark report:
  - Decomposition accuracy
  - Retrieval coverage improvement
  - End-to-end latency analysis

### 🛠 Tech Stack & Phân Tích

#### Công Nghệ Sử Dụng

| Công nghệ | Mục đích | Điểm mạnh | Điểm yếu | Lý do chọn |
|-----------|----------|-----------|-----------|------------|
| **LangChain** | Decomposition framework | Built-in decomposition chains | Black-box, overhead | Rapid development |
| **Gemini API** | LLM cho decomposition | Vietnamese support, fast | API cost, dependency | Best Vietnamese understanding |
| **asyncio** | Parallel execution | Native Python, no overhead | Complex error handling | Built-in async support |
| **httpx** | Async HTTP client | Modern, fully async | Newer than requests | Async API calls |
| **Redis** | Query cache | Fast, distributed | Memory-bound | Cache decomposition results |

#### Query Decomposition Approaches

**Approach 1: LLM-based Decomposition (Recommended)**
```python
DECOMPOSITION_PROMPT = """
Phân tách câu hỏi sau thành các câu hỏi con độc lập:

Câu hỏi: {query}

Yêu cầu:
1. Mỗi câu hỏi con phải trả lời độc lập được
2. Không tạo quá 5 câu hỏi con
3. Giữ nguyên entities và keywords quan trọng

Output format (JSON):
{{
  "sub_queries": ["...", "...", ...],
  "reasoning": "..."
}}
"""
```
- **Pros**: Flexible, handles complex queries
- **Cons**: Latency, cost, requires LLM
- **Reference**: Press et al. (2022). "Measuring and Narrowing the Compositionality Gap in Language Models"

**Approach 2: Rule-based Decomposition**
```python
def rule_based_decompose(query):
    # Detect conjunctions và comparison keywords
    conjunctions = ["và", "hoặc", "so sánh", ","]
    # Split on conjunctions
    # Extract entities
    # Form atomic queries
```
- **Pros**: Fast, deterministic, no API calls
- **Cons**: Limited coverage, requires manual rules
- **Use case**: Supplement to LLM approach

**Approach 3: Hybrid**
- Use rules for simple cases (e.g., "A và B")
- Use LLM for complex cases
- **Decision logic**: If query matches pattern → rule-based, else → LLM

### 📐 Thuật Toán & Mô Hình Học Thuật

#### 1. Query Decomposition Algorithm

**Least-to-Most Prompting** (Zhou et al., 2022):
- **Step 1**: Decompose into sub-problems
- **Step 2**: Solve each sub-problem sequentially
- **Formula**:
  ```
  Q = {q_1, q_2, ..., q_n}
  A_i = LLM(q_i | context={A_1, ..., A_{i-1}})
  ```
- **Reference**: Zhou et al. (2022). "Least-to-Most Prompting Enables Complex Reasoning in Large Language Models"

**Adaptation for RAG**:
```
1. Decompose: Q → {q_1, q_2, ..., q_n}
2. Route each q_i through Semantic Router
3. Retrieve: R_i = Retrieve(q_i, Index(q_i))
4. Fuse: R = Fuse({R_1, ..., R_n})
5. Generate: A = LLM(Q | context=R)
```

#### 2. Multi-Hop Reasoning

**Problem**: Một số queries require chained reasoning
- **Example**: "Công ty nào có P/E thấp nhất và tuân thủ quy định mới về governance?"
  - Sub-query 1: "List công ty và P/E"
  - Sub-query 2: "Quy định về governance"
  - Reasoning: Filter companies từ (1) based on (2)

**IRCoT (Interleaving Retrieval with Chain-of-Thought)**:
```
Thought 1: Cần tìm P/E của các công ty
Action 1: Retrieve("P/E ratios các công ty niêm yết")
Observation 1: [Results from financial index]

Thought 2: Cần biết quy định governance
Action 2: Retrieve("quy định corporate governance")
Observation 2: [Results from legal index]

Thought 3: Filter companies matching criteria
Action 3: Compare & rank
Final Answer: ...
```
- **Reference**: Trivedi et al. (2022). "Interleaving Retrieval with Chain-of-Thought Reasoning for Knowledge-Intensive Multi-Step Questions"

#### 3. Parallel Retrieval Implementation

**Algorithm**:
```python
async def parallel_retrieve(sub_queries, router, retrievers):
    # Step 1: Route all queries
    routes = await asyncio.gather(
        *[router.route(q) for q in sub_queries]
    )
    
    # Step 2: Group by index
    index_queries = defaultdict(list)
    for q, route in zip(sub_queries, routes):
        for idx in route:
            index_queries[idx].append(q)
    
    # Step 3: Batch retrieve from each index
    all_results = await asyncio.gather(
        *[retrievers[idx].batch_retrieve(queries) 
          for idx, queries in index_queries.items()]
    )
    
    # Step 4: Flatten and deduplicate
    results = deduplicate(flatten(all_results))
    return results
```

**Complexity Analysis**:
- **Sequential**: `O(n × L)` với `n` = số sub-queries, `L` = latency per query
- **Parallel**: `O(max(L_1, ..., L_k) + overhead)` với `k` = số unique indices
- **Speedup**: ~2-3× cho typical queries

#### 4. Result Fusion Strategies

**Strategy 1: Reciprocal Rank Fusion (RRF)** [Đã mô tả ở Bước 2]

**Strategy 2: Weighted Score Fusion**
```
Score(d) = Σ w_i × score_i(d)
```
- `w_i`: Weight của sub-query `i` (dựa vào importance)
- `score_i(d)`: Similarity score từ retriever `i`
- **Weight estimation**: 
  - Manual: Based on query analysis
  - Learned: Train trên labeled data

**Strategy 3: LLM-based Reranking**
```python
# After fusion, use LLM để rerank top-K results
reranked = llm_rerank(
    query=original_query,
    candidates=top_k_results,
    k=final_k
)
```
- **Pros**: Context-aware, handles semantic nuances
- **Cons**: Latency, cost
- **Reference**: Nogueira et al. (2019). "Passage Re-ranking with BERT"

#### 5. Context Window Optimization

**Problem**: LLM có limited context window (e.g., 32K tokens)

**Solutions**:

**a) Smart Truncation**
- Prioritize results by relevance score
- Ensure diversity (ít nhất 1 result từ mỗi sub-query)

**b) Hierarchical Summarization**
```
If context > limit:
    Summarize low-priority chunks
    Keep high-priority chunks intact
```

**c) Lost-in-the-Middle Mitigation**
- **Finding**: LLMs struggle với info in middle của long context
- **Solution**: Place most relevant info at beginning và end
- **Reference**: Liu et al. (2023). "Lost in the Middle: How Language Models Use Long Contexts"

**Optimal Ordering**:
```
[High relevance] → [Medium relevance] → [Low relevance] → [High relevance]
```

### 🔬 Mô Tả Tổng Quan Bước

Query Decomposition giải quyết vấn đề của complex, multi-faceted queries mà single retrieval không xử lý tốt. Bằng cách phân tách thành atomic sub-queries và retrieve parallel, hệ thống đạt được:
- **Higher recall**: Cover nhiều aspects của query
- **Better precision**: Mỗi sub-query focused hơn
- **Compositionality**: Handle multi-hop reasoning

**Workflow**:
```
Complex Query → Decomposition (LLM) → Sub-queries → 
Parallel Routing → Parallel Retrieval → Result Fusion → 
Context Optimization → Generation
```

**Challenges**:
- **Decomposition quality**: Depends on LLM capability
- **Redundancy**: Overlapping results từ sub-queries
- **Latency**: Decomposition + routing overhead
- **Context limit**: Fusion có thể vượt quá LLM context window

**Solutions**:
- **Caching**: Cache frequent decomposition patterns
- **Deduplication**: Exact + semantic dedup
- **Batching**: Group similar sub-queries
- **Summarization**: Compress low-relevance contexts

### 📊 Metrics & Evaluation

**Decomposition Quality**:
- **Coverage**: % sub-queries cover original query intent
- **Atomicity**: Sub-queries có thể trả lời độc lập không
- **Manual evaluation**: Sample 100 decompositions, human rating

**Retrieval Quality**:
- **Recall improvement**: Recall_decomposed vs. Recall_single
- **Precision@K**: Precision trong fused results
- **Redundancy rate**: % duplicate results

**Efficiency**:
- **Latency**: 
  - Decomposition time
  - Parallel retrieval time
  - Total time vs. single query baseline
- **Throughput**: Queries per second

**End-to-End**:
- **Answer quality**: Human evaluation (Likert scale 1-5)
- **Factual accuracy**: % answers supported by retrieved contexts
- **Comparison**: With vs. without decomposition

### ⏱ Thời Gian Ước Tính

- Decomposition module implementation: 3-4 ngày
- Parallel retrieval engine: 3-4 ngày
- Result fusion strategies: 2-3 ngày
- Context optimization: 2 ngày
- Integration & testing: 3 ngày
- Evaluation: 2-3 ngày
- **Tổng**: ~2.5 tuần

---

## BƯỚC 5: Reranking & Grounded Generation

### 🎯 Mục Tiêu Của Bước Này

- Implement cross-encoder reranker để improve retrieval precision
- Xây dựng grounded generation pipeline với citation enforcement
- Develop hallucination detection và answer verification mechanisms
- Đảm bảo factual accuracy và traceability của generated answers

### ✅ Điều Kiện Tiên Quyết (Prerequisites)

- ✔ Hoàn thành Bước 4: Retrieval và fusion pipeline đang hoạt động
- ✔ Chọn và setup reranker model
- ✔ LLM API với support cho structured output hoặc function calling
- ✔ Evaluation dataset với ground-truth answers

### 🎁 Kết Quả Mong Đợi (Expected Outputs)

- ✅ Reranker module:
  - Input: Query + candidate documents (top-K từ retrieval)
  - Output: Reranked documents với fine-grained scores
  - Latency: <200ms cho K=20
- ✅ Grounded generation system:
  - Citations inline trong answer
  - Traceability: Mỗi claim → source document
  - Example output:
    ```
    Theo Điều 10 Luật Doanh nghiệp 2020 [1], công ty cổ phần phải có 
    ít nhất 3 cổ đông. P/E ratio của VNM hiện là 15.2 [2], thấp hơn 
    trung bình ngành là 18.5 [3].
    
    [1] Luật Doanh nghiệp 2020, Điều 10, Khoản 1
    [2] Báo cáo tài chính VNM Q3/2024, trang 5
    [3] Phân tích ngành sữa, VNDirect, 15/11/2024
    ```
- ✅ Answer verification module:
  - Hallucination detection score
  - Factual consistency check
  - Confidence calibration
- ✅ Evaluation results:
  - Reranker impact: NDCG improvement
  - Citation accuracy: % citations đúng
  - Hallucination rate: % answers với unfounded claims

### 🛠 Tech Stack & Phân Tích

#### Công Nghệ Sử Dụng

| Công nghệ | Mục đích | Điểm mạnh | Điểm yếu | Lý do chọn |
|-----------|----------|-----------|-----------|------------|
| **Cohere Rerank API** | Reranking service | SOTA performance, multilingual | Cost, API dependency | Production-ready, Vietnamese support |
| **cross-encoder/ms-marco** | Local reranker | Free, good performance | English-centric | Fine-tune cho Vietnamese |
| **BGE-reranker** | Open-source reranker | SOTA open-source | Large model size | Alternative local option |
| **Gemini Flash** | Fast LLM | Low latency, structured output | Shorter context than Pro | Grounded generation |
| **NLI models** | Entailment detection | Verify consistency | Limited Vietnamese | Hallucination detection |
| **LangChain** | Citation framework | Built-in citation tools | Overhead | Rapid development |

#### Reranker Architecture Comparison

| Model | Parameters | Latency (20 docs) | NDCG@10 (MS MARCO) | Vietnamese Support |
|-------|-----------|-------------------|--------------------|--------------------|
| Cohere Rerank 3 | Proprietary | ~150ms | 0.89 | Yes (multilingual) |
| BGE-reranker-large | 560M | ~300ms | 0.86 | Limited (fine-tune) |
| cross-encoder-ms-marco | 340M | ~200ms | 0.84 | No (fine-tune) |
| **PhoBERT-reranker** (custom) | 135M | ~180ms | 0.80 (estimated) | Native |

**Quyết định**: 
- **Primary**: Cohere Rerank API (best Vietnamese + performance)
- **Backup**: Fine-tuned PhoBERT cross-encoder (cost optimization)

### 📐 Thuật Toán & Mô Hình Học Thuật

#### 1. Cross-Encoder Reranking

**Architecture**:
```
[CLS] Query [SEP] Document [SEP] → BERT → MLP → Relevance Score
```

**Vs. Bi-Encoder** (used in retrieval):

| Aspect | Bi-Encoder | Cross-Encoder |
|--------|------------|---------------|
| Encoding | Separate | Joint |
| Interaction | Dot product | Full attention |
| Speed | Fast (pre-compute doc embeddings) | Slow (runtime encoding) |
| Accuracy | Good | Excellent |
| Use case | First-stage retrieval | Reranking top-K |

**Two-Stage Retrieval**:
```
Corpus (10K+ docs) → Bi-Encoder → Top-100 → Cross-Encoder → Top-10 → LLM
```
- **Rationale**: Bi-encoder filters, cross-encoder refines
- **Reference**: Nogueira et al. (2019). "Multi-stage document ranking with BERT"

#### 2. Fine-tuning Cross-Encoder for Vietnamese

**Training Data**:
- **Positive pairs**: (query, relevant_doc) từ manual labels
- **Negative pairs**: (query, irrelevant_doc) từ retrieval mistakes
- **Hard negatives**: Top-K retrieved nhưng not relevant (quan trọng!)

**Loss Function** (Pairwise Margin Loss):
```
L = max(0, margin - (score_pos - score_neg))
```
- `score_pos`: Score của relevant doc
- `score_neg`: Score của irrelevant doc
- `margin`: Hyperparameter (e.g., 0.5)

**Alternative** (Pointwise BCE Loss):
```
L = -[y log(s) + (1-y) log(1-s)]
```
- `y ∈ {0, 1}`: Binary relevance label
- `s`: Predicted relevance score

**Reference**: Hofstätter et al. (2021). "Efficiently Teaching an Effective Dense Retriever with Balanced Topic Aware Sampling"

#### 3. Grounded Generation

**Problem**: LLMs có xu hướng hallucinate (generate info không có trong context)

**Solution**: Attribution-based generation

**Method 1: Inline Citation Prompting**
```
System prompt:
"Bạn là trợ lý tài chính. Trả lời câu hỏi DỰA TRÊN context được cung cấp.
Với mỗi claim, PHẢI cite nguồn theo format [1], [2], etc.
Nếu context không đủ thông tin, nói rõ ràng 'Không có thông tin trong 
tài liệu cung cấp'."

User:
Context:
[1] Luật Doanh nghiệp 2020, Điều 10: "Công ty cổ phần phải có ít nhất 3 cổ đông..."
[2] Báo cáo VNM Q3/2024: "P/E ratio: 15.2"

Question: Quy định về số lượng cổ đông và P/E của VNM?
```

**Example Response**:
```
Theo Điều 10 Luật Doanh nghiệp 2020 [1], công ty cổ phần phải có ít nhất 3 cổ đông.  
P/E ratio của VNM hiện tại là 15.2 [2].

Nguồn:
[1] Luật Doanh nghiệp 2020, Điều 10
[2] Báo cáo tài chính VNM Q3/2024
```

- **Reference**: Bohnet et al. (2022). "Attributed Question Answering: Evaluation and Modeling for Attributed Large Language Models"

**Method 2: Natural Language Inference (NLI) Verification**
```python
def verify_claim(claim, context):
    # Use NLI model để check entailment
    nli_input = f"{context} [SEP] {claim}"
    result = nli_model(nli_input)
    # result ∈ {entailment, neutral, contradiction}
    return result == "entailment"
```

**Method 3: Post-hoc Attribution**
- Generate answer first
- Extract claims
- Match claims với source documents
- Add citations
- **Reference**: Gao et al. (2023). "Enabling Large Language Models to Generate Text with Citations"

#### 4. Hallucination Detection

**Metrics**:

**a) Grounding Score**
```
Grounding = (# claims supported by context) / (# total claims)
```

**b) Citation Accuracy**
```
Accuracy = (# correct citations) / (# total citations)
```

**c) Answer Attribution F1**
- Precision: % cited info actually in source
- Recall: % info from source được cited
- F1: Harmonic mean

**Implementation**:
```python
def compute_grounding_score(answer, contexts):
    # 1. Extract claims từ answer
    claims = extract_claims(answer)  # NER + dependency parsing
    
    # 2. Check each claim
    supported = 0
    for claim in claims:
        for ctx in contexts:
            if verify_claim(claim, ctx):  # NLI
                supported += 1
                break
    
    return supported / len(claims) if claims else 0
```

#### 5. Answer Verification Pipeline

**Multi-stage Verification**:
```
Generated Answer → Claim Extraction → NLI Verification → 
Citation Matching → Confidence Scoring → (If low confidence) → Regenerate
```

**Confidence Calibration**:
- **External calibration**: Compare model confidence với actual accuracy
- **Temperature scaling**: Adjust softmax temperature `T`
  ```
  P_calibrated = softmax(logits / T)
  ```
- **Reference**: Guo et al. (2017). "On Calibration of Modern Neural Networks"

### 🔬 Mô Tả Tổng Quan Bước

Bước này nâng cao chất lượng retrieval và generation:
- **Reranking**: Fine-grained scoring để chọn best documents
- **Grounded generation**: Đảm bảo mọi claim được support bởi nguồn
- **Verification**: Detect và mitigate hallucinations

**Workflow**:
```
Retrieved Docs (Top-100) → Reranker → Top-10 → Context Assembly →
Grounded Generation → Citation Addition → Verification → 
(If fail) → Feedback Loop → Final Answer
```

**Key Principles**:
- **Attributability**: Mỗi claim phải traceable về source
- **Transparency**: Users thấy nguồn information
- **Accuracy**: Reduce false information

### 📊 Metrics & Evaluation

**Reranker Metrics**:
- **NDCG improvement**: NDCG_after_rerank - NDCG_before_rerank
- **MRR improvement**: Similar
- **Top-10 precision**: % relevant docs in top-10

**Grounded Generation Metrics**:
- **Grounding score**: >0.90 target
- **Citation accuracy**: >0.95 target
- **Hallucination rate**: <5% target
- **User trust**: Survey ratings

**Human Evaluation** (100 samples):
- Factual accuracy (1-5 scale)
- Citation quality (1-5 scale)
- Helpfulness (1-5 scale)
- Inter-annotator agreement (Fleiss' Kappa)

### ⏱ Thời Gian Ước Tính

- Reranker selection & fine-tuning: 4-5 ngày
- Grounded generation implementation: 3-4 ngày
- Hallucination detection: 3 ngày
- Verification pipeline: 2-3 ngày
- Evaluation & human study: 1 tuần
- **Tổng**: ~3 tuần

---

## BƯỚC 6: MVP Development & API Integration

### 🎯 Mục Tiêu Của Bước Này

- Xây dựng production-ready API cho RAG system
- Develop frontend MVP cho fintech chatbot
- Implement monitoring và logging infrastructure
- Deploy lên cloud platform với scalability

### ✅ Điều Kiện Tiên Quyết (Prerequisites)

- ✔ Hoàn thành Bước 1-5: Core RAG pipeline đang hoạt động
- ✔ Chọn deployment platform (Cloud Run, AWS Lambda, Azure, etc.)
- ✔ Frontend framework setup (React, Next.js, etc.)
- ✔ DevOps infrastructure (Docker, CI/CD)

### 🎁 Kết Quả Mong Đợi (Expected Outputs)

- ✅ Backend API (FastAPI):
  - `/query` endpoint: Main RAG query
  - `/health` endpoint: Health check
  - `/metrics` endpoint: System metrics
  - WebSocket support cho streaming responses
- ✅ Frontend MVP:
  - Chat interface
  - Citation display
  - Index toggle (Legal/News/Financial/Glossary)
  - Response streaming
- ✅ Infrastructure:
  - Docker containers
  - Kubernetes deployment configs (optional)
  - Monitoring dashboard (Prometheus + Grafana)
- ✅ Documentation:
  - API documentation (OpenAPI/Swagger)
  - User guide
  - System architecture diagram

### 🛠 Tech Stack & Phân Tích

#### Backend Stack

| Công nghệ | Mục đích | Điểm mạnh | Điểm yếu | Lý do chọn |
|-----------|----------|-----------|-----------|------------|
| **FastAPI** | Web framework | Async, fast, auto docs | Python-only | Best Python API framework |
| **Pydantic** | Data validation | Type safety, clear errors | Verbose schemas | Comes with FastAPI |
| **Redis** | Caching | Fast, distributed | Memory-limited | Cache embeddings & results |
| **Celery** | Task queue | Async tasks, reliable | Complex setup | Background processing |
| **Docker** | Containerization | Reproducible, portable | Size overhead | Industry standard |
| **Nginx** | Reverse proxy | Load balancing, SSL | Configuration complexity | Production serving |

#### Frontend Stack

| Công nghệ | Mục đích | Điểm mạnh | Điểm yếu | Lý do chọn |
|-----------|----------|-----------|-----------|------------|
| **Next.js** | React framework | SSR, routing, performance | Learning curve | Modern, production-ready |
| **TypeScript** | Type safety | Catch errors early, better DX | Compilation overhead | Industry standard |
| **TailwindCSS** | Styling | Utility-first, fast development | Large bundle | Rapid UI development |
| **SWR** | Data fetching | Caching, revalidation | React-only | Optimistic UI updates |
| **Socket.IO** | WebSocket | Real-time, fallback support | Overhead | Streaming responses |

#### Deployment & Monitoring

| Công nghệ | Mục đích | Điểm mạnh | Điểm yếu | Lý do chọn |
|-----------|----------|-----------|-----------|------------|
| **Google Cloud Run** | Serverless hosting | Auto-scaling, pay-per-use | Cold starts | Easy deployment |
| **Vercel** | Frontend hosting | CDN, edge functions | Vendor lock-in | Best Next.js experience |
| **Prometheus** | Metrics collection | Powerful querying, alerting | Setup complexity | Industry standard |
| **Grafana** | Visualization | Beautiful dashboards, alerts | Resource intensive | Best with Prometheus |
| **Sentry** | Error tracking | Detailed error context, alerts | Privacy concerns | Comprehensive error tracking |

### 📐 System Architecture & Implementation

#### API Design

**RESTful Endpoints**:

```python
# main.py
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel

app = FastAPI(title="Multi-Index RAG API", version="1.0.0")

class QueryRequest(BaseModel):
    query: str
    indices: list[str] = ["legal", "news", "financial", "glossary"]
    k: int = 10
    use_reranker: bool = True
    stream: bool = False

class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    metadata: dict[str, any]

@app.post("/query", response_model=Query Response)
async def query_endpoint(request: QueryRequest):
    # 1. Route query
    routes = await semantic_router.route(request.query)
    
    # 2. Decompose if complex
    sub_queries = await decompose_query(request.query)
    
    # 3. Parallel retrieval
    results = await parallel_retrieve(sub_queries, routes)
    
    # 4. Rerank
    if request.use_reranker:
        results = await rerank(request.query, results, k=request.k)
    
    # 5. Generate answer
    answer = await grounded_generate(
        query=request.query,
        contexts=results
    )
    
    return QueryResponse(
        answer=answer.text,
        sources=answer.sources,
        metadata={
            "routes": routes,
            "num_retrieved": len(results),
            "latency_ms": ...
        }
    )

@app.websocket("/ws/query")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    async for message in websocket.iter_text():
        # Stream response chunks
        async for chunk in generate_stream(message):
            await websocket.send_text(chunk)
```

**Caching Strategy**:
```python
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379)

def cache_embeddings(ttl=3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(text):
            # Check cache
            cache_key = f"emb:{hash(text)}"
            cached = redis_client.get(cache_key)
            if cached:
                return pickle.loads(cached)
            
            # Compute and cache
            result = await func(text)
            redis_client.setex(cache_key, ttl, pickle.dumps(result))
            return result
        return wrapper
    return decorator

@cache_embeddings(ttl=86400)  # 24 hours
async def embed_query(text):
    return await embedding_model.encode(text)
```

#### Frontend Implementation

**Chat Interface** (Next.js + TypeScript):

```typescript
// components/ChatInterface.tsx
import { useState } from 'react';
import { useSWR } from 'swr';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  
  const sendMessage = async () => {
    // Add user message
    setMessages([...messages, { role: 'user', content: input }]);
    
    // Call API
    const response = await fetch('/api/query', {
      method: 'POST',
      body: JSON.stringify({ query: input }),
      headers: { 'Content-Type': 'application/json' }
    });
    
    const data = await response.json();
    
    // Add assistant message
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: data.answer,
      sources: data.sources
    }]);
    
    setInput('');
  };
  
  return (
    <div className="flex flex-col h-screen">
      <MessageList messages={messages} />
      <Input value={input} onChange={setInput} onSend={sendMessage} />
    </div>
  );
}
```

**Citation Display**:
```typescript
// components/CitationCard.tsx
interface CitationCardProps {
  source: {
    title: string;
    excerpt: string;
    url?: string;
    metadata: Record<string, any>;
  };
  index: number;
}

export function CitationCard({ source, index }: CitationCardProps) {
  return (
    <div className="border rounded-lg p-4 hover:shadow-md transition">
      <div className="flex items-start gap-3">
        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-500 
                         text-white flex items-center justify-center text-sm">
          {index}
        </span>
        <div>
          <h4 className="font-semibold">{source.title}</h4>
          <p className="text-sm text-gray-600 mt-1">{source.excerpt}</p>
          <div className="flex gap-2 mt-2">
            {source.metadata.law_code && (
              <Badge>{source.metadata.law_code}</Badge>
            )}
            {source.metadata.date && (
              <Badge variant="outline">{source.metadata.date}</Badge>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
```

#### Monitoring & Logging

**Prometheus Metrics**:
```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
query_counter = Counter('rag_queries_total', 'Total queries', ['index'])
query_latency = Histogram('rag_query_latency_seconds', 'Query latency')
active_connections = Gauge('rag_active_connections', 'Active connections')

@query_latency.time()
@app.post("/query")
async def query_endpoint(request):
    query_counter.labels(index=detect_index(request.query)).inc()
    # ... handle query
```

**Structured Logging**:
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "query_processed",
    query=request.query,
    routes=routes,
    num_results=len(results),
    latency_ms=latency,
    user_id=user_id
)
```

### 📊 Metrics & Evaluation

**System Performance**:
- **Throughput**: Queries per second
- **Latency**: p50, p95, p99
- **Error rate**: % failed requests
- **Uptime**: 99.9% target (SLA)

**User Metrics**:
- **Engagement**: Messages per session
- **Retention**: DAU/MAU
- **Satisfaction**: CSAT score, NPS

**Business Metrics**:
- **API usage**: Calls per user
- **Cost**: Per query cost (LLM + infrastructure)
- **ROI**: Value delivered vs. cost

### ⏱ Thời Gian Ước Tính

- Backend API development: 1 tuần
- Frontend MVP: 1-1.5 tuần
- Integration & testing: 4-5 ngày
- Deployment setup: 3-4 ngày
- Monitoring & logging: 2-3 ngày
- **Tổng**: ~4 tuần

---

## BƯỚC 7: System Evaluation & Benchmarking

### 🎯 Mục Tiêu Của Bước Này

- Thiết lập comprehensive evaluation framework
- Benchmark system với baselines và SOTA methods
- Conduct ablation studies để understand component contributions
- Perform user studies và qualitative analysis

### ✅ Điều Kiện Tiên Quyết (Prerequisites)

- ✔ Hoàn thành Bước 1-6: Full system đang hoạt động
- ✔ Chuẩn bị evaluation datasets với ground-truth answers
- ✔ Setup baseline systems cho comparison
- ✔ Recruit participants cho user study (nếu có)

### 🎁 Kết Quả Mong Đợi (Expected Outputs)

- ✅ Evaluation dataset:
  - 500+ query-answer pairs với annotations
  - Coverage các use cases: simple, complex, multi-hop
  - Balanced across indices
- ✅ Benchmark results:
  - Comparison với baselines (single-index RAG, no routing, etc.)
  - Ablation study results
  - Statistical significance tests
- ✅ Analysis report:
  - Error analysis với categorization
  - Failure case identification
  - Performance breakdown by query type
- ✅ User study results:
  - Quantitative metrics (task success rate, time)
  - Qualitative feedback
  - Preference comparisons

### 🛠 Evaluation Framework

#### Datasets

**1. Test Set Construction**
```json
{
  "id": "test_001",
  "query": "Điều 10 Luật Doanh nghiệp quy định gì về số lượng cổ đông?",
  "gold_answer": "Theo Điều 10 Luật Doanh nghiệp 2020, công ty cổ phần phải có ít nhất 3 cổ đông...",
  "gold_sources": [
    {
      "doc_id": "legal_001",
      "relevance": 3  // 0-3 scale
    }
  ],
  "expected_route": ["legal"],
  "query_type": "factoid",
  "difficulty": "easy",
  "requires_multi_hop": false
}
```

**Query Types**:
- **Factoid**: Direct fact lookup
- **Analytical**: Comparison, analysis
- **Multi-hop**: Requires reasoning across documents
- **Open-ended**: No single correct answer

**Difficulty Levels**:
- **Easy**: Single document, explicit answer
- **Medium**: Multiple documents, synthesis needed
- **Hard**: Multi-hop reasoning, implicit info

#### Metrics

**Retrieval Metrics**:
```
Recall@K = |Relevant ∩ Retrieved@K| / |Relevant|
Precision@K = |Relevant ∩ Retrieved@K| / K
MRR = (1/|Q|) Σ 1/rank_i
NDCG@K = Σ (2^rel_i - 1) / log₂(i+1) / IDCG
```

**Generation Metrics**:

**a) Lexical Overlap**
- **BLEU**: Precision-based n-gram overlap
- **ROUGE**: Recall-based n-gram overlap
- **METEOR**: Considers synonyms, stemming

**b) Semantic Similarity**
- **BERTScore**: Contextual embedding similarity
  ```
  F_BERT = (2 × P_BERT × R_BERT) / (P_BERT + R_BERT)
  ```
- **Vietnamese SentenceBERT**: PhoBERT-based similarity

**c) Factual Accuracy**
- **QA-based**: Use QA model to verify claims
- **NLI-based**: Entailment check
- **Human judgment**: Gold standard

**d) Attribution Quality**
- **Citation precision**: % citations correct
- **Citation recall**: % gold sources cited
- **Attribution F1**: Harmonic mean

**End-to-End Metrics**:
```python
def evaluate_system(test_set, system):
    results = {
        'retrieval': {'recall@10': [], 'ndcg@10': []},
        'generation': {'bertscore': [], 'bleu': []},
        'attribution': {'cite_precision': [], 'cite_recall': []},
        'routing': {'accuracy': []},
        'latency': []
    }
    
    for sample in test_set:
        start = time.time()
        
        # Get system output
        output = system.query(sample['query'])
        
        # Evaluate routing
        route_correct = set(output['routes']) == set(sample['expected_route'])
        results['routing']['accuracy'].append(route_correct)
        
        # Evaluate retrieval
        retrieved_ids = [d['id'] for d in output['documents']]
        gold_ids = [s['doc_id'] for s in sample['gold_sources']]
        recall = len(set(retrieved_ids) & set(gold_ids)) / len(gold_ids)
        results['retrieval']['recall@10'].append(recall)
        
        # Evaluate generation
        bertscore = compute_bertscore(output['answer'], sample['gold_answer'])
        results['generation']['bertscore'].append(bertscore)
        
        # Evaluate attribution
        cite_precision, cite_recall = evaluate_citations(
            output['answer'], output['sources'], sample['gold_sources']
        )
        results['attribution']['cite_precision'].append(cite_precision)
        results['attribution']['cite_recall'].append(cite_recall)
        
        # Latency
        results['latency'].append(time.time() - start)
    
    # Aggregate
    return {k: {metric: np.mean(values) for metric, values in v.items()} 
            for k, v in results.items()}
```

#### Ablation Studies

**Components to Ablate**:
1. **Semantic Router**: Compare với uniform retrieval across all indices
2. **Query Decomposition**: Single query vs. decomposed
3. **Reranker**: With vs. without reranking
4. **Grounded Generation**: With vs. without citation enforcement
5. **Hybrid Search**: Dense-only vs. dense+sparse

**Experimental Design**:
```
Baseline: Single-index RAG (no router, no decomposition)
+ Semantic Router
+ Query Decomposition
+ Reranker
+ Grounded Generation
= Full System
```

**Statistical Testing**:
- **Paired t-test**: Compare means
- **Wilcoxon signed-rank test**: Non-parametric alternative
- **Bonferroni correction**: Multiple comparisons
- Significance level: α = 0.05

####User Study Design

**Tasks**:
1. **Information seeking**: "Find regulation về corporate governance"
2. **Comparison**: "Compare P/E của VNM vs. FPT"
3. **Multi-hop reasoning**: "Công ty nào compliant với luật mới và có P/E thấp?"

**Metrics**:
- **Task success rate**: % tasks completed correctly
- **Time on task**: Seconds to completion
- **User satisfaction**: 7-point Likert scale
- **System usability**: SUS (System Usability Scale)
- **Preference**: A/B comparison với baseline

**Participants**: N = 20-30 (domain experts + general users)

### 📊 Expected Results

**Hypothesis**:
- **H1**: Multi-index với routing > single-index (higher precision, lower latency)
- **H2**: Query decomposition > single query (higher recall on complex queries)
- **H3**: Grounded generation > standard generation (lower hallucination rate)

**Target Performance**:
- Retrieval Recall@10: >0.85
- Generation BERTScore: >0.75
- Routing Accuracy: >0.95
- Attribution F1: >0.80
- End-to-end latency: <2s (p95)

### ⏱ Thời Gian Ước Tính

- Dataset creation & annotation: 1.5 tuần
- Baseline implementation: 1 tuần
- Ablation experiments: 1 tuần
- User study: 1 tuần
- Analysis & reporting: 1 tuần
- **Tổng**: ~5-6 tuần

---

## BƯỚC 8: Research Paper Writing & Documentation

### 🎯 Mục Tiêu Của Bước Này

- Viết báo cáo nghiên cứu khoa học theo chuẩn quốc tế
- Chuẩn bị submission cho conference/journal
- Tạo comprehensive code documentation
- Publish code và datasets (nếu được phép)

### ✅ Điều Kiện Tiên Quyết (Prerequisites)

- ✔ Hoàn thành Bước 7: Có đầy đủ evaluation results
- ✔ Chọn target venue (conference/journal)
- ✔ Understand submission guidelines (page limit, format)
- ✔ Co-authors agreement (nếu có)

### 🎁 Kết Quả Mong Đợi (Expected Outputs)

- ✅ Research paper (8-10 pages):
  - Abstract
  - Introduction
  - Related Work
  - Methodology
  - Experiments
  - Results & Discussion
  - Conclusion
  - References (30-50 papers)
- ✅ Supplementary materials:
  - Appendix với additional results
  - Code repository (GitHub)
  - Dataset documentation
  - Reproducibility checklist
- ✅ Presentation materials:
  - Conference slides (nếu accepted)
  - Poster (nếu required)
- ✅ Documentation:
  - README với setup instructions
  - API documentation
  - Tutorial notebook

### 📐 Paper Structure & Content

#### Abstract (200-250 words)

**Template**:
```
[Context] Retrieval-Augmented Generation (RAG) has shown promise for domain-specific QA, 
but existing approaches struggle with [problem].

[Gap] Specifically, [specific limitation], leading to [consequences].

[Solution] We propose [system name], a semantic-router-based multi-index RAG system 
for Vietnamese financial and legal data. Our approach combines [key innovation 1], 
[key innovation 2], and [key innovation 3] to address [problem].

[Method] We construct four specialized indices (Legal, News, Financial, Glossary) and employ 
a semantic router to direct queries. Query decomposition handles complex queries, 
while grounded generation with citation enforcement reduces hallucinations.

[Results] Experiments on [dataset size] show our system achieves [metric1] of [value1], 
outperforming baselines by [improvement]. Ablation studies demonstrate that [key component] 
contributes [X]% to overall performance.

[Impact] Our work demonstrates the effectiveness of [approach] for [domain], with 
implications for [broader impact].
```

#### Introduction (1.5-2 pages)

**Structure**:
1. **Motivation** (2-3 paragraphs):
   - Financial sector needs reliable information access
   - Challenges: Multi-domain data, Vietnamese language, citation requirements
   - Existing RAG limitations

2. **Research Gap** (1 paragraph):
   - Single-index RAG → inefficient, lower precision
   - Lack of query complexity handling
   - Hallucination issues in financial domain

3. **Contributions** (bullet points):
   - Novel multi-index architecture với semantic routing
   - Query decomposition strategy cho complex reasoning
   - Grounded generation framework với citation
   - Comprehensive evaluation trên Vietnamese financial/legal data

4. **Paper Organization** (1 paragraph)

#### Related Work (2 pages)

**Sections**:

**2.1 Retrieval-Augmented Generation**
- **Classic RAG**: DPR (Karpukhin et al., 2020), REALM (Guu et al., 2020)
- **Recent advances**: RETRO (Borgeaud et al., 2022), Atlas (Izacard et al., 2022)
- **Domain-specific RAG**: Medical (Jin et al., 2023), Legal (Chalkidis et al., 2022)

**2.2 Query Routing & Decomposition**
- **Intent classification**: Dialogue systems (Zhang et al., 2020)
- **Semantic routing**: Aurelio et al. (2024)
- **Query decomposition**: Least-to-Most (Zhou et al., 2022), IRCoT (Trivedi et al., 2022)

**2.3 Hallucination Mitigation**
- **Attribution**: Attributed QA (Bohnet et al., 2022)
- **Grounding**: RARR (Gao et al., 2023), Self-RAG (Asai et al., 2023)
- **Verification**: NLI-based (Honovich et al., 2022)

**2.4 Vietnamese NLP**
- **Pre-trained models**: PhoBERT (Nguyen et al., 2020)
- **Applications**: Named Entity Recognition, Text Classification
- **Gap**: Limited work on RAG for Vietnamese financial data

#### Methodology (3-4 pages)

**3.1 System Overview**
- Architecture diagram (Mermaid/TikZ)
- Pipeline description

**3.2 Data Collection & Preprocessing**
```
Table 1: Dataset Statistics
| Index | Documents | Avg Length | Sources |
|-------|-----------|------------|---------|
| Legal | 5,000 | 800 tokens | Government portals |
| News  | 12,000 | 500 tokens | Financial news sites |
| Financial | 1,700 | 600 tokens | vnstock API |
```

**3.3 Multi-Index Construction**
- Embedding model selection
- Index architecture (HNSW parameters)
- Hybrid search strategy

**3.4 Semantic Router**
- Algorithm description
- Training procedure
- Multi-label classification approach

**3.5 Query Decomposition**
- Algorithm 1: Decomposition Procedure (pseudocode)
- Parallel retrieval strategy

**3.6 Reranking & Grounded Generation**
- Cross-encoder architecture
- Citation enforcement mechanism
- Verification pipeline

#### Experiments (2-3 pages)

**4.1 Experimental Setup**
- Test set: 500 queries
- Baselines: Single-index RAG, No-router, etc.
- Metrics: Retrieval (Recall, NDCG), Generation (BERTScore), Attribution

**4.2 Main Results**
```
Table 2: Performance Comparison
| System | Recall@10 | NDCG | BERTScore | Citation F1 | Latency (s) |
|--------|-----------|------|-----------|-------------|-------------|
| Single-index | 0.68 | 0.72 | 0.65 | 0.55 | 2.5 |
| Ours (no routing) | 0.72 | 0.75 | 0.68 | 0.62 | 3.2 |
| Ours (full) | **0.87** | **0.84** | **0.78** | **0.82** | **1.8** |
```

**4.3 Ablation Study**
```
Table 3: Ablation Results
| Component Removed | Recall@10 Δ | BERTScore Δ |
|-------------------|-------------|-------------|
| - Semantic Router | -0.15 | -0.05 |
| - Query Decomposition | -0.08 | -0.07 |
| - Reranker | -0.06 | -0.03 |
| - Grounded Gen | -0.02 | -0.08 |
```

**4.4 Qualitative Analysis**
- Example outputs
- Error analysis
- Failure cases

#### Results & Discussion (1-2 pages)

**5.1 Key Findings**
- Multi-index routing significantly improves efficiency & precision
- Query decomposition crucial for complex queries
- Grounded generation reduces hallucinations by X%

**5.2 Performance by Query Type**
```
Figure 1: Performance Breakdown
[Bar chart showing metrics across Easy/Medium/Hard queries]
```

**5.3 Limitations**
- Dependency on LLM APIs (cost, latency)
- Limited to Vietnamese language
- Dataset size constraints
- Manual annotation effort

**5.4 Future Work**
- Cross-lingual extension
- Fine-tuned Vietnamese LLM
- Real-time data updates
- User personalization

#### Conclusion (0.5 pages)

**Template**:
```
We presented [system name], a multi-index RAG system with semantic routing for Vietnamese 
financial and legal data. Our approach combines [innovations] to achieve [results]. 
Experiments demonstrate [key findings]. This work contributes [impact] and opens avenues 
for [future directions].
```

### 📊 Paper Writing Best Practices

**Writing Tips**:
1. **Clarity**: Use simple, direct language
2. **Precision**: Specific claims với quantitative support
3. **Structure**: Logical flow, clear transitions
4. **Figures**: High-quality, informative visualizations
5. **References**: Cite liberally, accurately

**Common Mistakes to Avoid**:
- Overclaiming results
- Missing baselines
- Weak statistical testing
- Poor figure quality
- Incomplete related work

**Submission Checklist**:
- [ ] Abstract fits limit (typically 200-300 words)
- [ ] Page limit met (e.g., 8 pages + references)
- [ ] Figures legible (vector graphics preferred)
- [ ] Tables formatted consistently
- [ ] References complete and formatted correctly
- [ ] Code/data availability statement
- [ ] Ethics statement (if required)
- [ ] Reproducibility checklist completed

### 📚 Target Venues

**Conferences** (NLP/IR/AI):
- **Tier 1**: ACL, EMNLP, NAACL, SIGIR, KDD, AAAI
- **Tier 2**: EACL, COLING, CIKM, WSDM
- **Domain-specific**: FinNLP, LegalAI workshops

**Journals**:
- Information Processing & Management
- ACM Transactions on Information Systems (TOIS)
- Journal of Artificial Intelligence Research (JAIR)

**Vietnamese Venues**:
- VLSP (Vietnamese Language and Speech Processing)
- RIVF (Research, Innovation and Vision for the Future)
- FAIR (Fundamental and Applied IT Research)

### 📝 Code & Data Release

**GitHub Repository Structure**:
```
multi-index-rag/
├── README.md
├── requirements.txt
├── setup.py
├── data/
│   ├── legal_processed.jsonl
│   ├── news_processed.jsonl
│   └── financial_processed.jsonl (or download script)
├── src/
│   ├── preprocessing/
│   ├── embedding/
│   ├── routing/
│   ├── decomposition/
│   ├── reranking/
│   ├── generation/
│   └── evaluation/
├── configs/
│   └── default.yaml
├── scripts/
│   ├── train_router.py
│   ├── build_indices.py
│   └── evaluate.py
├── notebooks/
│   └── demo.ipynb
├── tests/
└── docs/
    ├── API.md
    └── TUTORIAL.md
```

**README Template**:
```markdown
# Multi-Index RAG for Vietnamese Financial Data

[![Paper](badge-link)](paper-url)
[![Code](badge)](github-url)
[![Demo](badge)](demo-url)

Official implementation of "[Paper Title]" (Conference Year).

## Quick Start
\`\`\`bash
pip install -r requirements.txt
python scripts/download_data.py
python scripts/build_indices.py
python src/query.py "P/E ratio của VNM?"
\`\`\`

## Citation
\`\`\`bibtex
@inproceedings{yourname2025multiindex,
  title={A Semantic-Router Multi-Index RAG System for Vietnamese Financial Data},
  author={Your Name and Co-authors},
  booktitle={Conference Name},
  year={2025}
}
\`\`\`
```

**License**: Consider MIT or Apache 2.0 for code, CC-BY for data (nếu legally permissible)

### ⏱ Thời Gian Ước Tính

- Initial draft (all sections): 2 tuần
- Internal review & revision: 1 tuần
- Figures & tables polishing: 3-4 ngày
- Code documentation: 1 tuần
- Final proofreading: 2-3 ngày
- **Tổng**: ~5 tuần

**Post-submission** (nếu conference):
- Reviews: 2-3 tháng
- Rebuttal (nếu có): 1 tuần
- Camera-ready (nếu accepted): 2 tuần
- Presentation prep: 1-2 tuần

---

## 📈 Tổng Kết & Timeline

### Tổng Thời Gian Dự Kiến

| Bước | Thời gian | Cumulative |
|------|-----------|------------|
| Bước 1: Data Preprocessing | 2-3 tuần | 2-3 tuần |
| Bước 2: Embedding & Indexing | 2 tuần | 4-5 tuần |
| Bước 3: Semantic Router | 2.5 tuần | 6.5-7.5 tuần |
| Bước 4: Query Decomposition | 2.5 tuần | 9-10 tuần |
| Bước 5: Reranking & Generation | 3 tuần | 12-13 tuần |
| Bước 6: MVP Development | 4 tuần | 16-17 tuần |
| Bước 7: Evaluation | 5-6 tuần | 21-23 tuần |
| Bước 8: Paper Writing | 5 tuần | 26-28 tuần |

**Total: ~6-7 tháng** (full-time work)

### Milestones

**Month 1-2**: Data ready, indices built
**Month 3**: Core RAG pipeline working
**Month 4-5**: MVP deployed, evaluation done
**Month 6-7**: Paper submitted

### Risk Mitigation

**Risks**:
1. **Data quality issues** → Mitigation: Early validation, iterative cleaning
2. **Model performance below target** → Mitigation: Hyperparameter tuning, model ensemble
3. **Latency too high** → Mitigation: Caching, async processing, model optimization
4. **LLM API costs** → Mitigation: Use local models, batch processing
5. **Paper rejection** → Mitigation: Target multiple venues, incorporate feedback

### Success Criteria

**Technical**:
- [ ] Retrieval Recall@10 > 0.85
- [ ] Generation quality (human eval) > 4/5
- [ ] End-to-end latency < 2s (p95)
- [ ] System uptime > 99%

**Research**:
- [ ] Paper submitted to Tier 1/2 venue
- [ ] Code open-sourced
- [ ] At least 3 novel contributions acknowledged

**Product**:
- [ ] MVP deployed and accessible
- [ ] 100+ real user queries tested
- [ ] Positive user feedback (>4/5 satisfaction)

---

## BƯỚC 7: System Optimization Phase 1

### 🎯 Mục Tiêu Của Bước Này

- Cải thiện chất lượng câu trả lời từ "academic/legal" sang "consulting/actionable"
- Giảm latency từ ~56s xuống <20s
- Tối ưu hóa routing và retrieval dựa trên production feedback

### ✅ Điều Kiện Tiên Quyết

- ✔ Hoàn thành Bước 6: MVP đang hoạt động
- ✔ Production testing results với complex queries
- ✔ Identified bottlenecks và quality issues

### 🎁 Kết Quả Mong Đợi

- ✅ **Persona Rewriter Module**: Chuyển đổi câu trả lời theo user persona
- ✅ **Smart News Routing**: Chỉ route tới news khi có temporal keywords
- ✅ **Latency Optimization**:
  - True parallel retrieval
  - Query embedding cache
  - Fast/Deep mode split
- ✅ **Model Pre-warming**: Eliminate cold start latency

### 📋 Chi Tiết Implementation

Xem file: [Step7_Optimize_System_Phase1.md](./plan/Step7_Optimize_System_Phase1.md)

### 📊 Target Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Routes selected | 4 (all) | 2-3 (smart) |
| Latency (simple) | ~30s | <10s |
| Latency (complex) | ~56s | <25s |
| Answer style | Academic | Consulting |

### ⏱ Thời Gian Ước Tính

- Phase 1A (Persona Rewriter): 1 ngày
- Phase 1B (Smart Routing): 0.5 ngày
- Phase 1C (Latency): 2-3 ngày
- Phase 1D (Pre-warming): 0.5 ngày
- Integration & Testing: 1 ngày
- **Tổng**: ~5-6 ngày

---

## BƯỚC 9: Google Search Grounding Fallback Implementation

### 🎯 Mục Tiêu Của Bước Này

- Tích hợp **Google Search Grounding** vào pipeline RAG như cơ chế fallback khi dữ liệu từ Vector DB không đủ hoặc không liên quan.
- Sử dụng **langchain-google-genai** với tính năng `google_search` tool binding để Gemini tự động truy cập web khi cần.
- Đảm bảo câu trả lời từ web search được **grounded với citations** tương tự như dữ liệu nội bộ.
- Giữ **latency chấp nhận được** (<3s thêm cho fallback).

### ✅ Điều Kiện Tiên Quyết

- ✔ Hoàn thành Step 8: Canonical Answer Framework (CAF) hoạt động ổn định
- ✔ `GEMINI_API_KEY` đã cấu hình trong `.env`
- ✔ Package `langchain-google-genai>=2.0.0` đã cài đặt
- ✔ LangGraph pipeline có khả năng conditional branching

### 🎁 Kết Quả Mong Đợi

- ✅ **FallbackDecider Node**: Phân tích retrieval results và quyết định có cần web search không
- ✅ **GoogleSearchNode**: Thực hiện grounded search qua Gemini + Google Search tool
- ✅ **Merged Context Generator**: Kết hợp internal docs + web results vào unified context
- ✅ **Unified Citation Format**: `[1] Internal: Document Title` vs `[2] Web: URL`
- ✅ **Logging & Metrics**: Track fallback rate, web search latency, success rate

---

### 🛠 Tech Stack & Phân Tích

| Công nghệ | Mục đích | Lý do chọn |
|-----------|----------|------------|
| **langchain-google-genai** | Gemini + Google Search binding | Official integration, stable API |
| **ChatGoogleGenerativeAI** | LLM wrapper với tool support | Native support for `google_search` tool |
| **LangGraph** | Conditional fallback orchestration | Debug được, state management rõ ràng |
| **Pydantic** | Schema cho FallbackDecision | Type safety, validation |

---

### 📐 Kiến Trúc Chi Tiết

#### 1. Updated LangGraph Pipeline

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
               │            │            │
               ▼            │            ▼
        ┌─────────────┐     │     ┌─────────────┐
        │  decompose  │     │     │   retrieve  │
        └──────┬──────┘     │     └──────┬──────┘
               │            │            │
               ▼            │            │
        ┌─────────────┐     │            │
        │  retrieve   │     │            │
        └──────┬──────┘     │            │
               │            │            │
               └────────────┼────────────┘
                            │
                            ▼
                   ┌────────────────┐
                   │ fallback_check │  ◀── NEW NODE
                   └────────┬───────┘
                            │
               ┌────────────┼────────────┐
               │ LOW_CONFIDENCE         │ SUFFICIENT
               ▼                        │
        ┌─────────────────┐             │
        │ google_search   │  ◀── NEW   │
        │ _grounding      │             │
        └────────┬────────┘             │
                 │                      │
                 └──────────────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │  generate   │
                     └──────┬──────┘
                            │
                            ▼
                     ┌─────────────┐
                     │    END      │
                     └─────────────┘
```

#### 2. Fallback Decision Logic

```python
from pydantic import BaseModel
from typing import Literal

class FallbackDecision(BaseModel):
    should_fallback: bool
    reason: Literal[
        "NO_DOCS_RETRIEVED",
        "LOW_RELEVANCE_SCORE", 
        "TEMPORAL_QUERY",
        "SUFFICIENT_COVERAGE"
    ]
    max_similarity_score: float
    doc_count: int

def decide_fallback(state: RAGState) -> FallbackDecision:
    """Analyze retrieval results and decide if web search is needed."""
    
    contexts = state.get("contexts", [])
    query = state.get("query", "")
    
    # 1. No documents retrieved
    if not contexts:
        return FallbackDecision(
            should_fallback=True,
            reason="NO_DOCS_RETRIEVED",
            max_similarity_score=0.0,
            doc_count=0
        )
    
    # 2. Check similarity scores
    scores = [ctx.get("similarity", 0) for ctx in contexts]
    max_score = max(scores) if scores else 0.0
    
    RELEVANCE_THRESHOLD = 0.45  # Tunable parameter
    if max_score < RELEVANCE_THRESHOLD:
        return FallbackDecision(
            should_fallback=True,
            reason="LOW_RELEVANCE_SCORE",
            max_similarity_score=max_score,
            doc_count=len(contexts)
        )
    
    # 3. Temporal keywords detection
    TEMPORAL_KEYWORDS = [
        "hôm nay", "tuần này", "tháng này", "mới nhất", 
        "gần đây", "hiện tại", "2024", "2025",
        "today", "this week", "latest", "recent"
    ]
    query_lower = query.lower()
    if any(kw in query_lower for kw in TEMPORAL_KEYWORDS):
        # Only fallback if we don't have recent news
        has_recent_news = any(
            ctx.get("metadata", {}).get("source") == "news" 
            for ctx in contexts
        )
        if not has_recent_news:
            return FallbackDecision(
                should_fallback=True,
                reason="TEMPORAL_QUERY",
                max_similarity_score=max_score,
                doc_count=len(contexts)
            )
    
    # 4. Sufficient coverage
    return FallbackDecision(
        should_fallback=False,
        reason="SUFFICIENT_COVERAGE",
        max_similarity_score=max_score,
        doc_count=len(contexts)
    )
```

#### 3. Google Search Grounding Node

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

def google_search_grounding_node(state: RAGState) -> dict:
    """Execute grounded search using Gemini + Google Search tool."""
    
    query = state.get("query", "")
    sub_queries = state.get("sub_queries", [query])
    
    # Initialize Gemini with Google Search tool
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",  # Or gemini-1.5-pro
        temperature=0.0
    )
    
    # Bind the google_search tool
    llm_with_search = llm.bind_tools([{"google_search": {}}])
    
    # Construct search prompt
    search_prompt = f"""
    Bạn là trợ lý nghiên cứu tài chính. Hãy tìm kiếm thông tin mới nhất về:
    
    Query: {query}
    
    Yêu cầu:
    1. Sử dụng Google Search để tìm thông tin chính xác
    2. Ưu tiên nguồn uy tín: báo tài chính, trang chính phủ, công ty chứng khoán
    3. Trích dẫn URL nguồn cho mỗi thông tin quan trọng
    4. Tập trung vào dữ liệu số liệu cụ thể nếu có
    
    Trả về kết quả dưới dạng JSON:
    {{
        "findings": [
            {{
                "fact": "Thông tin tìm được",
                "source_url": "https://...",
                "source_title": "Tên nguồn"
            }}
        ],
        "summary": "Tóm tắt ngắn gọn"
    }}
    """
    
    try:
        response = llm_with_search.invoke([HumanMessage(content=search_prompt)])
        
        # Parse grounding metadata if available
        web_contexts = []
        if hasattr(response, 'additional_kwargs'):
            grounding_metadata = response.additional_kwargs.get('grounding_metadata', {})
            search_results = grounding_metadata.get('search_entry_point', {})
            
            # Extract web chunks as contexts
            for chunk in grounding_metadata.get('grounding_chunks', []):
                if 'web' in chunk:
                    web_contexts.append({
                        "content": chunk['web'].get('title', ''),
                        "url": chunk['web'].get('uri', ''),
                        "source": "web_search",
                        "similarity": 0.9  # High confidence for direct search
                    })
        
        # Fallback: parse from response content
        if not web_contexts:
            web_contexts.append({
                "content": response.content,
                "source": "web_search_synthesized",
                "similarity": 0.85
            })
        
        return {
            "web_contexts": web_contexts,
            "fallback_used": True,
            "fallback_response": response.content
        }
        
    except Exception as e:
        logger.error(f"Google Search Grounding failed: {e}")
        return {
            "web_contexts": [],
            "fallback_used": True,
            "fallback_error": str(e)
        }
```

#### 4. Updated RAGState Schema

```python
from typing import TypedDict, List, Optional, Annotated
import operator

class RAGState(TypedDict):
    # Input
    query: str
    
    # Routing
    routes: List[str]
    route_scores: dict
    
    # Decomposition
    sub_queries: List[str]
    is_composite: bool
    
    # Retrieval (Internal)
    contexts: Annotated[List[dict], operator.add]
    
    # Fallback (NEW)
    fallback_decision: Optional[dict]  # FallbackDecision as dict
    web_contexts: List[dict]           # Results from Google Search
    fallback_used: bool
    fallback_error: Optional[str]
    
    # Generation
    answer: str
    citations: List[dict]
    
    # Metadata
    processing_time_ms: float
    error: Optional[str]
```

#### 5. Merged Context for Generation

```python
def merge_contexts_for_generation(state: RAGState) -> List[dict]:
    """Combine internal and web contexts with unified citation format."""
    
    merged = []
    citation_index = 1
    
    # Internal contexts first (higher trust)
    for ctx in state.get("contexts", []):
        merged.append({
            "citation_id": citation_index,
            "content": ctx.get("content", ""),
            "source_type": "internal",
            "source_label": f"[{citation_index}] {ctx.get('metadata', {}).get('title', 'Internal Document')}",
            "similarity": ctx.get("similarity", 0)
        })
        citation_index += 1
    
    # Web contexts (clearly marked)
    for web_ctx in state.get("web_contexts", []):
        url = web_ctx.get("url", "")
        merged.append({
            "citation_id": citation_index,
            "content": web_ctx.get("content", ""),
            "source_type": "web",
            "source_label": f"[{citation_index}] Web: {url}" if url else f"[{citation_index}] Web Search",
            "similarity": web_ctx.get("similarity", 0)
        })
        citation_index += 1
    
    return merged
```

---

### 📊 Metrics & Monitoring

| Metric | Mô tả | Target |
|--------|-------|--------|
| `fallback_rate` | % queries triggering web search | < 20% |
| `fallback_latency_p95` | Latency added by web search | < 3000ms |
| `fallback_success_rate` | % fallbacks returning useful results | > 80% |
| `web_citation_accuracy` | % web citations with valid URLs | 100% |

```python
# Logging example
import structlog
logger = structlog.get_logger()

def log_fallback_decision(decision: FallbackDecision, query: str):
    logger.info(
        "fallback_decision",
        query=query[:100],
        should_fallback=decision.should_fallback,
        reason=decision.reason,
        max_score=decision.max_similarity_score,
        doc_count=decision.doc_count
    )
```

---

### 🔧 Configuration

```python
# src/config/fallback_config.py

class FallbackConfig:
    # Thresholds
    RELEVANCE_THRESHOLD: float = 0.45
    MIN_DOCS_REQUIRED: int = 1
    
    # Temporal detection
    TEMPORAL_KEYWORDS: list = [
        "hôm nay", "tuần này", "tháng này", "mới nhất",
        "gần đây", "hiện tại", "2024", "2025"
    ]
    
    # Google Search settings
    SEARCH_MODEL: str = "gemini-2.0-flash-exp"
    SEARCH_TEMPERATURE: float = 0.0
    MAX_SEARCH_RESULTS: int = 5
    
    # Safety
    ENABLE_FALLBACK: bool = True  # Feature flag
    FALLBACK_TIMEOUT_SECONDS: int = 10
```

---

### 📝 File Changes Required

| File | Thay đổi |
|------|----------|
| `src/config/fallback_config.py` | **[NEW]** Configuration cho fallback |
| `src/core/fallback/decider.py` | **[NEW]** FallbackDecision logic |
| `src/core/fallback/google_search.py` | **[NEW]** Google Search Grounding node |
| `src/pipeline/state.py` | **[MODIFY]** Add fallback fields to RAGState |
| `src/pipeline/nodes.py` | **[MODIFY]** Add fallback_check_node, google_search_node |
| `src/pipeline/graph.py` | **[MODIFY]** Add conditional edge for fallback |
| `requirements.txt` | **[MODIFY]** Ensure `langchain-google-genai>=2.0.0` |

---

### ✅ Verification Plan

#### 1. Unit Tests
```bash
# Test fallback decision logic
pytest tests/unit/test_fallback_decider.py -v

# Test cases:
# - Empty contexts → should_fallback=True
# - Low similarity scores → should_fallback=True  
# - Temporal keywords without news → should_fallback=True
# - Sufficient coverage → should_fallback=False
```

#### 2. Integration Test
```bash
# Test full pipeline with fallback
python -m pytest tests/integration/test_fallback_pipeline.py -v

# Test query that should trigger fallback:
# "VN-Index hôm nay biến động như thế nào?"
```

#### 3. Manual Verification
```python
# Run in Python REPL
from src.pipeline import run_rag_pipeline

# Query 1: Should use internal data (no fallback)
result1 = run_rag_pipeline("ROE là gì?")
assert result1.fallback_used == False

# Query 2: Should trigger fallback (temporal, no recent news)
result2 = run_rag_pipeline("Tin tức chứng khoán mới nhất hôm nay?")
assert result2.fallback_used == True
assert len(result2.web_contexts) > 0
```

---

### ⏱ Thời Gian Ước Tính

| Task | Thời gian |
|------|-----------|
| Setup `fallback_config.py` | 0.5 ngày |
| Implement `FallbackDecider` | 1 ngày |
| Implement `GoogleSearchNode` | 1.5 ngày |
| Update LangGraph pipeline | 1 ngày |
| Unit tests | 1 ngày |
| Integration testing & tuning | 1 ngày |
| **Tổng** | **~6 ngày** |

## 🔗 Tài Liệu Tham Khảo Chính


### Foundational Papers

1. **RAG**: Lewis et al. (2020). "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks". NeurIPS.

2. **Semantic Routing**: Aurelio AI (2024). "Semantic Router: A Framework for Autonomous Decision-Making".

3. **Query Decomposition**: Zhou et al. (2022). "Least-to-Most Prompting Enables Complex Reasoning in Large Language Models". ICLR.

4. **Multi-hop Reasoning**: Trivedi et al. (2022). "Interleaving Retrieval with Chain-of-Thought Reasoning for Knowledge-Intensive Multi-Step Questions". arXiv.

5. **Grounded Generation**: Bohnet et al. (2022). "Attributed Question Answering: Evaluation and Modeling for Attributed Large Language Models". ACL.

6. **Vietnamese NLP**: Nguyen et al. (2020). "PhoBERT: Pre-trained language models for Vietnamese". EMNLP Findings.

7. **Vector Search**: Malkov & Yashunin (2018). "Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs". IEEE TPAMI.

8. **Reranking**: Nogueira et al. (2019). "Multi-stage document ranking with BERT". arXiv.

9. **Evaluation**: Voorhees & Harman (2005). "TREC: Experiment and Evaluation in Information Retrieval". MIT Press.

10. **Hallucination**: Gao et al. (2023). "Enabling Large Language Models to Generate Text with Citations". arXiv.

---

## 📞 Hỗ Trợ & Resources

### Community & Tools

- **LangChain**: https://github.com/langchain-ai/langchain
- **Semantic Router**: https://github.com/aurelio-labs/semantic-router
- **PhoBERT**: https://github.com/VinAIResearch/PhoBERT
- **Supabase**: https://supabase.com/docs/guides/ai
- **Vietnamese NLP**: https://github.com/VinAIResearch

### Datasets

- **Vietnamese legal**: https://thuvienphapluat.vn
- **Financial news**: CafeF, VnExpress Kinh Doanh
- **Company data**: vnstock library

---

**Good luck với dự án! 🚀**

*Lưu ý: Plan này là hướng dẫn chi tiết nhưng flexible. Bạn có thể adjust based on actual progress và challenges encountered. Research thường iterative, jangan ngại backtrack nếu cần.*

