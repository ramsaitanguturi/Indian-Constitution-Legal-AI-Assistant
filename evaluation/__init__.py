"""
Evaluation and Empirical Benchmark Package for Indian Constitutional Legal AI Assistant.

Provides modular evaluators, mathematical metrics, and report generators for:
- Hybrid Information Retrieval (BM25, Dense, RRF, Entity Boost, Cross-Encoder)
- Legal Named Entity Recognition (10 constitutional categories)
- Intent Classification (Rule vs ML vs Hybrid with train/test separation)
- Canonical Entity Linking (exact ID resolution and nil handling)
- Evidence-Grounded Generation and Citation Validation
- Controlled Query Expansion
"""

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
from evaluation.retrieval_eval import RetrievalEvaluator
from evaluation.ner_eval import NEREvaluator
from evaluation.intent_eval import IntentEvaluator
from evaluation.classification_eval import ClassificationEvaluator
from evaluation.entity_linking_eval import EntityLinkingEvaluator
from evaluation.rag_eval import RAGEvaluator
from evaluation.qa_eval import QAEvaluator
from evaluation.report_generator import ReportGenerator
from evaluation.benchmark_runner import BenchmarkRunner

__all__ = [
    # Metrics
    "hit_at_k",
    "recall_at_k",
    "precision_at_k",
    "reciprocal_rank",
    "mean_reciprocal_rank",
    "dcg_at_k",
    "ndcg_at_k",
    "aggregate_retrieval_metrics",
    "calculate_ner_metrics",
    "calculate_classification_metrics",
    "calculate_entity_linking_metrics",
    "calculate_rag_citation_metrics",
    "calculate_query_expansion_metrics",
    "ALL_LEGAL_ENTITY_TYPES",
    # Evaluators
    "RetrievalEvaluator",
    "NEREvaluator",
    "IntentEvaluator",
    "ClassificationEvaluator",
    "EntityLinkingEvaluator",
    "RAGEvaluator",
    "QAEvaluator",
    "ReportGenerator",
    "BenchmarkRunner",
]
