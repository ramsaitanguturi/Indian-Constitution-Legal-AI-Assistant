# Code Explanation: `retrieval/hybrid_retriever.py` 🔀

> **Source File**: [`retrieval/hybrid_retriever.py`](../../retrieval/hybrid_retriever.py)  
> **Lines of Code**: 367 lines  
> **Primary Responsibility**: Master multi-stage hybrid search orchestrator with complete ablation switches, Reciprocal Rank Fusion, Legal Entity Boosting, Cross-Encoder Reranking, and Cross-Corpus Diversity Filtering.

---

## 1. Basic Introduction

### What is this file?
[`retrieval/hybrid_retriever.py`](../../retrieval/hybrid_retriever.py) is the central orchestrator for all Information Retrieval. It coordinates the candidate generation from BM25 and ChromaDB, manages rank fusion, applies domain entity boosts, invokes the neural cross-encoder reranker, and enforces diversity constraints across legal corpora.

### Why does this file exist?
In academic research and capstone defenses, professors often ask:
- *"How do you know BM25 is helping?"*
- *"What is the exact impact of RRF vs. Linear score weighting?"*
- *"What does the cross-encoder reranker add over pure embeddings?"*

To answer these questions empirically, [`retrieval/hybrid_retriever.py`](../../retrieval/hybrid_retriever.py) was built with **component ablation toggles**: every single stage (BM25, Dense, RRF, Entity Boost, Reranker) can be independently enabled or disabled at runtime.

---

## 2. Component Ablation Flags in `HybridRetriever`

The class constructor defines 5 explicit boolean switches:
```python
self.use_bm25 = use_bm25                  # Enable/disable sparse keyword search
self.use_dense = use_dense                # Enable/disable dense vector embeddings
self.use_rrf = use_rrf                    # True for RRF; False for linear score fusion
self.use_entity_boost = use_entity_boost  # Enable/disable +0.15 legal entity boost
self.use_reranker = use_reranker          # Enable/disable Cross-Encoder reranker
```

This allows running all 6 benchmark experiments (`experiments/experiment_01_bm25.py` through `experiment_06_reranker.py`) using the exact same underlying retriever class!

---

## 3. Step-by-Step Retrieval Execution Pipeline

When `retrieve(query, entities=None, top_k=5, filter_doc_type=None)` is called, it executes an 8-stage sequence:

### Step 1: Sparse Candidate Generation (Lines 143–148)
- If `use_bm25=True`, calls `self.bm25_retriever.retrieve(query, top_k=30)`.
- Obtains 30 sparse candidate passages.

### Step 2: Dense Candidate Generation (Lines 150–155)
- If `use_dense=True`, calls `self.dense_retriever.retrieve(query, top_k=30)`.
- Obtains 30 dense candidate passages.

### Step 3: Candidate Merging & Rank Fusion (Lines 157–211)
- If both BM25 and Dense are active:
  - If `use_rrf=True`: Merges candidates using `retrieval/rrf.py` (`fuse(k=60)`).
  - If `use_rrf=False`: Performs **Linear Score Fusion**:  
    $$\text{Score}(d) = \alpha \cdot \text{Score}_{\text{BM25}}(d) + (1 - \alpha) \cdot \text{Score}_{\text{Dense}}(d), \quad \alpha = 0.5$$

### Step 4: Legal Entity Ranking Boost (Lines 213–228)
- If `use_entity_boost=True`:
  - If entities are not passed explicitly, lazily calls `LegalNER.extract_entities(query)`.
  - Calls `apply_entity_boost(fused_candidates, entities, boost_weight=0.15)`.
  - Candidates matching statutory numbers or case names receive an additive $+0.15$ boost.

### Step 5: Candidate Pool Truncation (Line 230)
- Truncates the fused, boosted list to the top `top_k_candidates = 30`.

### Step 6: Neural Cross-Encoder Reranking (Lines 232–247)
- If `use_reranker=True`:
  - Passes the 30 `(query, passage)` pairs into `CrossEncoderReranker.rerank()`.
  - Evaluates joint cross-attention and updates primary score to cross-encoder logit scores.

### Step 7: Cross-Corpus Diversity Filtering (Lines 281–332)
- Implemented in `_apply_corpus_diversity()`:
  - When a query relates to criminal procedure, the CrPC has hundreds of sections and could easily fill all 5 top slots.
  - The diversity filter caps any single parent document (e.g. CrPC) to a maximum of 2 or 3 passages, guaranteeing that constitutional provisions (Article 21) and landmark case precedents (*Kharak Singh*) are preserved in the final top-5!

### Step 8: Parent Metadata Hydration (Lines 257–279)
- Attaches the complete parent document record from `parent_store.json` to each winning candidate.
- Ensures backward-compatible field aliases (`child_id`, `child_text`, `rrf_score`, `rerank_score`).

---

## 4. Actual Code Walkthrough

### Code Excerpt: Cross-Corpus Diversity Algorithm
```python
# Lines 298-320 in retrieval/hybrid_retriever.py
effective_max = max(2, (top_k + 1) // 2) if max_per_parent is None else max_per_parent

selected: List[Dict[str, Any]] = []
parent_counts: Dict[str, int] = {}
seen_chunk_ids = set()
deferred: List[Dict[str, Any]] = []

# Pass 1: Select candidates respecting effective_max cap
for c in ranked_candidates:
    cid = c.get("chunk_id", "")
    pid = c.get("parent_id") or c.get("document_id") or c.get("metadata", {}).get("parent_id", cid)
    cnt = parent_counts.get(pid, 0)
    if cnt < effective_max:
        selected.append(c)
        seen_chunk_ids.add(cid)
        parent_counts[pid] = cnt + 1
        if len(selected) >= top_k:
            break
    else:
        deferred.append(c)
```
- **Explanation**: Prevents a single statute from monopolizing all top positions. If a statute already has 2 chunks in top-5, additional chunks are deferred so other constitutional sources get represented.
- **Why is this needed?**: Constitutional law synthesis requires harmonizing statutory sections with constitutional articles and judicial bench ratios.

---

## 5. Practical Example

### Query:
`"Can police search house without warrant under Article 21 and CrPC?"`

### Retrieval Output (Top 5 Candidates):
1. `child_act_crpc_1973_s_165_0` (Section 165 CrPC: Search by police officer without warrant) — Rerank score: `1.842`
2. `child_const_art_021_cl_0` (Article 21: Protection of life and personal liberty) — Rerank score: `1.421`
3. `child_act_crpc_1973_s_100_0` (Section 100 CrPC: Search of closed place with independent witnesses) — Rerank score: `1.154`
4. `child_case_sc_kharak_singh_1963_ratio` (Kharak Singh v. State of U.P.: Inviolability of dwelling) — Rerank score: `0.982`
5. `child_act_crpc_1973_s_047_0` (Section 47 CrPC: Search of place entered by person sought to be arrested) — Rerank score: `0.741`

---

## 6. Connection to Other Files

- **Called by**: [`rag/pipeline.py`](../../rag/pipeline.py) (Lines 215–220).
- **Sub-components used**:
  - [`retrieval/bm25_retriever.py`](../../retrieval/bm25_retriever.py)
  - [`retrieval/dense_retriever.py`](../../retrieval/dense_retriever.py)
  - [`retrieval/rrf.py`](../../retrieval/rrf.py)
  - [`retrieval/entity_boost.py`](../../retrieval/entity_boost.py)
  - [`retrieval/reranker.py`](../../retrieval/reranker.py)
- **Proceed to**: [**`reciprocal_rank_fusion.md`**](reciprocal_rank_fusion.md) to inspect the mathematics of Reciprocal Rank Fusion.

