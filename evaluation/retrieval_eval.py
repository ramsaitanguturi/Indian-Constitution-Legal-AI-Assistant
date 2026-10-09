"""
Information Retrieval Benchmark Evaluator for Indian Constitutional Law.

Evaluates:
- BM25 Okapi baseline
- Dense Semantic Retrieval (ChromaDB + all-MiniLM-L6-v2)
- BM25 + Dense (without RRF)
- Reciprocal Rank Fusion (RRF)
- Legal Entity Boost
- Cross-Encoder Reranking
- Full End-to-End Hybrid Pipeline

Metrics:
- Hit@1, Hit@3, Hit@5, Hit@10
- Recall@5, Recall@10
- MRR (Mean Reciprocal Rank)
- NDCG@5, NDCG@10
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Union, Tuple

from config import (
    RETRIEVAL_BENCHMARK_PATH,
    RELEVANCE_LABELS_PATH,
    PARENT_STORE_PATH,
)
from evaluation.metrics import (
    hit_at_k,
    recall_at_k,
    precision_at_k,
    reciprocal_rank,
    ndcg_at_k,
    aggregate_retrieval_metrics,
)


class RetrievalEvaluator:
    """
    Evaluator for Information Retrieval models against gold-standard relevance judgments.
    """

    def __init__(
        self,
        benchmark_path: Optional[Union[str, Path]] = None,
        relevance_labels_path: Optional[Union[str, Path]] = None,
        parent_store: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.benchmark_path = Path(benchmark_path or RETRIEVAL_BENCHMARK_PATH)
        self.relevance_labels_path = Path(relevance_labels_path or RELEVANCE_LABELS_PATH)
        self.parent_store = parent_store or {}

        if not self.parent_store and os.path.exists(PARENT_STORE_PATH):
            try:
                with open(PARENT_STORE_PATH, "r", encoding="utf-8") as f:
                    self.parent_store = json.load(f)
            except Exception:
                pass

        self.queries: List[Dict[str, Any]] = []
        self.relevance_labels: Dict[str, Dict[str, float]] = {}
        self.load_benchmark()

    def load_benchmark(self) -> None:
        """Loads benchmark queries and graded relevance labels."""
        if self.benchmark_path.exists():
            with open(self.benchmark_path, "r", encoding="utf-8") as f:
                self.queries = json.load(f)
        else:
            self.queries = []

        if self.relevance_labels_path.exists():
            with open(self.relevance_labels_path, "r", encoding="utf-8") as f:
                self.relevance_labels = json.load(f)
        else:
            self.relevance_labels = {}

    def get_evaluable_queries(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Partitions queries into verified evaluable queries and queries requiring human annotation.
        Prevents fabricated results by explicitly excluding unannotated queries.
        """
        evaluable = []
        requires_annotation = []

        for q in self.queries:
            status = q.get("human_annotation_status", "verified")
            has_relevant = len(q.get("relevant_documents", [])) > 0 or q.get("query_id") in self.relevance_labels

            if status == "verified" and has_relevant:
                evaluable.append(q)
            else:
                requires_annotation.append(q)

        return evaluable, requires_annotation

    def evaluate_retriever(
        self,
        retriever_instance: Any,
        experiment_name: str = "retriever_evaluation",
        top_k: int = 10,
        eval_queries: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Executes evaluation against an instantiated retriever.
        
        Args:
            retriever_instance: Object with `.retrieve(query, top_k=...)` method.
            experiment_name: Descriptive name for experiment logging.
            top_k: Number of candidates to retrieve per query.
            eval_queries: Optional override of queries to evaluate.
            
        Returns:
            Dictionary with aggregated metrics, query breakdown, and reproducibility metadata.
        """
        evaluable, queued = self.get_evaluable_queries()
        queries_to_eval = eval_queries if eval_queries is not None else evaluable

        if not queries_to_eval:
            return {
                "experiment_name": experiment_name,
                "status": "NO_EVALUABLE_QUERIES",
                "sample_count": 0,
                "requires_annotation_count": len(queued),
                "metrics": aggregate_retrieval_metrics([]),
                "query_details": []
            }

        start_time = time.time()
        query_level_metrics: List[Dict[str, float]] = []
        query_details: List[Dict[str, Any]] = []

        for q in queries_to_eval:
            qid = q["query_id"]
            query_str = q["query"]

            # Ground truth targets
            gold_docs = set(q.get("relevant_documents", []))
            gold_chunks = set(q.get("relevant_chunks", []))
            graded_labels = self.relevance_labels.get(qid, {d: 1.0 for d in gold_docs})

            # Execute retrieval
            try:
                retrieved_results = retriever_instance.retrieve(query_str, top_k=top_k)
            except TypeError:
                retrieved_results = retriever_instance.retrieve(query_str)

            # Extract retrieved IDs (both document/parent level and chunk level)
            retrieved_doc_ids: List[str] = []
            retrieved_chunk_ids: List[str] = []

            for item in retrieved_results:
                if isinstance(item, dict):
                    pid = item.get("parent_id")
                    cid = item.get("chunk_id")
                    if pid and pid not in retrieved_doc_ids:
                        retrieved_doc_ids.append(pid)
                    if cid and cid not in retrieved_chunk_ids:
                        retrieved_chunk_ids.append(cid)
                elif isinstance(item, (list, tuple)) and len(item) >= 1:
                    cid = item[0]
                    retrieved_chunk_ids.append(cid)
                    # Lookup parent from parent store if available
                    if self.parent_store and cid in self.parent_store:
                        pid = self.parent_store[cid].get("parent_id")
                        if pid and pid not in retrieved_doc_ids:
                            retrieved_doc_ids.append(pid)

            # For document-level evaluation: use retrieved_doc_ids; fallback to chunk IDs
            eval_ids = retrieved_doc_ids if retrieved_doc_ids else retrieved_chunk_ids
            eval_gold = gold_docs if gold_docs else gold_chunks

            # Compute metrics for this query
            h1 = hit_at_k(eval_ids, eval_gold, 1)
            h3 = hit_at_k(eval_ids, eval_gold, 3)
            h5 = hit_at_k(eval_ids, eval_gold, 5)
            h10 = hit_at_k(eval_ids, eval_gold, 10)

            r5 = recall_at_k(eval_ids, eval_gold, 5)
            r10 = recall_at_k(eval_ids, eval_gold, 10)

            rr = reciprocal_rank(eval_ids, eval_gold)

            ndcg5 = ndcg_at_k(eval_ids, graded_labels, 5)
            ndcg10 = ndcg_at_k(eval_ids, graded_labels, 10)

            qm = {
                "Hit@1": h1,
                "Hit@3": h3,
                "Hit@5": h5,
                "Hit@10": h10,
                "Recall@5": r5,
                "Recall@10": r10,
                "MRR": rr,
                "NDCG@5": ndcg5,
                "NDCG@10": ndcg10
            }
            query_level_metrics.append(qm)

            query_details.append({
                "query_id": qid,
                "query": query_str,
                "intent": q.get("intent", ""),
                "gold_relevant": list(eval_gold),
                "retrieved_top_5": eval_ids[:5],
                "metrics": qm
            })

        latency = round(time.time() - start_time, 3)
        aggregated = aggregate_retrieval_metrics(query_level_metrics)

        return {
            "experiment_name": experiment_name,
            "status": "COMPLETED",
            "sample_count": len(query_level_metrics),
            "requires_human_annotation_count": len(queued),
            "total_latency_seconds": latency,
            "avg_latency_ms": round((latency / len(query_level_metrics)) * 1000, 2),
            "metrics": aggregated,
            "query_details": query_details
        }
