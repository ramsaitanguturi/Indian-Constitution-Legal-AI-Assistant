"""
Cross-Encoder Neural Reranking Module.
Takes top candidate passages retrieved by hybrid search and reranks them
using sentence_transformers.CrossEncoder ('cross-encoder/ms-marco-MiniLM-L-6-v2').
"""

import math
from typing import Dict, List, Any, Optional, Tuple
from config import RERANKER_MODEL_NAME, FINAL_TOP_K


class CrossEncoderReranker:
    """
    Second-Stage Neural Reranker.
    Computes fine-grained cross-attention query-document relevance scores.
    """

    def __init__(
        self,
        model_name: str = RERANKER_MODEL_NAME,
        device: Optional[str] = None,
        lazy_load: bool = True,
        batch_size: int = 32,
    ):
        self.model_name = model_name
        self.device = device
        self.lazy_load = lazy_load
        self.batch_size = batch_size
        self._model = None

        if not self.lazy_load:
            self._load_model()

    def _load_model(self) -> Any:
        """Loads CrossEncoder model instance."""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.model_name, device=self.device)
            except Exception as e:
                # If model fails to load, raise or retain None for fallback
                print(f"[RERANKER WARNING] Could not load CrossEncoder '{self.model_name}': {e}")
                self._model = None
        return self._model

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: Optional[int] = FINAL_TOP_K,
    ) -> List[Dict[str, Any]]:
        """
        Rerank a pool of candidate passages against user query.

        Args:
            query: User search query string.
            candidates: Candidate dictionaries containing passage text.
            top_k: Number of top reranked candidates to return (None for all).

        Returns:
            Reranked list of candidates ordered descending by cross-encoder score.
        """
        if not candidates or not query or not query.strip():
            return []

        # Prepare (query, text) pairs
        pairs: List[Tuple[str, str]] = []
        for cand in candidates:
            passage_text = cand.get("text") or cand.get("child_text") or ""
            pairs.append((query, passage_text))

        model = self._load_model()

        if model is not None:
            # Predict cross-encoder relevance scores
            try:
                scores = model.predict(pairs, batch_size=self.batch_size)
                # If single pair, score might be scalar
                if hasattr(scores, "__len__"):
                    score_list = [float(s) for s in scores]
                else:
                    score_list = [float(scores)]
            except Exception as e:
                print(f"[RERANKER ERROR] Prediction failed: {e}. Preserving candidates.")
                score_list = [float(c.get("score", 0.0)) for c in candidates]
        else:
            # Fallback: preserve existing scores if model unavailable
            score_list = [float(c.get("score", 0.0)) for c in candidates]

        # Attach reranker scores
        reranked_candidates: List[Dict[str, Any]] = []
        for cand, r_score in zip(candidates, score_list):
            cand_copy = dict(cand)
            prev_score = float(cand_copy.get("score", 0.0))
            cand_copy["previous_score"] = prev_score
            cand_copy["reranker_score"] = round(r_score, 5)

            # Update primary score to cross-encoder score
            cand_copy["score"] = round(r_score, 5)

            meta = dict(cand_copy.get("metadata", {}))
            meta["reranker_score"] = round(r_score, 5)
            meta["previous_score"] = prev_score
            cand_copy["metadata"] = meta

            reranked_candidates.append(cand_copy)

        # Sort descending by reranker_score
        reranked_candidates.sort(key=lambda c: c["reranker_score"], reverse=True)

        # Slice to top_k if specified
        if top_k is not None and top_k > 0:
            reranked_candidates = reranked_candidates[:top_k]

        # Update final ranks 1..N
        for rank, cand in enumerate(reranked_candidates, start=1):
            cand["rank"] = rank

        return reranked_candidates
