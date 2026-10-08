"""
Unit tests for Confidence Estimation and Abstention Decision (Stage 4).
Verifies:
- Transparent multi-signal confidence estimation
- Uncalibrated heuristic disclaimer
- Explainable signal breakdown
- Multi-stage abstention triggers (router, retrieval, recovery, confidence, citations)
"""

import pytest
from rag.confidence import ConfidenceEstimator
from rag.abstention import AbstentionManager


class TestConfidenceEstimator:
    """Verifies transparent Confidence Estimator calculation."""

    def test_empty_chunks_confidence_zero(self):
        """Confidence is 0.0 with VERY_LOW level when no chunks are retrieved."""
        estimator = ConfidenceEstimator()
        res = estimator.estimate("Query", [])
        assert res["confidence_score"] == 0.0
        assert res["confidence_level"] == "VERY_LOW"
        assert res["is_calibrated"] is False
        assert "not a mathematically calibrated probability" in res["disclaimer"]

    def test_high_confidence_with_strong_signals(self):
        """Strong reranker score, matching entities, and valid citations yield HIGH confidence."""
        estimator = ConfidenceEstimator()
        ranked_chunks = [
            {"chunk_id": "c1", "rerank_score": 3.5, "text": "Article 21 life and personal liberty"},
            {"chunk_id": "c2", "rerank_score": 2.8, "text": "procedure established by law"},
            {"chunk_id": "c3", "rerank_score": 2.1, "text": "protection against arbitrary action"},
        ]
        rec_context = {
            "parents": [
                {
                    "title": "Article 21",
                    "article_number": "Article 21",
                    "supporting_children": ranked_chunks,
                }
            ]
        }
        citation_val = {"validation_score": 1.0, "valid": True}
        query_entities = {"ARTICLE": ["Article 21"]}

        res = estimator.estimate(
            query="What is Article 21?",
            ranked_chunks=ranked_chunks,
            recovered_context=rec_context,
            citation_validation=citation_val,
            query_entities=query_entities,
        )

        assert res["confidence_score"] >= 0.70
        assert res["confidence_level"] == "HIGH"
        assert res["is_calibrated"] is False

        # Verify all signals are present and explainable
        breakdown = res["signal_breakdown"]
        assert "retrieval_strength" in breakdown
        assert "evidence_count" in breakdown
        assert "entity_alignment" in breakdown
        assert "method_agreement" in breakdown
        assert "citation_integrity" in breakdown
        assert "evidence_coverage" in breakdown
        assert breakdown["evidence_count"] == 1.0  # 3 chunks

    def test_low_confidence_on_poor_retrieval(self):
        """Negative cross-encoder logits and low overlap yield LOW or VERY_LOW confidence."""
        estimator = ConfidenceEstimator()
        ranked_chunks = [
            {"chunk_id": "c1", "rerank_score": -4.0, "text": "unrelated snippet"},
        ]
        citation_val = {"validation_score": 0.2, "valid": False}

        res = estimator.estimate(
            query="What is Article 21?",
            ranked_chunks=ranked_chunks,
            citation_validation=citation_val,
        )

        assert res["confidence_score"] < 0.45
        assert res["confidence_level"] in ("LOW", "VERY_LOW")


class TestAbstentionManager:
    """Verifies safe refusal behavior across pipeline stages."""

    def test_abstain_on_router_out_of_scope(self):
        """Abstention triggers immediately if query is out-of-scope."""
        manager = AbstentionManager()
        routing_mock = {"is_out_of_scope": True, "strategy": "OUT_OF_SCOPE"}

        res = manager.evaluate("How to bake a cake?", routing_decision=routing_mock)
        assert res["should_abstain"] is True
        assert res["abstention_reason"] == "OUT_OF_SCOPE"
        assert res["abstention_stage"] == "ROUTER"
        assert "outside the scope of Indian Constitutional Law" in res["safe_response"]

    def test_abstain_on_no_retrieval_results(self):
        """Abstention triggers if retrieval returns 0 results."""
        manager = AbstentionManager()
        res = manager.evaluate("Query", retrieved_chunks=[])
        assert res["should_abstain"] is True
        assert res["abstention_reason"] == "NO_RETRIEVAL_RESULTS"
        assert res["abstention_stage"] == "RETRIEVAL"
        assert "No relevant constitutional articles" in res["safe_response"]

    def test_abstain_on_low_retrieval_confidence(self):
        """Abstention triggers if reranker score indicates extreme irrelevance."""
        manager = AbstentionManager()
        chunks = [{"chunk_id": "c1", "rerank_score": -9.5, "text": "gibberish"}]
        res = manager.evaluate("Query", retrieved_chunks=chunks)
        assert res["should_abstain"] is True
        assert res["abstention_reason"] == "LOW_RETRIEVAL_CONFIDENCE"
        assert res["abstention_stage"] == "RERANKER"

    def test_abstain_on_empty_parents(self):
        """Abstention triggers if recovered parents are empty."""
        manager = AbstentionManager()
        chunks = [{"chunk_id": "c1", "score": 0.5, "text": "snippet"}]
        rec_context = {"parents": []}
        res = manager.evaluate("Query", retrieved_chunks=chunks, recovered_context=rec_context)
        assert res["should_abstain"] is True
        assert res["abstention_reason"] == "INSUFFICIENT_EVIDENCE"
        assert res["abstention_stage"] == "CONTEXT_RECOVERY"

    def test_abstain_on_low_composite_confidence(self):
        """Abstention triggers if confidence falls below threshold."""
        manager = AbstentionManager(confidence_threshold=0.35)
        chunks = [{"chunk_id": "c1", "score": 0.1, "text": "snippet"}]
        rec_context = {"parents": [{"document_id": "doc1"}]}
        conf_result = {"confidence_score": 0.20}

        res = manager.evaluate(
            "Query",
            retrieved_chunks=chunks,
            recovered_context=rec_context,
            confidence_result=conf_result,
        )
        assert res["should_abstain"] is True
        assert res["abstention_reason"] == "LOW_CONFIDENCE"
        assert res["abstention_stage"] == "CONFIDENCE_ESTIMATOR"

    def test_abstain_on_strict_citation_failure(self):
        """Abstention triggers on citation failure when strict mode enabled."""
        manager = AbstentionManager(strict_citation_validation=True)
        chunks = [{"chunk_id": "c1", "score": 0.9, "text": "snippet"}]
        rec_context = {"parents": [{"document_id": "doc1"}]}
        citation_val = {
            "valid": False,
            "invalid_citations": [{"reason": "DOCUMENT_DOES_NOT_EXIST"}],
            "valid_citations": [],
        }

        res = manager.evaluate(
            "Query",
            retrieved_chunks=chunks,
            recovered_context=rec_context,
            citation_validation=citation_val,
        )
        assert res["should_abstain"] is True
        assert res["abstention_reason"] == "CITATION_VALIDATION_FAILURE"
        assert res["abstention_stage"] == "CITATION_VALIDATOR"
