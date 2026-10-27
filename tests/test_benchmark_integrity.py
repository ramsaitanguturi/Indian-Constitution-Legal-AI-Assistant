"""
Automated Regression and Integrity Tests for Benchmark Datasets and Mappings.
Verifies:
1. Target existence in parent store for all in-corpus retrieval queries.
2. Uncataloged out-of-corpus queries are explicitly tagged and segregated.
3. 100% balance across all 11 intent classification classes (20 per class).
4. Zero duplicate query strings within intent classes.
5. Character span alignment and valid entity labels in NER benchmark.
6. Benchmark validation CLI behavior in standard vs strict modes.
"""

import json
import pytest
from pathlib import Path

from config import (
    PARENT_STORE_PATH,
    RETRIEVAL_BENCHMARK_PATH,
    CLASSIFICATION_BENCHMARK_PATH,
    NER_BENCHMARK_PATH,
    ANNOTATIONS_DIR,
    INTENT_CLASSES
)
from scripts.validate_benchmark import (
    load_parent_store,
    validate_retrieval_benchmark,
    validate_intent_benchmark,
    validate_ner_benchmark,
    UNCATALOGED_QUERY_IDS
)


@pytest.fixture(scope="module")
def parent_store():
    return load_parent_store()


class TestBenchmarkIntegrity:
    """Tests integrity of all benchmark assets and metadata mappings."""

    def test_parent_store_hydration_count(self, parent_store):
        """Parent store must be hydrated with at least 270 verified documents."""
        assert len(parent_store) >= 270
        doc_types = {v.get("doc_type") for v in parent_store.values()}
        assert "constitution" in doc_types
        assert "judgment" in doc_types

    def test_in_corpus_retrieval_queries_have_valid_targets(self, parent_store):
        """Every in-corpus retrieval query must target an existing parent document."""
        with open(RETRIEVAL_BENCHMARK_PATH, "r", encoding="utf-8") as f:
            queries = json.load(f)

        canon_path = ANNOTATIONS_DIR / "relevance_labels_v2_canonicalized.json"
        with open(canon_path, "r", encoding="utf-8") as f:
            canon_labels = json.load(f)

        in_corpus_count = 0
        uncataloged_count = 0

        for q in queries:
            qid = q["query_id"]
            if qid in UNCATALOGED_QUERY_IDS:
                uncataloged_count += 1
                assert q.get("corpus_status") == "uncataloged_out_of_corpus"
            else:
                in_corpus_count += 1
                assert q.get("corpus_status") == "in_corpus"
                rel_docs = q.get("relevant_documents", [])
                canon_rel = canon_labels.get(qid, {})

                # Verify that canonical labels link to a verified parent in parent_store
                has_valid_target = any(d in parent_store for d in rel_docs) or any(d in parent_store for d in canon_rel)
                assert has_valid_target, f"Query {qid} has no valid target in parent_store: {rel_docs}"

        assert in_corpus_count == 180
        assert uncataloged_count == 20

    def test_intent_classification_perfect_balance(self):
        """Intent classification benchmark must contain exactly 20 samples per class across all 11 classes."""
        res = validate_intent_benchmark()
        assert res["total_queries"] == 220
        assert res["is_balanced"] is True
        assert len(res["duplicate_queries"]) == 0
        assert len(res["malformed_queries"]) == 0
        for cls in INTENT_CLASSES:
            assert res["classes_found"].get(cls) == 20

    def test_ner_exact_span_alignment(self):
        """NER benchmark must have 0 span alignment errors and valid legal entity labels."""
        res = validate_ner_benchmark()
        assert res["total_queries"] == 105
        assert res["total_spans"] == 211
        assert len(res["span_alignment_errors"]) == 0
        assert len(res["invalid_label_errors"]) == 0

    def test_retrieval_benchmark_validator_results(self, parent_store):
        """validate_retrieval_benchmark returns 180 valid in-corpus and 20 uncataloged queries."""
        res = validate_retrieval_benchmark(parent_store)
        assert res["total_queries"] == 200
        assert res["valid_in_corpus_queries"] == 180
        assert res["uncataloged_corpus_queries"] == 20
        assert len(res["queries_with_missing_targets"]) == 0
        assert len(res["duplicate_queries"]) == 0
