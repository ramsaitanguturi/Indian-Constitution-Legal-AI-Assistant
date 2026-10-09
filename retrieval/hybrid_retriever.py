"""
Configurable Hybrid Retriever Pipeline with Component Ablation Controls.
Orchestrates BM25 Lexical Search, ChromaDB Dense Vector Search,
Reciprocal Rank Fusion (RRF), Legal Entity-Aware Boost, and Cross-Encoder Reranking.
"""

import json
import os
from typing import Dict, List, Any, Optional

from config import (
    RRF_K,
    DEFAULT_TOP_K,
    RETRIEVAL_CANDIDATE_POOL,
    ENTITY_BOOST_WEIGHT,
    FINAL_TOP_K,
    PARENT_STORE_PATH,
)
from retrieval.bm25_retriever import BM25Retriever
from retrieval.dense_retriever import DenseRetriever
from retrieval.rrf import fuse
from retrieval.entity_boost import apply_entity_boost
from retrieval.reranker import CrossEncoderReranker


class HybridRetriever:
    """
    Modular Orchestrator for Multi-Stage Legal Information Retrieval.
    Supports individual component switches for rigorous ablation studies:
        - BM25 Lexical Search
        - Dense Vector Search
        - Reciprocal Rank Fusion (RRF)
        - Legal Entity-Aware Boost
        - Cross-Encoder Neural Reranking
    """

    def __init__(
        self,
        bm25_retriever: Optional[BM25Retriever] = None,
        dense_retriever: Optional[DenseRetriever] = None,
        reranker: Optional[CrossEncoderReranker] = None,
        use_bm25: bool = True,
        use_dense: bool = True,
        use_rrf: bool = True,
        use_entity_boost: bool = True,
        use_reranker: bool = True,
        top_k_candidates: int = RETRIEVAL_CANDIDATE_POOL,
        final_top_k: int = FINAL_TOP_K,
        rrf_k: int = RRF_K,
        entity_boost_weight: float = ENTITY_BOOST_WEIGHT,
        linear_alpha: float = 0.5,
        parent_store: Optional[Dict[str, Dict[str, Any]]] = None,
        auto_hydrate_parent: bool = True,
    ):
        self.use_bm25 = use_bm25
        self.use_dense = use_dense
        self.use_rrf = use_rrf
        self.use_entity_boost = use_entity_boost
        self.use_reranker = use_reranker
        self.top_k_candidates = top_k_candidates
        self.final_top_k = final_top_k
        self.rrf_k = rrf_k
        self.entity_boost_weight = entity_boost_weight
        self.linear_alpha = linear_alpha
        self.auto_hydrate_parent = auto_hydrate_parent

        # Parent Store
        self.parent_store = parent_store if parent_store is not None else {}
        if not self.parent_store and os.path.exists(PARENT_STORE_PATH):
            try:
                with open(PARENT_STORE_PATH, "r", encoding="utf-8") as f:
                    self.parent_store = json.load(f)
            except Exception:
                pass

        # Sub-components with lazy initialization
        self.bm25_retriever = bm25_retriever
        self.dense_retriever = dense_retriever
        self.reranker = reranker

    def _ensure_retrievers(self) -> None:
        """Instantiate retrievers on demand if not injected."""
        if self.use_bm25 and self.bm25_retriever is None:
            self.bm25_retriever = BM25Retriever(parent_store=self.parent_store)
            if not self.parent_store and self.bm25_retriever.parent_store:
                self.parent_store = self.bm25_retriever.parent_store

        if self.use_dense and self.dense_retriever is None:
            self.dense_retriever = DenseRetriever(parent_store=self.parent_store)

        if self.use_reranker and self.reranker is None:
            self.reranker = CrossEncoderReranker(lazy_load=True)

    @classmethod
    def from_ingestor(
        cls,
        ingestor: Any,
        use_reranker: bool = True,
        **kwargs
    ) -> "HybridRetriever":
        """Factory constructor instantiating all components from a single ingestor."""
        bm25 = BM25Retriever.from_ingestor(ingestor)
        dense = DenseRetriever.from_ingestor(ingestor)
        parent_store = getattr(ingestor, "parent_store", {})
        reranker = CrossEncoderReranker(lazy_load=True) if use_reranker else None

        return cls(
            bm25_retriever=bm25,
            dense_retriever=dense,
            reranker=reranker,
            use_reranker=use_reranker,
            parent_store=parent_store,
            **kwargs
        )

    def retrieve(
        self,
        query: str,
        entities: Optional[Any] = None,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute full retrieval pipeline with configured ablation components.

        Args:
            query: User query string.
            entities: Extracted or linked legal entities for entity-aware boosting.
            top_k: Number of final results to return (defaults to self.final_top_k).

        Returns:
            List of structured result dictionaries with uniform schema.
        """
        target_top_k = top_k if (top_k is not None and top_k > 0) else self.final_top_k

        if not query or not query.strip():
            return []

        self._ensure_retrievers()

        # Step 1: Candidate Generation (Sparse BM25)
        bm25_results: List[Dict[str, Any]] = []
        if self.use_bm25 and self.bm25_retriever is not None:
            bm25_results = self.bm25_retriever.retrieve(query, top_k=self.top_k_candidates)

        # Step 2: Candidate Generation (Dense ChromaDB)
        dense_results: List[Dict[str, Any]] = []
        if self.use_dense and self.dense_retriever is not None:
            dense_results = self.dense_retriever.retrieve(query, top_k=self.top_k_candidates)

        # Step 3: Candidate Merging / Fusion
        fused_candidates: List[Dict[str, Any]] = []
        if self.use_bm25 and self.use_dense:
            if self.use_rrf:
                fused_candidates = fuse([bm25_results, dense_results], k=self.rrf_k)
            else:
                # Genuine Linear Score Fusion: alpha * BM25_score + (1 - alpha) * Dense_score
                alpha = getattr(self, "linear_alpha", 0.5)
                candidates_map: Dict[str, Dict[str, Any]] = {}
                bm25_score_map: Dict[str, float] = {}
                dense_score_map: Dict[str, float] = {}

                for c in bm25_results:
                    cid = c.get("chunk_id", "")
                    if cid:
                        candidates_map[cid] = dict(c)
                        bm25_score_map[cid] = float(c.get("score", 0.0))

                for c in dense_results:
                    cid = c.get("chunk_id", "")
                    if cid:
                        if cid not in candidates_map:
                            candidates_map[cid] = dict(c)
                        dense_score_map[cid] = float(c.get("score", 0.0))

                # Normalize BM25 scores to [0, 1] relative to candidate pool max
                max_b = max(bm25_score_map.values()) if bm25_score_map else 1.0
                norm_b = {cid: (s / max_b if max_b > 0 else 0.0) for cid, s in bm25_score_map.items()}

                # Dense cosine similarities are in [0, 1]
                max_d = max(dense_score_map.values()) if dense_score_map else 1.0
                norm_d = {cid: (s / max_d if max_d > 0 else 0.0) for cid, s in dense_score_map.items()}

                scored_list = []
                for cid, cand in candidates_map.items():
                    sb = norm_b.get(cid, 0.0)
                    sd = norm_d.get(cid, 0.0)
                    linear_comb = round(alpha * sb + (1.0 - alpha) * sd, 4)
                    cand["score"] = linear_comb
                    cand["linear_score"] = linear_comb
                    scored_list.append(cand)

                # Rank by combined linear score descending
                fused_candidates = sorted(scored_list, key=lambda x: x.get("score", 0.0), reverse=True)
                for r_idx, c in enumerate(fused_candidates, start=1):
                    c["rank"] = r_idx
        elif self.use_bm25:
            fused_candidates = bm25_results
        elif self.use_dense:
            fused_candidates = dense_results
        else:
            return []

        if not fused_candidates:
            return []

        # Step 4: Legal Entity Boost
        if self.use_entity_boost:
            # If entities not passed explicitly, attempt extraction if legal_ner available
            if entities is None:
                try:
                    from nlp.legal_ner import get_legal_ner
                    ner = get_legal_ner()
                    entities = ner.extract_entities(query)
                except Exception:
                    entities = None

            fused_candidates = apply_entity_boost(
                fused_candidates,
                linked_entities=entities,
                boost_weight=self.entity_boost_weight,
            )

        # Step 5: Truncate candidate pool prior to reranking
        candidates_pool = fused_candidates[: self.top_k_candidates]

        # Step 6: Neural Reranking (Cross-Encoder)
        if self.use_reranker and self.reranker is not None:
            final_results = self.reranker.rerank(
                query=query,
                candidates=candidates_pool,
                top_k=target_top_k,
            )
        else:
            final_results = candidates_pool[:target_top_k]
            # Ensure final ranks are 1..N
            for rank, c in enumerate(final_results, start=1):
                c["rank"] = rank

        # Step 7: Hydrate Parent Metadata & Backward Compatibility Aliases
        for item in final_results:
            parent_id = item.get("document_id") or item.get("parent_id", "")
            if self.auto_hydrate_parent and parent_id and self.parent_store:
                parent_data = self.parent_store.get(parent_id, {})
                if parent_data:
                    item["parent_data"] = parent_data
                    meta = item.setdefault("metadata", {})
                    if isinstance(meta, dict):
                        meta["parent_data"] = parent_data

            # Guarantee backward-compatible aliases
            chunk_id = item.get("chunk_id", "")
            text = item.get("text", "")
            item["child_id"] = chunk_id
            item["child_text"] = text
            item["parent_id"] = parent_id
            if "rrf_score" not in item:
                item["rrf_score"] = item.get("score", 0.0)

        return final_results

    def retrieve_with_provenance(
        self,
        query: str,
        entities: Optional[Any] = None,
        top_k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute retrieval and return full provenance and pipeline diagnostics.

        Returns:
            Dictionary containing query, entities, results list, and provenance dictionary.
        """
        target_top_k = top_k if (top_k is not None and top_k > 0) else self.final_top_k
        results = self.retrieve(query=query, entities=entities, top_k=target_top_k)

        return {
            "query": query,
            "entities": entities or {},
            "results": results,
            "provenance": {
                "top_k_returned": len(results),
                "pipeline_config": {
                    "use_bm25": self.use_bm25,
                    "use_dense": self.use_dense,
                    "use_rrf": self.use_rrf,
                    "use_entity_boost": self.use_entity_boost,
                    "use_reranker": self.use_reranker,
                    "top_k_candidates": self.top_k_candidates,
                    "final_top_k": target_top_k,
                    "rrf_k": self.rrf_k,
                    "entity_boost_weight": self.entity_boost_weight,
                },
            },
        }
