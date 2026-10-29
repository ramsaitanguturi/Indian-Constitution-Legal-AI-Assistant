"""
BGE-M3 Embedding Engine Module (Enhanced with Persistent Disk Caching).
Provides batch embeddings, L2 normalization, CUDA/CPU detection,
persistent SQLite-backed embedding cache, and ChromaDB-compatible embedding function
using BAAI/bge-m3 and sentence-transformers.
"""

import os
import sys
import sqlite3
import hashlib
from pathlib import Path
from typing import List, Optional, Union, Dict, Any, Tuple
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from config import (
    BASE_DIR,
    DEFAULT_EMBEDDING_MODEL,
    BGE_M3_MODEL_NAME,
    BGE_M3_EMBEDDING_DIM,
    EMBEDDING_BATCH_SIZE,
)

os.environ.setdefault("HF_HUB_OFFLINE", "1")

CACHE_DIR = BASE_DIR / "data" / ".cache"
EMBEDDING_DB_PATH = CACHE_DIR / "embeddings_cache.sqlite"


def _init_sqlite_cache() -> None:
    """Initialize persistent SQLite embedding cache table."""
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


_init_sqlite_cache()


class BGEM3EmbeddingFunction(EmbeddingFunction[Documents]):
    """
    ChromaDB compatible EmbeddingFunction wrapping BAAI/bge-m3 or MiniLM.
    Features:
    - Persistent SQLite disk cache to avoid redundant neural encoding
    - Automatic GPU / CPU fallback
    - Batch inference with L2 normalization
    - Query and document encoding consistency
    """

    def __init__(
        self,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
        device: Optional[str] = None,
        batch_size: int = EMBEDDING_BATCH_SIZE,
        normalize_embeddings: bool = True,
        use_disk_cache: bool = True,
    ):
        self.model_name = model_name
        self.batch_size = batch_size
        self.normalize_embeddings = normalize_embeddings
        self.use_disk_cache = use_disk_cache

        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self._model: Optional[SentenceTransformer] = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy load SentenceTransformer model."""
        if self._model is None:
            try:
                self._model = SentenceTransformer(self.model_name, device=self.device, local_files_only=True)
            except Exception:
                try:
                    self._model = SentenceTransformer(self.model_name, device=self.device)
                except Exception as e:
                    # If CUDA failed, fallback to CPU
                    if self.device != "cpu":
                        print(f"[EMBEDDINGS] CUDA initialization failed ({e}), falling back to CPU.")
                        self.device = "cpu"
                        try:
                            self._model = SentenceTransformer(self.model_name, device="cpu", local_files_only=True)
                        except Exception:
                            self._model = SentenceTransformer(self.model_name, device="cpu")
                    else:
                        raise RuntimeError(
                            f"Failed to load embedding model '{self.model_name}': {e}. "
                            "Check disk space and HuggingFace cache."
                        ) from e
            if hasattr(self._model, "max_seq_length") and self._model.max_seq_length > 512:
                self._model.max_seq_length = 512
        return self._model

    def _fetch_from_cache(self, hashes: List[str]) -> Dict[str, np.ndarray]:
        """Fetch cached vectors from SQLite."""
        if not self.use_disk_cache or not hashes:
            return {}
        
        cached_vectors = {}
        try:
            with sqlite3.connect(str(EMBEDDING_DB_PATH)) as conn:
                # Query in batches of 900 (SQLite parameter limit)
                for i in range(0, len(hashes), 900):
                    batch_hashes = hashes[i:i + 900]
                    placeholders = ",".join("?" for _ in batch_hashes)
                    cursor = conn.execute(
                        f"SELECT content_hash, vector FROM embedding_cache WHERE model_name = ? AND content_hash IN ({placeholders})",
                        [self.model_name] + batch_hashes,
                    )
                    for chash, v_blob in cursor.fetchall():
                        arr = np.frombuffer(v_blob, dtype=np.float32)
                        cached_vectors[chash] = arr
        except Exception as e:
            print(f"[EMBEDDING CACHE WARNING] Error reading cache: {e}")
        return cached_vectors

    def _store_in_cache(self, items: List[Tuple[str, np.ndarray]]) -> None:
        """Store newly computed vectors in SQLite cache."""
        if not self.use_disk_cache or not items:
            return
        try:
            with sqlite3.connect(str(EMBEDDING_DB_PATH)) as conn:
                params = [
                    (chash, self.model_name, len(vec), vec.astype(np.float32).tobytes())
                    for chash, vec in items
                ]
                conn.executemany(
                    "INSERT OR REPLACE INTO embedding_cache (content_hash, model_name, dim, vector) VALUES (?, ?, ?, ?)",
                    params,
                )
                conn.commit()
        except Exception as e:
            print(f"[EMBEDDING CACHE WARNING] Error writing cache: {e}")

    def __call__(self, input: Documents) -> Embeddings:
        """Encode list of document strings into normalized embeddings using cache."""
        if not input:
            return []

        texts = [str(t) if t is not None else "" for t in input]
        hashes = [hashlib.sha256(t.encode("utf-8")).hexdigest() for t in texts]

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

    def encode_queries(self, queries: Union[str, List[str]]) -> np.ndarray:
        """Encode query strings for dense retrieval with normalization."""
        if isinstance(queries, str):
            queries = [queries]
        return self.model.encode(
            queries,
            batch_size=self.batch_size,
            show_progress_bar=False,
            normalize_embeddings=self.normalize_embeddings,
            convert_to_numpy=True,
        )

    def get_dimension(self) -> int:
        """Return embedding dimension."""
        dim = getattr(self.model, "get_embedding_dimension", None)
        if callable(dim):
            return dim()
        dim_legacy = getattr(self.model, "get_sentence_embedding_dimension", None)
        if callable(dim_legacy):
            return dim_legacy()
        if "bge-m3" in self.model_name.lower():
            return BGE_M3_EMBEDDING_DIM
        return 384


_EMBEDDING_FUNCTION_CACHE: Dict[str, BGEM3EmbeddingFunction] = {}


def get_embedding_function(
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    device: Optional[str] = None,
    batch_size: int = EMBEDDING_BATCH_SIZE,
) -> BGEM3EmbeddingFunction:
    """Retrieve or initialize cached embedding function singleton."""
    cache_key = f"{model_name}_{device}_{batch_size}"
    if cache_key not in _EMBEDDING_FUNCTION_CACHE:
        _EMBEDDING_FUNCTION_CACHE[cache_key] = BGEM3EmbeddingFunction(
            model_name=model_name,
            device=device,
            batch_size=batch_size,
        )
    return _EMBEDDING_FUNCTION_CACHE[cache_key]
