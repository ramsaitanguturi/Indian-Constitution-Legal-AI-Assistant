"""
Intent Classification Benchmark Evaluator for Indian Constitutional Legal AI.

Compares:
1. Rule-Based Baseline (Deterministic keyword & regex rules)
2. ML Classifier (TF-IDF N-Grams + Logistic Regression)
3. Hybrid Classifier (Consensus orchestration + Out-of-Scope gating)

Features:
- Strict Train / Validation / Test separation (no data leakage!)
- K-Fold Stratified Cross-Validation for statistical confidence on small datasets
- Full reporting of dataset limitations (185 queries across 11 classes)
- Metrics: Accuracy, Macro P/R/F1, Per-class breakdown, Confusion Matrix
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

import numpy as np
from sklearn.model_selection import StratifiedKFold, train_test_split

from config import (
    CLASSIFICATION_BENCHMARK_PATH,
    INTENT_CLASSES,
    EVAL_RANDOM_SEED,
    EVAL_TRAIN_RATIO,
    EVAL_TEST_RATIO,
)
from evaluation.metrics import calculate_classification_metrics
from nlp.intent_classifier import (
    RuleBasedIntentClassifier,
    MLIntentClassifier,
    HybridIntentClassifier,
)


class IntentEvaluator:
    """
    Evaluates intent classification systems with rigorous train/test separation.
    """

    def __init__(
        self,
        benchmark_path: Optional[Union[str, Path]] = None,
        random_seed: int = EVAL_RANDOM_SEED,
    ):
        self.benchmark_path = Path(benchmark_path or CLASSIFICATION_BENCHMARK_PATH)
        self.random_seed = random_seed
        self.raw_data: List[Dict[str, str]] = []
        self.queries: List[str] = []
        self.labels: List[str] = []
        self.load_benchmark()

    def load_benchmark(self) -> None:
        """Loads labeled intent queries from benchmark JSON."""
        if self.benchmark_path.exists():
            with open(self.benchmark_path, "r", encoding="utf-8") as f:
                self.raw_data = json.load(f)
            self.queries = [item["query"] for item in self.raw_data]
            self.labels = [item["intent"] for item in self.raw_data]
        else:
            self.raw_data = []
            self.queries = []
            self.labels = []

    def get_train_test_split(
        self,
        test_ratio: float = EVAL_TEST_RATIO
    ) -> Tuple[List[str], List[str], List[str], List[str]]:
        """
        Creates a stratified train/test split.
        Ensures strict separation so models are never evaluated on training examples.
        """
        if not self.queries or not self.labels:
            return [], [], [], []

        X_train, X_test, y_train, y_test = train_test_split(
            self.queries,
            self.labels,
            test_size=test_ratio,
            random_state=self.random_seed,
            stratify=self.labels
        )
        return list(X_train), list(X_test), list(y_train), list(y_test)

    def evaluate_model(
        self,
        model_type: str,  # 'rule', 'ml', 'hybrid'
        test_queries: List[str],
        test_labels: List[str],
        trained_ml_classifier: Optional[MLIntentClassifier] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates a specified model architecture on provided test queries.
        """
        predictions: List[str] = []

        if model_type == "rule":
            classifier = RuleBasedIntentClassifier()
            for q in test_queries:
                decision = classifier.classify(q)
                if isinstance(decision, tuple):
                    predictions.append(decision[0])
                elif isinstance(decision, dict):
                    predictions.append(decision.get("intent", "OUT_OF_SCOPE"))
                else:
                    predictions.append(str(decision))

        elif model_type == "ml":
            if trained_ml_classifier is None:
                raise ValueError("Must provide trained MLIntentClassifier for 'ml' evaluation.")
            for q in test_queries:
                predictions.append(trained_ml_classifier.predict(q))

        elif model_type == "hybrid":
            # Hybrid uses provided ML classifier if passed, else internal
            if trained_ml_classifier is not None:
                rule_c = RuleBasedIntentClassifier()
                for q in test_queries:
                    rule_dec = rule_c.classify(q)
                    rule_intent = rule_dec[0] if isinstance(rule_dec, tuple) else rule_dec.get("intent", "OUT_OF_SCOPE")
                    rule_conf = rule_dec[1] if isinstance(rule_dec, tuple) else rule_dec.get("confidence", 0.5)

                    ml_pred = trained_ml_classifier.predict(q)
                    ml_probs = trained_ml_classifier.predict_proba(q)
                    ml_conf = ml_probs.get(ml_pred, 0.0)

                    # Consensus logic matching HybridIntentClassifier
                    if ml_conf >= 0.60:
                        predictions.append(ml_pred)
                    elif rule_intent != "OUT_OF_SCOPE" and rule_conf >= 0.70:
                        predictions.append(rule_intent)
                    else:
                        predictions.append(ml_pred if ml_conf >= 0.35 else "OUT_OF_SCOPE")
            else:
                hybrid_c = HybridIntentClassifier()
                for q in test_queries:
                    dec = hybrid_c.classify(q)
                    predictions.append(dec["intent"])
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

        metrics = calculate_classification_metrics(test_labels, predictions, classes=INTENT_CLASSES)
        return metrics

    def run_comparative_evaluation(self) -> Dict[str, Any]:
        """
        Runs comprehensive comparative benchmark across Rule, ML, and Hybrid models.
        
        Guarantees:
        1. ML model is trained ONLY on X_train.
        2. Evaluation occurs strictly on held-out X_test.
        3. Statistical limitations are explicitly documented.
        """
        if len(self.queries) < 10:
            return {"status": "INSUFFICIENT_DATA", "sample_count": len(self.queries)}

        start_time = time.time()
        X_train, X_test, y_train, y_test = self.get_train_test_split(test_ratio=EVAL_TEST_RATIO)

        # 1. Train fresh ML classifier strictly on training partition (zero leakage)
        ml_fresh = MLIntentClassifier()
        ml_fresh.pipeline = ml_fresh.build_pipeline()
        ml_fresh.pipeline.fit(X_train, y_train)
        ml_fresh.is_trained = True

        # 2. Evaluate all 3 models on identical held-out test split
        rule_results = self.evaluate_model("rule", X_test, y_test)
        ml_results = self.evaluate_model("ml", X_test, y_test, trained_ml_classifier=ml_fresh)
        hybrid_results = self.evaluate_model("hybrid", X_test, y_test, trained_ml_classifier=ml_fresh)

        # 3. K-Fold Cross Validation for ML classifier to assess variance
        cv_scores = self.run_cross_validation(k=5)

        total_latency = round(time.time() - start_time, 3)

        limitation_notice = (
            f"DATASET LIMITATION: Total benchmark contains {len(self.queries)} examples across "
            f"{len(set(self.labels))} classes (~{len(self.queries)//len(set(self.labels))} samples/class). "
            f"The held-out test set contains {len(X_test)} samples (~{len(X_test)//len(set(self.labels))} per class). "
            f"Class distributions have variance; 5-fold cross-validation is reported to provide confidence intervals."
        )

        return {
            "status": "COMPLETED",
            "total_samples": len(self.queries),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "random_seed": self.random_seed,
            "split_ratio": f"{int((1 - EVAL_TEST_RATIO)*100)}/{int(EVAL_TEST_RATIO*100)}",
            "total_latency_seconds": total_latency,
            "models": {
                "rule_based_baseline": rule_results,
                "tfidf_logistic_regression": ml_results,
                "hybrid_classifier": hybrid_results
            },
            "comparison_summary": {
                "rule_vs_ml_accuracy_delta": round(ml_results["accuracy"] - rule_results["accuracy"], 4),
                "rule_vs_ml_macro_f1_delta": round(ml_results["macro_f1"] - rule_results["macro_f1"], 4),
                "hybrid_vs_ml_accuracy_delta": round(hybrid_results["accuracy"] - ml_results["accuracy"], 4),
                "hybrid_vs_ml_macro_f1_delta": round(hybrid_results["macro_f1"] - ml_results["macro_f1"], 4),
            },
            "cross_validation_ml_5fold": cv_scores,
            "statistical_limitation": limitation_notice
        }

    def run_cross_validation(self, k: int = 5) -> Dict[str, Any]:
        """
        Executes Stratified K-Fold cross validation on the TF-IDF Logistic Regression model.
        Returns mean and standard deviation for accuracy and macro F1.
        """
        if len(self.queries) < k:
            return {"mean_accuracy": 0.0, "std_accuracy": 0.0, "mean_macro_f1": 0.0, "std_macro_f1": 0.0}

        skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=self.random_seed)
        accuracies = []
        macro_f1s = []

        X = np.array(self.queries)
        y = np.array(self.labels)

        for train_idx, val_idx in skf.split(X, y):
            X_tr, X_val = X[train_idx], X[val_idx]
            y_tr, y_val = y[train_idx], y[val_idx]

            fold_model = MLIntentClassifier()
            fold_model.pipeline = fold_model.build_pipeline()
            fold_model.pipeline.fit(list(X_tr), list(y_tr))
            fold_model.is_trained = True

            preds = fold_model.pipeline.predict(list(X_val))
            metrics = calculate_classification_metrics(list(y_val), list(preds), classes=INTENT_CLASSES)
            accuracies.append(metrics["accuracy"])
            macro_f1s.append(metrics["macro_f1"])

        return {
            "folds": k,
            "mean_accuracy": round(float(np.mean(accuracies)), 4),
            "std_accuracy": round(float(np.std(accuracies)), 4),
            "mean_macro_f1": round(float(np.mean(macro_f1s)), 4),
            "std_macro_f1": round(float(np.std(macro_f1s)), 4),
            "fold_accuracies": [round(a, 4) for a in accuracies],
            "fold_macro_f1s": [round(f, 4) for f in macro_f1s]
        }
