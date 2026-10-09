"""
Experiment 01: BM25 Lexical Retrieval Baseline.
Evaluates standalone BM25Okapi retrieval on the 200-query Indian Constitutional benchmark.
Metrics: Hit@1, Hit@5, Hit@10, Recall@5, Recall@10, MRR, NDCG@5, NDCG@10.
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from retrieval.bm25_retriever import BM25Retriever
from evaluation.retrieval_eval import RetrievalEvaluator
from evaluation.metrics import print_retrieval_metrics_table
from config import PARENT_STORE_PATH


def run_experiment():
    print("=" * 65)
    print("EXPERIMENT 01: BM25 LEXICAL RETRIEVAL BASELINE")
    print("=" * 65)

    parent_store = {}
    if PARENT_STORE_PATH.exists():
        with open(PARENT_STORE_PATH, "r", encoding="utf-8") as f:
            parent_store = json.load(f)

    bm25 = BM25Retriever(parent_store=parent_store)
    evaluator = RetrievalEvaluator(parent_store=parent_store)

    results = evaluator.evaluate_retriever(
        retriever_instance=bm25,
        experiment_name="Exp_01_BM25_Baseline",
        top_k=10
    )

    metrics = results["metrics"]
    print(f"Evaluated on {results['sample_count']} benchmark queries.")
    print(f"Average query latency: {results.get('avg_latency_ms', 0):.2f} ms")
    print("-" * 65)
    for k, v in metrics.items():
        print(f"  {k:<12}: {v:.4f}")
    print("=" * 65)

    out_file = PROJECT_ROOT / "experiments" / "results" / "experiment_01_bm25.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[SAVED] Results saved to {out_file}")
    return results


if __name__ == "__main__":
    run_experiment()
