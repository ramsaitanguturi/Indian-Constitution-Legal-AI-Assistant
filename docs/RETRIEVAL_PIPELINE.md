# Retrieval Pipeline & Grounding Architecture

This document describes the multi-stage hybrid retrieval architecture, dense embedding configurations, compound legal tokenization, Reciprocal Rank Fusion (RRF), cross-encoder neural reranking, and parent context hydration used in the **Indian Constitution Legal AI Assistant**.

---

## 1. High-Level Architecture Overview

```
                      +-----------------------------+
                      |         User Query          |
                      +--------------+--------------+
                                     |
                 +-------------------+-------------------+
                 |                                       |
                 v                                       v
     +-----------------------+               +-----------------------+
     |   BM25 Sparse Lexical  |               |  BGE-M3 / MiniLM Dense |
     |  (Compound Legal Tok) |               |  Normalized Vector    |
     +-----------+-----------+               +-----------+-----------+
                 |                                       |
                 | (Top-15 Candidates)                   | (Top-15 Candidates)
                 v                                       v
     +---------------------------------------------------------------+
     |              Reciprocal Rank Fusion (RRF, k=60)               |
     |           + Optional Legal Entity Keyword Boosting            |
     +-------------------------------+-------------------------------+
                                     |
                                     v (Top-20 Fused Candidates)
     +---------------------------------------------------------------+
     |           Cross-Encoder Reranker (ms-marco-MiniLM)            |
     |              Full Query-Passage Interaction                   |
     +-------------------------------+-------------------------------+
                                     |
                                     v (Top-5 Reranked Passages)
     +---------------------------------------------------------------+
     |                   Parent Context Hydration                    |
     |             (Map child chunks to parent_store.json)           |
     +-------------------------------+-------------------------------+
                                     |
                                     v
     +---------------------------------------------------------------+
     |               Multi-Stage Abstention Gate                     |
     |      - Minimum Reranker Score Threshold (Sigmoid >= 0.35)     |
     |      - Grounded Citation & Metadata Verifier                  |
     +-------------------------------+-------------------------------+
                                     |
                                     v
     +---------------------------------------------------------------+
     |            Grounded Constitutional Answer Generation          |
     |         (Verifiable Citations, Zero Halucinated Law)          |
     +---------------------------------------------------------------+
```

---

## 2. Embedding Engine: BGE-M3 & MiniLM

The system supports dual dense embedding backends via dynamic collection routing without vector collision:

1. **`BAAI/bge-m3` (Default SOTA Model):**
   - **Dimensions:** 1024-dimensional normalized dense vectors.
   - **Capabilities:** Multilingual representation (English, Hindi, regional Indian languages), extended context window (up to 8192 tokens), multi-granularity representation.
   - **Normalization:** Full L2 normalization applied to all query and passage vectors to enable fast, accurate cosine distance computation in ChromaDB.
   - **ChromaDB Collection:** `indian_legal_rag_bgem3`.
   - **Device Fallback:** Automatically runs on GPU (`cuda`) if available, falling back safely to multi-threaded CPU.

2. **`sentence-transformers/all-MiniLM-L6-v2` (Fast Baseline):**
   - **Dimensions:** 384-dimensional dense vectors.
   - **Latency:** ~15–25ms CPU inference time.
   - **ChromaDB Collection:** `indian_legal_rag`.

Dynamic routing is managed via `config.py::get_chroma_collection_name(model_name)` and `retrieval/embeddings.py::get_embedding_function(model_name)`.

---

## 3. Sparse Retrieval: Enhanced BM25 with Compound Legal Tokens

Standard whitespace or word-level tokenization frequently fragments Indian legal references into disjoint tokens (e.g., `"Article 21"` $\to$ `["article", "21"]`, `"Section 124A"` $\to$ `["section", "124a"]`).

The enhanced tokenizer in `rag/ingestion.py` and `retrieval/bm25_retriever.py` captures compound legal tokens alongside standard alphanumeric unigrams:
- Constitutional Articles: `article_21`, `article_32`, `article_370`
- Statutory Sections: `section_124a`, `section_302`, `section_377`
- Neutral Supreme Court Citations: `1950insc14`, `1973insc258`, `2017insc777`
- Amendments: `42th_amendment`, `44th_amendment`, `103rd_amendment`

This preserves exact-match precision for specific statutory citations while retaining fuzzy keyword search for narrative queries.

---

## 4. Hybrid Reciprocal Rank Fusion (RRF)

Dense and sparse search candidates are merged using Reciprocal Rank Fusion:
$$RRF\_Score(d \in D) = \sum_{m \in \{dense, bm25\}} \frac{1}{k + r_m(d)}$$
where $k = 60$ (smoothing constant preventing high-rank dominance) and $r_m(d)$ is the 1-based rank of document $d$ in system $m$.

If specific legal entities (e.g. recognized Article numbers or case titles) are extracted from the query, matching documents receive a calibrated multiplicative boost ($1.2\times$).

---

## 5. Neural Cross-Encoder Reranking

The top fused candidates are evaluated by `cross-encoder/ms-marco-MiniLM-L-6-v2`. Unlike bi-encoders which compute independent query and document representations, the cross-encoder feeds the query-document pair $(q, d)$ simultaneously into self-attention layers:
- Captures fine-grained semantic nuances, statutory provisos, and jurisdictional conditions.
- Raw logits are converted to calibrated confidence scores using the standard sigmoid function $\sigma(z) = \frac{1}{1 + e^{-z}}$.
- Graceful Fallback: If the cross-encoder is disabled, fails, or encounters an out-of-memory condition, the pipeline falls back seamlessly to the top RRF-ranked candidates.

---

## 6. Grounding, Parent Store Hydration, and Citation Verification

1. **Parent Store Hydration:** Retrieved chunk IDs are linked to `data/processed/parent_store.json` to hydrate the full context (parent article text, bench strength, ratio decidendi) before LLM prompt assembly.
2. **Citation Validation (`rag/citation_validator.py`):**
   - Extracts all citations from synthesized legal text.
   - Verifies each cited document ID and title against retrieved context passages.
   - If an LLM attempts to cite an unretrieved judgment or nonexistent constitutional provision, the validation score drops and the claim is flagged with an explicit advisory.
3. **Multi-Stage Abstention (`rag/abstention.py`):**
   - Out-of-Scope Queries: Queries with zero constitutional or legal relevance are intercepted before retrieval.
   - Low Confidence Queries: If the maximum reranker confidence falls below 0.35, the system responds with a calibrated refusal stating that insufficient authoritative evidence is present in the corpus.

