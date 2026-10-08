"""
Unit and Integration Tests for Neural Cross-Encoder Reranker.
Verifies model loading, query-candidate scoring, candidate reordering,
top-k slicing, edge case handling, and integration into HybridRetriever.
"""

import pytest
from typing import List, Dict, Any

from config import RERANKER_MODEL_NAME, FINAL_TOP_K
from retrieval.reranker import CrossEncoderReranker
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.bm25_retriever import BM25Retriever, simple_tokenize
from rank_bm25 import BM25Okapi


@pytest.fixture(scope="module")
def shared_reranker() -> CrossEncoderReranker:
    """Instantiate a shared CrossEncoderReranker to avoid reloading model across tests."""
    return CrossEncoderReranker(model_name=RERANKER_MODEL_NAME, lazy_load=False)


@pytest.fixture
def sample_candidates() -> List[Dict[str, Any]]:
    return [
        {
            "chunk_id": "chunk_unrelated",
            "document_id": "doc_unrelated",
            "text": "The tax rate on inter-state commercial sales shall be determined by the regional finance officer.",
            "score": 0.040,
            "rank": 1,
            "doc_type": "statute",
            "metadata": {"title": "Tax Code"},
        },
        {
            "chunk_id": "chunk_privacy_article_21",
            "document_id": "doc_art_21",
            "text": "Article 21: Protection of life and personal liberty. The right to privacy is protected under Article 21.",
            "score": 0.015,
            "rank": 2,
            "doc_type": "constitution",
            "metadata": {"article_number": "Article 21", "title": "Life and Liberty"},
        },
        {
            "chunk_id": "chunk_arbitrary_procedure",
            "document_id": "doc_procedure",
            "text": "The meeting shall be convened on the second Monday of every alternate month following the general assembly.",
            "score": 0.025,
            "rank": 3,
            "doc_type": "bylaw",
            "metadata": {"title": "Meeting Rules"},
        },
    ]


class TestCrossEncoderReranker:
    """Verifies neural cross-encoder scoring, reordering, and boundary conditions."""

    def test_reranker_reordering(self, shared_reranker, sample_candidates):
        """
        Verify that a highly relevant passage initially ranked #2 (lower RRF score)
        is promoted to rank #1 by the CrossEncoder.
        """
        query = "Is privacy a fundamental right under Article 21?"
        reranked = shared_reranker.rerank(query, sample_candidates, top_k=3)

        assert len(reranked) == 3
        # Privacy chunk must be promoted to rank #1
        top_cand = reranked[0]
        assert top_cand["chunk_id"] == "chunk_privacy_article_21"
        assert top_cand["rank"] == 1
        assert "reranker_score" in top_cand
        assert isinstance(top_cand["reranker_score"], float)

        # Unrelated tax passage should have lower cross-encoder score than Article 21 passage
        tax_cand = next(c for c in reranked if c["chunk_id"] == "chunk_unrelated")
        assert top_cand["reranker_score"] > tax_cand["reranker_score"]

    def test_reranker_top_k_slicing(self, shared_reranker, sample_candidates):
        """Verify top_k parameter bounds output list length correctly."""
        query = "Article 21 privacy"
        reranked_1 = shared_reranker.rerank(query, sample_candidates, top_k=1)
        assert len(reranked_1) == 1
        assert reranked_1[0]["rank"] == 1

        reranked_all = shared_reranker.rerank(query, sample_candidates, top_k=10)
        assert len(reranked_all) == 3

    def test_reranker_empty_inputs(self, shared_reranker, sample_candidates):
        """Verify graceful handling of empty queries and candidate pools."""
        assert shared_reranker.rerank("", sample_candidates) == []
        assert shared_reranker.rerank("   ", sample_candidates) == []
        assert shared_reranker.rerank("Article 21", []) == []

    def test_schema_preservation_after_rerank(self, shared_reranker, sample_candidates):
        """Ensure standard keys and metadata are preserved after neural reranking."""
        query = "right to privacy"
        reranked = shared_reranker.rerank(query, sample_candidates, top_k=2)
        for item in reranked:
            assert "chunk_id" in item
            assert "document_id" in item
            assert "score" in item
            assert "rank" in item
            assert "text" in item
            assert "metadata" in item
            assert "reranker_score" in item
            assert "previous_score" in item
            assert item["metadata"]["reranker_score"] == item["reranker_score"]

    def test_fallback_when_model_is_none(self, sample_candidates):
        """Test fallback pass-through if model fails to load."""
        reranker = CrossEncoderReranker(model_name="invalid/nonexistent-model", lazy_load=True)
        # Mock _model as None to simulate offline/failure state
        reranker._model = None
        reranker._load_model = lambda: None

        reranked = reranker.rerank("Article 21", sample_candidates, top_k=2)
        assert len(reranked) == 2
        # Order should be preserved based on existing score
        assert reranked[0]["chunk_id"] == sample_candidates[0]["chunk_id"]


class TestHybridRetrieverRerankerIntegration:
    """Verifies end-to-end integration of CrossEncoderReranker within HybridRetriever."""

    def test_hybrid_with_reranker_enabled(self, shared_reranker):
        mock_chunks = [
            {"child_id": "c_tax", "parent_id": "p_tax", "text": "Annual income tax return filing rules.", "doc_type": "statute"},
            {"child_id": "c_art21", "parent_id": "p_art21", "text": "Article 21 guarantees personal liberty and privacy.", "doc_type": "constitution"},
        ]
        bm25_idx = BM25Okapi([simple_tokenize(c["text"]) for c in mock_chunks])
        bm25 = BM25Retriever(bm25_index=bm25_idx, child_chunks=mock_chunks)

        hybrid = HybridRetriever(
            bm25_retriever=bm25,
            dense_retriever=None,
            reranker=shared_reranker,
            use_bm25=True,
            use_dense=False,
            use_rrf=False,
            use_entity_boost=False,
            use_reranker=True,
            final_top_k=2,
        )

        results = hybrid.retrieve("personal liberty under Article 21", top_k=2)
        assert len(results) > 0
        # Article 21 chunk must be promoted to rank 1
        assert results[0]["chunk_id"] == "c_art21"
        assert results[0]["rank"] == 1
        assert "reranker_score" in results[0]
