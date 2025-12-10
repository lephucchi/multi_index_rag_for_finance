# BƯỚC 4: Query Decomposition & Parallel Retrieval - Implementation Plan

> **Mục tiêu**: Phân tách truy vấn phức tạp thành các sub-queries và thực hiện truy xuất song song trên nhiều indices  
> **Thời gian dự kiến**: 1 tuần  
> **Dependencies**: Step 3 (Semantic Router) ✅

---

## PHẦN I: NỀN TẢNG LÝ THUYẾT

### 1.1. Tại Sao Cần Query Decomposition?

Trong RAG truyền thống, một truy vấn phức tạp được gửi trực tiếp đến retrieval system. Điều này gây ra các vấn đề:

| Vấn đề | Ví dụ | Hậu quả |
|--------|-------|---------|
| **Information Loss** | "ROE là gì và VNM có ROE bao nhiêu năm 2024" | Retrieval chỉ tập trung vào một khía cạnh |
| **Semantic Drift** | Embedding của câu dài bị "diluted" | Recall giảm |
| **Multi-domain Queries** | Truy vấn liên quan cả glossary và financial | Một index không đủ |

**Query Decomposition** giải quyết bằng cách:
1. Phân tách thành các atomic sub-queries
2. Route mỗi sub-query đến đúng index
3. Retrieve song song → Merge results

### 1.2. Least-to-Most Prompting

Dựa trên paper "Least-to-Most Prompting Enables Complex Reasoning" (Zhou et al., 2022):

```
Original: "ROE là gì và VNM có ROE bao nhiêu năm 2024"

Decomposition:
1. "ROE là gì" → glossary_index
2. "VNM có ROE bao nhiêu năm 2024" → financial_index

Order: Sub-query 1 trước (định nghĩa) → Sub-query 2 (dữ liệu cụ thể)
```

**Lợi ích:**
- Mỗi sub-query ngắn gọn, focused
- Routing chính xác hơn
- Có thể parallel retrieve

### 1.3. Parallel Retrieval Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                      Query Decomposition                        │
│                                                                  │
│  Input: "Quy định về ROE và so sánh ROE các ngân hàng"          │
│                            │                                     │
│                            ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Sub-queries:                                             │    │
│  │   1. "Quy định về ROE" → legal_index                     │    │
│  │   2. "ROE là gì" → glossary_index                        │    │
│  │   3. "So sánh ROE các ngân hàng" → financial_index       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                     │
│              ┌─────────────┼─────────────┐                      │
│              ▼             ▼             ▼                      │
│        ┌─────────┐   ┌─────────┐   ┌─────────┐                  │
│        │ legal   │   │glossary │   │financial│                  │
│        │ search  │   │ search  │   │ search  │                  │
│        └────┬────┘   └────┬────┘   └────┬────┘                  │
│             │             │             │                        │
│             └─────────────┼─────────────┘                        │
│                           ▼                                      │
│                    ┌─────────────┐                               │
│                    │ Result      │                               │
│                    │ Fusion      │                               │
│                    └─────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## PHẦN II: YÊU CẦU CHỨC NĂNG

### 2.1. Query Decomposition Module

| Requirement | Description | Priority |
|-------------|-------------|----------|
| **REQ-4.1** | Detect composite vs simple queries | P0 |
| **REQ-4.2** | Decompose into 2-5 atomic sub-queries | P0 |
| **REQ-4.3** | Preserve semantic relationships | P0 |
| **REQ-4.4** | Handle Vietnamese language properly | P0 |
| **REQ-4.5** | Fallback to original query if decomposition fails | P1 |
| **REQ-4.6** | Cache decomposition results | P2 |

### 2.2. Parallel Retrieval Module

| Requirement | Description | Priority |
|-------------|-------------|----------|
| **REQ-4.7** | Async parallel search across indices | P0 |
| **REQ-4.8** | Per-sub-query routing (từ Step 3) | P0 |
| **REQ-4.9** | Weighted result fusion | P0 |
| **REQ-4.10** | Deduplication of similar results | P1 |
| **REQ-4.11** | Configurable top-k per index | P1 |
| **REQ-4.12** | Timeout handling for slow queries | P1 |

### 2.3. Performance Requirements

| Metric | Target |
|--------|--------|
| Decomposition latency | < 500ms |
| Total retrieval latency (parallel) | < 1s |
| Result quality (vs baseline) | ≥ 10% improvement |
| Decomposition accuracy | > 90% |

---

## PHẦN III: KIẾN TRÚC VÀ THIẾT KẾ

### 3.1. Module Structure

```
src/
├── query_decomposition/
│   ├── __init__.py
│   ├── decomposer.py        # Main decomposition logic
│   ├── prompts.py           # LLM prompts for decomposition
│   ├── classifier.py        # Simple vs Complex classifier
│   └── config.py            # Decomposition config
├── retrieval/
│   ├── __init__.py
│   ├── parallel.py          # Async parallel retrieval
│   ├── fusion.py            # Result fusion strategies
│   └── supabase_client.py   # Supabase vector search client
└── pipeline/
    ├── __init__.py
    ├── state.py             # LangGraph state definition
    └── graph.py             # LangGraph pipeline
```

### 3.2. Data Flow

```python
# Step 1: Classify query complexity
is_complex = classifier.is_complex(query)
# "ROE là gì và VNM có ROE bao nhiêu" → True

# Step 2: Decompose if complex
if is_complex:
    sub_queries = decomposer.decompose(query)
    # → ["ROE là gì", "VNM có ROE bao nhiêu"]
else:
    sub_queries = [query]

# Step 3: Route each sub-query
routing_results = [router.route(sq) for sq in sub_queries]
# → [("glossary", 0.92), ("financial", 0.88)]

# Step 4: Parallel retrieve
contexts = await parallel_retriever.retrieve_all(
    sub_queries=sub_queries,
    routes=routing_results,
    k_per_index=5
)

# Step 5: Fuse results
fused_context = fusion.merge(contexts, strategy="weighted")
```

### 3.3. LangGraph State

```python
from typing import TypedDict, List, Optional, Annotated
import operator

class RAGState(TypedDict):
    # Input
    query: str
    
    # Decomposition
    is_complex: bool
    sub_queries: List[str]
    
    # Routing (per sub-query)
    routes: List[dict]  # [{sub_query, route, score}, ...]
    
    # Retrieval
    contexts: Annotated[List[dict], operator.add]
    
    # Metadata
    decomposition_time_ms: float
    retrieval_time_ms: float
    total_docs_retrieved: int
```

---

## PHẦN IV: IMPLEMENTATION PLAN

### Phase 1: Query Complexity Classifier (Day 1)

#### 4.1.1. File: `src/query_decomposition/classifier.py`

```python
"""
Query complexity classifier.
Determines if a query needs decomposition.
"""
import re
from typing import Tuple

# Complexity indicators
COMPOSITE_PATTERNS = [
    r"\bvà\b",           # "X và Y"
    r"\bvới\b",          # "X với Y"
    r"\bcũng như\b",     # "X cũng như Y"
    r"\bngoài ra\b",     # "ngoài ra"
    r"\bđồng thời\b",    # "đồng thời"
    r"\bso sánh\b.*\bvà\b",  # "so sánh X và Y"
    r"\blà gì.*\bvà\b",  # "X là gì và ..."
]

MULTI_INTENT_PATTERNS = [
    r"(là gì|là sao).*(bao nhiêu|như thế nào)",  # Definition + Data
    r"(quy định|luật).*(chỉ số|dữ liệu)",        # Legal + Financial
    r"(tin tức|mới nhất).*(là gì|định nghĩa)",   # News + Glossary
]


class QueryComplexityClassifier:
    """Classify query as simple or complex."""
    
    def __init__(self, min_words_for_complex: int = 8):
        self.min_words = min_words_for_complex
    
    def is_complex(self, query: str) -> Tuple[bool, str]:
        """
        Determine if query is complex.
        
        Returns:
            (is_complex, reason)
        """
        query_lower = query.lower()
        
        # Check composite patterns
        for pattern in COMPOSITE_PATTERNS:
            if re.search(pattern, query_lower):
                return True, f"composite_pattern: {pattern}"
        
        # Check multi-intent patterns
        for pattern in MULTI_INTENT_PATTERNS:
            if re.search(pattern, query_lower):
                return True, f"multi_intent: {pattern}"
        
        # Check word count
        word_count = len(query.split())
        if word_count >= self.min_words:
            return True, f"long_query: {word_count} words"
        
        return False, "simple_query"
```

### Phase 2: Query Decomposer with LLM (Day 2-3)

#### 4.2.1. File: `src/query_decomposition/prompts.py`

```python
"""
Prompts for query decomposition using Gemini.
"""

DECOMPOSITION_SYSTEM_PROMPT = """Bạn là một chuyên gia phân tách truy vấn tài chính-pháp lý Việt Nam.

NHIỆM VỤ: Phân tách truy vấn phức tạp thành các sub-queries đơn giản, atomic.

QUY TẮC:
1. Mỗi sub-query chỉ hỏi MỘT thông tin cụ thể
2. Giữ nguyên ngữ cảnh cần thiết trong mỗi sub-query
3. Sắp xếp theo thứ tự logic (định nghĩa trước, dữ liệu sau)
4. Giữ nguyên tên công ty, mã chứng khoán, số điều luật
5. Tối đa 5 sub-queries
6. Nếu query đã đơn giản, trả về nguyên bản

PHÂN LOẠI SUB-QUERY:
- [GLOSSARY]: Hỏi định nghĩa, thuật ngữ (ví dụ: "ROE là gì")
- [LEGAL]: Hỏi quy định, luật (ví dụ: "Điều 10 Luật Doanh nghiệp")
- [FINANCIAL]: Hỏi dữ liệu tài chính cụ thể (ví dụ: "ROE của VNM")
- [NEWS]: Hỏi tin tức, xu hướng (ví dụ: "thị trường hôm nay")
"""

DECOMPOSITION_USER_TEMPLATE = """Phân tách truy vấn sau:

QUERY: {query}

Trả về JSON với format:
{{
    "original_query": "...",
    "is_decomposed": true/false,
    "sub_queries": [
        {{"query": "...", "type": "GLOSSARY/LEGAL/FINANCIAL/NEWS", "order": 1}},
        ...
    ],
    "reasoning": "Giải thích ngắn gọn"
}}

CHỈ TRẢ VỀ JSON, KHÔNG CÓ TEXT KHÁC."""

# Few-shot examples
DECOMPOSITION_EXAMPLES = [
    {
        "input": "ROE là gì và VNM có ROE bao nhiêu năm 2024",
        "output": {
            "original_query": "ROE là gì và VNM có ROE bao nhiêu năm 2024",
            "is_decomposed": True,
            "sub_queries": [
                {"query": "ROE là gì", "type": "GLOSSARY", "order": 1},
                {"query": "VNM có ROE bao nhiêu năm 2024", "type": "FINANCIAL", "order": 2}
            ],
            "reasoning": "Tách định nghĩa (glossary) và dữ liệu cụ thể (financial)"
        }
    },
    {
        "input": "Quy định về công bố thông tin và FPT đã công bố gì mới nhất",
        "output": {
            "original_query": "Quy định về công bố thông tin và FPT đã công bố gì mới nhất",
            "is_decomposed": True,
            "sub_queries": [
                {"query": "Quy định về công bố thông tin", "type": "LEGAL", "order": 1},
                {"query": "FPT đã công bố gì mới nhất", "type": "NEWS", "order": 2}
            ],
            "reasoning": "Tách quy định pháp lý (legal) và tin tức (news)"
        }
    },
    {
        "input": "P/E của VNM",
        "output": {
            "original_query": "P/E của VNM",
            "is_decomposed": False,
            "sub_queries": [
                {"query": "P/E của VNM", "type": "FINANCIAL", "order": 1}
            ],
            "reasoning": "Query đơn giản, không cần phân tách"
        }
    }
]
```

#### 4.2.2. File: `src/query_decomposition/decomposer.py`

```python
"""
Query Decomposer using Gemini 2.0 Flash.
"""
import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass
import google.generativeai as genai
from .prompts import (
    DECOMPOSITION_SYSTEM_PROMPT,
    DECOMPOSITION_USER_TEMPLATE,
    DECOMPOSITION_EXAMPLES
)
from .classifier import QueryComplexityClassifier


@dataclass
class SubQuery:
    """A decomposed sub-query."""
    query: str
    query_type: str  # GLOSSARY, LEGAL, FINANCIAL, NEWS
    order: int


@dataclass
class DecompositionResult:
    """Result of query decomposition."""
    original_query: str
    is_decomposed: bool
    sub_queries: List[SubQuery]
    reasoning: str
    latency_ms: float


class QueryDecomposer:
    """Decompose complex queries into atomic sub-queries."""
    
    def __init__(
        self,
        model_name: str = "gemini-2.0-flash-exp",
        use_classifier: bool = True,
        max_sub_queries: int = 5
    ):
        self.model = genai.GenerativeModel(model_name)
        self.classifier = QueryComplexityClassifier() if use_classifier else None
        self.max_sub_queries = max_sub_queries
    
    def decompose(self, query: str) -> DecompositionResult:
        """
        Decompose a query into sub-queries.
        
        Args:
            query: User query string
            
        Returns:
            DecompositionResult with sub-queries
        """
        start = time.time()
        
        # Quick check with classifier
        if self.classifier:
            is_complex, reason = self.classifier.is_complex(query)
            if not is_complex:
                return DecompositionResult(
                    original_query=query,
                    is_decomposed=False,
                    sub_queries=[SubQuery(query=query, query_type="UNKNOWN", order=1)],
                    reasoning=f"Simple query: {reason}",
                    latency_ms=(time.time() - start) * 1000
                )
        
        # Use LLM for decomposition
        try:
            result = self._llm_decompose(query)
            result.latency_ms = (time.time() - start) * 1000
            return result
        except Exception as e:
            # Fallback to original query
            return DecompositionResult(
                original_query=query,
                is_decomposed=False,
                sub_queries=[SubQuery(query=query, query_type="UNKNOWN", order=1)],
                reasoning=f"Decomposition failed: {str(e)}",
                latency_ms=(time.time() - start) * 1000
            )
    
    def _llm_decompose(self, query: str) -> DecompositionResult:
        """Use LLM to decompose query."""
        # Build prompt with examples
        examples_text = "\n\n".join([
            f"VÍ DỤ {i+1}:\nInput: {ex['input']}\nOutput: {json.dumps(ex['output'], ensure_ascii=False)}"
            for i, ex in enumerate(DECOMPOSITION_EXAMPLES)
        ])
        
        full_prompt = f"""{DECOMPOSITION_SYSTEM_PROMPT}

{examples_text}

---

{DECOMPOSITION_USER_TEMPLATE.format(query=query)}"""
        
        response = self.model.generate_content(full_prompt)
        
        # Parse JSON response
        response_text = response.text.strip()
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        data = json.loads(response_text)
        
        sub_queries = [
            SubQuery(
                query=sq["query"],
                query_type=sq["type"],
                order=sq["order"]
            )
            for sq in data["sub_queries"][:self.max_sub_queries]
        ]
        
        return DecompositionResult(
            original_query=data["original_query"],
            is_decomposed=data["is_decomposed"],
            sub_queries=sub_queries,
            reasoning=data.get("reasoning", ""),
            latency_ms=0  # Will be set by caller
        )
```

### Phase 3: Parallel Retrieval (Day 4-5)

#### 4.3.1. File: `src/retrieval/parallel.py`

```python
"""
Parallel retrieval across multiple indices.
"""
import asyncio
import time
from typing import List, Dict, Optional
from dataclasses import dataclass
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
import os


@dataclass
class RetrievedDocument:
    """A retrieved document with metadata."""
    content: str
    source_index: str
    similarity: float
    metadata: dict
    sub_query: str  # Which sub-query retrieved this


@dataclass
class RetrievalResult:
    """Result of parallel retrieval."""
    documents: List[RetrievedDocument]
    sub_query_results: Dict[str, List[RetrievedDocument]]
    total_time_ms: float
    per_index_time_ms: Dict[str, float]


class ParallelRetriever:
    """Async parallel retrieval from Supabase indices."""
    
    INDEX_TABLE_MAP = {
        "glossary": "glossary_index",
        "legal": "legal_index",
        "financial": "financial_index",
        "news": "news_index"
    }
    
    def __init__(
        self,
        encoder_model: str = "BAAI/bge-m3",
        k_per_index: int = 5,
        timeout_seconds: float = 10.0
    ):
        self.supabase: Client = create_client(
            os.getenv("supabase_url"),
            os.getenv("supabase_service_role_key")
        )
        self.encoder = SentenceTransformer(encoder_model)
        self.k_per_index = k_per_index
        self.timeout = timeout_seconds
    
    async def retrieve_all(
        self,
        sub_queries: List[str],
        routes: List[str],
        k_per_index: Optional[int] = None
    ) -> RetrievalResult:
        """
        Retrieve documents for all sub-queries in parallel.
        
        Args:
            sub_queries: List of sub-query strings
            routes: List of route names (same length as sub_queries)
            k_per_index: Override default k
            
        Returns:
            RetrievalResult with all documents
        """
        start = time.time()
        k = k_per_index or self.k_per_index
        
        # Create tasks for parallel execution
        tasks = []
        for sq, route in zip(sub_queries, routes):
            tasks.append(self._retrieve_single(sq, route, k))
        
        # Execute in parallel with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            results = [[] for _ in tasks]
        
        # Aggregate results
        all_docs = []
        sub_query_results = {}
        per_index_time = {}
        
        for sq, route, result in zip(sub_queries, routes, results):
            if isinstance(result, Exception):
                sub_query_results[sq] = []
            else:
                docs, time_ms = result
                sub_query_results[sq] = docs
                all_docs.extend(docs)
                per_index_time[route] = time_ms
        
        # Deduplicate by content hash
        seen = set()
        unique_docs = []
        for doc in all_docs:
            content_hash = hash(doc.content[:200])
            if content_hash not in seen:
                seen.add(content_hash)
                unique_docs.append(doc)
        
        return RetrievalResult(
            documents=unique_docs,
            sub_query_results=sub_query_results,
            total_time_ms=(time.time() - start) * 1000,
            per_index_time_ms=per_index_time
        )
    
    async def _retrieve_single(
        self,
        query: str,
        route: str,
        k: int
    ) -> tuple[List[RetrievedDocument], float]:
        """Retrieve from a single index."""
        start = time.time()
        
        table = self.INDEX_TABLE_MAP.get(route)
        if not table:
            return [], 0
        
        # Encode query
        query_embedding = self.encoder.encode(query).tolist()
        
        # Search via Supabase RPC
        response = self.supabase.rpc(
            "match_documents",
            {
                "query_embedding": query_embedding,
                "match_count": k,
                "table_name": table
            }
        ).execute()
        
        docs = [
            RetrievedDocument(
                content=row["content"],
                source_index=route,
                similarity=row["similarity"],
                metadata=row.get("metadata", {}),
                sub_query=query
            )
            for row in response.data
        ]
        
        return docs, (time.time() - start) * 1000
```

#### 4.3.2. File: `src/retrieval/fusion.py`

```python
"""
Result fusion strategies for multi-index retrieval.
"""
from typing import List, Dict
from dataclasses import dataclass
from .parallel import RetrievedDocument


@dataclass
class FusedContext:
    """Fused context ready for generation."""
    documents: List[RetrievedDocument]
    formatted_context: str
    source_distribution: Dict[str, int]


class ResultFusion:
    """Strategies for fusing results from multiple indices."""
    
    STRATEGY_WEIGHTS = {
        "glossary": 1.2,   # Boost definitions (context first)
        "legal": 1.0,
        "financial": 1.0,
        "news": 0.9       # Slightly lower weight for news
    }
    
    def merge(
        self,
        documents: List[RetrievedDocument],
        strategy: str = "weighted",
        max_docs: int = 10
    ) -> FusedContext:
        """
        Merge and rank documents from multiple indices.
        
        Args:
            documents: List of retrieved documents
            strategy: "weighted", "round_robin", or "top_k"
            max_docs: Maximum documents to return
            
        Returns:
            FusedContext with merged documents
        """
        if strategy == "weighted":
            ranked = self._weighted_rank(documents)
        elif strategy == "round_robin":
            ranked = self._round_robin(documents)
        else:
            ranked = sorted(documents, key=lambda x: -x.similarity)
        
        final_docs = ranked[:max_docs]
        
        # Format context for LLM
        formatted = self._format_context(final_docs)
        
        # Count source distribution
        distribution = {}
        for doc in final_docs:
            distribution[doc.source_index] = distribution.get(doc.source_index, 0) + 1
        
        return FusedContext(
            documents=final_docs,
            formatted_context=formatted,
            source_distribution=distribution
        )
    
    def _weighted_rank(self, docs: List[RetrievedDocument]) -> List[RetrievedDocument]:
        """Rank documents with source-based weights."""
        for doc in docs:
            weight = self.STRATEGY_WEIGHTS.get(doc.source_index, 1.0)
            doc.similarity *= weight
        
        return sorted(docs, key=lambda x: -x.similarity)
    
    def _round_robin(self, docs: List[RetrievedDocument]) -> List[RetrievedDocument]:
        """Interleave documents from different sources."""
        by_source = {}
        for doc in docs:
            if doc.source_index not in by_source:
                by_source[doc.source_index] = []
            by_source[doc.source_index].append(doc)
        
        # Sort each source by similarity
        for source in by_source:
            by_source[source].sort(key=lambda x: -x.similarity)
        
        # Interleave
        result = []
        max_len = max(len(v) for v in by_source.values())
        for i in range(max_len):
            for source in ["glossary", "legal", "financial", "news"]:
                if source in by_source and i < len(by_source[source]):
                    result.append(by_source[source][i])
        
        return result
    
    def _format_context(self, docs: List[RetrievedDocument]) -> str:
        """Format documents for LLM context."""
        parts = []
        for i, doc in enumerate(docs, 1):
            parts.append(f"[{i}] ({doc.source_index.upper()}) {doc.content}")
        return "\n\n".join(parts)
```

### Phase 4: Integration & Testing (Day 6-7)

#### 4.4.1. File: `src/query_decomposition/__init__.py`

```python
from .decomposer import QueryDecomposer, DecompositionResult, SubQuery
from .classifier import QueryComplexityClassifier

__all__ = [
    "QueryDecomposer",
    "DecompositionResult",
    "SubQuery",
    "QueryComplexityClassifier"
]
```

#### 4.4.2. File: `src/retrieval/__init__.py`

```python
from .parallel import ParallelRetriever, RetrievalResult, RetrievedDocument
from .fusion import ResultFusion, FusedContext

__all__ = [
    "ParallelRetriever",
    "RetrievalResult",
    "RetrievedDocument",
    "ResultFusion",
    "FusedContext"
]
```

#### 4.4.3. File: `src/query_decomposition/test_decomposer.py`

```python
"""
Test suite for Query Decomposer.
"""
import os
from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

from decomposer import QueryDecomposer
from classifier import QueryComplexityClassifier


# Test cases
TEST_CASES = [
    # Complex queries (should decompose)
    {
        "query": "ROE là gì và VNM có ROE bao nhiêu năm 2024",
        "expected_decomposed": True,
        "expected_count": 2
    },
    {
        "query": "Quy định về IPO và điều kiện niêm yết sàn HOSE",
        "expected_decomposed": True,
        "expected_count": 2
    },
    {
        "query": "So sánh P/E của VNM và FPT, giải thích P/E là gì",
        "expected_decomposed": True,
        "expected_count": 3
    },
    # Simple queries (should NOT decompose)
    {
        "query": "P/E của VNM",
        "expected_decomposed": False,
        "expected_count": 1
    },
    {
        "query": "ROE là gì",
        "expected_decomposed": False,
        "expected_count": 1
    },
    {
        "query": "Điều 10 Luật Doanh nghiệp",
        "expected_decomposed": False,
        "expected_count": 1
    }
]


def test_classifier():
    """Test the complexity classifier."""
    print("\n=== Testing Complexity Classifier ===")
    classifier = QueryComplexityClassifier()
    
    for tc in TEST_CASES:
        is_complex, reason = classifier.is_complex(tc["query"])
        expected = tc["expected_decomposed"]
        status = "✓" if is_complex == expected else "✗"
        print(f'{status} "{tc["query"][:40]}..."')
        print(f'   Expected: {expected}, Got: {is_complex} ({reason})')


def test_decomposer():
    """Test the full decomposer with LLM."""
    print("\n=== Testing Query Decomposer ===")
    decomposer = QueryDecomposer()
    
    for tc in TEST_CASES:
        result = decomposer.decompose(tc["query"])
        
        status = "✓" if result.is_decomposed == tc["expected_decomposed"] else "✗"
        print(f'\n{status} "{tc["query"][:50]}..."')
        print(f'   Decomposed: {result.is_decomposed}')
        print(f'   Sub-queries: {len(result.sub_queries)}')
        for sq in result.sub_queries:
            print(f'      - [{sq.query_type}] {sq.query}')
        print(f'   Latency: {result.latency_ms:.1f}ms')
        print(f'   Reasoning: {result.reasoning}')


if __name__ == "__main__":
    test_classifier()
    test_decomposer()
```

---

## PHẦN V: VERIFICATION PLAN

### 5.1. Unit Tests

| Test | Description | Expected |
|------|-------------|----------|
| `test_classifier_simple` | Simple queries không bị decompose | Pass |
| `test_classifier_complex` | Complex queries được detect | Pass |
| `test_decomposer_llm` | LLM decomposition works | Pass |
| `test_decomposer_fallback` | Fallback khi LLM fails | Pass |
| `test_parallel_retrieval` | Async retrieve hoạt động | Pass |
| `test_fusion_weighted` | Weighted fusion đúng thứ tự | Pass |

### 5.2. Integration Tests

```bash
# Test decomposition
python -m src.query_decomposition.test_decomposer

# Test retrieval
python -m src.retrieval.test_parallel

# Full pipeline test
python -m src.pipeline.test_pipeline
```

### 5.3. Performance Benchmarks

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Decomposition latency | < 500ms | Timer in decomposer |
| Classification latency | < 5ms | Timer in classifier |
| Parallel retrieval | < 1s | Timer in parallel.py |
| End-to-end | < 2s | Full pipeline timer |

---

## PHẦN VI: ENVIRONMENT SETUP

### 6.1. Dependencies Mới

```bash
# Add to requirements.txt
google-generativeai>=0.3.0
asyncio>=3.4.3
```

### 6.2. Environment Variables

```bash
# Add to .env
GEMINI_API_KEY=your-gemini-api-key
```

### 6.3. Supabase RPC Function

Cần tạo function `match_documents` trong Supabase:

```sql
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1024),
    match_count int,
    table_name text
)
RETURNS TABLE (
    id bigint,
    content text,
    metadata jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF table_name = 'glossary_index' THEN
        RETURN QUERY
        SELECT 
            glossary_index.id,
            glossary_index.content,
            glossary_index.metadata,
            1 - (glossary_index.embedding <=> query_embedding) as similarity
        FROM glossary_index
        ORDER BY glossary_index.embedding <=> query_embedding
        LIMIT match_count;
    ELSIF table_name = 'legal_index' THEN
        RETURN QUERY
        SELECT 
            legal_index.id,
            legal_index.content,
            legal_index.metadata,
            1 - (legal_index.embedding <=> query_embedding) as similarity
        FROM legal_index
        ORDER BY legal_index.embedding <=> query_embedding
        LIMIT match_count;
    -- Add other indices...
    END IF;
END;
$$;
```

---

## PHẦN VII: CHECKLIST

### Day 1
- [ ] Tạo folder structure `src/query_decomposition/` và `src/retrieval/`
- [ ] Implement `classifier.py`
- [ ] Test classifier với test cases

### Day 2-3
- [ ] Implement `prompts.py` với few-shot examples
- [ ] Implement `decomposer.py` với Gemini integration
- [ ] Test decomposer với complex queries

### Day 4-5
- [ ] Implement `parallel.py` với async retrieval
- [ ] Implement `fusion.py` với multiple strategies
- [ ] Tạo Supabase RPC function

### Day 6-7
- [ ] Integration testing
- [ ] Performance benchmarks
- [ ] Documentation update
- [ ] Git commit & push

---

*Tạo: 10/12/2024*
