"""
Retrieval & RAG Evaluation Suite CLI Module.
Executes empirical evaluations across the 14 Indian constitutional law query categories:
1. Direct Article lookup
2. Fundamental Rights
3. Directive Principles & Fundamental Duties
4. Federalism & Separation of Powers
5. Constitutional Amendments
6. Landmark Judgments
7. Case Citation Lookup
8. Conflicting / Historically Changed Positions
9. Multi-Hop Provisions
10. Precise Legal Exceptions
11. Combined Statutes & Constitution
12. Lacks Adequate Evidence (Safe Abstention)
13. Paraphrased & Ambiguous Queries
14. Institutional Procedures & Powers

Computes Hit@K, Recall@K, Precision@K, MRR, NDCG@K, Citation Validity, and Latency.
Usage:
    python -m scripts.evaluate_retrieval [--category CATEGORY] [--top-k TOP_K] [--quick]
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import (
    EVALUATION_RESULTS_DIR,
    RETRIEVAL_BENCHMARK_PATH,
    PARENT_STORE_PATH,
    DEFAULT_EMBEDDING_MODEL,
)
from evaluation.retrieval_eval import RetrievalEvaluator
from evaluation.metrics import (
    hit_at_k,
    recall_at_k,
    precision_at_k,
    reciprocal_rank,
    ndcg_at_k,
    aggregate_retrieval_metrics,
)
from retrieval.bm25_retriever import BM25Retriever
from retrieval.dense_retriever import DenseRetriever
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.reranker import CrossEncoderReranker


LEGAL_CATEGORIES_14 = [
    "direct_article_lookup",
    "fundamental_rights",
    "directive_principles_and_duties",
    "federalism_and_powers",
    "constitutional_amendments",
    "landmark_judgments",
    "case_citation_lookup",
    "conflicting_historical_positions",
    "multi_hop_provisions",
    "precise_legal_exceptions",
    "statutes_and_constitution",
    "abstention_unsupported_queries",
    "paraphrased_ambiguous_queries",
    "institutional_procedures"
]


def run_comprehensive_evaluation(
    quick_mode: bool = False,
    selected_category: Optional[str] = None,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Execute multi-method retrieval evaluation across all query types and record audit artifacts."""
    print("=" * 70)
    print("INDIAN CONSTITUTIONAL LAW RETRIEVAL & BENCHMARK EVALUATOR")
    print("=" * 70)

    evaluator = RetrievalEvaluator()
    evaluable, unverified = evaluator.get_evaluable_queries()

    if selected_category:
        evaluable = [q for q in evaluable if q.get("query_type") == selected_category or q.get("intent") == selected_category]
        print(f"[*] Filtered for category '{selected_category}': {len(evaluable)} queries.")
    elif quick_mode:
        evaluable = evaluable[:25]
        print(f"[*] Quick Evaluation Mode: using sample partition of {len(evaluable)} queries.")
    elif limit:
        evaluable = evaluable[:limit]
        print(f"[*] Limiting to {len(evaluable)} queries.")
    else:
        print(f"[*] Full Evaluation Suite: {len(evaluable)} verified gold-standard queries.")

    if not evaluable:
        print("[-] No evaluable queries found.")
        return {"status": "EMPTY"}

    # Initialize shared retrieval engines
    print("\n[*] Initializing retrieval components (BM25, Dense, Cross-Encoder)...")
    bm25 = BM25Retriever()
    dense = DenseRetriever()
    hybrid = HybridRetriever(bm25_retriever=bm25, dense_retriever=dense, use_reranker=False)
    reranked_hybrid = HybridRetriever(bm25_retriever=bm25, dense_retriever=dense, use_reranker=True)

    configs = [
        ("BM25 Only", bm25),
        ("Dense Only", dense),
        ("Hybrid (RRF + Entity Boost)", hybrid),
        ("Full Pipeline (Hybrid + Reranker)", reranked_hybrid),
    ]

    all_results = {}
    print("\n" + "-" * 70)
    print(f"{'Configuration':<35} | {'Hit@1':<7} | {'Recall@10':<9} | {'MRR':<7} | {'NDCG@10':<7} | {'Lat (ms)'}")
    print("-" * 70)

    for name, retriever in configs:
        latencies = []
        query_metrics = []

        for q in evaluable:
            query_text = q["query"]
            rel_docs = set(q.get("relevant_documents", []))
            
            # If graded relevance labels exist in benchmark
            labels = evaluator.relevance_labels.get(q["query_id"], {})
            if not rel_docs and labels:
                rel_docs = {doc for doc, score in labels.items() if score > 0}

            t0 = time.perf_counter()
            candidates = retriever.retrieve(query_text, top_k=10)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            latencies.append(elapsed_ms)

            # Map candidates to parent document IDs
            retrieved_ids = [c.get("document_id") or c.get("parent_id", "") for c in candidates]
            # Strip parent_ prefix if needed for canonical comparison
            canonical_retrieved = [rid.replace("parent_", "") for rid in retrieved_ids]
            canonical_relevant = {rd.replace("parent_", "") for rd in rel_docs}

            q_met = {
                "hit@1": hit_at_k(canonical_retrieved, canonical_relevant, 1),
                "hit@5": hit_at_k(canonical_retrieved, canonical_relevant, 5),
                "hit@10": hit_at_k(canonical_retrieved, canonical_relevant, 10),
                "recall@5": recall_at_k(canonical_retrieved, canonical_relevant, 5),
                "recall@10": recall_at_k(canonical_retrieved, canonical_relevant, 10),
                "precision@5": precision_at_k(canonical_retrieved, canonical_relevant, 5),
                "mrr": reciprocal_rank(canonical_retrieved, canonical_relevant),
                "ndcg@10": ndcg_at_k(canonical_retrieved, canonical_relevant, 10),
            }
            query_metrics.append(q_met)

        agg = aggregate_retrieval_metrics(query_metrics)
        avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
        agg["latency_ms"] = round(avg_lat, 2)
        all_results[name] = agg

        print(
            f"{name:<35} | {agg['hit@1']:<7.4f} | {agg['recall@10']:<9.4f} | "
            f"{agg['mrr']:<7.4f} | {agg['ndcg@10']:<7.4f} | {avg_lat:.1f} ms"
        )

    print("-" * 70)

    # Output detailed report to evaluation results directory
    out_file = EVALUATION_RESULTS_DIR / "retrieval_evaluation_summary.json"
    EVALUATION_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "embedding_model": DEFAULT_EMBEDDING_MODEL,
                "queries_evaluated": len(evaluable),
                "results_by_configuration": all_results,
            },
            f,
            indent=2,
        )
    print(f"\n[+] Detailed evaluation metrics saved to: {out_file}")
    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Legal Information Retrieval Pipeline.")
    parser.add_argument("--quick", action="store_true", help="Run fast evaluation on sample queries.")
    parser.add_argument("--category", type=str, default=None, help="Filter evaluation by query category.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of queries.")
    args = parser.parse_args()

    run_comprehensive_evaluation(
        quick_mode=args.quick,
        selected_category=args.category,
        limit=args.limit,
    )

