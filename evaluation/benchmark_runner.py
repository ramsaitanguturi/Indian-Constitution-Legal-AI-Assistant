"""
Master Benchmark Runner for Indian Constitutional Legal AI Assistant.

Coordinates and executes:
1. Retrieval Evaluation across all ablation configurations:
   - BM25 Only
   - Dense Only
   - BM25 + Dense (without RRF)
   - BM25 + Dense + RRF
   - RRF + Legal Entity Boost
   - Full Pipeline (+ Cross-Encoder Reranker)
2. Legal NER Evaluation across all 10 entity categories
3. Intent Classification Evaluation (Rule vs ML vs Hybrid with zero data leakage)
4. Canonical Entity Linking Evaluation
5. Grounded RAG & Citation Integrity Evaluation
6. Controlled Query Expansion Evaluation

Outputs all machine-readable CSVs, JSON summaries, and Markdown reports.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Ensure project root is in PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    EVALUATION_RESULTS_DIR,
    PARENT_STORE_PATH,
    DATASET_VERSION,
    EVAL_RANDOM_SEED,
)
from evaluation.retrieval_eval import RetrievalEvaluator
from evaluation.ner_eval import NEREvaluator
from evaluation.intent_eval import IntentEvaluator
from evaluation.entity_linking_eval import EntityLinkingEvaluator
from evaluation.rag_eval import RAGEvaluator
from evaluation.report_generator import ReportGenerator
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.bm25_retriever import BM25Retriever
from retrieval.dense_retriever import DenseRetriever


class BenchmarkRunner:
    """
    Orchestrates execution of the entire Stage 5 evaluation suite.
    """

    def __init__(
        self,
        results_dir: Optional[Path] = None,
        parent_store: Optional[Dict[str, Dict[str, Any]]] = None,
        quick_mode: bool = False
    ):
        self.results_dir = Path(results_dir or EVALUATION_RESULTS_DIR)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.quick_mode = quick_mode

        # Load parent store
        self.parent_store = parent_store or {}
        if not self.parent_store and os.path.exists(PARENT_STORE_PATH):
            try:
                with open(PARENT_STORE_PATH, "r", encoding="utf-8") as f:
                    self.parent_store = json.load(f)
            except Exception:
                pass

        self.report_generator = ReportGenerator(output_dir=self.results_dir)

    def run_retrieval_suite(self) -> List[Dict[str, Any]]:
        """
        Executes IR evaluations across the 6 core configurations:
        1. BM25 Only
        2. Dense Only
        3. BM25 + Dense (Linear without RRF)
        4. BM25 + Dense + RRF
        5. RRF + Entity Boost
        6. Full Pipeline (RRF + Entity Boost + Cross-Encoder Reranker)
        """
        print("\n" + "=" * 60)
        print("1. RUNNING RETRIEVAL ABLATION BENCHMARK SUITE")
        print("=" * 60)

        evaluator = RetrievalEvaluator(parent_store=self.parent_store)
        evaluable, queued = evaluator.get_evaluable_queries()
        print(f"[RETRIEVAL] Found {len(evaluable)} verified benchmark queries ({len(queued)} queued for annotation).")

        # Initialize shared components to optimize runtime
        bm25 = BM25Retriever(parent_store=self.parent_store)
        dense = DenseRetriever(parent_store=self.parent_store)

        configurations = [
            ("Exp 1: BM25 Only", {"use_bm25": True, "use_dense": False, "use_rrf": False, "use_entity_boost": False, "use_reranker": False}),
            ("Exp 2: Dense Only", {"use_bm25": False, "use_dense": True, "use_rrf": False, "use_entity_boost": False, "use_reranker": False}),
            ("Exp 3: BM25 + Dense (Linear)", {"use_bm25": True, "use_dense": True, "use_rrf": False, "use_entity_boost": False, "use_reranker": False}),
            ("Exp 4: BM25 + Dense + RRF", {"use_bm25": True, "use_dense": True, "use_rrf": True, "use_entity_boost": False, "use_reranker": False}),
            ("Exp 5: RRF + Entity Boost", {"use_bm25": True, "use_dense": True, "use_rrf": True, "use_entity_boost": True, "use_reranker": False}),
            ("Exp 6: Full Pipeline (+ Cross-Encoder)", {"use_bm25": True, "use_dense": True, "use_rrf": True, "use_entity_boost": True, "use_reranker": True}),
        ]

        # In quick mode, evaluate top 5 queries for fast unit testing
        queries_to_run = evaluable[:5] if self.quick_mode else evaluable
        retrieval_results = []

        for exp_name, flags in configurations:
            print(f"  -> Evaluating '{exp_name}'...")
            retriever = HybridRetriever(
                bm25_retriever=bm25,
                dense_retriever=dense,
                parent_store=self.parent_store,
                **flags
            )
            res = evaluator.evaluate_retriever(
                retriever_instance=retriever,
                experiment_name=exp_name,
                top_k=10,
                eval_queries=queries_to_run
            )
            retrieval_results.append(res)
            m = res.get("metrics", {})
            print(f"     Hit@5: {m.get('Hit@5', 0.0):.4f} | MRR: {m.get('MRR', 0.0):.4f} | NDCG@10: {m.get('NDCG@10', 0.0):.4f}")

        # Save CSV
        csv_path = self.report_generator.save_retrieval_csv(retrieval_results)
        audit_csv_path = self.report_generator.save_retrieval_query_audit_csv(retrieval_results)
        print(f"[RETRIEVAL] Saved results table to {csv_path}")
        print(f"[RETRIEVAL] Saved query-level audit log to {audit_csv_path}")
        return retrieval_results

    def run_ner_suite(self) -> Dict[str, Any]:
        """Executes Legal NER evaluation."""
        print("\n" + "=" * 60)
        print("2. RUNNING LEGAL NER BENCHMARK SUITE")
        print("=" * 60)

        evaluator = NEREvaluator()
        verified, queued = evaluator.get_evaluable_records()
        print(f"[NER] Found {len(verified)} verified records ({len(queued)} queued for human annotation).")

        res = evaluator.evaluate(exact_span_match=True, experiment_name="LegalNER_Exact_Span")
        m = res.get("metrics", {})
        print(f"  -> Exact Span Micro-F1: {m.get('micro_f1', 0.0):.4f} | Macro-F1: {m.get('macro_f1', 0.0):.4f}")

        # Save CSV
        csv_path = self.report_generator.save_ner_csv(res)
        print(f"[NER] Saved per-class breakdown to {csv_path}")
        return res

    def run_intent_suite(self) -> Dict[str, Any]:
        """Executes Intent Classification evaluation."""
        print("\n" + "=" * 60)
        print("3. RUNNING INTENT CLASSIFICATION BENCHMARK SUITE")
        print("=" * 60)

        evaluator = IntentEvaluator()
        print(f"[INTENT] Found {len(evaluator.queries)} queries across {len(set(evaluator.labels))} classes.")
        res = evaluator.run_comparative_evaluation()

        models = res.get("models", {})
        for name, stats in models.items():
            print(f"  -> {name}: Accuracy = {stats.get('accuracy', 0.0):.4f} | Macro-F1 = {stats.get('macro_f1', 0.0):.4f}")

        # Save CSV
        csv_path = self.report_generator.save_classification_csv(res)
        print(f"[INTENT] Saved model comparison to {csv_path}")
        return res

    def run_entity_linking_suite(self) -> Dict[str, Any]:
        """Executes Canonical Entity Linking evaluation."""
        print("\n" + "=" * 60)
        print("4. RUNNING CANONICAL ENTITY LINKING BENCHMARK SUITE")
        print("=" * 60)

        evaluator = EntityLinkingEvaluator()
        res = evaluator.evaluate(experiment_name="Canonical_Entity_Linker")
        m = res.get("metrics", {})
        print(f"  -> Overall Canonical Linking Accuracy: {m.get('exact_linking_accuracy', 0.0):.4f}")
        print(f"  -> Out-of-KB Rejection Accuracy: {m.get('out_of_kb_rejection_accuracy', 0.0):.4f}")
        return res

    def run_rag_suite(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Executes RAG citation integrity, grounding, and expansion evaluation."""
        print("\n" + "=" * 60)
        print("5. RUNNING RAG CITATION INTEGRITY & GROUNDING SUITE")
        print("=" * 60)

        evaluator = RAGEvaluator()
        rag_res = evaluator.evaluate_citation_validation()
        m = rag_res.get("metrics", {})
        print(f"  -> Citation Validity Rate: {m.get('citation_validity_rate', 0.0):.4f}")
        print(f"  -> Citation Precision: {m.get('citation_precision', 0.0):.4f}")
        print(f"  -> Abstention Accuracy: {m.get('abstention_accuracy', 0.0):.4f}")

        print("\n  -> Evaluating Controlled Query Expansion...")
        exp_res = evaluator.evaluate_query_expansion()
        em = exp_res.get("metrics", {})
        print(f"     Expansion Precision: {em.get('expansion_precision', 0.0):.4f} | Drift Rate: {em.get('drift_rate', 0.0):.4f}")

        return rag_res, exp_res

    def run_all(self) -> Dict[str, Any]:
        """Executes all benchmarks and generates master outputs."""
        start_all = time.time()
        print("\n" + "#" * 60)
        print("STARTING COMPREHENSIVE STAGE 5 EVALUATION RUN")
        print("#" * 60)

        retrieval_res = self.run_retrieval_suite()
        ner_res = self.run_ner_suite()
        intent_res = self.run_intent_suite()
        entity_linking_res = self.run_entity_linking_suite()
        rag_res, expansion_res = self.run_rag_suite()

        # Generate Markdown summary report
        md_path = self.report_generator.generate_markdown_report(
            retrieval_experiments=retrieval_res,
            ner_results=ner_res,
            intent_results=intent_res,
            entity_linking_results=entity_linking_res,
            rag_results=rag_res,
            expansion_results=expansion_res,
            filename="evaluation_report.md"
        )
        print(f"\n[REPORT] Generated Markdown report at: {md_path}")

        # Generate consolidated JSON summary
        summary = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "dataset_version": DATASET_VERSION,
                "random_seed": EVAL_RANDOM_SEED,
                "total_run_time_seconds": round(time.time() - start_all, 3),
                "quick_mode": self.quick_mode
            },
            "retrieval": retrieval_res,
            "ner": ner_res,
            "intent_classification": intent_res,
            "entity_linking": entity_linking_res,
            "rag_citations": rag_res,
            "query_expansion": expansion_res
        }

        json_path = self.report_generator.save_json(summary, "evaluation_summary.json")
        print(f"[REPORT] Saved consolidated JSON summary to: {json_path}")
        print("\n" + "#" * 60)
        print("EVALUATION SUITE COMPLETED SUCCESSFULLY")
        print("#" * 60)
        return summary


def main():
    parser = argparse.ArgumentParser(description="Run Stage 5 Evaluation Framework")
    parser.add_argument("--all", action="store_true", default=True, help="Run all benchmarks")
    parser.add_argument("--quick", action="store_true", default=False, help="Run fast mode (subset of queries)")
    parser.add_argument("--retrieval-only", action="store_true", help="Run only retrieval benchmarks")
    parser.add_argument("--ner-only", action="store_true", help="Run only NER benchmark")
    parser.add_argument("--intent-only", action="store_true", help="Run only Intent classification benchmark")
    parser.add_argument("--linking-only", action="store_true", help="Run only Entity Linking benchmark")
    parser.add_argument("--rag-only", action="store_true", help="Run only RAG citation benchmark")
    args = parser.parse_args()

    runner = BenchmarkRunner(quick_mode=args.quick)

    if args.retrieval_only:
        runner.run_retrieval_suite()
    elif args.ner_only:
        runner.run_ner_suite()
    elif args.intent_only:
        runner.run_intent_suite()
    elif args.linking_only:
        runner.run_entity_linking_suite()
    elif args.rag_only:
        runner.run_rag_suite()
    else:
        runner.run_all()


if __name__ == "__main__":
    main()
