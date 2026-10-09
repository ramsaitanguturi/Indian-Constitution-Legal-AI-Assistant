"""
Comprehensive Unit and Integration Tests for Stage 3 Retrieval Upgrade.
Validates standardized schemas, BM25Retriever, DenseRetriever, RRF fusion math,
Entity-Aware Boost with explainability logs, and HybridRetriever ablations.
"""

import pytest
from typing import Dict, List, Any

from config import (
    RRF_K,
    ENTITY_BOOST_WEIGHT,
    FINAL_TOP_K,
    RETRIEVAL_CANDIDATE_POOL,
)
from retrieval.bm25_retriever import BM25Retriever, simple_tokenize
from retrieval.dense_retriever import DenseRetriever
from retrieval.rrf import fuse, get_candidate_key
from retrieval.entity_boost import apply_entity_boost, _parse_entities
from retrieval.hybrid_retriever import HybridRetriever
from rank_bm25 import BM25Okapi


# Standard schema keys that MUST be present on every returned candidate
REQUIRED_SCHEMA_KEYS = {
    "document_id",
    "chunk_id",
    "score",
    "rank",
    "text",
    "doc_type",
    "metadata",
}

BACKWARD_COMPAT_KEYS = {
    "child_id",
    "child_text",
    "parent_id",
}


# =========================================================================
# Mock Fixtures for Fast and Deterministic Unit Testing
# =========================================================================

@pytest.fixture
def mock_chunks() -> List[Dict[str, Any]]:
    return [
        {
            "child_id": "child_art_21_0",
            "parent_id": "parent_art_21",
            "text": "Article 21: Protection of life and personal liberty. No person shall be deprived of his life or personal liberty.",
            "doc_type": "constitution",
            "article_number": "Article 21",
            "title": "Protection of Life and Personal Liberty",
        },
        {
            "child_id": "child_art_19_0",
            "parent_id": "parent_art_19",
            "text": "Article 19: Protection of certain rights regarding freedom of speech and expression.",
            "doc_type": "constitution",
            "article_number": "Article 19",
            "title": "Protection of Freedom of Speech",
        },
        {
            "child_id": "child_puttaswamy_0",
            "parent_id": "parent_puttaswamy",
            "text": "Justice K.S. Puttaswamy v. Union of India. The right to privacy is protected as an intrinsic part of the right to life under Article 21.",
            "doc_type": "judgment",
            "case_name": "Justice K.S. Puttaswamy v. Union of India",
            "year": 2017,
            "title": "Puttaswamy Privacy Judgment",
        },
        {
            "child_id": "child_kesavananda_0",
            "parent_id": "parent_kesavananda",
            "text": "Kesavananda Bharati v. State of Kerala. Parliament cannot alter the basic structure of the Constitution under Article 368.",
            "doc_type": "judgment",
            "case_name": "Kesavananda Bharati v. State of Kerala",
            "year": 1973,
            "title": "Basic Structure Doctrine",
        },
    ]


@pytest.fixture
def mock_parent_store() -> Dict[str, Dict[str, Any]]:
    return {
        "parent_art_21": {
            "document_id": "art_21",
            "article_number": "Article 21",
            "title": "Protection of Life and Personal Liberty",
            "doc_type": "constitution",
            "raw_text": "No person shall be deprived of his life or personal liberty.",
        },
        "parent_art_19": {
            "document_id": "art_19",
            "article_number": "Article 19",
            "title": "Protection of Freedom of Speech",
            "doc_type": "constitution",
            "raw_text": "All citizens shall have the right to freedom of speech and expression.",
        },
        "parent_puttaswamy": {
            "document_id": "case_puttaswamy",
            "case_name": "Justice K.S. Puttaswamy v. Union of India",
            "year": 2017,
            "citation": "(2017) 10 SCC 1",
            "doc_type": "judgment",
        },
        "parent_kesavananda": {
            "document_id": "case_kesavananda",
            "case_name": "Kesavananda Bharati v. State of Kerala",
            "year": 1973,
            "citation": "(1973) 4 SCC 225",
            "doc_type": "judgment",
        },
    }


@pytest.fixture
def mock_bm25_retriever(mock_chunks, mock_parent_store) -> BM25Retriever:
    tokenized = [simple_tokenize(c["text"]) for c in mock_chunks]
    bm25_idx = BM25Okapi(tokenized)
    return BM25Retriever(
        bm25_index=bm25_idx,
        child_chunks=mock_chunks,
        parent_store=mock_parent_store,
    )


# =========================================================================
# 1. Standard Result Schema Verification
# =========================================================================

class TestStandardResultSchema:
    """Verifies that all retrieval outputs adhere strictly to the standardized dictionary schema."""

    def test_bm25_result_schema(self, mock_bm25_retriever):
        results = mock_bm25_retriever.retrieve("Article 21 privacy", top_k=2)
        assert len(results) > 0
        for item in results:
            # Check all standardized keys
            for key in REQUIRED_SCHEMA_KEYS:
                assert key in item, f"Missing required schema key: {key}"
            # Check backward-compatibility keys
            for key in BACKWARD_COMPAT_KEYS:
                assert key in item, f"Missing backward compatibility key: {key}"
            assert isinstance(item["score"], float)
            assert isinstance(item["rank"], int)
            assert isinstance(item["metadata"], dict)
            assert item["rank"] >= 1
            assert 0.0 <= item["score"] <= 1.0

    def test_rrf_result_schema(self):
        sample_list1 = [
            {"chunk_id": "c1", "document_id": "p1", "text": "text1", "score": 0.9, "rank": 1, "doc_type": "art", "metadata": {}},
        ]
        sample_list2 = [
            {"chunk_id": "c1", "document_id": "p1", "text": "text1", "score": 0.8, "rank": 1, "doc_type": "art", "metadata": {}},
        ]
        fused = fuse([sample_list1, sample_list2], k=60)
        assert len(fused) == 1
        item = fused[0]
        for key in REQUIRED_SCHEMA_KEYS:
            assert key in item
        assert "rrf_score" in item
        assert item["rank"] == 1


# =========================================================================
# 2. Standalone BM25 Retriever Tests
# =========================================================================

class TestBM25Retriever:
    """Verifies lexical BM25 retrieval, score normalization, and boundary handling."""

    def test_retrieve_matching_query(self, mock_bm25_retriever):
        results = mock_bm25_retriever.retrieve("privacy Puttaswamy", top_k=3)
        assert len(results) >= 1
        top_hit = results[0]
        assert "puttaswamy" in top_hit["chunk_id"].lower() or "art_21" in top_hit["chunk_id"].lower()
        # Top score must be normalized to 1.0
        assert top_hit["score"] == 1.0
        assert top_hit["rank"] == 1

    def test_retrieve_score_ordering(self, mock_bm25_retriever):
        results = mock_bm25_retriever.retrieve("liberty speech", top_k=4)
        scores = [r["score"] for r in results]
        # Descending order verification
        assert scores == sorted(scores, reverse=True)
        # Ranks must be 1, 2, ...
        ranks = [r["rank"] for r in results]
        assert ranks == list(range(1, len(results) + 1))

    def test_retrieve_out_of_vocabulary(self, mock_bm25_retriever):
        results = mock_bm25_retriever.retrieve("nonexistentrandomgibberishwordxyz123", top_k=5)
        assert results == []

    def test_retrieve_empty_query(self, mock_bm25_retriever):
        assert mock_bm25_retriever.retrieve("", top_k=5) == []
        assert mock_bm25_retriever.retrieve("   ", top_k=5) == []
        assert mock_bm25_retriever.retrieve("!@#$%", top_k=5) == []

    def test_retrieve_zero_or_negative_top_k(self, mock_bm25_retriever):
        assert mock_bm25_retriever.retrieve("Article 21", top_k=0) == []
        assert mock_bm25_retriever.retrieve("Article 21", top_k=-2) == []


# =========================================================================
# 3. Standalone Dense Retriever Tests
# =========================================================================

class MockChromaCollection:
    """Mock ChromaDB collection for isolated DenseRetriever testing."""
    def __init__(self, count: int = 2):
        self._count = count

    def count(self) -> int:
        return self._count

    def query(self, query_texts: List[str], n_results: int, include: Any = None) -> Dict[str, Any]:
        return {
            "ids": [["child_art_21_0", "child_art_19_0"][:n_results]],
            "documents": [["Article 21 text...", "Article 19 text..."][:n_results]],
            "metadatas": [[
                {"parent_id": "parent_art_21", "article_number": "Article 21", "doc_type": "constitution"},
                {"parent_id": "parent_art_19", "article_number": "Article 19", "doc_type": "constitution"},
            ][:n_results]],
            "distances": [[0.25, 0.40][:n_results]],
        }


class TestDenseRetriever:
    """Verifies dense vector retrieval, cosine similarity score conversion, and boundaries."""

    def test_retrieve_normal_query(self, mock_parent_store):
        mock_col = MockChromaCollection(count=2)
        dense = DenseRetriever(collection=mock_col, parent_store=mock_parent_store)
        results = dense.retrieve("right to life", top_k=2)

        assert len(results) == 2
        for item in results:
            for key in REQUIRED_SCHEMA_KEYS:
                assert key in item
            for key in BACKWARD_COMPAT_KEYS:
                assert key in item

        # Cosine similarity score conversion: 1 - 0.25 = 0.75, 1 - 0.40 = 0.60
        assert results[0]["score"] == 0.75
        assert results[0]["rank"] == 1
        assert results[0]["chunk_id"] == "child_art_21_0"
        assert results[0]["vector_rank"] == 1

        assert results[1]["score"] == 0.60
        assert results[1]["rank"] == 2
        assert results[1]["chunk_id"] == "child_art_19_0"

    def test_retrieve_empty_query(self, mock_parent_store):
        mock_col = MockChromaCollection(count=2)
        dense = DenseRetriever(collection=mock_col, parent_store=mock_parent_store)
        assert dense.retrieve("", top_k=2) == []
        assert dense.retrieve("   ", top_k=2) == []

    def test_retrieve_empty_collection(self, mock_parent_store):
        mock_col = MockChromaCollection(count=0)
        dense = DenseRetriever(collection=mock_col, parent_store=mock_parent_store)
        assert dense.retrieve("Article 21", top_k=2) == []


# =========================================================================
# 4. Reciprocal Rank Fusion (RRF) Tests
# =========================================================================

class TestReciprocalRankFusion:
    """Verifies mathematical correctness of score fusion, rank preservation, and deduplication."""

    def test_exact_mathematical_rrf_calculation(self):
        """
        Formula: sum(1.0 / (k + rank))
        Given k = 60:
        List 1: docA (rank 1), docB (rank 2)
        List 2: docA (rank 2), docC (rank 1)
        docA score = 1/(60+1) + 1/(60+2) = 1/61 + 1/62 = 0.01639344 + 0.01612903 = 0.032522
        docC score = 1/(60+1) = 1/61 = 0.016393
        docB score = 1/(60+2) = 1/62 = 0.016129
        """
        list1 = [
            {"chunk_id": "docA", "rank": 1, "text": "A"},
            {"chunk_id": "docB", "rank": 2, "text": "B"},
        ]
        list2 = [
            {"chunk_id": "docC", "rank": 1, "text": "C"},
            {"chunk_id": "docA", "rank": 2, "text": "A"},
        ]
        fused = fuse([list1, list2], k=60)
        assert len(fused) == 3

        # docA must be ranked #1
        assert fused[0]["chunk_id"] == "docA"
        expected_score_a = round((1.0 / 61.0) + (1.0 / 62.0), 6)
        assert abs(fused[0]["score"] - expected_score_a) < 1e-5
        assert fused[0]["rank"] == 1

        # docC must be ranked #2
        assert fused[1]["chunk_id"] == "docC"
        expected_score_c = round(1.0 / 61.0, 6)
        assert abs(fused[1]["score"] - expected_score_c) < 1e-5
        assert fused[1]["rank"] == 2

        # docB must be ranked #3
        assert fused[2]["chunk_id"] == "docB"
        expected_score_b = round(1.0 / 62.0, 6)
        assert abs(fused[2]["score"] - expected_score_b) < 1e-5
        assert fused[2]["rank"] == 3

    def test_single_list_fusion(self):
        single_list = [
            {"chunk_id": "doc1", "rank": 1, "text": "1"},
            {"chunk_id": "doc2", "rank": 2, "text": "2"},
        ]
        fused = fuse([single_list], k=60)
        assert len(fused) == 2
        assert fused[0]["chunk_id"] == "doc1"
        assert fused[1]["chunk_id"] == "doc2"
        assert fused[0]["score"] > fused[1]["score"]

    def test_empty_lists_handling(self):
        assert fuse([]) == []
        assert fuse([[], []]) == []
        assert fuse([[{"chunk_id": "c1", "rank": 1, "text": "t"}]]) != []

    def test_custom_k_parameter(self):
        list1 = [{"chunk_id": "c1", "rank": 1, "text": "t"}]
        fused_k20 = fuse([list1], k=20)
        fused_k60 = fuse([list1], k=60)
        assert fused_k20[0]["score"] == round(1.0 / (20 + 1), 6)
        assert fused_k60[0]["score"] == round(1.0 / (60 + 1), 6)
        assert fused_k20[0]["score"] > fused_k60[0]["score"]


# =========================================================================
# 4. Entity-Aware Ranking Boost Tests
# =========================================================================

class TestEntityAwareBoost:
    """Verifies that entity matching properly boosts candidate scores with explainable logging."""

    def test_article_entity_boost(self):
        candidates = [
            {
                "chunk_id": "c_other",
                "score": 0.020,
                "rank": 1,
                "metadata": {"article_number": "Article 19", "title": "Freedom of Speech"},
            },
            {
                "chunk_id": "c_art21",
                "score": 0.015,
                "rank": 2,
                "metadata": {"article_number": "Article 21", "title": "Life and Liberty"},
            },
        ]
        entities = {"articles": ["Article 21"], "cases": [], "concepts": []}
        boosted = apply_entity_boost(candidates, linked_entities=entities, boost_weight=0.15)

        # c_art21 was originally rank 2, but received +0.15 boost, so it must now be rank 1
        assert boosted[0]["chunk_id"] == "c_art21"
        assert boosted[0]["rank"] == 1
        assert boosted[0]["boost_applied"] == 0.15
        assert len(boosted[0]["boost_reasons"]) >= 1
        assert "Article 21" in boosted[0]["boost_reasons"][0]

        # c_other had no match, so boost_applied == 0.0
        assert boosted[1]["chunk_id"] == "c_other"
        assert boosted[1]["rank"] == 2
        assert boosted[1]["boost_applied"] == 0.0

    def test_case_entity_boost(self):
        candidates = [
            {
                "chunk_id": "c1",
                "score": 0.020,
                "rank": 1,
                "metadata": {"case_name": "Minerva Mills v. Union of India"},
            },
            {
                "chunk_id": "c2",
                "score": 0.018,
                "rank": 2,
                "metadata": {"case_name": "Justice K.S. Puttaswamy v. Union of India"},
            },
        ]
        entities = {"articles": [], "cases": ["Puttaswamy"], "concepts": []}
        boosted = apply_entity_boost(candidates, linked_entities=entities, boost_weight=0.15)

        assert boosted[0]["chunk_id"] == "c2"
        assert boosted[0]["boost_applied"] == 0.15
        assert any("Puttaswamy" in r for r in boosted[0]["boost_reasons"])

    def test_linked_entity_records_input(self):
        """Verify boost works when passed list of dicts from EntityLinker."""
        candidates = [
            {
                "chunk_id": "c_kesav",
                "document_id": "parent_kesavananda",
                "score": 0.010,
                "rank": 1,
                "metadata": {"case_name": "Kesavananda Bharati", "title": "Basic Structure"},
            }
        ]
        linked_list = [
            {
                "entity_id": "CASE_KESAVANANDA_1973",
                "canonical_name": "Kesavananda Bharati v. State of Kerala",
                "entity_type": "CASE",
                "surface_form": "Kesavananda",
            }
        ]
        boosted = apply_entity_boost(candidates, linked_entities=linked_list, boost_weight=0.15)
        assert boosted[0]["boost_applied"] == 0.15
        assert boosted[0]["score"] == round(0.010 + 0.15, 5)

    def test_empty_entities_preserves_ordering(self):
        candidates = [
            {"chunk_id": "c1", "score": 0.02, "rank": 1, "metadata": {}},
            {"chunk_id": "c2", "score": 0.01, "rank": 2, "metadata": {}},
        ]
        boosted = apply_entity_boost(candidates, linked_entities=None)
        assert [c["chunk_id"] for c in boosted] == ["c1", "c2"]
        assert boosted[0]["boost_applied"] == 0.0


# =========================================================================
# 5. Hybrid Retriever Orchestration & Ablation Tests
# =========================================================================

class TestHybridRetrieverAblations:
    """Verifies that individual component toggles work cleanly without runtime errors."""

    def test_bm25_only_ablation(self, mock_bm25_retriever, mock_parent_store):
        """Ablation: use_bm25=True, use_dense=False, use_reranker=False."""
        hybrid = HybridRetriever(
            bm25_retriever=mock_bm25_retriever,
            dense_retriever=None,
            reranker=None,
            use_bm25=True,
            use_dense=False,
            use_rrf=False,
            use_entity_boost=False,
            use_reranker=False,
            parent_store=mock_parent_store,
        )
        results = hybrid.retrieve("Article 21 privacy", top_k=2)
        assert len(results) > 0
        assert len(results) <= 2
        for item in results:
            for key in REQUIRED_SCHEMA_KEYS:
                assert key in item
            assert item["parent_data"] != {}

    def test_both_disabled_returns_empty(self, mock_parent_store):
        """Ablation: use_bm25=False, use_dense=False."""
        hybrid = HybridRetriever(
            use_bm25=False,
            use_dense=False,
            use_reranker=False,
            parent_store=mock_parent_store,
        )
        results = hybrid.retrieve("Article 21", top_k=2)
        assert results == []

    def test_hybrid_with_entity_boost_ablation(self, mock_bm25_retriever, mock_parent_store):
        """Ablation: BM25 + Entity Boost enabled."""
        hybrid = HybridRetriever(
            bm25_retriever=mock_bm25_retriever,
            use_bm25=True,
            use_dense=False,
            use_rrf=False,
            use_entity_boost=True,
            use_reranker=False,
            entity_boost_weight=0.20,
            parent_store=mock_parent_store,
        )
        entities = {"articles": ["Article 21"], "cases": [], "concepts": []}
        results = hybrid.retrieve("Protection of life", entities=entities, top_k=3)
        assert len(results) > 0
        top_doc = results[0]
        assert "art_21" in top_doc["chunk_id"].lower()
        assert top_doc["boost_applied"] > 0.0

    def test_retrieve_with_provenance_diagnostics(self, mock_bm25_retriever, mock_parent_store):
        """Verifies diagnostic provenance report."""
        hybrid = HybridRetriever(
            bm25_retriever=mock_bm25_retriever,
            use_bm25=True,
            use_dense=False,
            use_rrf=False,
            use_entity_boost=False,
            use_reranker=False,
            parent_store=mock_parent_store,
        )
        output = hybrid.retrieve_with_provenance("freedom of speech", top_k=2)
        assert "query" in output
        assert "results" in output
        assert "provenance" in output
        prov = output["provenance"]
        assert "pipeline_config" in prov
        assert prov["pipeline_config"]["use_bm25"] is True
        assert prov["pipeline_config"]["use_dense"] is False

    def test_bm25_dense_linear_fusion(self, mock_bm25_retriever, mock_parent_store):
        """Verifies that non-RRF linear combination genuinely merges BM25 and dense scores."""
        mock_col = MockChromaCollection(count=2)
        dense = DenseRetriever(collection=mock_col, parent_store=mock_parent_store)
        hybrid = HybridRetriever(
            bm25_retriever=mock_bm25_retriever,
            dense_retriever=dense,
            use_bm25=True,
            use_dense=True,
            use_rrf=False,
            use_entity_boost=False,
            use_reranker=False,
            linear_alpha=0.5,
            parent_store=mock_parent_store,
        )
        results = hybrid.retrieve("Article 21", top_k=2)
        assert len(results) > 0
        for item in results:
            assert "score" in item
            assert 0.0 <= item["score"] <= 1.0
