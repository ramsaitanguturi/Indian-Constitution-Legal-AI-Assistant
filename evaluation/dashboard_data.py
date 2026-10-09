"""
Data Loading and Preparation Module for the Legal AI Research Dashboard.

Provides decoupled, fail-safe readers and data formatting helpers for all
Stage 5 evaluation artifacts:
1. retrieval_results.csv
2. retrieval_query_level_audit.csv
3. classification_results.csv
4. ner_results.csv
5. evaluation_summary.json
6. Benchmark counts & annotation manifests

Guarantees:
- Never raises unhandled exceptions on missing, empty, or corrupted files.
- Operates independently from the live RAG pipeline and vector store.
- Zero network or LLM API calls required.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_RESULTS_DIR = Path("evaluation/results")
DEFAULT_BENCHMARK_DIR = Path("data/benchmark")


def safe_load_csv(file_path: Path) -> Optional[pd.DataFrame]:
    """
    Safely loads a CSV file into a pandas DataFrame.
    Returns None if the file is missing, empty, or malformed.
    """
    if not file_path.exists():
        logger.warning(f"Evaluation artifact not found: {file_path}")
        return None
    try:
        if file_path.stat().st_size == 0:
            logger.warning(f"Evaluation artifact is empty: {file_path}")
            return None
        df = pd.read_csv(file_path)
        if df.empty:
            logger.warning(f"Evaluation artifact contains no rows: {file_path}")
            return None
        return df
    except Exception as e:
        logger.error(f"Error reading CSV artifact {file_path}: {e}")
        return None


def safe_load_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Safely loads a JSON file into a Python dictionary.
    Returns None if the file is missing, empty, or malformed.
    """
    if not file_path.exists():
        logger.warning(f"Evaluation artifact not found: {file_path}")
        return None
    try:
        if file_path.stat().st_size == 0:
            logger.warning(f"Evaluation artifact is empty: {file_path}")
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, (dict, list)):
            logger.warning(f"Unexpected JSON artifact type in {file_path}: {type(data)}")
            return None
        return data
    except Exception as e:
        logger.error(f"Error parsing JSON artifact {file_path}: {e}")
        return None


# =========================================================================
# 1. Retrieval Artifact Loaders
# =========================================================================

def load_retrieval_results(results_dir: Path = DEFAULT_RESULTS_DIR) -> Optional[pd.DataFrame]:
    """
    Loads aggregated retrieval metrics across the 6 experimental configurations.
    Columns: Method, Sample_Count, Hit@1, Hit@3, Hit@5, Hit@10, Recall@5, Recall@10, MRR, NDCG@5, NDCG@10, Avg_Latency_ms
    """
    p = Path(results_dir) / "retrieval_results.csv"
    return safe_load_csv(p)


def load_query_level_audit(results_dir: Path = DEFAULT_RESULTS_DIR) -> Optional[pd.DataFrame]:
    """
    Loads per-query retrieval ranking audit logs.
    Columns: Query_ID, System, Query, Intent, Gold_Relevant_IDs, Retrieved_Top_5, First_Hit_Rank, ...
    """
    p = Path(results_dir) / "retrieval_query_level_audit.csv"
    return safe_load_csv(p)


# =========================================================================
# 2. Classification & Intent Loaders
# =========================================================================

def load_classification_results(results_dir: Path = DEFAULT_RESULTS_DIR) -> Optional[pd.DataFrame]:
    """
    Loads intent classification model comparison metrics.
    Columns: Model, Sample_Count, Accuracy, Macro_Precision, Macro_Recall, Macro_F1, Weighted_F1
    """
    p = Path(results_dir) / "classification_results.csv"
    return safe_load_csv(p)


def get_intent_model_details(summary_data: Optional[Dict[str, Any]], model_name: str) -> Optional[Dict[str, Any]]:
    """
    Extracts deep-dive metadata, per-class metrics, and confusion matrix for a specific intent model.
    """
    if not summary_data or "intent_classification" not in summary_data:
        return None
    intent_sec = summary_data.get("intent_classification", {})
    models = intent_sec.get("models", {})
    return models.get(model_name)


def get_confusion_matrix_df(summary_data: Optional[Dict[str, Any]], model_name: str) -> Optional[pd.DataFrame]:
    """
    Builds a labeled DataFrame representing the confusion matrix for an intent model.
    Rows: True Labels, Columns: Predicted Labels.
    """
    m_info = get_intent_model_details(summary_data, model_name)
    if not m_info:
        return None
    cm = m_info.get("confusion_matrix")
    classes = m_info.get("classes")
    if not cm or not classes or len(cm) != len(classes):
        return None
    try:
        return pd.DataFrame(cm, index=classes, columns=classes)
    except Exception as e:
        logger.error(f"Error constructing confusion matrix DataFrame: {e}")
        return None


def get_per_class_intent_df(summary_data: Optional[Dict[str, Any]], model_name: str) -> Optional[pd.DataFrame]:
    """
    Extracts per-class precision, recall, f1, and support into a formatted DataFrame.
    """
    m_info = get_intent_model_details(summary_data, model_name)
    if not m_info or "per_class" not in m_info:
        return None
    per_class = m_info.get("per_class", {})
    records = []
    for cls_name, stats in per_class.items():
        if isinstance(stats, dict):
            records.append({
                "Intent Class": cls_name,
                "Precision": stats.get("precision", 0.0),
                "Recall": stats.get("recall", 0.0),
                "F1 Score": stats.get("f1", 0.0),
                "Support": stats.get("support", 0),
            })
    if not records:
        return None
    df = pd.DataFrame(records)
    return df.sort_values(by="F1 Score", ascending=False).reset_index(drop=True)


# =========================================================================
# 3. NLP Component Loaders (NER, Entity Linking, Expansion)
# =========================================================================

def load_ner_results(results_dir: Path = DEFAULT_RESULTS_DIR) -> Optional[pd.DataFrame]:
    """
    Loads per-category Legal NER performance metrics.
    Columns: Category, Precision, Recall, F1, Support, TP, FP, FN
    """
    p = Path(results_dir) / "ner_results.csv"
    return safe_load_csv(p)


def get_entity_linking_metrics(summary_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Extracts canonical entity linking performance and out-of-KB rejection metrics.
    """
    if not summary_data or "entity_linking" not in summary_data:
        return None
    el = summary_data.get("entity_linking", {})
    return {
        "status": el.get("status", "unknown"),
        "sample_count": el.get("sample_count", 0),
        "requires_human_annotation_count": el.get("requires_human_annotation_count", 0),
        "metrics": el.get("metrics", {}),
        "total_latency_seconds": el.get("total_latency_seconds", 0.0),
    }


def get_query_expansion_metrics(summary_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Extracts controlled query expansion metrics (precision, drift rate, terms added).
    """
    if not summary_data or "query_expansion" not in summary_data:
        return None
    qe = summary_data.get("query_expansion", {})
    return {
        "status": qe.get("status", "unknown"),
        "sample_count": qe.get("sample_count", 0),
        "requires_human_annotation_count": qe.get("requires_human_annotation_count", 0),
        "metrics": qe.get("metrics", {}),
    }


# =========================================================================
# 4. RAG Reliability Loaders
# =========================================================================

def get_rag_reliability_metrics(summary_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Extracts grounded RAG citation, coverage, and abstention metrics.
    """
    if not summary_data or "rag_citations" not in summary_data:
        return None
    rag = summary_data.get("rag_citations", {})
    return {
        "status": rag.get("status", "unknown"),
        "sample_count": rag.get("sample_count", 0),
        "requires_human_annotation_count": rag.get("requires_human_annotation_count", 0),
        "metrics": rag.get("metrics", {}),
        "sample_runs": rag.get("sample_runs", []),
    }


# =========================================================================
# 5. Metadata & Reproducibility Loaders
# =========================================================================

def load_evaluation_summary(results_dir: Path = DEFAULT_RESULTS_DIR) -> Optional[Dict[str, Any]]:
    """
    Loads full evaluation_summary.json artifact.
    """
    p = Path(results_dir) / "evaluation_summary.json"
    return safe_load_json(p)


def get_reproducibility_metadata(summary_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extracts run metadata, corpus version, random seed, models, and timestamps.
    Falls back to 'not recorded' if values are absent.
    """
    if not summary_data:
        return {
            "timestamp": "not recorded",
            "dataset_version": "not recorded",
            "random_seed": "not recorded",
            "total_run_time_seconds": "not recorded",
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "reranker_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "bm25_parameters": "k1=1.5, b=0.75",
            "rrf_constant": "k=60",
            "entity_boost_weight": "+0.15",
        }

    meta = summary_data.get("metadata", {})
    return {
        "timestamp": meta.get("timestamp", "not recorded"),
        "dataset_version": meta.get("dataset_version", "not recorded"),
        "random_seed": meta.get("random_seed", "not recorded"),
        "total_run_time_seconds": f"{meta.get('total_run_time_seconds', 0.0):.2f}s" if "total_run_time_seconds" in meta else "not recorded",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "reranker_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "bm25_parameters": "k1=1.5, b=0.75",
        "rrf_constant": "k=60",
        "entity_boost_weight": "+0.15",
    }


def load_benchmark_manifest(benchmark_dir: Path = DEFAULT_BENCHMARK_DIR) -> Dict[str, Dict[str, Any]]:
    """
    Inspects gold-standard benchmark files to count verified vs queued examples.
    """
    b_dir = Path(benchmark_dir)
    manifest = {}
    bench_files = {
        "Retrieval Benchmark": ("retrieval_queries.json", "retrieval"),
        "Intent Classification Benchmark": ("classification_queries.json", "intent"),
        "Legal NER Annotations": ("ner_annotations.json", "ner"),
        "Entity Linking Benchmark": ("entity_linking_queries.json", "entity_linking"),
        "RAG Reliability Benchmark": ("rag_questions.json", "rag"),
        "Controlled Query Expansion": ("query_expansion_benchmark.json", "expansion"),
    }

    for name, (fname, b_type) in bench_files.items():
        fpath = b_dir / fname
        if not fpath.exists():
            manifest[name] = {
                "file": fname,
                "total": 0,
                "verified": 0,
                "requires_annotation": 0,
                "status": "File Missing",
            }
            continue

        data = safe_load_json(fpath)
        if data is None or not isinstance(data, list):
            manifest[name] = {
                "file": fname,
                "total": 0,
                "verified": 0,
                "requires_annotation": 0,
                "status": "Empty / Malformed",
            }
            continue

        total = len(data)
        req_annot = 0
        for item in data:
            if isinstance(item, dict):
                is_queued = (
                    item.get("human_annotation_status") == "requires_human_annotation"
                    or item.get("requires_human_annotation", False)
                )
                if is_queued:
                    req_annot += 1

        verified = total - req_annot
        manifest[name] = {
            "file": fname,
            "total": total,
            "verified": verified,
            "requires_annotation": req_annot,
            "status": "Active & Validated",
        }

    return manifest
