# Indian Constitution Legal AI Assistant — Architecture & Technical Specification

## 1. System Overview

The **Indian Constitution Legal AI Assistant** is an empirical Natural Language Processing (NLP) and Information Retrieval (IR) framework engineered specifically for Indian Constitutional Law. It addresses unique domain challenges including nested statutory articles, multi-clause provisions, doctrine citations, and extensive judicial precedent interpretation.

The system replaces speculative multi-agent autonomy with a **deterministic, explainable 16-stage NLP Query Understanding and Reliable Retrieval-Augmented Generation (RAG) pipeline**.

---

## 2. Component Responsibilities

```
                                USER QUERY
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │  Language Detection   │  (nlp/language_detection.py)
                        └───────────┬───────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │  Query Preprocessing  │  (nlp/preprocessing.py)
                        └───────────┬───────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │   Domain Legal NER    │  (nlp/legal_ner.py)
                        └───────────┬───────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │ Canonical Entity Link │  (nlp/entity_linking.py)
                        └───────────┬───────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │ Intent Classification │  (nlp/intent_classifier.py)
                        └───────────┬───────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │ Controlled Expansion  │  (nlp/query_expansion.py)
                        └───────────┬───────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │ Specialized Router    │  (routing/query_router.py)
                        └───────────┬───────────┘
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        ▼                                                       ▼
 ┌──────────────┐                                        ┌──────────────┐
 │ Sparse Search│ BM25Okapi                              │ Dense Search │ ChromaDB
 │  (lexical)   │ k1=1.5, b=0.75                         │   (vector)   │ all-MiniLM-L6-v2
 └──────┬───────┘                                        └──────┬───────┘
        │                                                       │
        └───────────────────────────┬───────────────────────────┘
                                    ▼
                        ┌───────────────────────┐
                        │ Reciprocal Rank Fusion│  (retrieval/rrf.py, k=60)
                        └───────────┬───────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │  Entity Rank Boosting │  (retrieval/entity_boost.py, +0.15)
                        └───────────┬───────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │ Cross-Encoder Rerank  │  (retrieval/reranker.py)
                        │ ms-marco-MiniLM-L-6-v2│  Top 20 -> Top 5
                        └───────────┬───────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │ Context Recovery      │  (rag/parent_child.py)
                        │  (Parent-Child RAG)   │  Hydrate full articles & judgments
                        └───────────┬───────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │ Grounded Generator    │  (rag/generator.py)
                        │ Gemini / Offline Fall │  Strict evidence-bounded prompt
                        └───────────┬───────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │ Structural Citation   │  (rag/citation_validator.py)
                        │      Validation       │  Verify provenance against context
                        └───────────┬───────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │ Confidence Estimator  │  (rag/confidence.py)
                        │ 6 Weighted Signals    │  Uncalibrated heuristic disclosure
                        └───────────┬───────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │ Multi-Stage Abstention│  (rag/abstention.py)
                        │ Router/IR/Post-Gen    │  Safe refusal on low confidence
                        └───────────────────────┘
```

---

## 3. Mathematical & Algorithmic Formulations

### 3.1 BM25Okapi Lexical Retrieval
Scoring document $D$ for query $Q = \{q_1, \dots, q_n\}$:
$$\text{BM25}(D, Q) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$
Parameters: $k_1 = 1.5, b = 0.75$.

### 3.2 Dense Vector Retrieval
Dense representations are generated using `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions). Cosine similarity between query vector $\mathbf{q}$ and passage vector $\mathbf{d}$:
$$\text{CosineSim}(\mathbf{q}, \mathbf{d}) = \frac{\mathbf{q} \cdot \mathbf{d}}{\|\mathbf{q}\| \|\mathbf{d}\|}$$

### 3.3 Reciprocal Rank Fusion (RRF)
Combines candidate rankings from sparse lexical and dense semantic retrievers:
$$\text{RRF\_Score}(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$
where $M = \{\text{BM25}, \text{Dense}\}$, $k = 60$, and $r_m(d)$ is document $d$'s 1-based rank in retriever $m$.

### 3.4 Legal Entity Score Boost
Candidates matching canonical legal entities extracted and linked from the query receive an additive boost:
$$\text{Score}_{\text{boosted}}(d) = \text{Score}_{\text{RRF}}(d) + \omega_{\text{boost}} \cdot \mathbb{I}(d \in \text{Entities}(Q))$$
where $\omega_{\text{boost}} = 0.15$.

### 3.5 Cross-Encoder Neural Reranking
Top-20 candidate passages from entity-boosted RRF are reranked using `cross-encoder/ms-marco-MiniLM-L-6-v2`:
$$s_{\text{rerank}}(Q, d) = \sigma\left(\mathbf{W} \cdot \text{Transformer}([Q; d])\right)$$
The final top 5 candidates are passed to the Context Recovery stage.

---

## 4. RAG Reliability & Safety

### 4.1 Structural Citation Validation
Post-generation verification confirms:
1. Every cited Article or Case exists in the verified database.
2. Every cited authority was present in the retrieved context hydrated for that query.
3. Unsupported citations or ungrounded claims are flagged immediately.

> **Scientific Notice:** Structural citation validation checks provenance and context alignment. It does not establish semantic truth or substantive legal interpretation accuracy.

### 4.2 Explainable Confidence Estimation
Composite weighted heuristic over 6 observable signals:
- Retrieval strength ($\omega = 0.25$)
- Retrieved evidence volume ($\omega = 0.15$)
- Entity alignment ($\omega = 0.20$)
- BM25/Dense rank agreement ($\omega = 0.15$)
- Citation validity ($\omega = 0.15$)
- Query coverage ($\omega = 0.10$)

*Disclosure:* Confidence scores are explainable decision heuristics, not mathematically calibrated posterior probabilities.
