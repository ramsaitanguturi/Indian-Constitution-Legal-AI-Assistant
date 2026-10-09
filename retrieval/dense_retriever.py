"""
Standalone Dense Vector Retriever for Indian Constitutional Legal Corpus.
Uses ChromaDB and SentenceTransformer embeddings, converts distance to cosine similarity,
and returns candidates adhering to the standardized schema.
"""

import json
import os
import re
from typing import Dict, List, Any, Optional
import chromadb
from chromadb.utils import embedding_functions

from config import (
    CHROMA_PERSIST_DIR,
    CHROMA_COLLECTION_NAME,
    DEFAULT_EMBEDDING_MODEL,
    PARENT_STORE_PATH,
)


class DenseRetriever:
    """
    Independent Dense Vector Retriever.
    Queries ChromaDB embeddings using cosine similarity.
    """

    def __init__(
        self,
        collection: Optional[Any] = None,
        parent_store: Optional[Dict[str, Dict[str, Any]]] = None,
        child_chunks: Optional[List[Dict[str, Any]]] = None,
        embedding_model_name: str = DEFAULT_EMBEDDING_MODEL,
    ):
        self.embedding_model_name = embedding_model_name
        self.parent_store = parent_store if parent_store is not None else {}
        self.child_chunks = child_chunks if child_chunks is not None else []
        self.child_dict = {c["child_id"]: c for c in self.child_chunks if "child_id" in c}

        if self.parent_store == {} and os.path.exists(PARENT_STORE_PATH):
            try:
                with open(PARENT_STORE_PATH, "r", encoding="utf-8") as f:
                    self.parent_store = json.load(f)
            except Exception:
                pass

        if collection is not None:
            self.collection = collection
        else:
            self.collection = self._connect_chromadb()

    def _connect_chromadb(self) -> Any:
        """Establish connection to persistent ChromaDB collection."""
        client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model_name
        )
        return client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            embedding_function=embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    @classmethod
    def from_ingestor(cls, ingestor: Any) -> "DenseRetriever":
        """Factory method to instantiate directly from an ingestor instance."""
        collection = getattr(ingestor, "collection", None)
        return cls(
            collection=collection,
            parent_store=getattr(ingestor, "parent_store", None),
            child_chunks=getattr(ingestor, "child_chunks", None),
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 20,
        filter_doc_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute dense vector search and return standardized candidate dictionaries.

        Args:
            query: User search query string.
            top_k: Maximum number of ranked candidates to return.
            filter_doc_type: Optional metadata filter by doc_type ('constitution', 'judgment', 'amendment').

        Returns:
            List of structured result dictionaries with uniform schema.
        """
        if not query or not str(query).strip() or top_k <= 0:
            return []

        if not re.search(r"[a-zA-Z0-9]+", str(query)):
            return []

        if self.collection is None:
            return []

        count = self.collection.count()
        if count == 0:
            return []

        n_results = min(top_k, count)
        query_kwargs = {
            "query_texts": [query],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if filter_doc_type:
            query_kwargs["where"] = {"doc_type": filter_doc_type}

        try:
            query_results = self.collection.query(**query_kwargs)
        except Exception:
            # Fallback if mock collection does not support 'where' argument
            query_kwargs.pop("where", None)
            query_results = self.collection.query(**query_kwargs)

        if not query_results or not query_results.get("ids") or not query_results["ids"][0]:
            return []

        ids = query_results["ids"][0]
        documents = query_results.get("documents", [[]])[0]
        metadatas = query_results.get("metadatas", [[]])[0]
        distances = query_results.get("distances", [[]])[0]

        results: List[Dict[str, Any]] = []
        for rank, (chunk_id, doc_text, meta, dist) in enumerate(
            zip(ids, documents, metadatas, distances), start=1
        ):
            meta = meta or {}
            parent_id = meta.get("parent_id", "")

            # Cosine similarity conversion: score = 1 - distance, clamped to [0.0, 1.0]
            # ChromaDB cosine distance is in [0, 2]
            cosine_sim = max(0.0, min(1.0, 1.0 - float(dist)))
            similarity_score = round(cosine_sim, 4)

            # Hydrate parent data
            parent_data = self.parent_store.get(parent_id, {})
            merged_metadata = {
                "parent_id": parent_id,
                "article_number": meta.get("article_number", parent_data.get("article_number", "")),
                "case_name": meta.get("case_name", parent_data.get("case_name", "")),
                "title": meta.get("title", parent_data.get("title", "")),
                "citation": meta.get("citation", parent_data.get("citation", "")),
                "year": meta.get("year", parent_data.get("year", 0)),
                "section": meta.get("section", ""),
                "source": meta.get("source", ""),
                "raw_distance": float(dist),
                "parent_data": parent_data,
            }

            candidate = {
                "document_id": parent_id,
                "chunk_id": chunk_id,
                "score": similarity_score,
                "rank": rank,
                "text": doc_text or "",
                "doc_type": meta.get("doc_type", "legal_document"),
                "metadata": merged_metadata,
                # Backward-compatibility aliases
                "child_id": chunk_id,
                "child_text": doc_text or "",
                "parent_id": parent_id,
                "parent_data": parent_data,
                "vector_rank": rank,
                "raw_distance": float(dist),
            }
            results.append(candidate)

        if filter_doc_type:
            results = [
                c for c in results
                if c.get("doc_type") == filter_doc_type
                or c.get("metadata", {}).get("doc_type") == filter_doc_type
            ]
            for r_idx, c in enumerate(results, start=1):
                c["rank"] = r_idx

        return results
