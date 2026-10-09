"""
Comprehensive Integration Tests for Stage 5 Evaluation Framework.

Validates:
1. RetrievalEvaluator (loading, partitioning, ablation flags, edge cases, missing labels)
2. NEREvaluator (benchmark loading, span extraction, per-class breakdown)
3. IntentEvaluator (zero-leakage train/test split, Rule vs ML vs Hybrid, K-fold CV)
4. EntityLinkingEvaluator (canonical IDs, nil handling)
5. RAGEvaluator (citation integrity, abstention, query expansion)
6. ReportGenerator (JSON, CSV, Markdown generation and reproducibility)
7. BenchmarkRunner (orchestrator execution in quick mode)
"""

import os
import json
import tempfile
import pytest
from pathlib import Path

from evaluation.metrics import aggregate_retrieval_metrics
from evaluation.retrieval_eval import RetrievalEvaluator
from evaluation.ner_eval import NEREvaluator
from evaluation.intent_eval import IntentEvaluator
from evaluation.entity_linking_eval import EntityLinkingEvaluator
from evaluation.rag_eval import RAGEvaluator
from evaluation.report_generator import ReportGenerator
from evaluation.benchmark_runner import BenchmarkRunner
from nlp.legal_ner import get_legal_ner
from nlp.entity_linking import get_entity_linker


# =========================================================================
# Mock Retriever Fixture
# =========================================================================

class MockRetriever:
    """Lightweight mock retriever returning deterministic documents for testing."""

    def __init__(self, return_docs=None):
        self.return_docs = ["parent_const_art_21", "parent_case_puttaswamy"] if return_docs is None else return_docs

    def retrieve(self, query: str, top_k: int = 5):
        results = []
        for rank, doc_id in enumerate(self.return_docs[:top_k], start=1):
            results.append({
                "parent_id": doc_id,
                "chunk_id": f"child_{doc_id}_0",
                "score": 1.0 / rank,
                "rank": rank
            })
        return results


# =========================================================================
# 1. Retrieval Evaluator Tests
# =========================================================================

class TestRetrievalEvaluator:
    """Verifies IR evaluation harness and boundary handling."""

    def test_benchmark_loading_and_partitioning(self):
        evaluator = RetrievalEvaluator()
        assert len(evaluator.queries) > 0
        evaluable, queued = evaluator.get_evaluable_queries()
        assert len(evaluable) > 0
        assert len(queued) > 0
        # Check that queued records are explicitly flagged
        for q in queued:
            assert q.get("human_annotation_status") == "requires_human_annotation" or len(q.get("relevant_documents", [])) == 0

    def test_evaluate_retriever_mock(self):
        evaluator = RetrievalEvaluator()
        mock = MockRetriever(return_docs=["parent_const_art_32", "parent_const_art_21"])
        res = evaluator.evaluate_retriever(mock, experiment_name="mock_test", top_k=5)

        assert res["status"] == "COMPLETED"
        assert res["sample_count"] > 0
        assert "Hit@5" in res["metrics"]
        assert "MRR" in res["metrics"]
        assert "NDCG@5" in res["metrics"]
        assert len(res["query_details"]) == res["sample_count"]

    def test_evaluate_retriever_empty_results(self):
        evaluator = RetrievalEvaluator()
        mock_empty = MockRetriever(return_docs=[])
        res = evaluator.evaluate_retriever(mock_empty, experiment_name="mock_empty", top_k=5)
        assert res["status"] == "COMPLETED"
        assert res["metrics"]["Hit@1"] == 0.0
        assert res["metrics"]["MRR"] == 0.0

    def test_missing_relevance_labels_handling(self, tmp_path):
        # Create empty benchmark files
        bench_file = tmp_path / "empty_bench.json"
        rel_file = tmp_path / "empty_rel.json"
        bench_file.write_text("[]", encoding="utf-8")
        rel_file.write_text("{}", encoding="utf-8")

        evaluator = RetrievalEvaluator(benchmark_path=bench_file, relevance_labels_path=rel_file)
        mock = MockRetriever()
        res = evaluator.evaluate_retriever(mock)
        assert res["status"] == "NO_EVALUABLE_QUERIES"
        assert res["sample_count"] == 0


# =========================================================================
# 2. NER Evaluator Tests
# =========================================================================

class TestNEREvaluator:
    """Verifies Legal NER evaluation harness."""

    def test_ner_benchmark_loading(self):
        evaluator = NEREvaluator()
        assert len(evaluator.gold_records) > 0
        verified, queued = evaluator.get_evaluable_records()
        assert len(verified) > 0
        assert len(queued) > 0

    def test_ner_evaluation_run(self):
        evaluator = NEREvaluator()
        res = evaluator.evaluate(exact_span_match=True, experiment_name="test_ner")
        assert res["status"] == "COMPLETED"
        assert res["sample_count"] > 0
        m = res["metrics"]
        assert "micro_f1" in m
        assert "macro_f1" in m
        assert "per_class" in m
        # Check that per-class metrics contain legal types
        assert "ARTICLE" in m["per_class"]
        assert "CASE" in m["per_class"]


# =========================================================================
# 3. Intent Evaluator Tests
# =========================================================================

class TestIntentEvaluator:
    """Verifies intent classification evaluation and train/test leakage prevention."""

    def test_train_test_split_zero_leakage(self):
        evaluator = IntentEvaluator(random_seed=42)
        assert len(evaluator.queries) > 0
        X_train, X_test, y_train, y_test = evaluator.get_train_test_split(test_ratio=0.15)

        assert len(X_train) > 0
        assert len(X_test) > 0
        # Check NO overlap between train and test queries
        train_set = set(X_train)
        test_set = set(X_test)
        overlap = train_set.intersection(test_set)
        assert len(overlap) == 0, f"Data leakage detected! Overlapping queries: {overlap}"

    def test_intent_comparative_evaluation(self):
        evaluator = IntentEvaluator(random_seed=42)
        res = evaluator.run_comparative_evaluation()
        assert res["status"] == "COMPLETED"
        assert "rule_based_baseline" in res["models"]
        assert "tfidf_logistic_regression" in res["models"]
        assert "hybrid_classifier" in res["models"]

        # Models must have valid numerical scores
        for m_name, stats in res["models"].items():
            assert 0.0 <= stats["accuracy"] <= 1.0
            assert 0.0 <= stats["macro_f1"] <= 1.0
            assert len(stats["confusion_matrix"]) > 0

        # Limitation notice must be present
        assert "statistical_limitation" in res
        assert "DATASET LIMITATION" in res["statistical_limitation"]

    def test_cross_validation_run(self):
        evaluator = IntentEvaluator(random_seed=42)
        cv = evaluator.run_cross_validation(k=3)
        assert cv["folds"] == 3
        assert 0.0 <= cv["mean_accuracy"] <= 1.0
        assert cv["std_accuracy"] >= 0.0
        assert len(cv["fold_accuracies"]) == 3


# =========================================================================
# 4. Canonical Entity Linking Evaluator Tests
# =========================================================================

class TestEntityLinkingEvaluator:
    """Verifies canonical entity linking evaluation."""

    def test_entity_linking_evaluation(self):
        evaluator = EntityLinkingEvaluator()
        assert len(evaluator.benchmark_records) > 0
        res = evaluator.evaluate(experiment_name="test_linking")

        assert res["status"] == "COMPLETED"
        m = res["metrics"]
        assert "exact_linking_accuracy" in m
        assert "out_of_kb_rejection_accuracy" in m
        assert 0.0 <= m["exact_linking_accuracy"] <= 1.0
        assert 0.0 <= m["out_of_kb_rejection_accuracy"] <= 1.0


# =========================================================================
# 5. RAG & Citations Evaluator Tests
# =========================================================================

class TestRAGEvaluator:
    """Verifies RAG grounding, citation verification, and abstention."""

    def test_rag_citation_evaluation(self):
        evaluator = RAGEvaluator()
        assert len(evaluator.rag_questions) > 0
        res = evaluator.evaluate_citation_validation(experiment_name="test_rag")

        assert res["status"] == "COMPLETED"
        m = res["metrics"]
        assert "citation_validity_rate" in m
        assert "citation_precision" in m
        assert "abstention_accuracy" in m
        assert 0.0 <= m["citation_validity_rate"] <= 1.0
        assert 0.0 <= m["abstention_accuracy"] <= 1.0

    def test_query_expansion_evaluation(self):
        evaluator = RAGEvaluator()
        assert len(evaluator.expansion_records) > 0
        res = evaluator.evaluate_query_expansion(experiment_name="test_expansion")

        assert res["status"] == "COMPLETED"
        m = res["metrics"]
        assert "expansion_precision" in m
        assert 0.0 <= m["expansion_precision"] <= 1.0


# =========================================================================
# 6. Report Generator & Serialization Tests
# =========================================================================

class TestReportGenerator:
    """Verifies report creation, serialization to disk, and file format validity."""

    def test_report_generation_files_created(self, tmp_path):
        generator = ReportGenerator(output_dir=tmp_path)

        retrieval_mock = [
            {
                "experiment_name": "BM25_Baseline",
                "sample_count": 10,
                "avg_latency_ms": 12.5,
                "metrics": {"Hit@1": 0.8, "Hit@5": 0.9, "MRR": 0.85, "NDCG@10": 0.88}
            }
        ]
        ner_mock = {
            "exact_span_match": True,
            "sample_count": 10,
            "metrics": {
                "micro_f1": 0.92,
                "macro_f1": 0.89,
                "total_gold_entities": 25,
                "per_class": {
                    "ARTICLE": {"precision": 0.95, "recall": 0.95, "f1": 0.95, "support": 10, "tp": 10, "fp": 0, "fn": 0}
                }
            }
        }
        intent_mock = {
            "split_ratio": "85/15",
            "train_samples": 85,
            "test_samples": 15,
            "models": {
                "rule_based": {"accuracy": 0.80, "macro_f1": 0.78, "sample_count": 15},
                "ml_classifier": {"accuracy": 0.87, "macro_f1": 0.85, "sample_count": 15}
            }
        }
        el_mock = {
            "sample_count": 20,
            "metrics": {
                "exact_linking_accuracy": 0.90,
                "out_of_kb_rejection_accuracy": 1.0,
                "per_entity_type": {
                    "ARTICLE": {"accuracy": 1.0, "correct": 5, "total": 5}
                }
            }
        }
        rag_mock = {
            "sample_count": 5,
            "metrics": {
                "citation_validity_rate": 1.0,
                "citation_precision": 1.0,
                "evidence_coverage": 0.6,
                "abstention_accuracy": 1.0,
                "structural_vs_semantic_note": "Notice: Structural citation validation"
            }
        }

        # Save CSVs
        csv_ret = generator.save_retrieval_csv(retrieval_mock)
        csv_ner = generator.save_ner_csv(ner_mock)
        csv_intent = generator.save_classification_csv(intent_mock)

        assert csv_ret.exists()
        assert csv_ner.exists()
        assert csv_intent.exists()

        # Save Markdown Report
        md_file = generator.generate_markdown_report(
            retrieval_experiments=retrieval_mock,
            ner_results=ner_mock,
            intent_results=intent_mock,
            entity_linking_results=el_mock,
            rag_results=rag_mock
        )
        assert md_file.exists()
        md_content = md_file.read_text(encoding="utf-8")
        assert "BM25_Baseline" in md_content
        assert "Information Retrieval Empirical Evaluation" in md_content
        assert "Notice: Structural citation validation" in md_content

        # Save JSON
        json_file = generator.save_json({"status": "ok"}, "summary.json")
        assert json_file.exists()


# =========================================================================
# 7. Benchmark Runner & Quick Mode Test
# =========================================================================

class TestBenchmarkRunner:
    """Verifies master orchestrator run in quick mode."""

    def test_benchmark_runner_quick_mode(self, tmp_path):
        runner = BenchmarkRunner(results_dir=tmp_path, quick_mode=True)
        # Run retrieval suite in quick mode (evaluates subset of queries)
        ret_results = runner.run_retrieval_suite()
        assert len(ret_results) == 6
        assert (tmp_path / "retrieval_results.csv").exists()
