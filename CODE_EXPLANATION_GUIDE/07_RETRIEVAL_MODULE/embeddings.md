# Code Explanation: `retrieval/embeddings.py` 🧠

> **Source File**: [`retrieval/embeddings.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/embeddings.py)  
> **Lines of Code**: 228 lines  
> **Primary Responsibility**: Pretrained dense vector embeddings (`BAAI/bge-m3` 1024-d / MiniLM 384-d), L2 vector normalization, automatic CUDA/CPU detection, and persistent SQLite disk caching.

---

## 1. Basic Introduction

### What is this file?
[`retrieval/embeddings.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/embeddings.py) defines the dense vector embedding engine for the assistant. It wraps Hugging Face's `sentence-transformers` library into a ChromaDB-compatible `EmbeddingFunction`.

### Why does this file exist?
Computing 1024-dimensional embeddings using a transformer model (`BAAI/bge-m3`) is computationally expensive:
- Running a forward pass over thousands of legal passages on a CPU takes significant time.
- If the system re-encoded every passage every time the server rebooted, startup would take 15–20 minutes.

[`retrieval/embeddings.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/embeddings.py) implements a **Persistent SQLite Embedding Disk Cache**:
1. It hashes each text using SHA-256: `hash = sha256(text)`.
2. Before invoking the neural model, it queries `embeddings_cache.sqlite`.
3. If the vector exists, it reads the binary blob directly in microseconds.
4. Only new or modified texts are encoded by the transformer.

---

## 2. Imports and Dependencies

```python
import os
import sys
import sqlite3                              # Local embedded disk cache
import hashlib                              # SHA-256 cryptographic content hashing
from pathlib import Path
from typing import List, Optional, Union, Dict, Any, Tuple
import numpy as np                          # Vector manipulation & serialization
import torch                                # PyTorch CPU/CUDA detection
from sentence_transformers import SentenceTransformer # Neural transformer bi-encoder
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings # ChromaDB interface

from config import (
    BASE_DIR,
    DEFAULT_EMBEDDING_MODEL,
    BGE_M3_MODEL_NAME,
    BGE_M3_EMBEDDING_DIM,
    EMBEDDING_BATCH_SIZE,
)
```

---

## 3. Persistent SQLite Cache Architecture

The module initializes a local cache database at `data/.cache/embeddings_cache.sqlite` on startup:

```python
# Lines 33-47 in retrieval/embeddings.py
def _init_sqlite_cache() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(EMBEDDING_DB_PATH)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS embedding_cache (
                content_hash TEXT NOT NULL,
                model_name TEXT NOT NULL,
                dim INTEGER NOT NULL,
                vector BLOB NOT NULL,
                PRIMARY KEY (content_hash, model_name)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_lookup ON embedding_cache (content_hash, model_name)")
        conn.commit()
```
- **Composite Primary Key**: `(content_hash, model_name)` ensures that if you switch from MiniLM to BGE-M3, vectors for both models can coexist without collision.
- **Storage Format**: Vectors are stored as raw `np.float32` byte buffers (`vector BLOB`), minimizing disk space.

---

## 4. Class Structure: `BGEM3EmbeddingFunction`

### Constructor: `__init__(model_name, device, batch_size, normalize_embeddings, use_disk_cache)` (Lines 63–82)
- Resolves device: `device = "cuda" if torch.cuda.is_available() else "cpu"`.
- Sets batch size to `32` and `normalize_embeddings = True`.
- Model is lazily loaded on first use (`self._model = None`).

### Lazy Model Property: `model` (Lines 83–108)
- On first access:
  1. Attempts offline loading (`local_files_only=True`) from local Hugging Face cache.
  2. If CUDA initialization fails (common on laptops with missing Nvidia drivers), it catches the error and **gracefully falls back to CPU**.
  3. Caps `max_seq_length = 512` to ensure fast CPU inference.

---

## 5. Key Methods in `BGEM3EmbeddingFunction`

### 1. `_fetch_from_cache(hashes: List[str]) -> Dict[str, np.ndarray]` (Lines 110–131)
- Connects to SQLite and queries in batches of 900 (respecting SQLite's variable limit).
- Converts raw byte blobs back into NumPy arrays: `np.frombuffer(v_blob, dtype=np.float32)`.

### 2. `_store_in_cache(items: List[Tuple[str, np.ndarray]]) -> None` (Lines 133–149)
- Inserts computed vectors into SQLite via `INSERT OR REPLACE INTO embedding_cache`.

### 3. `__call__(input: Documents) -> Embeddings` (Lines 151–185)
- Standard ChromaDB interface method:
  1. Computes SHA-256 hash for every text in `input`.
  2. Looks up all hashes in `_fetch_from_cache()`.
  3. Slices out any missing indices.
  4. Runs `self.model.encode(missing_texts)` with L2 normalization.
  5. Stores new vectors in SQLite cache.
  6. Assembles and returns all embeddings in original order as lists of floats.

### 4. `encode_queries(queries: Union[str, List[str]]) -> np.ndarray` (Lines 187–197)
- Encodes search queries with L2 normalization for cosine similarity search.

---

## 6. Actual Code Walkthrough

### Code Excerpt: Caching and Missing Vector Inference
```python
# Lines 160-184 in retrieval/embeddings.py
# 1. Lookup cache
cached = self._fetch_from_cache(hashes)

# 2. Identify missing indices
missing_indices = [idx for idx, h in enumerate(hashes) if h not in cached]

if missing_indices:
    missing_texts = [texts[idx] for idx in missing_indices]
    computed_vectors = self.model.encode(
        missing_texts,
        batch_size=self.batch_size,
        show_progress_bar=False,
        normalize_embeddings=self.normalize_embeddings,
        convert_to_numpy=True,
    )

    to_store = []
    for orig_idx, vec in zip(missing_indices, computed_vectors):
        chash = hashes[orig_idx]
        cached[chash] = vec
        to_store.append((chash, vec))

    self._store_in_cache(to_store)

# 3. Assemble results in original order
results = [cached[h].tolist() for h in hashes]
return results
```
- **Explanation**: Only texts missing from the SQLite database are passed through PyTorch transformer layers.
- **Why is this needed?**: Slashes indexing time by $> 95\%$ on subsequent runs.

---

## 7. Connection to Other Files

- **Supplied to**: ChromaDB collections created in [`retrieval/dense_retriever.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/dense_retriever.py) and [`rag/ingestion.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/rag/ingestion.py).
- **Settings from**: [`config.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/config.py) (`BGE_M3_MODEL_NAME`, `BGE_M3_EMBEDDING_DIM`).
- **Proceed to**: [**`dense_retrieval.md`**](dense_retrieval.md) to inspect how ChromaDB executes vector search.

