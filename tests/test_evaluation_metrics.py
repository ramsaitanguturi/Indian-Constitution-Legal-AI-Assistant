"""
Unit tests for evaluation/metrics.py.
Validates mathematical correctness, boundary conditions, and edge cases across:
- Information Retrieval metrics (Hit@K, Recall@K, Precision@K, RR, MRR, DCG@K, NDCG@K)
- Legal Named Entity Recognition metrics (Exact span, Micro/Macro P/R/F1, all 10 categories)
- Intent Classification metrics (Accuracy, Macro/Weighted P/R/F1, Confusion Matrix)
- Canonical Entity Linking metrics (Exact ID, Out-of-KB rejection, per-type accuracy)
- Grounded RAG & Citation metrics (Validity, Precision, Coverage, Claims, Abstention)
- Query Expansion metrics (Precision, Drift rate)
"""

import pytest
import math

from evaluation.metrics import (
    hit_at_k,
    recall_at_k,
    precision_at_k,
    reciprocal_rank,
    mean_reciprocal_rank,
    dcg_at_k,
    ndcg_at_k,
    aggregate_retrieval_metrics,
    calculate_ner_metrics,
    calculate_classification_metrics,
    calculate_entity_linking_metrics,
    calculate_rag_citation_metrics,
    calculate_query_expansion_metrics,
    ALL_LEGAL_ENTITY_TYPES,
)


# =========================================================================
# 1. Retrieval Metrics Tests
# =========================================================================

class TestRetrievalMetrics:
    """Verifies mathematical formulas and edge cases for IR metrics."""

    def test_hit_at_k_normal(self):
        retrieved = ["doc_a", "doc_b", "doc_c", "doc_d"]
        relevant = {"doc_c"}
        assert hit_at_k(retrieved, relevant, k=1) == 0.0
        assert hit_at_k(retrieved, relevant, k=2) == 0.0
        assert hit_at_k(retrieved, relevant, k=3) == 1.0
        assert hit_at_k(retrieved, relevant, k=5) == 1.0

    def test_hit_at_k_edge_cases(self):
        assert hit_at_k([], {"doc_a"}, k=5) == 0.0
        assert hit_at_k(["doc_a"], set(), k=5) == 0.0
        assert hit_at_k(["doc_a"], {"doc_a"}, k=0) == 0.0
        assert hit_at_k(["doc_a"], {"doc_a"}, k=-1) == 0.0

    def test_recall_at_k_normal(self):
        retrieved = ["doc_1", "doc_2", "doc_3", "doc_4"]
        relevant = {"doc_1", "doc_3", "doc_5"}  # 3 relevant documents
        # at k=1: {doc_1} -> 1/3
        assert recall_at_k(retrieved, relevant, k=1) == pytest.approx(1/3, 0.001)
        # at k=2: {doc_1} -> 1/3
        assert recall_at_k(retrieved, relevant, k=2) == pytest.approx(1/3, 0.001)
        # at k=3: {doc_1, doc_3} -> 2/3
        assert recall_at_k(retrieved, relevant, k=3) == pytest.approx(2/3, 0.001)
        # at k=10: {doc_1, doc_3} -> 2/3
        assert recall_at_k(retrieved, relevant, k=10) == pytest.approx(2/3, 0.001)

    def test_recall_at_k_edge_cases(self):
        assert recall_at_k([], {"doc_1"}, k=5) == 0.0
        assert recall_at_k(["doc_1"], set(), k=5) == 0.0
        assert recall_at_k(["doc_1"], {"doc_1"}, k=0) == 0.0

    def test_precision_at_k_normal(self):
        retrieved = ["doc_1", "doc_2", "doc_3", "doc_4"]
        relevant = {"doc_1", "doc_3"}
        assert precision_at_k(retrieved, relevant, k=1) == 1.0  # 1/1
        assert precision_at_k(retrieved, relevant, k=2) == 0.5  # 1/2
        assert precision_at_k(retrieved, relevant, k=4) == 0.5  # 2/4

    def test_precision_at_k_edge_cases(self):
        assert precision_at_k([], {"doc_1"}, k=5) == 0.0
        assert precision_at_k(["doc_1"], set(), k=5) == 0.0
        assert precision_at_k(["doc_1"], {"doc_1"}, k=0) == 0.0

    def test_reciprocal_rank_normal(self):
        retrieved = ["doc_a", "doc_b", "doc_c"]
        assert reciprocal_rank(retrieved, {"doc_a"}) == 1.0
        assert reciprocal_rank(retrieved, {"doc_b"}) == 0.5
        assert reciprocal_rank(retrieved, {"doc_c"}) == pytest.approx(1/3, 0.001)
        assert reciprocal_rank(retrieved, {"doc_z"}) == 0.0

    def test_reciprocal_rank_edge_cases(self):
        assert reciprocal_rank([], {"doc_a"}) == 0.0
        assert reciprocal_rank(["doc_a"], set()) == 0.0

    def test_mean_reciprocal_rank(self):
        assert mean_reciprocal_rank([1.0, 0.5, 0.25]) == pytest.approx(1.75 / 3, 0.001)
        assert mean_reciprocal_rank([]) == 0.0

    def test_dcg_and_ndcg_at_k(self):
        retrieved = ["doc_1", "doc_2", "doc_3"]
        graded = {"doc_1": 2.0, "doc_2": 1.0, "doc_3": 0.0}

        # DCG@3: (2^2 - 1)/log2(2) + (2^1 - 1)/log2(3) + (2^0 - 1)/log2(4) = 3/1 + 1/1.58496 + 0
        expected_dcg = 3.0 + (1.0 / math.log2(3))
        assert dcg_at_k(retrieved, graded, k=3) == pytest.approx(expected_dcg, 0.001)

        # In this case retrieved order is already ideal, so NDCG@3 should be 1.0
        assert ndcg_at_k(retrieved, graded, k=3) == 1.0

        # Sub-optimal order: doc_2 first, doc_1 second
        subopt_retrieved = ["doc_2", "doc_1", "doc_3"]
        subopt_ndcg = ndcg_at_k(subopt_retrieved, graded, k=3)
        assert 0.0 < subopt_ndcg < 1.0

    def test_ndcg_at_k_edge_cases(self):
        assert ndcg_at_k([], {"doc_1": 1.0}, k=5) == 0.0
        assert ndcg_at_k(["doc_1"], {}, k=5) == 0.0
        assert ndcg_at_k(["doc_1"], {"doc_1": 0.0}, k=5) == 0.0  # all rels zero
        assert ndcg_at_k(["doc_1"], {"doc_1": 1.0}, k=0) == 0.0

    def test_aggregate_retrieval_metrics(self):
        q1 = {"Hit@1": 1.0, "MRR": 1.0, "NDCG@5": 1.0}
        q2 = {"Hit@1": 0.0, "MRR": 0.5, "NDCG@5": 0.5}
        agg = aggregate_retrieval_metrics([q1, q2])
        assert agg["Hit@1"] == 0.5
        assert agg["MRR"] == 0.75
        assert agg["NDCG@5"] == 0.75
        assert aggregate_retrieval_metrics([])["Hit@1"] == 0.0


# =========================================================================
# 2. Legal NER Metrics Tests
# =========================================================================

class TestNERMetrics:
    """Verifies entity-level P/R/F1 across categories and edge cases."""

    def test_ner_exact_match_perfect(self):
        gold = [
            {
                "id": "1",
                "entities": [
                    {"text": "Article 21", "label": "ARTICLE", "start": 0, "end": 10},
                    {"text": "Puttaswamy", "label": "CASE", "start": 15, "end": 25}
                ]
            }
        ]
        pred = [
            {
                "id": "1",
                "entities": [
                    {"text": "Article 21", "label": "ARTICLE", "start": 0, "end": 10},
                    {"text": "Puttaswamy", "label": "CASE", "start": 15, "end": 25}
                ]
            }
        ]
        res = calculate_ner_metrics(gold, pred, exact_span_match=True)
        assert res["micro_f1"] == 1.0
        assert res["macro_f1"] == 1.0
        assert res["per_class"]["ARTICLE"]["f1"] == 1.0
        assert res["per_class"]["CASE"]["f1"] == 1.0

    def test_ner_partial_match_and_false_positives(self):
        gold = [
            {
                "id": "1",
                "entities": [
                    {"text": "Article 21", "label": "ARTICLE", "start": 0, "end": 10},
                    {"text": "Puttaswamy", "label": "CASE", "start": 15, "end": 25}
                ]
            }
        ]
        pred = [
            {
                "id": "1",
                "entities": [
                    {"text": "Article 21", "label": "ARTICLE", "start": 0, "end": 10},
                    # Missing CASE (FN)
                    # Extra hallucinated ACT (FP)
                    {"text": "IT Act", "label": "ACT", "start": 30, "end": 36}
                ]
            }
        ]
        res = calculate_ner_metrics(gold, pred, exact_span_match=True)
        assert res["per_class"]["ARTICLE"]["precision"] == 1.0
        assert res["per_class"]["ARTICLE"]["recall"] == 1.0
        assert res["per_class"]["CASE"]["recall"] == 0.0
        assert res["per_class"]["ACT"]["precision"] == 0.0
        assert res["micro_f1"] < 1.0

    def test_ner_all_ten_categories_handled(self):
        gold = [{"id": "1", "entities": []}]
        pred = [{"id": "1", "entities": []}]
        res = calculate_ner_metrics(gold, pred)
        # All 10 legal categories must be present in output
        for cat in ALL_LEGAL_ENTITY_TYPES:
            assert cat in res["per_class"]
            assert res["per_class"][cat]["support"] == 0
            assert res["per_class"][cat]["f1"] == 0.0

    def test_ner_empty_annotations(self):
        res = calculate_ner_metrics([], [])
        assert res["micro_f1"] == 0.0
        assert res["total_gold_entities"] == 0


# =========================================================================
# 3. Intent Classification Metrics Tests
# =========================================================================

class TestIntentMetrics:
    """Verifies classification accuracy, macro F1, and confusion matrix."""

    def test_classification_perfect(self):
        y_true = ["ARTICLE_LOOKUP", "CASE_LAW_QUERY", "RIGHTS_QUERY"]
        y_pred = ["ARTICLE_LOOKUP", "CASE_LAW_QUERY", "RIGHTS_QUERY"]
        res = calculate_classification_metrics(y_true, y_pred)
        assert res["accuracy"] == 1.0
        assert res["macro_f1"] == 1.0
        assert res["sample_count"] == 3

    def test_classification_partial_imbalanced(self):
        y_true = ["ARTICLE_LOOKUP", "ARTICLE_LOOKUP", "CASE_LAW_QUERY", "OUT_OF_SCOPE"]
        y_pred = ["ARTICLE_LOOKUP", "CASE_LAW_QUERY", "CASE_LAW_QUERY", "OUT_OF_SCOPE"]
        res = calculate_classification_metrics(y_true, y_pred)
        assert res["accuracy"] == 0.75  # 3 of 4
        assert res["per_class"]["ARTICLE_LOOKUP"]["recall"] == 0.5  # 1 of 2
        assert res["per_class"]["CASE_LAW_QUERY"]["precision"] == 0.5  # 1 of 2
        assert res["per_class"]["OUT_OF_SCOPE"]["f1"] == 1.0

    def test_classification_empty_and_mismatched(self):
        assert calculate_classification_metrics([], [])["accuracy"] == 0.0
        with pytest.raises(AssertionError):
            calculate_classification_metrics(["A"], ["A", "B"])


# =========================================================================
# 4. Canonical Entity Linking Metrics Tests
# =========================================================================

class TestEntityLinkingMetrics:
    """Verifies canonical entity linking accuracy and out-of-KB rejection."""

    def test_entity_linking_normal(self):
        gold = [
            {"id": "1", "entity_type": "ARTICLE", "expected_canonical_id": "ARTICLE_21"},
            {"id": "2", "entity_type": "CASE", "expected_canonical_id": "CASE_PUTTASWAMY_2017"},
            {"id": "3", "entity_type": "UNKNOWN", "expected_canonical_id": None}  # Out-of-KB
        ]
        pred = [
            {"id": "1", "predicted_canonical_id": "ARTICLE_21"},
            {"id": "2", "predicted_canonical_id": "CASE_PUTTASWAMY_2017"},
            {"id": "3", "predicted_canonical_id": None}  # Correctly rejected
        ]
        res = calculate_entity_linking_metrics(gold, pred)
        assert res["exact_linking_accuracy"] == 1.0
        assert res["out_of_kb_rejection_accuracy"] == 1.0
        assert res["per_entity_type"]["ARTICLE"]["accuracy"] == 1.0
        assert res["per_entity_type"]["UNKNOWN"]["accuracy"] == 1.0

    def test_entity_linking_failure_modes(self):
        gold = [
            {"id": "1", "entity_type": "ARTICLE", "expected_canonical_id": "ARTICLE_21"},
            {"id": "2", "entity_type": "UNKNOWN", "expected_canonical_id": None}
        ]
        pred = [
            {"id": "1", "predicted_canonical_id": "ARTICLE_14"},  # Wrong ID
            {"id": "2", "predicted_canonical_id": "ARTICLE_99"}   # Hallucinated ID for unknown
        ]
        res = calculate_entity_linking_metrics(gold, pred)
        assert res["exact_linking_accuracy"] == 0.0
        assert res["out_of_kb_rejection_accuracy"] == 0.0

    def test_entity_linking_empty(self):
        res = calculate_entity_linking_metrics([], [])
        assert res["exact_linking_accuracy"] == 0.0


# =========================================================================
# 5. RAG & Citation Metrics Tests
# =========================================================================

class TestRAGCitationsMetrics:
    """Verifies citation validity, evidence coverage, and abstention accuracy."""

    def test_rag_citation_metrics_normal(self):
        runs = [
            {
                "citations_checked": 2,
                "valid_citations_count": 2,
                "retrieved_evidence_count": 4,
                "cited_evidence_count": 2,
                "supported_claims_count": 2,
                "unsupported_claims_count": 0,
                "expected_action": "answer",
                "actual_action": "answer"
            },
            {
                "citations_checked": 0,
                "valid_citations_count": 0,
                "retrieved_evidence_count": 0,
                "cited_evidence_count": 0,
                "supported_claims_count": 0,
                "unsupported_claims_count": 0,
                "expected_action": "abstain",
                "actual_action": "abstain"
            }
        ]
        res = calculate_rag_citation_metrics(runs)
        assert res["citation_validity_rate"] == 1.0
        assert res["citation_precision"] == 1.0
        assert res["evidence_coverage"] == 0.5  # 2 of 4
        assert res["supported_claim_rate"] == 1.0
        assert res["abstention_accuracy"] == 1.0
        assert "Notice: Structural citation validation" in res["structural_vs_semantic_note"]

    def test_rag_citation_metrics_empty(self):
        res = calculate_rag_citation_metrics([])
        assert res["citation_validity_rate"] == 0.0
        assert res["sample_count"] == 0


# =========================================================================
# 6. Query Expansion Metrics Tests
# =========================================================================

class TestQueryExpansionMetrics:
    """Verifies query expansion precision and drift rate."""

    def test_query_expansion_normal(self):
        records = [
            {
                "expanded_terms": ["right to privacy", "Article 21"],
                "expected_useful_terms": ["right to privacy", "Article 21", "personal liberty"],
                "distractor_terms": ["income tax"]
            }
        ]
        res = calculate_query_expansion_metrics(records)
        assert res["expansion_precision"] == 1.0
        assert res["drift_rate"] == 0.0
        assert res["average_terms_added"] == 2.0

    def test_query_expansion_empty(self):
        res = calculate_query_expansion_metrics([])
        assert res["expansion_precision"] == 0.0
