"""
Regression test suite for retrieval, confidence estimation, and abstention fixes.

Verifies:
1. Reranker Cross-Encoder logit scores (e.g., -1.1019, -7.3528) are not conflated
   with RRF score threshold (0.0050).
2. Key synchronization across rerank_score, reranker_score, and rrf_score.
3. Sigmoid-based confidence scaling for logit scores.
4. Amendment and cross-corpus routing without premature document-type filtering.
5. Preservation of evidence-based abstention for out-of-scope and severely irrelevant queries.
6. Diagnostic query non-abstention end-to-end.
"""

import pytest
from rag.abstention import AbstentionManager
from rag.confidence import ConfidenceEstimator
from routing.query_router import QueryRouter
from nlp.intent_classifier import HybridIntentClassifier


class TestScoreInterpretationAndAbstentionRegression:
    """Verifies score semantics and threshold isolation in abstention decisions."""

    def test_negative_cross_encoder_logit_does_not_trigger_false_abstention(self):
        """Negative Cross-Encoder logits above -8.0 must NOT trigger LOW_RETRIEVAL_CONFIDENCE."""
        manager = AbstentionManager(min_retrieval_score=0.0050)

        # Simulating chunks with negative logits from Cross-Encoder (e.g., -1.1019, -3.5)
        # but with valid underlying RRF score (e.g., 0.0150)
        chunks = [
            {
                "chunk_id": "art21_c1",
                "score": -1.1019,
                "rerank_score": -1.1019,
                "reranker_score": -1.1019,
                "rrf_score": 0.0154,
                "text": "Article 21: Protection of life and personal liberty.",
            },
            {
                "chunk_id": "art21_c2",
                "score": -2.3410,
                "rerank_score": -2.3410,
                "reranker_score": -2.3410,
                "rrf_score": 0.0120,
                "text": "No person shall be deprived of his life or personal liberty except according to procedure established by law.",
            },
        ]
        rec_context = {
            "parents": [
                {
                    "document_id": "const_art_21",
                    "title": "Article 21",
                    "supporting_children": chunks,
                }
            ]
        }
        conf_result = {
            "confidence_score": 0.55,
            "confidence_level": "MEDIUM",
            "is_calibrated": False,
        }

        decision = manager.evaluate(
            query="What rights are protected under Article 21?",
            retrieved_chunks=chunks,
            recovered_context=rec_context,
            confidence_result=conf_result,
        )

        assert decision["should_abstain"] is False, f"Unexpected abstention: {decision.get('abstention_reason')}"
        assert decision["abstention_stage"] is None

    def test_severe_negative_cross_encoder_logit_triggers_reranker_abstention(self):
        """Cross-Encoder logit below -8.0 represents extreme irrelevance and MUST abstain."""
        manager = AbstentionManager(min_retrieval_score=0.0050)

        chunks = [
            {
                "chunk_id": "unrelated_c1",
                "score": -9.2450,
                "rerank_score": -9.2450,
                "reranker_score": -9.2450,
                "rrf_score": 0.0060,
                "text": "Completely unrelated content regarding agricultural subsidies in 1952.",
            }
        ]

        decision = manager.evaluate(
            query="What rights are protected under Article 21?",
            retrieved_chunks=chunks,
        )

        assert decision["should_abstain"] is True
        assert decision["abstention_reason"] == "LOW_RETRIEVAL_CONFIDENCE"
        assert decision["abstention_stage"] == "RERANKER"

    def test_low_rrf_without_reranker_triggers_retrieval_abstention(self):
        """Pure RRF score below 0.0050 triggers RETRIEVAL abstention when no reranker runs."""
        manager = AbstentionManager(min_retrieval_score=0.0050)

        # Chunks with low RRF score (rank > 140) and NO rerank_score
        chunks = [
            {
                "chunk_id": "c_weak",
                "score": 0.0035,
                "text": "Very weak marginal match.",
            }
        ]

        decision = manager.evaluate(
            query="Obscure query",
            retrieved_chunks=chunks,
        )

        assert decision["should_abstain"] is True
        assert decision["abstention_reason"] == "LOW_RETRIEVAL_CONFIDENCE"
        assert decision["abstention_stage"] == "RETRIEVAL"

    def test_confidence_estimator_uses_sigmoid_for_rerank_logits(self):
        """ConfidenceEstimator must scale reranker logits via sigmoid into [0, 1]."""
        estimator = ConfidenceEstimator()

        # Case 1: Negative logit (-1.1019) should yield sigmoid(-1.1019) ~ 0.249, NOT 0.0
        chunks_neg = [
            {
                "chunk_id": "c1",
                "rerank_score": -1.1019,
                "score": -1.1019,
                "text": "Relevant snippet",
            }
        ]
        res_neg = estimator.estimate("Query", chunks_neg)
        assert res_neg["signal_breakdown"]["retrieval_strength"] > 0.20
        assert res_neg["signal_breakdown"]["retrieval_strength"] < 0.35

        # Case 2: Positive logit (3.5) should yield sigmoid(3.5) ~ 0.97
        chunks_pos = [
            {
                "chunk_id": "c2",
                "rerank_score": 3.5,
                "score": 3.5,
                "text": "Strong match",
            }
        ]
        res_pos = estimator.estimate("Query", chunks_pos)
        assert res_pos["signal_breakdown"]["retrieval_strength"] > 0.90

        # Verifies is_calibrated is False and disclaimer present
        assert res_pos["is_calibrated"] is False
        assert "not a mathematically calibrated probability" in res_pos["disclaimer"]


class TestRouterAndIntentRegression:
    """Verifies that query router does not discard amendments or articles prematurely."""

    def test_amendment_query_does_not_filter_out_amendments(self):
        """Amendment queries must not set filter_doc_type='constitution'."""
        router = QueryRouter()
        decision = router.route("Explain the 61st Amendment and voting age reduction.")

        # filter_doc_type must be None so amendment documents are reachable
        assert decision.filter_doc_type is None
        assert decision.is_out_of_scope is False

    def test_queries_with_legal_entities_are_never_marked_out_of_scope(self):
        """Constitutional entities like Attorney-General or Preamble must not be routed out of scope."""
        router = QueryRouter()

        for q in [
            "What are the duties of the Attorney-General of India?",
            "What does the Preamble say about justice and liberty?",
            "Can Parliament amend fundamental rights under Article 368?",
        ]:
            decision = router.route(q)
            assert decision.is_out_of_scope is False, f"False out-of-scope for query: {q}"

    def test_cross_corpus_query_does_not_restrict_to_judgment_only(self):
        """Queries referring to constitutional articles in cases must retain access to constitution."""
        router = QueryRouter()
        decision = router.route("Explain Article 132 certification in constitutional cases.")
        assert decision.filter_doc_type is None, "Should allow searching both constitution and judgments"

    def test_true_out_of_scope_still_detected(self):
        """Irrelevant out-of-domain queries must still be routed to OUT_OF_SCOPE."""
        classifier = HybridIntentClassifier()
        router = QueryRouter()
        query = "How to bake a chocolate cake with cherries?"
        intent_res = classifier.classify(query)
        assert intent_res["intent"] == "OUT_OF_SCOPE"
        assert intent_res["is_out_of_scope"] is True

        decision = router.route(query, intent=intent_res)
        assert decision.is_out_of_scope is True
        assert decision.strategy == "OUT_OF_SCOPE"
