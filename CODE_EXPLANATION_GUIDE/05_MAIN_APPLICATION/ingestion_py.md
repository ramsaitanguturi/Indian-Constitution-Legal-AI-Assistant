# Code Explanation: `ingestion.py` 📥

> **Source File**: [`ingestion.py`](../../ingestion.py)  
> **Lines of Code**: 285 lines  
> **Primary Responsibility**: Document ingestion facade, parent document parsing, child passage generation, ChromaDB vector indexing, and BM25 index creation.

---

## 1. Basic Introduction

### What is this file?
[`ingestion.py`](../../ingestion.py) defines the **Hierarchical Parent-Child Ingestion Engine** for the legal assistant. It is a backward-compatible facade that coordinates document parsing, structure-aware chunking, vector database population, and sparse BM25 indexing.

### Why does this file exist?
To achieve high retrieval performance without losing legal context, the assistant separates **indexing units** from **generation units**:
- **Parent documents** retain the entire, unbroken text of Constitutional Articles and Supreme Court decisions (~1,200 characters).
- **Child passages** are small, dense text snippets (~300 characters / structure-aware clauses) that are indexed in ChromaDB and BM25 for laser-accurate retrieval.

[`ingestion.py`](../../ingestion.py) bridges the legacy baseline pipeline with the production 886-document expanded corpus in [`rag/ingestion.py`](../../rag/ingestion.py), ensuring that existing unit tests and new production workflows run seamlessly.

---

## 2. Imports and Dependencies

```python
import json
import os
import re
from typing import Dict, List, Tuple, Any, Optional
import chromadb                                       # Local vector store
from chromadb.utils import embedding_functions         # ChromaDB embedding wrapper
from rank_bm25 import BM25Okapi                        # Sparse BM25 keyword index

from config import (                                   # Paths & chunking hyperparameters
    CONSTITUTION_DATA_PATH,
    JUDGMENTS_DATA_PATH,
    CHROMA_PERSIST_DIR,
    PARENT_STORE_PATH,
    CHROMA_COLLECTION_NAME,
    DEFAULT_EMBEDDING_MODEL,
    CHILD_CHUNK_SIZE,
    CHILD_CHUNK_OVERLAP,
    BM25_K1,
    BM25_B,
    get_chroma_collection_name,
    get_embedding_dimension,
    validate_collection_dimension,
)
from rag.chunking import LegalStructureChunker, estimate_tokens # Modular legal chunker
from rag.ingestion import ProductionIngestor, simple_tokenize   # Modular production ingestor
```

---

## 3. Classes in `ingestion.py`

### `ParentChildIngestor`
- **Lines in Source**: [Lines 35–281](../../ingestion.py#L35-L281)
- **Purpose**: Oversees the parsing of legal JSON files, builds `parent_store`, derives `child_chunks`, and populates ChromaDB and the BM25 index.

#### Attributes:
- `self.use_full_corpus` (bool): If True, routes to the expanded 886-document production corpus in `rag/ingestion.py`. If False, uses baseline sample JSON datasets.
- `self.batch_size` (int): Number of chunks upserted into ChromaDB per batch.
- `self.model_name` (str): Active dense model (`BAAI/bge-m3` or `all-MiniLM-L6-v2`).
- `self.chunker`: Instance of `LegalStructureChunker`.
- `self.parent_store` (dict): Dictionary mapping `parent_id` $\to$ full parent document record.
- `self.child_chunks` (list): List of child chunk dictionaries.
- `self.bm25_index` (BM25Okapi): In-memory BM25 index over tokenized child passages.
- `self.collection`: ChromaDB collection instance.

---

## 4. Method-by-Method Walkthrough

### 1. `load_raw_datasets()` (Lines 64–78)
- Loads `sample_constitution.json` and `sample_judgments.json` from `data/` if they exist.
- Returns a tuple of two lists: `(constitution_data, judgments_data)`.

### 2. `_split_text_into_children(text, chunk_size=300, overlap=50)` (Lines 79–87)
- Invokes `self.chunker.chunk_legacy_sliding_window(text, chunk_size, overlap)`.
- Slices long text into overlapping sliding-window passages.

### 3. `process_parent_child_chunks()` (Lines 88–185)
- **Core logic for hierarchical chunking**:
  - If `use_full_corpus == True`, delegates to `self._production_ingestor.process_parent_child_chunks()`.
  - For each Constitutional Article:
    - Builds a unified parent string: Title, Part, Category, Constitutional Text, Legal Explanation, Historical Context.
    - Stores parent record in `parent_store` with key `parent_{id}`.
    - Slices text into 300-character child passages.
    - Appends each passage to `child_chunks` with metadata (`child_id`, `parent_id`, `article_number`, `title`).
  - For each Supreme Court Judgment:
    - Builds parent record: Case Name, Citation, Bench, Articles Referred, Facts, Ratio Decidendi, Verdict, Key Takeaways.
    - Stores parent record in `parent_store` with key `parent_{id}`.
    - Slices text into 300-character child passages.
- **Return**: Tuple `(parent_store, child_chunks)`.

### 4. `save_parent_store()` & `load_parent_store()` (Lines 186–207)
- `save_parent_store()`: Saves `self.parent_store` to `parent_store.json`. Contains safety logic: if the on-disk file is already larger (e.g. from the full corpus), it merges records to prevent accidental downsizing.
- `load_parent_store()`: Reads `parent_store.json` from disk into memory.

### 5. `build_vector_store(force_rebuild=False)` (Lines 208–258)
- Connects to ChromaDB via `chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))`.
- Resolves collection name: `indian_legal_rag_bgem3` (for BGE-M3) or `indian_legal_rag` (for MiniLM).
- Validates that the collection dimension matches the model dimension using `validate_collection_dimension()`.
- **Idempotency Guard**: If `collection.count() > 0` and `force_rebuild=False`, skips re-indexing to avoid wasting CPU/GPU time.
- If rebuilding or unpopulated, upserts all `child_chunks` (IDs, texts, metadata) into ChromaDB.
- **Return**: ChromaDB collection object.

### 6. `build_bm25_index()` (Lines 259–264)
- Tokenizes each child chunk using `simple_tokenize()`.
- Instantiates `BM25Okapi(tokenized_corpus, k1=1.5, b=0.75)`.
- **Return**: Initialized `BM25Okapi` instance.

### 7. `run_pipeline(force_rebuild=False)` (Lines 265–281)
- Executes the entire sequence in order:
  1. `process_parent_child_chunks()`
  2. `save_parent_store()`
  3. `build_vector_store()`
  4. `build_bm25_index()`
- Returns `(parent_store, collection, bm25_index, child_chunks)`.

---

## 5. Actual Code Walkthrough

### Code Excerpt: Creating Parent Document and Child Passages
```python
# Lines 100-136 in ingestion.py
for item in const_data:
    parent_id = f"parent_{item['id']}"
    full_parent_text = (
        f"ARTICLE/TITLE: {item['article_number']} - {item['title']}\n"
        f"PART: {item['part']} | CATEGORY: {item['category']}\n"
        f"CONSTITUTIONAL TEXT: {item['text']}\n"
        f"LEGAL EXPLANATION: {item.get('explanation', '')}\n"
        f"HISTORICAL CONTEXT: {item.get('historical_context', '')}"
    )

    parent_store[parent_id] = {
        "parent_id": parent_id,
        "doc_type": "constitution",
        "article_number": item["article_number"],
        "title": item["title"],
        "part": item["part"],
        "category": item["category"],
        "full_text": full_parent_text,
        "raw_text": item["text"],
        "explanation": item.get("explanation", ""),
        "historical_context": item.get("historical_context", "")
    }

    combined_text_for_children = f"{item['title']}. {item['text']} {item.get('explanation', '')}"
    passages = self._split_text_into_children(combined_text_for_children)

    for p_idx, passage in enumerate(passages):
        child_id = f"child_const_{item['id']}_{p_idx}"
        child_chunks.append({
            "child_id": child_id,
            "parent_id": parent_id,
            "text": passage,
            "doc_type": "constitution",
            "article_number": item["article_number"],
            "title": item["title"],
            "category": item["category"]
        })
```
- **Explanation**: Creates a rich parent document containing complete constitutional text and legal explanation, then derives smaller child passages linking back via `parent_id`.
- **Why is this needed?**: Powers the Parent-Child RAG pattern: searches small child passages, but hydrates the entire parent document for answer generation.

---

## 6. Practical Example

### Input Record from Dataset:
```json
{
  "id": "art_21",
  "article_number": "Article 21",
  "title": "Protection of life and personal liberty",
  "part": "Part III",
  "category": "Fundamental Rights",
  "text": "No person shall be deprived of his life or personal liberty except according to procedure established by law."
}
```

### Derived Ingestion Output:
1. **Parent Document** in `parent_store.json`:
   - `parent_id`: `"parent_art_21"`
   - `full_text`: Includes title, part, article text, and judicial interpretation.
2. **Child Chunks** in ChromaDB & BM25:
   - `child_const_art_21_0`: `"Protection of life and personal liberty. No person shall be deprived of his life or personal liberty..."`
   - Child metadata: `{"parent_id": "parent_art_21", "article_number": "Article 21"}`.

---

## 7. Connection to Other Files

- **Called by**: [`app.py`](../../app.py) (`load_rag_pipeline()`) and [`retriever.py`](../../retriever.py).
- **Delegates to**: [`rag/ingestion.py`](../../rag/ingestion.py) (`ProductionIngestor`) for the full 886-document production corpus.
- **Proceed to**: [**`retriever_py.md`**](retriever_py.md) to inspect how BM25 and vector search are combined via Reciprocal Rank Fusion.

