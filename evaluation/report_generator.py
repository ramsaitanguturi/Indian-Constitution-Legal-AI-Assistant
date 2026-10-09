"""
Evaluation Report Generator for Indian Constitutional Legal AI Assistant.

Generates:
1. Machine-readable JSON summary (`evaluation/results/evaluation_summary.json`)
2. Structured CSV benchmark tables (`evaluation/results/retrieval_results.csv`, `classification_results.csv`, etc.)
3. Comprehensive human-readable Markdown evaluation report (`evaluation/results/evaluation_report.md`)

Records complete provenance, timestamps, hyperparameters, sample sizes, and limitations.
"""

import csv
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from config import (
    EVALUATION_RESULTS_DIR,
    DEFAULT_EMBEDDING_MODEL,
    RERANKER_MODEL_NAME,
    BM25_K1,
    BM25_B,
    RRF_K,
    ENTITY_BOOST_WEIGHT,
    DATASET_VERSION,
    EVAL_RANDOM_SEED,
)


class ReportGenerator:
    """
    Serializes quantitative experiment outcomes into JSON, CSV, and Markdown formats.
    """

    def __init__(self, output_dir: Optional[Union[str, Path]] = None):
        self.output_dir = Path(output_dir or EVALUATION_RESULTS_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_json(self, data: Dict[str, Any], filename: str) -> Path:
        """Saves dictionary as formatted JSON file."""
        target = self.output_dir / filename
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return target

    def save_retrieval_csv(self, retrieval_experiments: List[Dict[str, Any]], filename: str = "retrieval_results.csv") -> Path:
        """
        Saves retrieval metrics comparison table to CSV.
        Headers: Method, Sample Count, Hit@1, Hit@3, Hit@5, Hit@10, Recall@5, Recall@10, MRR, NDCG@5, NDCG@10, Latency(ms)
        """
        target = self.output_dir / filename
        headers = [
            "Method", "Sample_Count", "Hit@1", "Hit@3", "Hit@5", "Hit@10",
            "Recall@5", "Recall@10", "MRR", "NDCG@5", "NDCG@10", "Avg_Latency_ms"
        ]

        with open(target, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            for exp in retrieval_experiments:
                m = exp.get("metrics", {})
                writer.writerow([
                    exp.get("experiment_name", "unknown"),
                    exp.get("sample_count", 0),
                    m.get("Hit@1", 0.0),
                    m.get("Hit@3", 0.0),
                    m.get("Hit@5", 0.0),
                    m.get("Hit@10", 0.0),
                    m.get("Recall@5", 0.0),
                    m.get("Recall@10", 0.0),
                    m.get("MRR", 0.0),
                    m.get("NDCG@5", 0.0),
                    m.get("NDCG@10", 0.0),
                    exp.get("avg_latency_ms", 0.0)
                ])
        return target

    def save_classification_csv(self, classification_data: Dict[str, Any], filename: str = "classification_results.csv") -> Path:
        """Saves intent classification model comparison table to CSV."""
        target = self.output_dir / filename
        headers = ["Model", "Sample_Count", "Accuracy", "Macro_Precision", "Macro_Recall", "Macro_F1", "Weighted_F1"]

        with open(target, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            models = classification_data.get("models", {})
            for m_name, m_res in models.items():
                writer.writerow([
                    m_name,
                    m_res.get("sample_count", 0),
                    m_res.get("accuracy", 0.0),
                    m_res.get("macro_precision", 0.0),
                    m_res.get("macro_recall", 0.0),
                    m_res.get("macro_f1", 0.0),
                    m_res.get("weighted_f1", 0.0)
                ])
        return target

    def save_ner_csv(self, ner_data: Dict[str, Any], filename: str = "ner_results.csv") -> Path:
        """Saves per-category NER metrics to CSV."""
        target = self.output_dir / filename
        headers = ["Category", "Precision", "Recall", "F1", "Support", "TP", "FP", "FN"]

        with open(target, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            per_class = ner_data.get("metrics", {}).get("per_class", {})
            for cat, stats in per_class.items():
                writer.writerow([
                    cat,
                    stats.get("precision", 0.0),
                    stats.get("recall", 0.0),
                    stats.get("f1", 0.0),
                    stats.get("support", 0),
                    stats.get("tp", 0),
                    stats.get("fp", 0),
                    stats.get("fn", 0)
                ])
        return target

    def generate_markdown_report(
        self,
        retrieval_experiments: List[Dict[str, Any]],
        ner_results: Dict[str, Any],
        intent_results: Dict[str, Any],
        entity_linking_results: Dict[str, Any],
        rag_results: Dict[str, Any],
        expansion_results: Optional[Dict[str, Any]] = None,
        filename: str = "evaluation_report.md"
    ) -> Path:
        """
        Generates comprehensive human-readable Markdown evaluation report.
        """
        target = self.output_dir / filename
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        md = []
        md.append("# Indian Constitution Legal AI Assistant — Empirical Evaluation Report")
        md.append(f"**Generated:** {timestamp_str} | **Corpus Version:** {DATASET_VERSION} | **Random Seed:** {EVAL_RANDOM_SEED}\n")
        md.append("> **Research Purpose:** Quantitative empirical evaluation of NLP query understanding, entity-aware hybrid retrieval, and grounded RAG reliability.\n")

        # -------------------------------------------------------------
        # Section 1: Retrieval Experiments Matrix
        # -------------------------------------------------------------
        md.append("## 1. Information Retrieval Empirical Evaluation")
        md.append("Evaluated across standard Information Retrieval metrics using verified relevance judgments.\n")

        md.append("| Retrieval Configuration | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Recall@5 | Recall@10 | MRR | NDCG@5 | NDCG@10 | Latency (ms) |")
        md.append("|---|---|---|---|---|---|---|---|---|---|---|")

        for exp in retrieval_experiments:
            name = exp.get("experiment_name", "unknown")
            m = exp.get("metrics", {})
            lat = exp.get("avg_latency_ms", 0.0)
            md.append(
                f"| **{name}** | {m.get('Hit@1', 0.0):.4f} | {m.get('Hit@3', 0.0):.4f} | "
                f"{m.get('Hit@5', 0.0):.4f} | {m.get('Hit@10', 0.0):.4f} | {m.get('Recall@5', 0.0):.4f} | "
                f"{m.get('Recall@10', 0.0):.4f} | {m.get('MRR', 0.0):.4f} | {m.get('NDCG@5', 0.0):.4f} | "
                f"{m.get('NDCG@10', 0.0):.4f} | {lat:.1f} ms |"
            )

        md.append("\n*Configuration Details:*")
        md.append(f"- BM25: Okapi ($k_1={BM25_K1}, b={BM25_B}$)")
        md.append(f"- Dense Model: `{DEFAULT_EMBEDDING_MODEL}`")
        md.append(f"- Fusion: Reciprocal Rank Fusion ($k={RRF_K}$)")
        md.append(f"- Entity Boost Weight: $+{ENTITY_BOOST_WEIGHT}$")
        md.append(f"- Neural Reranker: `{RERANKER_MODEL_NAME}`\n")

        # -------------------------------------------------------------
        # Section 2: Legal NER Evaluation
        # -------------------------------------------------------------
        md.append("## 2. Legal Named Entity Recognition (NER) Evaluation")
        ner_m = ner_results.get("metrics", {})
        md.append(
            f"**Exact Span Match:** {ner_results.get('exact_span_match', True)} | "
            f"**Micro-F1:** {ner_m.get('micro_f1', 0.0):.4f} | "
            f"**Macro-F1:** {ner_m.get('macro_f1', 0.0):.4f} | "
            f"**Gold Entities:** {ner_m.get('total_gold_entities', 0)}\n"
        )

        md.append("| Entity Category | Precision | Recall | F1 Score | Support | TP | FP | FN |")
        md.append("|---|---|---|---|---|---|---|---|")
        per_class_ner = ner_m.get("per_class", {})
        for cat, s in per_class_ner.items():
            md.append(
                f"| `{cat}` | {s.get('precision', 0.0):.4f} | {s.get('recall', 0.0):.4f} | "
                f"**{s.get('f1', 0.0):.4f}** | {s.get('support', 0)} | {s.get('tp', 0)} | "
                f"{s.get('fp', 0)} | {s.get('fn', 0)} |"
            )

        # -------------------------------------------------------------
        # Section 3: Intent Classification Evaluation
        # -------------------------------------------------------------
        md.append("\n## 3. Intent Classification Model Comparison")
        md.append(
            f"**Partitioning:** {intent_results.get('split_ratio', 'N/A')} Stratified Split "
            f"({intent_results.get('train_samples', 0)} Train / {intent_results.get('test_samples', 0)} Test) | "
            f"**Random Seed:** {intent_results.get('random_seed', EVAL_RANDOM_SEED)}\n"
        )

        md.append("| Model Architecture | Accuracy | Macro Precision | Macro Recall | Macro F1 | Weighted F1 |")
        md.append("|---|---|---|---|---|---|")
        models = intent_results.get("models", {})
        for m_name, s in models.items():
            md.append(
                f"| **{m_name}** | {s.get('accuracy', 0.0):.4f} | {s.get('macro_precision', 0.0):.4f} | "
                f"{s.get('macro_recall', 0.0):.4f} | **{s.get('macro_f1', 0.0):.4f}** | {s.get('weighted_f1', 0.0):.4f} |"
            )

        cv_ml = intent_results.get("cross_validation_ml_5fold", {})
        if cv_ml:
            md.append(
                f"\n*5-Fold Stratified Cross-Validation (TF-IDF + Logistic Regression):* "
                f"Accuracy = {cv_ml.get('mean_accuracy', 0.0):.4f} (±{cv_ml.get('std_accuracy', 0.0):.4f}), "
                f"Macro-F1 = {cv_ml.get('mean_macro_f1', 0.0):.4f} (±{cv_ml.get('std_macro_f1', 0.0):.4f})"
            )

        if "statistical_limitation" in intent_results:
            md.append(f"\n> [!NOTE]\n> {intent_results['statistical_limitation']}\n")

        # -------------------------------------------------------------
        # Section 4: Canonical Entity Linking Evaluation
        # -------------------------------------------------------------
        md.append("## 4. Canonical Entity Linking Evaluation")
        el_m = entity_linking_results.get("metrics", {})
        md.append(
            f"**Overall Canonical Linking Accuracy:** {el_m.get('exact_linking_accuracy', 0.0):.4f} | "
            f"**Out-of-KB Rejection Accuracy:** {el_m.get('out_of_kb_rejection_accuracy', 0.0):.4f} | "
            f"**Evaluated Mentions:** {el_m.get('sample_count', 0)}\n"
        )

        md.append("| Entity Type | Linking Accuracy | Correct | Total |")
        md.append("|---|---|---|---|")
        for etype, s in el_m.get("per_entity_type", {}).items():
            md.append(f"| `{etype}` | **{s.get('accuracy', 0.0):.4f}** | {s.get('correct', 0)} | {s.get('total', 0)} |")

        # -------------------------------------------------------------
        # Section 5: RAG Grounding & Citation Validation
        # -------------------------------------------------------------
        md.append("\n## 5. RAG Grounding & Citation Validation")
        rag_m = rag_results.get("metrics", {})
        md.append(
            f"**Citation Validity Rate:** {rag_m.get('citation_validity_rate', 0.0):.4f} | "
            f"**Citation Precision:** {rag_m.get('citation_precision', 0.0):.4f} | "
            f"**Evidence Coverage:** {rag_m.get('evidence_coverage', 0.0):.4f} | "
            f"**Abstention Accuracy:** {rag_m.get('abstention_accuracy', 0.0):.4f}\n"
        )
        md.append(f"> [!IMPORTANT]\n> {rag_m.get('structural_vs_semantic_note', '')}\n")

        # -------------------------------------------------------------
        # Section 6: Controlled Query Expansion Evaluation
        # -------------------------------------------------------------
        if expansion_results:
            qe_m = expansion_results.get("metrics", {})
            md.append("## 6. Controlled Query Expansion Evaluation")
            md.append(
                f"**Expansion Precision:** {qe_m.get('expansion_precision', 0.0):.4f} | "
                f"**Semantic Drift Rate:** {qe_m.get('drift_rate', 0.0):.4f} | "
                f"**Average Terms Appended:** {qe_m.get('average_terms_added', 0.0)}\n"
            )

        # -------------------------------------------------------------
        # Section 7: Human Annotation Audit
        # -------------------------------------------------------------
        md.append("## 7. Benchmark Integrity & Human Annotation Audit")
        md.append("Records requiring ongoing human annotation are strictly tracked to prevent fabricated scores:\n")
        md.append(f"- **Retrieval Benchmark:** {retrieval_experiments[0].get('sample_count', 0) if retrieval_experiments else 0} verified queries, {retrieval_experiments[0].get('requires_human_annotation_count', 0) if retrieval_experiments else 0} queued for future annotation.")
        md.append(f"- **NER Benchmark:** {ner_results.get('sample_count', 0)} verified queries, {ner_results.get('requires_human_annotation_count', 0)} queued.")
        md.append(f"- **Entity Linking Benchmark:** {entity_linking_results.get('sample_count', 0)} verified mentions, {entity_linking_results.get('requires_human_annotation_count', 0)} queued.")
        md.append(f"- **RAG Benchmark:** {rag_results.get('sample_count', 0)} verified test cases, {rag_results.get('requires_human_annotation_count', 0)} queued.\n")

        with open(target, "w", encoding="utf-8") as f:
            f.write("\n".join(md) + "\n")

        return target
