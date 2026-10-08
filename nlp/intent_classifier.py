"""
Intent Classification Module for Indian Constitutional Legal AI.
Implements dual-tier intent classification:
1. RuleBasedIntentClassifier (deterministic baseline)
2. MLIntentClassifier (Scikit-learn TF-IDF + Logistic Regression)
3. HybridIntentClassifier (unified orchestrator with out-of-scope detection)

Supports 10 constitutional intent classes + OUT_OF_SCOPE:
- ARTICLE_LOOKUP
- CASE_LAW_QUERY
- CASE_COMPARISON
- LEGAL_EXPLANATION
- RIGHTS_QUERY
- AMENDMENT_QUERY
- PRECEDENT_QUERY
- DEFINITION_QUERY
- CONSTITUTIONAL_PROCEDURE
- MULTI_DOCUMENT_QUERY
- OUT_OF_SCOPE
"""

import os
import re
import json
import pickle
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix

from config import (
    INTENT_CLASSES,
    INTENT_MODEL_PATH,
    CLASSIFICATION_BENCHMARK_PATH,
    INTENT_CONFIDENCE_THRESHOLD,
)
from nlp.preprocessing import normalize_legal_text
from nlp.legal_ner import get_legal_ner


class RuleBasedIntentClassifier:
    """
    Deterministic rule-based baseline intent classifier.
    Uses regex patterns, domain keywords, and entity markers.
    """

    COMPARISON_MARKERS = [
        r"\b(?:compare|comparison|versus|distinguish|difference between|contrast|shift from)\b",
        r"\b(?:differ from|gopalan vs|gopalan and maneka|shankari prasad and golak)\b"
    ]

    PROCEDURE_MARKERS = [
        r"\b(?:procedure to|process to|how is|how are|steps required|mechanism for)\b",
        r"\b(?:impeach|impeached|dissolve|promulgate|elected|appointment of|proclamation of)\b"
    ]

    PRECEDENT_MARKERS = [
        r"\b(?:overrule|overruled|set aside|binding precedent|previous decision|reconsidered)\b",
        r"\b(?:still valid law|reaffirmed|governing precedent|earlier ruling)\b"
    ]

    DEFINITION_MARKERS = [
        r"\b(?:define|definition of|what is meant by|meaning of)\b",
        r"\b(?:what does .* mean|what is the concept of)\b"
    ]

    AMENDMENT_MARKERS = [
        r"\b(?:\d{1,3}(?:st|nd|rd|th)?\s+amendment|amendment act|which amendment|amended by)\b",
        r"\b(?:first amendment|twenty-fourth amendment|forty-second amendment)\b"
    ]

    MULTI_DOC_MARKERS = [
        r"\b(?:synthesize|cross-reference|interplay|harmonize|interrelate)\b",
        r"\b(?:golden triangle|across.*and.*and|trace.*jurisprudence.*from.*to)\b"
    ]

    OUT_OF_SCOPE_MARKERS = [
        r"\b(?:recipe|pizza|cake|cooking|bake|weather|forecast|rain|temperature)\b",
        r"\b(?:python|javascript|coding|function|array|quicksort|algorithm|debug)\b",
        r"\b(?:movie|actor|film|cricket|fifa|football|world cup|olympics|score)\b",
        r"\b(?:train ticket|flight ticket|irctc|hotel|restaurant|shopping|cloth)\b",
        r"\b(?:faucet|tyre|plumbing|engine|car|repair|bookshelf|ikea|poem)\b"
    ]

    def classify(self, query: str, entities: Optional[Dict[str, List[str]]] = None) -> Tuple[str, float, str]:
        """
        Classifies query into intent category.
        
        Returns:
            Tuple of (intent_label, confidence, rationale)
        """
        if not query or not query.strip():
            return "OUT_OF_SCOPE", 0.1, "Empty query"

        q_norm = normalize_legal_text(query, expand_abbreviations=True).lower()
        ents = entities or {}

        # 0. Check out of scope markers
        for pat in self.OUT_OF_SCOPE_MARKERS:
            if re.search(pat, q_norm):
                return "OUT_OF_SCOPE", 0.95, f"Matched out-of-scope pattern '{pat}'"

        # 1. Multi-document synthesis
        for pat in self.MULTI_DOC_MARKERS:
            if re.search(pat, q_norm):
                return "MULTI_DOCUMENT_QUERY", 0.88, "Matched multi-document synthesis marker"

        # 2. Case comparison
        for pat in self.COMPARISON_MARKERS:
            if re.search(pat, q_norm):
                return "CASE_COMPARISON", 0.90, "Matched case comparison marker"

        # 3. Constitutional procedure
        for pat in self.PROCEDURE_MARKERS:
            if re.search(pat, q_norm) and any(w in q_norm for w in ["president", "judge", "amend", "article", "emergency", "bill", "ordinance"]):
                return "CONSTITUTIONAL_PROCEDURE", 0.88, "Matched constitutional procedure marker"

        # 4. Precedent & Overruling
        for pat in self.PRECEDENT_MARKERS:
            if re.search(pat, q_norm):
                return "PRECEDENT_QUERY", 0.89, "Matched judicial precedent marker"

        # 5. Definition query
        for pat in self.DEFINITION_MARKERS:
            if re.search(pat, q_norm):
                return "DEFINITION_QUERY", 0.85, "Matched definition query marker"

        # 6. Amendment query
        for pat in self.AMENDMENT_MARKERS:
            if re.search(pat, q_norm) or bool(ents.get("AMENDMENT")):
                return "AMENDMENT_QUERY", 0.92, "Matched constitutional amendment marker"

        # 7. Article Lookup (specific text request)
        if any(w in q_norm for w in ["text of", "wording of", "state article", "what does article", "show article", "read out", "clauses in"]):
            if bool(ents.get("ARTICLE")) or "article" in q_norm or "preamble" in q_norm:
                return "ARTICLE_LOOKUP", 0.90, "Matched specific constitutional article lookup"

        # 8. Rights Query
        if any(w in q_norm for w in ["fundamental right", "fundamental rights", "freedoms guaranteed", "right to", "rights protect", "discrimination"]):
            return "RIGHTS_QUERY", 0.86, "Matched fundamental rights query"

        # 9. Case Law Query
        if bool(ents.get("CASE")) or any(w in q_norm for w in ["judgment", "ruling", "verdict", "bench", "ratio decidendi", "case"]):
            return "CASE_LAW_QUERY", 0.88, "Matched landmark case query"

        # 10. Legal Explanation (fallback for doctrinal inquiries)
        if any(w in q_norm for w in ["doctrine", "principle", "how does", "explain", "meaning", "applied"]):
            return "LEGAL_EXPLANATION", 0.75, "Matched general legal explanation query"

        # Default fallback if legal terms present
        if bool(ents.get("ARTICLE")):
            return "ARTICLE_LOOKUP", 0.65, "Defaulted to article lookup based on extracted article"

        # If nothing matches and no legal terms present
        legal_terms = ["constitution", "court", "law", "supreme", "right", "justice", "article", "section"]
        if not any(lt in q_norm for lt in legal_terms):
            return "OUT_OF_SCOPE", 0.70, "No constitutional or legal terminology detected"

        return "LEGAL_EXPLANATION", 0.50, "Defaulted to general legal explanation"


class MLIntentClassifier:
    """
    Supervised Machine Learning Intent Classifier using TF-IDF + Logistic Regression.
    """

    def __init__(self):
        self.pipeline: Optional[Pipeline] = None
        self.is_trained: bool = False

    def build_pipeline(self) -> Pipeline:
        """Constructs Scikit-learn Pipeline with TF-IDF Vectorizer and Logistic Regression."""
        return Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=(1, 2),
                min_df=1,
                sublinear_tf=True,
                strip_accents="unicode"
            )),
            ("clf", LogisticRegression(
                C=2.0,
                max_iter=1000,
                class_weight="balanced",
                random_state=42
            ))
        ])

    def train_on_benchmark(self, benchmark_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Trains the classifier on benchmark queries dataset.
        """
        target_path = benchmark_path or CLASSIFICATION_BENCHMARK_PATH
        if not Path(target_path).exists():
            raise FileNotFoundError(f"Classification benchmark dataset not found at: {target_path}")

        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        queries = [item["query"] for item in data]
        labels = [item["intent"] for item in data]

        self.pipeline = self.build_pipeline()
        self.pipeline.fit(queries, labels)
        self.is_trained = True

        # Compute training metrics
        preds = self.pipeline.predict(queries)
        acc = accuracy_score(labels, preds)
        p, r, f1, _ = precision_recall_fscore_support(labels, preds, average="macro", zero_division=0)

        metrics = {
            "samples": len(queries),
            "classes": len(set(labels)),
            "accuracy": round(float(acc), 4),
            "macro_precision": round(float(p), 4),
            "macro_recall": round(float(r), 4),
            "macro_f1": round(float(f1), 4)
        }
        return metrics

    def predict(self, query: str) -> str:
        """Predicts the intent class label."""
        if not self.is_trained or self.pipeline is None:
            raise RuntimeError("MLIntentClassifier is not trained yet.")
        norm_q = normalize_legal_text(query, expand_abbreviations=True)
        return str(self.pipeline.predict([norm_q])[0])

    def predict_proba(self, query: str) -> Dict[str, float]:
        """Returns dictionary of probabilities across all intent classes."""
        if not self.is_trained or self.pipeline is None:
            raise RuntimeError("MLIntentClassifier is not trained yet.")
        norm_q = normalize_legal_text(query, expand_abbreviations=True)
        probs = self.pipeline.predict_proba([norm_q])[0]
        classes = self.pipeline.classes_
        return {str(cls_name): round(float(prob), 4) for cls_name, prob in zip(classes, probs)}

    def save_model(self, path: Optional[Path] = None):
        """Persists trained model pipeline to disk."""
        if not self.is_trained or self.pipeline is None:
            raise RuntimeError("Cannot save untrained model.")
        save_path = path or INTENT_MODEL_PATH
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            pickle.dump(self.pipeline, f)

    def load_model(self, path: Optional[Path] = None) -> bool:
        """Loads serialized model pipeline from disk."""
        target_path = path or INTENT_MODEL_PATH
        if not Path(target_path).exists():
            return False
        try:
            with open(target_path, "rb") as f:
                self.pipeline = pickle.load(f)
            self.is_trained = True
            return True
        except Exception:
            return False

    def evaluate(self, test_queries: List[str], test_labels: List[str]) -> Dict[str, Any]:
        """Calculates evaluation metrics against test set."""
        if not self.is_trained or self.pipeline is None:
            raise RuntimeError("MLIntentClassifier is not trained.")
        preds = self.pipeline.predict(test_queries)
        acc = accuracy_score(test_labels, preds)
        p, r, f1, _ = precision_recall_fscore_support(test_labels, preds, average="macro", zero_division=0)
        cm = confusion_matrix(test_labels, preds, labels=self.pipeline.classes_)
        return {
            "accuracy": round(float(acc), 4),
            "macro_precision": round(float(p), 4),
            "macro_recall": round(float(r), 4),
            "macro_f1": round(float(f1), 4),
            "classes": list(self.pipeline.classes_),
            "confusion_matrix": cm.tolist()
        }


class HybridIntentClassifier:
    """
    Unified Intent Classifier orchestrating rule baseline and trained ML model.
    """

    def __init__(self, force_retrain: bool = False):
        self.rule_classifier = RuleBasedIntentClassifier()
        self.ml_classifier = MLIntentClassifier()
        
        # Load or train ML model
        loaded = False
        if not force_retrain:
            loaded = self.ml_classifier.load_model()
            
        if not loaded:
            # Auto-train and cache model
            try:
                self.ml_classifier.train_on_benchmark()
                self.ml_classifier.save_model()
            except Exception as e:
                # If benchmark file cannot be loaded, rely on rule classifier
                print(f"[INTENT] Warning: Could not train ML classifier ({e}). Falling back to rule classifier.")

    def classify(self, query: str, entities: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
        """
        Classifies query into intent category using hybrid strategy.
        
        Returns:
            {
                "intent": str,
                "confidence": float,
                "method": "ml" | "rule" | "consensus",
                "rule_intent": str,
                "ml_intent": Optional[str],
                "probabilities": Dict[str, float],
                "is_out_of_scope": bool,
                "explanation": str
            }
        """
        if not query or not query.strip():
            return {
                "intent": "OUT_OF_SCOPE",
                "confidence": 1.0,
                "method": "rule",
                "rule_intent": "OUT_OF_SCOPE",
                "ml_intent": None,
                "probabilities": {},
                "is_out_of_scope": True,
                "explanation": "Query is empty"
            }

        rule_label, rule_conf, rule_exp = self.rule_classifier.classify(query, entities)

        # Immediate rule decision for obvious out-of-scope queries
        if rule_label == "OUT_OF_SCOPE" and rule_conf >= 0.9:
            return {
                "intent": "OUT_OF_SCOPE",
                "confidence": rule_conf,
                "method": "rule",
                "rule_intent": "OUT_OF_SCOPE",
                "ml_intent": None,
                "probabilities": {},
                "is_out_of_scope": True,
                "explanation": rule_exp
            }

        # Check ML model prediction if trained
        if self.ml_classifier.is_trained:
            probs = self.ml_classifier.predict_proba(query)
            sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
            top_ml_label, top_ml_conf = sorted_probs[0]

            # Consensus: Both models agree
            if top_ml_label == rule_label:
                final_intent = top_ml_label
                final_conf = max(top_ml_conf, rule_conf)
                method = "consensus"
                explanation = f"Consensus between ML ({top_ml_conf:.2f}) and rule baseline ({rule_conf:.2f}): {final_intent}"
            # High confidence ML
            elif top_ml_conf >= 0.50:
                final_intent = top_ml_label
                final_conf = top_ml_conf
                method = "ml"
                explanation = f"ML model prediction ({top_ml_conf:.2f}) over rule baseline ({rule_label})"
            # Fall back to high-confidence rule
            elif rule_conf >= 0.85:
                final_intent = rule_label
                final_conf = rule_conf
                method = "rule"
                explanation = f"High-confidence rule pattern ({rule_conf:.2f}): {rule_exp}"
            else:
                final_intent = top_ml_label
                final_conf = top_ml_conf
                method = "ml"
                explanation = f"ML prediction with moderate confidence ({top_ml_conf:.2f})"

            is_oos = (final_intent == "OUT_OF_SCOPE")
            return {
                "intent": final_intent,
                "confidence": round(float(final_conf), 4),
                "method": method,
                "rule_intent": rule_label,
                "ml_intent": top_ml_label,
                "probabilities": dict(sorted_probs[:5]),
                "is_out_of_scope": is_oos,
                "explanation": explanation
            }

        # ML not available, rely purely on rule baseline
        return {
            "intent": rule_label,
            "confidence": round(float(rule_conf), 4),
            "method": "rule",
            "rule_intent": rule_label,
            "ml_intent": None,
            "probabilities": {},
            "is_out_of_scope": (rule_label == "OUT_OF_SCOPE"),
            "explanation": rule_exp
        }


# Global shared instance
_INTENT_INSTANCE: Optional[HybridIntentClassifier] = None


def get_intent_classifier() -> HybridIntentClassifier:
    """Returns or lazily initializes the shared HybridIntentClassifier."""
    global _INTENT_INSTANCE
    if _INTENT_INSTANCE is None:
        _INTENT_INSTANCE = HybridIntentClassifier()
    return _INTENT_INSTANCE
