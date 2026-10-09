"""
Unit tests for NLP Intent Classification module.
Verifies RuleBasedIntentClassifier, MLIntentClassifier (TF-IDF + Logistic Regression),
HybridIntentClassifier, out-of-scope query filtering, model metrics, and edge cases.
"""

import pytest
from nlp.intent_classifier import (
    RuleBasedIntentClassifier,
    MLIntentClassifier,
    HybridIntentClassifier,
    get_intent_classifier,
)


@pytest.fixture(scope="module")
def rule_classifier():
    return RuleBasedIntentClassifier()


@pytest.fixture(scope="module")
def ml_classifier():
    clf = MLIntentClassifier()
    clf.train_on_benchmark()
    return clf


@pytest.fixture(scope="module")
def hybrid_classifier():
    return get_intent_classifier()


class TestRuleBasedIntentClassifier:
    """Verifies baseline rule-based intent categorization."""

    def test_article_lookup_rule(self, rule_classifier):
        query = "What does Article 21 state regarding life and personal liberty?"
        intent, conf, _ = rule_classifier.classify(query, entities={"ARTICLE": ["Article 21"]})
        assert intent == "ARTICLE_LOOKUP"
        assert conf > 0.6

    def test_case_comparison_rule(self, rule_classifier):
        query = "Compare AK Gopalan and Maneka Gandhi regarding personal liberty"
        intent, conf, _ = rule_classifier.classify(query)
        assert intent == "CASE_COMPARISON"

    def test_constitutional_procedure_rule(self, rule_classifier):
        query = "What is the procedure to amend the Constitution under Article 368?"
        intent, conf, _ = rule_classifier.classify(query)
        assert intent == "CONSTITUTIONAL_PROCEDURE"

    def test_precedent_query_rule(self, rule_classifier):
        query = "Which landmark case overruled AK Gopalan v State of Madras?"
        intent, conf, _ = rule_classifier.classify(query)
        assert intent == "PRECEDENT_QUERY"

    def test_definition_query_rule(self, rule_classifier):
        query = "Define the Basic Structure of the Constitution"
        intent, conf, _ = rule_classifier.classify(query)
        assert intent == "DEFINITION_QUERY"

    def test_amendment_query_rule(self, rule_classifier):
        query = "What changes were made by the 42nd Amendment Act?"
        intent, conf, _ = rule_classifier.classify(query, entities={"AMENDMENT": ["42nd Amendment"]})
        assert intent == "AMENDMENT_QUERY"

    def test_out_of_scope_rule(self, rule_classifier):
        query = "What is the recipe for baking chocolate cake?"
        intent, conf, _ = rule_classifier.classify(query)
        assert intent == "OUT_OF_SCOPE"
        assert conf >= 0.9


class TestMLIntentClassifier:
    """Verifies Scikit-learn TF-IDF + Logistic Regression training, inference, and metrics."""

    def test_training_metrics(self, ml_classifier):
        """Ensure trained classifier achieves academic performance on training benchmark."""
        metrics = ml_classifier.train_on_benchmark()
        assert metrics["samples"] >= 150
        assert metrics["classes"] >= 10
        assert metrics["accuracy"] >= 0.90
        assert metrics["macro_f1"] >= 0.85

    def test_ml_predict_classes(self, ml_classifier):
        test_cases = [
            ("Text of Article 14 equality before law", "ARTICLE_LOOKUP"),
            ("Verdict in Kesavananda Bharati basic structure case", "CASE_LAW_QUERY"),
            ("Compare Gopalan and Maneka Gandhi on Article 21", "CASE_COMPARISON"),
            ("What is the procedure to impeach a Supreme Court judge?", "CONSTITUTIONAL_PROCEDURE"),
            ("Which cases overruled ADM Jabalpur?", "PRECEDENT_QUERY"),
            ("Define the term law as used in Article 13 of the Constitution", "DEFINITION_QUERY"),
            ("How do I install Python on a Windows computer?", "OUT_OF_SCOPE")
        ]
        for query, expected_intent in test_cases:
            pred = ml_classifier.predict(query)
            assert pred == expected_intent, f"Query '{query}' predicted as '{pred}', expected '{expected_intent}'"

    def test_ml_predict_proba(self, ml_classifier):
        probs = ml_classifier.predict_proba("What are the provisions of Article 21?")
        assert isinstance(probs, dict)
        assert "ARTICLE_LOOKUP" in probs
        # Probability of ARTICLE_LOOKUP should be dominant
        assert probs["ARTICLE_LOOKUP"] > 0.20
        total_p = sum(probs.values())
        assert abs(total_p - 1.0) < 0.05

    def test_model_persistence(self, ml_classifier, tmp_path):
        save_path = tmp_path / "temp_intent_model.pkl"
        ml_classifier.save_model(save_path)
        assert save_path.exists()

        new_clf = MLIntentClassifier()
        assert new_clf.load_model(save_path) is True
        pred = new_clf.predict("What is Article 21?")
        assert pred == "ARTICLE_LOOKUP"


class TestHybridIntentClassifier:
    """Verifies unified hybrid classifier integration and out-of-scope handling."""

    def test_classify_structure(self, hybrid_classifier):
        res = hybrid_classifier.classify("Explain the doctrine of severability in constitutional law")
        assert "intent" in res
        assert "confidence" in res
        assert "method" in res
        assert "rule_intent" in res
        assert "probabilities" in res
        assert "is_out_of_scope" in res
        assert "explanation" in res
        assert res["is_out_of_scope"] is False

    def test_out_of_scope_detection(self, hybrid_classifier):
        queries = [
            "How do I cook Italian pasta with red sauce?",
            "Write a python quicksort function",
            "What is the weather forecast in Delhi tomorrow?"
        ]
        for q in queries:
            res = hybrid_classifier.classify(q)
            assert res["intent"] == "OUT_OF_SCOPE"
            assert res["is_out_of_scope"] is True
            assert res["confidence"] > 0.5

    def test_empty_and_whitespace_query(self, hybrid_classifier):
        res = hybrid_classifier.classify("   ")
        assert res["intent"] == "OUT_OF_SCOPE"
        assert res["is_out_of_scope"] is True
