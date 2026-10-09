"""
Standalone BM25 Lexical Retriever for Indian Constitutional Legal Corpus.
Provides keyword-based search over child chunks using BM25Okapi,
normalizes scores to [0, 1], and returns standardized candidate dictionaries.
"""

import json
import os
import re
from typing import Dict, List, Any, Optional
from rank_bm25 import BM25Okapi

from config import (
    BM25_K1,
    BM25_B,
    PARENT_STORE_PATH,
    CONSTITUTION_ARTICLES_PATH,
)


def simple_tokenize(text: str) -> List[str]:
    """Tokenize query or document into lower-case alphanumeric tokens."""
    if not text:
        return []
    return re.findall(r"\b\w+\b", text.lower())


class BM25Retriever:
    """
    Independent BM25 Lexical Retriever.
    Indexes child chunks of Constitutional Articles, Amendments, and Judgments.
    """

    def __init__(
        self,
        bm25_index: Optional[BM25Okapi] = None,
        child_chunks: Optional[List[Dict[str, Any]]] = None,
        parent_store: Optional[Dict[str, Dict[str, Any]]] = None,
        k1: float = BM25_K1,
        b: float = BM25_B,
    ):
        self.k1 = k1
        self.b = b
        self.bm25_index = bm25_index
        self.child_chunks = child_chunks if child_chunks is not None else []
        self.parent_store = parent_store if parent_store is not None else {}
        self.child_dict = {c["child_id"]: c for c in self.child_chunks if "child_id" in c}

        # Lazy load if index or chunks not provided
        if self.bm25_index is None or not self.child_chunks:
            self._initialize_from_corpus()

    def _initialize_from_corpus(self) -> None:
        """Initialize index and child chunks from corpus / production ingestor."""
        from rag.ingestion import ProductionIngestor

        use_full = os.path.exists(CONSTITUTION_ARTICLES_PATH)
        ingestor = ProductionIngestor(use_full_corpus=use_full)
        parent_store, child_chunks = ingestor.process_parent_child_chunks()
        bm25_index = ingestor.build_bm25_index()

        self.bm25_index = bm25_index
        self.child_chunks = child_chunks
        self.parent_store = parent_store
        self.child_dict = {c["child_id"]: c for c in self.child_chunks if "child_id" in c}

    @classmethod
    def from_ingestor(cls, ingestor: Any) -> "BM25Retriever":
        """Factory method to instantiate directly from an ingestor instance."""
        return cls(
            bm25_index=getattr(ingestor, "bm25_index", None),
            child_chunks=getattr(ingestor, "child_chunks", None),
            parent_store=getattr(ingestor, "parent_store", None),
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 20,
        filter_doc_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute BM25 lexical search and return standardized candidate dictionaries.

        Args:
            query: User search query string.
            top_k: Maximum number of ranked candidates to return.
            filter_doc_type: Optional metadata filter by doc_type ('constitution', 'judgment', 'amendment').

        Returns:
            List of structured result dictionaries with uniform schema.
        """
        if not query or not query.strip() or top_k <= 0:
            return []

        if self.bm25_index is None or not self.child_chunks:
            return []

        tokens = simple_tokenize(query)
        if not tokens:
            return []

        # Get raw BM25 scores across all child passages
        raw_scores = self.bm25_index.get_scores(tokens)

        # Filter indices with positive relevance score
        positive_indices = [i for i, score in enumerate(raw_scores) if score > 0.0]
        if not positive_indices:
            # Fallback for very small test corpora or high-frequency terms where Robertson IDF <= 0:
            # Check simple token overlap matches
            token_set = set(tokens)
            tf_scores = []
            for i, chunk in enumerate(self.child_chunks):
                chunk_tokens = simple_tokenize(chunk.get("text", ""))
                matches = sum(1 for t in chunk_tokens if t in token_set)
                tf_scores.append(float(matches))
            positive_indices = [i for i, s in enumerate(tf_scores) if s > 0.0]
            if positive_indices:
                raw_scores = tf_scores
            else:
                return []

        # Optional metadata filtering by doc_type
        if filter_doc_type:
            filtered_indices = [
                i for i in positive_indices
                if self.child_chunks[i].get("doc_type") == filter_doc_type
                or self.child_chunks[i].get("metadata", {}).get("doc_type") == filter_doc_type
            ]
            if filtered_indices:
                positive_indices = filtered_indices
            else:
                return []

        # Sort descending by score
        ranked_indices = sorted(positive_indices, key=lambda i: raw_scores[i], reverse=True)[:top_k]

        max_score = float(raw_scores[ranked_indices[0]]) if ranked_indices else 1.0

        results: List[Dict[str, Any]] = []
        for rank, idx in enumerate(ranked_indices, start=1):
            chunk = self.child_chunks[idx]
            chunk_id = chunk.get("child_id", f"chunk_{idx}")
            parent_id = chunk.get("parent_id", "")
            raw_s = float(raw_scores[idx])

            # Normalized score bounded in [0.0, 1.0]
            normalized_score = round(raw_s / max_score, 4) if max_score > 0 else 0.0

            # Resolve parent metadata
            parent_data = self.parent_store.get(parent_id, {})
            metadata = {
                "parent_id": parent_id,
                "article_number": chunk.get("article_number", parent_data.get("article_number", "")),
                "case_name": chunk.get("case_name", parent_data.get("case_name", "")),
                "title": chunk.get("title", parent_data.get("title", "")),
                "citation": chunk.get("citation", parent_data.get("citation", "")),
                "year": chunk.get("year", parent_data.get("year", 0)),
                "section": chunk.get("section", ""),
                "source": chunk.get("source", ""),
                "raw_bm25_score": raw_s,
                "parent_data": parent_data,
            }

            candidate = {
                "document_id": parent_id,
                "chunk_id": chunk_id,
                "score": normalized_score,
                "rank": rank,
                "text": chunk.get("text", ""),
                "doc_type": chunk.get("doc_type", "legal_document"),
                "metadata": metadata,
                # Backward-compatibility aliases
                "child_id": chunk_id,
                "child_text": chunk.get("text", ""),
                "parent_id": parent_id,
                "parent_data": parent_data,
                "bm25_rank": rank,
                "raw_score": raw_s,
            }
            results.append(candidate)

        return results
