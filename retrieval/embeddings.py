"""
BGE-M3 Embedding Engine Module.
Provides batch embeddings, L2 normalization, CUDA/CPU detection,
and ChromaDB-compatible embedding function using BAAI/bge-m3.
"""

import os
import hashlib
from typing import List, Optional, Union, Dict, Any
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from config import (
    DEFAULT_EMBEDDING_MODEL,
    BGE_M3_MODEL_NAME,
    BGE_M3_EMBEDDING_DIM,
    EMBEDDING_BATCH_SIZE,
)


class BGEM3EmbeddingFunction(EmbeddingFunction[Documents]):
    """
    ChromaDB compatible EmbeddingFunction wrapping BAAI/bge-m3.
    Ensures identical preprocessing, batched inference, L2 normalization,
    and automatic GPU/CPU device placement.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
        device: Optional[str] = None,
        batch_size: int = EMBEDDING_BATCH_SIZE,
        normalize_embeddings: bool = True,
    ):
        self.model_name = model_name
        self.batch_size = batch_size
        self.normalize_embeddings = normalize_embeddings

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
                self._model = SentenceTransformer(self.model_name, device=self.device)
            except Exception as e:
                # If CUDA failed, fallback to CPU
                if self.device != "cpu":
                    print(f"[EMBEDDINGS] CUDA initialization failed ({e}), falling back to CPU.")
                    self.device = "cpu"
                    self._model = SentenceTransformer(self.model_name, device="cpu")
                else:
                    raise RuntimeError(
                        f"Failed to load embedding model '{self.model_name}': {e}. "
                        "Check disk space and HuggingFace cache."
                    ) from e
        return self._model

    def __call__(self, input: Documents) -> Embeddings:
        """Encode list of document strings into normalized embeddings."""
        if not input:
            return []
        
        # Ensure input is a list of strings
        texts = [str(t) if t is not None else "" for t in input]
        
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            normalize_embeddings=self.normalize_embeddings,
            convert_to_numpy=True,
        )
        return embeddings.tolist()

    def encode_queries(self, queries: Union[str, List[str]]) -> np.ndarray:
        """Encode query strings for dense retrieval."""
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
        return BGE_M3_EMBEDDING_DIM


# Global singleton cache for embedding functions to avoid reloading large weights
_EMBEDDING_FUNCTION_CACHE: Dict[str, BGEM3EmbeddingFunction] = {}


def get_embedding_function(
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    device: Optional[str] = None,
    batch_size: int = EMBEDDING_BATCH_SIZE,
) -> BGEM3EmbeddingFunction:
    """Retrieve or initialize cached embedding function."""
    cache_key = f"{model_name}_{device}_{batch_size}"
    if cache_key not in _EMBEDDING_FUNCTION_CACHE:
        _EMBEDDING_FUNCTION_CACHE[cache_key] = BGEM3EmbeddingFunction(
            model_name=model_name,
            device=device,
            batch_size=batch_size,
        )
    return _EMBEDDING_FUNCTION_CACHE[cache_key]

