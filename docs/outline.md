# Student Information
Student Name: Lê Phúc Chí
Student ID: K224141652
Class: K22414

# Title of the Study
“A Semantic-Router Multi-Index Retrieval-Augmented Generation System for Vietnamese Financial Data and the Economic–Regulatory Framework”

Language: English

---

# Abstract
(To be completed: Summary of 1.5M vector system, hybrid routing, and CAF for FinTech/RegTech)

# Keywords
- Retrieval-Augmented Generation
- FinTech
- Semantic Routing
- Vietnamese Financial Data
- Regulatory Compliance

---

# 1. Introduction

## 1.1 Statement of the Problem
The Vietnamese financial landscape is characterized by a "Dual Challenge": the exponential growth of unstructured data (1.5M+ documents/year) and the rigidity of regulatory frameworks. Traditional search engines fail to bridge the semantic gap between "market-speak" and "legal-speak," while generic LLMs hallucinate crucial quantitative figures. This research proposes a Domain-Specific Multi-Index RAG system to solve these issues.

## 1.2 Related Work
*   **Retrieval-Augmented Generation**: Foundations (Lewis et al., 2020) and recent advancements in Modular RAG.
*   **Graph-based and Agentic RAG**: Comparison with LangGraph-based agentic workflows.
*   **Hallucinations in Financial QA**: The risks of ungrounded generation in high-stakes environments.
*   **Vietnamese IR**: Leveraging BGE-M3 for superior Vietnamese semantic retrieval.

## 1.3 Research Objectives
1.  **Multi-Index Architecture**: Build 4 specialized indices (Legal, Business, News, Glossary).
2.  **Semantic Routing**: Develop a Hybrid Router (Rule+Embedding) for >95% intent classification.
3.  **Agentic Pipeline**: Implement Query Decomposition and Parallel Retrieval.
4.  **Grounded Generation**: Deploy Canonical Answer Framework (CAF) for zero-hallucination outputs.

## 1.4 Research Questions
1.  **Routing**: Does semantic routing improve Precision@K?
2.  **Complexity**: Can decomposition solve multi-hop queries?
3.  **Latency**: Is <500ms latency achievable with 1.5M vectors?
4.  **Reliability**: Does CAF mitigate hallucinations effectively?

---

# 2. Methodology

This study adopts a system-oriented experimental methodology to investigate how retrieval architecture and query routing strategies affect factual reliability, retrieval precision, and real-time performance in financial and regulatory question answering systems. Retrieval-Augmented Generation (RAG) is selected as the foundational paradigm due to its demonstrated ability to reduce hallucinations by grounding generation in external knowledge sources (Guu et al., 2020; Gao et al., 2023).

## 2.1 Research Design

A comparative experimental design is employed, following evaluation principles commonly adopted in RAG system studies (Yu et al., 2024). The independent variables are the index organization strategy (Single vs Multi-Index) and the presence of semantic routing, while dependent variables include retrieval effectiveness, answer groundedness, citation accuracy, and system latency.

All experimental systems share identical embedding models, retrieval depth (k=10), and generation configurations (Gemini/OpenAI, temp=0.0) to ensure controlled comparison. Evaluation is conducted using a **curated benchmark of 100 domain-specific queries** (see `docs/benchmark_queries.json`) spanning Vietnamese financial analysis, regulatory compliance, and market intelligence. The query set is multilingual, including Vietnamese, English, and Chinese, to reflect realistic FinTech usage scenarios in Vietnam.
*   **Source**: Synthesized by domain experts based on real-world queries from financial analysts and legal compliance officers.
*   **Composition**: 40% Financial, 30% Legal, 20% News, 10% Glossary (Glossary queries often embedded within others).

## 2.2 Data Sources and Collection

The knowledge corpus is constructed from authoritative sources and organized into four specialized indices to reflect domain-specific information needs.

*   **Legal Index**: 5,012 articles from Vietnamese laws, decrees, and circulars collected from official government repositories, ensuring regulatory accuracy.
*   **Business Index**: Fundamental profiles and financial ratios (`P/E`, `ROE`) of 1,720 publicly listed companies on HOSE, HNX, and UPCoM exchanges, supporting fundamental analysis.
*   **News Index**: Over 1.47 million market news and macroeconomic documents enriched with temporal metadata (Year/Month/Day), enabling time-sensitive reasoning.
*   **Glossary Index**: 485 standardized financial and legal terminology entries with 1,240 aliases to support semantic normalization.

## 2.3 Data Preprocessing

Preprocessing strategies are designed to preserve semantic coherence while mitigating known failure modes in long-context retrieval (Liu et al., 2023).

*   **Contextual Chunking (Legal)**: Legal texts are segmented using a proprietary "Contextual Chunking" algorithm that preserves the hierarchy of Law -> Chapter -> Article. Even if an Article is split, the Law Title and Article Title are injected into every chunk to ensure standalone semantic completeness.
*   **Smart Chunking (General)**: For News and Financial narratives, we employ a "Smart Chunking" strategy that respects paragraph boundaries (`\n\n`) and sentence delimiters, with a sliding window overlap of 50-80 tokens to prevent context loss at boundaries.
*   **Table-to-Text**: Financial tables extracted from corporate reports are transformed into structured text representations (Markdown), embedding numerical values with their semantic headers (e.g., "Revenue 2023: 100B"). This directly addresses numerical hallucinations.
*   **Metadata Enrichment**: Every chunk is tagged with structured metadata (Source ID, Temporal Tags, Ticker Symbol) enabling hybrid search (Vector + Metadata Filter).

## 2.4 Embedding Models and Vector Indexing

All documents are embedded using the **BAAI/bge-m3** multilingual embedding model, selected for its strong cross-lingual retrieval performance and suitability for Vietnamese financial text (MTEB Score: 73.2).

Approximate nearest neighbor search is implemented using **Hierarchical Navigable Small World (HNSW)** graphs on Supabase pgvector.
*   **Configuration**: `m=16`, `ef_construction=64`.
*   **Performance**: Achieves O(log n) search complexity, delivering <100ms retrieval latency on the 1.5M vector dataset.

Knowledge is physically separated into four vector indices, reducing retrieval noise and enabling targeted query routing. This design aligns with prior findings that modular retrieval improves robustness in complex question-answering tasks.

## 2.5 Baseline Systems

Two baseline systems are implemented for controlled comparison:
1.  **Single-Index RAG**: Merges all knowledge sources into a monolithic vector store, representing a conventional "Naive RAG" architecture.
2.  **Multi-Index RAG ('Naive Parallel')**: Queries all indices in parallel without semantic routing, isolating the effect of routing decisions on latency and precision.

## 2.6 Evaluation Metrics

Evaluation follows established RAG assessment frameworks (Yu et al., 2024; Friel et al., 2025).
*   **Retrieval Effectiveness**: Recall@K and Mean Reciprocal Rank (MRR).
*   **Answer Groundedness**: Measured by the "Citation Accuracy" rate—percentage of sentences supported by valid footnotes.
*   **System Efficiency**: p95 and p99 latency metrics (ms).

---

# 3. System Architecture

This section presents the overall architecture of the proposed *Semantic-Router Multi-Index Retrieval-Augmented Generation (SR-MI-RAG)* system, designed for Vietnamese financial and legal question answering. The architecture emphasizes modularity, controllability, and grounded generation, while explicitly addressing known limitations of monolithic RAG systems such as retrieval noise, hallucination, and poor handling of multi-domain queries.

## 3.1 Overall System Overview

The system follows a layered architecture composed of four primary components: (i) a **user-facing interaction layer**, (ii) a **backend orchestration layer**, (iii) a **multi-index vector storage layer**, and (iv) **large language models** for reasoning and generation.

At a high level, user queries are processed by a backend service that orchestrates routing, decomposition, retrieval, and generation through a LangGraph-based execution graph. Retrieved evidence is strictly grounded in structured indices or controlled external sources before being synthesized into a cited response. This design ensures that all generated answers remain traceable to verifiable sources, a critical requirement in financial and legal domains.

## 3.2 Multi-Index Knowledge Organization

Unlike conventional RAG systems that store heterogeneous documents in a single vector index, the proposed architecture organizes knowledge into four semantically distinct indices:

*   **Legal Index**: Vietnamese laws, decrees, circulars, and regulatory documents, chunked by article and clause boundaries to preserve legal semantics.
*   **Financial Index**: Structured profiles and financial disclosures of publicly listed Vietnamese companies, including fundamental indicators such as ROE, P/E, revenue, and ownership information.
*   **News Index**: Large-scale financial and economic news articles enriched with temporal metadata to support time-aware reasoning.
*   **Glossary Index**: Standardized definitions of financial and legal terminology, including aliases and common abbreviations.

Each index is embedded independently using the same embedding model but stored in separate vector tables. This physical separation reduces retrieval interference across domains and enables selective querying based on inferred user intent. The design is motivated by prior findings that domain-homogeneous retrieval spaces improve precision and reduce hallucination risk in RAG systems.

## 3.3 Hybrid Semantic Routing Mechanism

To dynamically select relevant indices for each query, the system employs a *Hybrid Semantic Router* that combines rule-based pattern matching with embedding-based semantic classification.

The router operates in two stages. First, high-precision regular expressions and keyword rules capture deterministic query patterns (e.g., definitional questions, legal citations). Second, queries not matched by rules are embedded and compared against a small set of route prototypes using cosine similarity. The final routing decision supports multi-label outputs, allowing a single query to target multiple indices when necessary.

This hybrid design achieves two objectives: (i) deterministic correctness for frequent query types and (ii) robustness to linguistic variation in open-ended user questions. Routing accuracy is evaluated independently from retrieval performance to isolate its contribution to the overall system effectiveness.

## 3.4 LangGraph-Based RAG Orchestration

The core retrieval and generation workflow is implemented as a directed execution graph using LangGraph. Each node represents a well-defined operation, and edges encode conditional control flow, enabling adaptive query processing.

The pipeline begins with semantic routing, followed by optional query decomposition for composite questions. Decomposed sub-queries are retrieved in parallel from the selected indices, and their results are merged into a unified evidence set. This design supports low-latency execution while preserving the logical dependencies between sub-questions.

By explicitly modeling control flow as a graph rather than a linear chain, the system ensures transparency, debuggability, and extensibility. This approach aligns with recent research advocating graph-based orchestration for advanced RAG systems.

## 3.5 Grounded Generation and Canonical Answer Framework

To mitigate hallucination and enforce factual consistency, the system adopts a two-pass *Canonical Answer Framework (CAF)* for response generation.

In the first pass, retrieved documents are processed to extract atomic canonical facts, each explicitly linked to its source. In the second pass, the language model synthesizes a coherent natural language answer exclusively from these facts. Any claim not supported by extracted evidence is rejected.

All final outputs include inline citations that map directly to the underlying documents. This strict grounding protocol is particularly important for high-stakes domains, where unsupported or outdated information may lead to incorrect decision-making.

## 3.6 Controlled External Knowledge Expansion

While the multi-index knowledge base covers a broad range of financial and legal information, certain queries may require real-time or recently published data. To address this limitation, the system incorporates a controlled external knowledge expansion mechanism.

External retrieval is triggered only when internal retrieval confidence falls below a predefined threshold, as determined by coverage and relevance signals. In such cases, the system selectively invokes real-time web search via Google GenAI APIs or iterative DeepSearch strategies. Retrieved external evidence is normalized and subjected to the same grounding constraints as internal documents before being passed to the generation module.

Importantly, external search functions as a fallback strategy rather than a primary knowledge source, ensuring that the core evaluation of the system remains focused on the proposed multi-index RAG architecture.

## 3.7 Design Rationale and Scope Control

The architectural choices in SR-MI-RAG are guided by three principles: (i) domain separation to reduce retrieval noise, (ii) explicit control over reasoning and generation steps, and (iii) strict grounding to mitigate hallucination. By treating routing, retrieval, and generation as independently analyzable components, the system enables fine-grained evaluation and ablation studies.

Overall, the architecture balances practical deployability with methodological rigor, positioning the proposed system as both a production-ready solution and a research framework for studying advanced RAG behaviors in financial and legal contexts.

---

# 4. Experiments and Results

## 4.1 Experimental Setup
(Hardware: Supabase managed DB, Python 3.11 environment)

## 4.2 Retrieval Performance Evaluation
(HNSW latency results: ~87ms; Hybrid Router accuracy >95%)

## 4.3 End-to-End Question Answering Results
(Qualitative and Quantitative analysis of answers)

## 4.4 Hallucination Analysis
(Impact of CAF in reducing numerical hallucinations)

---

# 5. Discussion

## 5.1 Implications for FinTech Applications
(Due diligence, compliance checking, investment research)

## 5.2 Trade-offs and Limitations
(Latency costs of 2-pass generation vs accuracy benefits)

## 5.3 Comparison with Existing Systems
(vs GraphRAG, vs Standard RAG)

---

# 6. Conclusion and Future Work

## 6.1 Conclusion
(Summary of contributions)

## 6.2 Future Work
(Real-time data, regulatory monitoring)

---

# References
(Bibliography)

---

# Appendices (Optional)

## Appendix A: Semantic Routing Rules
(Regex patterns)

## Appendix B: Prompt Templates
(CAF Prompts)

## Appendix C: Example Queries and Outputs
(See `docs/benchmark_queries.json` for full query list)
