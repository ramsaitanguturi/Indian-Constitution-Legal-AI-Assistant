"""
Experiment 05: Hybrid Retrieval with Legal Entity-Aware Rank Boosting.
Evaluates RRF fusion enhanced with domain-specific legal entity matching (+0.15 boost) on 200 queries.
Metrics: Hit@1, Hit@5, Hit@10, Recall@5, Recall@10, MRR, NDCG@5, NDCG@10.
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from retrieval.bm25_retriever import BM25Retriever
from retrieval.dense_retriever import DenseRetriever
from retrieval.hybrid_retriever import HybridRetriever
from evaluation.retrieval_eval import RetrievalEvaluator
from config import PARENT_STORE_PATH


def run_experiment():
    print("=" * 65)
    print("EXPERIMENT 05: RRF + DOMAIN-SPECIFIC LEGAL ENTITY BOOSTING")
    print("=" * 65)

    parent_store = {}
    if PARENT_STORE_PATH.exists():
        with open(PARENT_STORE_PATH, "r", encoding="utf-8") as f:
            parent_store = json.load(f)

    bm25 = BM25Retriever(parent_store=parent_store)
    dense = DenseRetriever(parent_store=parent_store)
    hybrid = HybridRetriever(
        bm25_retriever=bm25,
        dense_retriever=dense,
        parent_store=parent_store,
        use_bm25=True,
        use_dense=True,
        use_rrf=True,
        use_entity_boost=True,
        use_reranker=False,
    )
    evaluator = RetrievalEvaluator(parent_store=parent_store)

    results = evaluator.evaluate_retriever(
        retriever_instance=hybrid,
        experiment_name="Exp_05_RRF_Entity_Boost",
        top_k=10,
    )

    metrics = results["metrics"]
    print(f"Evaluated on {results['sample_count']} benchmark queries.")
    print(f"Average query latency: {results.get('avg_latency_ms', 0):.2f} ms")
    print("-" * 65)
    for k, v in metrics.items():
        print(f"  {k:<12}: {v:.4f}")
    print("=" * 65)

    out_file = PROJECT_ROOT / "experiments" / "results" / "experiment_05_entity_boost.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[SAVED] Results saved to {out_file}")
    return results


if __name__ == "__main__":
    run_experiment()
