# Code Explanation: `retriever.py` 🔍

> **Source File**: [`retriever.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retriever.py)  
> **Lines of Code**: 376 lines  
> **Primary Responsibility**: Backward-compatible facade for hybrid search, Reciprocal Rank Fusion (RRF), regex-based legal entity extraction, and parent context rehydration.

---

## 1. Basic Introduction

### What is this file?
[`retriever.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retriever.py) is the legacy hybrid retrieval facade. It combines sparse lexical search (BM25Okapi) and dense semantic search (ChromaDB vectors) using **Reciprocal Rank Fusion (RRF)**, enhanced with legal entity context boosting.

### Why does this file exist?
As the codebase was upgraded to the enterprise 16-stage pipeline, retrieval logic was modularized into the [`retrieval/`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/) package (`BM25Retriever`, `DenseRetriever`, `fuse`, `apply_entity_boost`, `CrossEncoderReranker`). [`retriever.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retriever.py) preserves exact class names (`HybridRRFRetriever`, `LegalNERExtractor`) and method signatures so existing unit tests and legacy scripts run without breaking.

---

## 2. Imports and Dependencies

```python
import os
import json
import re
from typing import Dict, List, Tuple, Any, Optional
import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi

from config import (
    CHROMA_PERSIST_DIR,
    CHROMA_COLLECTION_NAME,
    DEFAULT_EMBEDDING_MODEL,
    RRF_K,
    DEFAULT_TOP_K,
    ENTITY_BOOST_WEIGHT,
    FINAL_TOP_K,
    PARENT_STORE_PATH,
    get_chroma_collection_name,
    get_embedding_dimension,
    validate_collection_dimension,
)
from ingestion import ParentChildIngestor, simple_tokenize
from retrieval.bm25_retriever import BM25Retriever
from retrieval.dense_retriever import DenseRetriever
from retrieval.rrf import fuse
from retrieval.entity_boost import apply_entity_boost
from retrieval.reranker import CrossEncoderReranker
from retrieval.hybrid_retriever import HybridRetriever
```

---

## 3. Classes in `retriever.py`

### Class 1: `LegalNERExtractor`
- **Lines in Source**: [Lines 38–96](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retriever.py#L38-L96)
- **Purpose**: A regex-driven Named Entity Recognition engine tailored for Indian Constitutional Law. Extracts Article numbers, landmark case names, and core legal concepts.
- **Key Attributes**:
  - `ARTICLE_PATTERN`: Regex `\b(?:Article|Art\.?|Art)\s*(\d+[A-Z]?|Preamble)\b`.
  - `KNOWN_CASES`: Curated list of landmark precedents (`Kesavananda Bharati`, `Maneka Gandhi`, `Puttaswamy`, `Minerva Mills`, `S.R. Bommai`, `A.K. Gopalan`).
  - `LEGAL_CONCEPTS`: Curated list of fundamental concepts (`basic structure`, `right to privacy`, `due process`, `habeas corpus`, `secularism`, `amendment`).
- **Method `extract_entities(cls, query)`**:
  - Scans query using regex and case-insensitive substring checks.
  - Returns dictionary: `{"articles": [...], "cases": [...], "concepts": [...]}`.

---

### Class 2: `HybridRRFRetriever`
- **Lines in Source**: [Lines 99–353](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retriever.py#L99-L353)
- **Purpose**: Orchestrates BM25 search, ChromaDB vector search, Reciprocal Rank Fusion, and parent document rehydration.

#### Constructor: `__init__(ingestor=None, embedding_model_name=None)` (Lines 106–174)
1. Resolves `self.embedding_model_name` (defaults to `BAAI/bge-m3` or model from `ingestor`).
2. Loads `parent_store` from `ingestor` or directly from `parent_store.json`.
3. Connects to the appropriate ChromaDB collection (`indian_legal_rag_bgem3`).
4. Validates embedding dimensions using `validate_collection_dimension()`.
5. Maps `child_id` $\to$ child chunk dictionary in `self.child_dict` for fast $O(1)$ lookups.
6. Instantiates sub-components: `BM25Retriever`, `DenseRetriever`, and `HybridRetriever`.

#### Key Methods:

##### 1. `sparse_search_bm25(query, top_k=10)` (Lines 175–191)
- Tokenizes query using `simple_tokenize()`.
- Obtains BM25 scores across all child chunks.
- Sorts chunk indices descending by score.
- Returns list of tuples: `[(child_id, score, rank), ...]`.

##### 2. `dense_search_vector(query, top_k=10)` (Lines 193–211)
- Submits query text to ChromaDB via `self.collection.query()`.
- Extracts matching chunk IDs and cosine distances.
- Returns list of tuples: `[(child_id, distance, rank), ...]`.

##### 3. `reciprocal_rank_fusion(bm25_results, vector_results, ner_entities, k_constant=60)` (Lines 213–323)
- Computes RRF scores:
  $$\text{Score}(d) = \sum \frac{1}{k + \text{rank}(d)}$$
- Applies entity boosting: Adds $+0.05$ if candidate matches an identified article number, and $+0.05$ if it matches an identified case name.
- Sorts candidates descending by final fused score.
- Hydrates parent document metadata from `self.parent_store`.
- Returns standardized result dictionaries containing: `document_id`, `chunk_id`, `score`, `rank`, `text`, `doc_type`, and `parent_data`.

##### 4. `retrieve(query, top_k=4)` (Lines 325–353)
- Executes the complete workflow:
  1. Extracts legal entities via `LegalNERExtractor.extract_entities(query)`.
  2. Runs sparse BM25 search for `top_k * 3` candidates.
  3. Runs dense vector search for `top_k * 3` candidates.
  4. Fuses rankings with RRF and entity boosting.
  5. Slices and returns top results.

---

## 4. Actual Code Walkthrough

### Code Excerpt: Reciprocal Rank Fusion & Entity Boost
```python
# Lines 228-256 in retriever.py
# 1. Add BM25 scores
for child_id, score, rank in bm25_results:
    rrf_scores[child_id] = rrf_scores.get(child_id, 0.0) + (1.0 / (k_constant + rank))
    if child_id not in child_rank_details:
        child_rank_details[child_id] = {}
    child_rank_details[child_id]["bm25_rank"] = rank

# 2. Add Vector scores
for child_id, dist, rank in vector_results:
    rrf_scores[child_id] = rrf_scores.get(child_id, 0.0) + (1.0 / (k_constant + rank))
    if child_id not in child_rank_details:
        child_rank_details[child_id] = {}
    child_rank_details[child_id]["vector_rank"] = rank

# 3. Apply Legal NER context boost
for child_id in rrf_scores:
    child = self.child_dict.get(child_id, {})
    # Boost if article matches
    art_num = child.get("article_number", "")
    for ent_art in ner_entities.get("articles", []):
        if ent_art.lower() in art_num.lower() or art_num.lower() in ent_art.lower():
            rrf_scores[child_id] += 0.05

    # Boost if case matches
    c_name = child.get("case_name", "")
    for ent_case in ner_entities.get("cases", []):
        if ent_case.lower() in c_name.lower():
            rrf_scores[child_id] += 0.05
```
- **Explanation**: Blends ranks from BM25 and vector search using the reciprocal formula, then applies an additive boost if the chunk metadata matches query entities.
- **Why is this needed?**: Fuses different scoring scales (BM25 unbounded positive scores vs vector cosine distances) into a unified, fair ranking scale.

---

## 5. Practical Example

### Query:
`"What did Supreme Court rule regarding Right to Privacy in Puttaswamy under Article 21?"`

### Execution Trace:
1. `LegalNERExtractor.extract_entities()` extracts:
   - `articles`: `['Article 21']`
   - `cases`: `['Puttaswamy']`
   - `concepts`: `['right to privacy', 'privacy']`
2. BM25 retrieves 12 candidate passages (finds exact tokens *"Puttaswamy"* and *"Article 21"*).
3. Dense search retrieves 12 candidate passages (finds semantic passages on privacy and personal liberty).
4. `reciprocal_rank_fusion()` merges both lists, applies $+0.05$ for Article 21 and $+0.05$ for Puttaswamy, rehydrates the full parent judgment from `parent_store.json`, and returns top candidates.

---

## 6. Connection to Other Files

- **Imported by**: [`app.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/app.py) in `load_rag_pipeline()` and baseline regression tests.
- **Delegates to**:
  - [`retrieval/bm25_retriever.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/bm25_retriever.py)
  - [`retrieval/dense_retriever.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/dense_retriever.py)
  - [`retrieval/rrf.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/rrf.py)
  - [`retrieval/entity_boost.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/entity_boost.py)
- **Proceed to**: [**`06_NLP_MODULE/README.md`**](../06_NLP_MODULE/README.md) to explore the Natural Language Processing subsystem.

