"""
Unit and Integration Tests for the Research Dashboard Data and View Layer.

Verifies:
1. Loading evaluation artifacts when files are present.
2. Graceful fallback on missing, empty, or malformed files.
3. Confusion matrix extraction and labeling.
4. Per-class intent metrics extraction.
5. Entity linking, query expansion, and RAG reliability summaries.
6. Benchmark manifest integrity counting.
7. Reproducibility metadata extraction and missing parameter handling.
"""

import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd

from evaluation.dashboard_data import (
    safe_load_csv,
    safe_load_json,
    load_retrieval_results,
    load_query_level_audit,
    load_classification_results,
    load_ner_results,
    load_evaluation_summary,
    load_benchmark_manifest,
    get_confusion_matrix_df,
    get_per_class_intent_df,
    get_entity_linking_metrics,
    get_query_expansion_metrics,
    get_rag_reliability_metrics,
    get_reproducibility_metadata,
)


class TestDashboardDataLoading:
    """Verifies that actual saved evaluation artifacts load correctly."""

    def test_load_real_retrieval_results(self):
        df = load_retrieval_results()
        assert df is not None
        assert not df.empty
        assert "Method" in df.columns
        assert "MRR" in df.columns
        assert "NDCG@10" in df.columns
        assert len(df) == 6

    def test_load_real_query_level_audit(self):
        df = load_query_level_audit()
        assert df is not None
        assert not df.empty
        assert "Query_ID" in df.columns
        assert "Gold_Relevant_IDs" in df.columns
        assert "First_Hit_Rank" in df.columns
        assert len(df) >= 20

    def test_load_real_classification_results(self):
        df = load_classification_results()
        assert df is not None
        assert not df.empty
        assert "Model" in df.columns
        assert "Accuracy" in df.columns
        assert "Macro_F1" in df.columns
        assert len(df) == 3

    def test_load_real_ner_results(self):
        df = load_ner_results()
        assert df is not None
        assert not df.empty
        assert "Category" in df.columns
        assert "Precision" in df.columns
        assert "Recall" in df.columns
        assert "F1" in df.columns
        assert len(df) >= 10

    def test_load_real_evaluation_summary(self):
        data = load_evaluation_summary()
        assert data is not None
        assert "metadata" in data
        assert "retrieval" in data
        assert "intent_classification" in data
        assert "ner" in data
        assert "entity_linking" in data
        assert "rag_citations" in data

    def test_load_real_benchmark_manifest(self):
        manifest = load_benchmark_manifest()
        assert manifest is not None
        assert "Retrieval Benchmark" in manifest
        assert manifest["Retrieval Benchmark"]["verified"] == 20
        assert manifest["Retrieval Benchmark"]["requires_annotation"] == 3


class TestDashboardMalformedAndMissingHandling:
    """Verifies graceful handling when files are missing, empty, or malformed."""

    def test_missing_files_return_none(self, tmp_path):
        assert load_retrieval_results(tmp_path) is None
        assert load_query_level_audit(tmp_path) is None
        assert load_classification_results(tmp_path) is None
        assert load_ner_results(tmp_path) is None
        assert load_evaluation_summary(tmp_path) is None

    def test_empty_csv_file_returns_none(self, tmp_path):
        empty_csv = tmp_path / "retrieval_results.csv"
        empty_csv.write_text("", encoding="utf-8")
        assert load_retrieval_results(tmp_path) is None

    def test_malformed_csv_returns_none(self, tmp_path):
        bad_csv = tmp_path / "retrieval_results.csv"
        bad_csv.write_bytes(b"\x00\xff\xfe\x00corrupt")
        assert load_retrieval_results(tmp_path) is None

    def test_empty_json_file_returns_none(self, tmp_path):
        empty_json = tmp_path / "evaluation_summary.json"
        empty_json.write_text("", encoding="utf-8")
        assert load_evaluation_summary(tmp_path) is None

    def test_malformed_json_file_returns_none(self, tmp_path):
        bad_json = tmp_path / "evaluation_summary.json"
        bad_json.write_text("{invalid_json: 123", encoding="utf-8")
        assert load_evaluation_summary(tmp_path) is None

    def test_missing_benchmark_dir_manifest(self, tmp_path):
        manifest = load_benchmark_manifest(tmp_path)
        assert manifest is not None
        for b_info in manifest.values():
            assert b_info["status"] == "File Missing"
            assert b_info["total"] == 0


class TestDashboardMetricExtractors:
    """Verifies extractor helpers for confusion matrices, per-class tables, etc."""

    def test_confusion_matrix_extraction(self):
        summary = load_evaluation_summary()
        cm_df = get_confusion_matrix_df(summary, "hybrid_classifier")
        assert cm_df is not None
        assert isinstance(cm_df, pd.DataFrame)
        assert cm_df.shape[0] == cm_df.shape[1] == 11
        assert "ARTICLE_LOOKUP" in cm_df.columns
        assert "ARTICLE_LOOKUP" in cm_df.index

    def test_confusion_matrix_missing_model_returns_none(self):
        summary = load_evaluation_summary()
        cm_df = get_confusion_matrix_df(summary, "non_existent_model")
        assert cm_df is None

    def test_per_class_intent_extraction(self):
        summary = load_evaluation_summary()
        pc_df = get_per_class_intent_df(summary, "hybrid_classifier")
        assert pc_df is not None
        assert "Intent Class" in pc_df.columns
        assert "Precision" in pc_df.columns
        assert "Recall" in pc_df.columns
        assert "F1 Score" in pc_df.columns
        assert len(pc_df) == 11

    def test_entity_linking_metrics(self):
        summary = load_evaluation_summary()
        el = get_entity_linking_metrics(summary)
        assert el is not None
        assert el["sample_count"] == 30
        assert "exact_linking_accuracy" in el["metrics"]
        assert el["metrics"]["out_of_kb_rejection_accuracy"] == 1.0

    def test_query_expansion_metrics(self):
        summary = load_evaluation_summary()
        qe = get_query_expansion_metrics(summary)
        assert qe is not None
        assert qe["sample_count"] == 4
        assert qe["metrics"]["drift_rate"] == 0.0

    def test_rag_reliability_metrics(self):
        summary = load_evaluation_summary()
        rag = get_rag_reliability_metrics(summary)
        assert rag is not None
        assert rag["sample_count"] == 8
        assert rag["metrics"]["citation_validity_rate"] == 1.0
        assert len(rag["sample_runs"]) == 8

    def test_reproducibility_metadata(self):
        summary = load_evaluation_summary()
        meta = get_reproducibility_metadata(summary)
        assert meta["dataset_version"] == "1.0.0-capstone"
        assert meta["random_seed"] == 42
        assert "embedding_model" in meta
        assert "reranker_model" in meta

    def test_reproducibility_metadata_fallback(self):
        meta = get_reproducibility_metadata(None)
        assert meta["dataset_version"] == "not recorded"
        assert meta["random_seed"] == "not recorded"
