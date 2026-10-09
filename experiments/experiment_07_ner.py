"""
Experiment 07: Legal Named Entity Recognition (NER) Evaluation.
Evaluates precision, recall, and F1 across all 10 constitutional entity categories
using exact character span matching on the benchmark dataset.
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.ner_eval import NEREvaluator
from evaluation.report_generator import ReportGenerator


def run_experiment():
    print("=" * 65)
    print("EXPERIMENT 07: LEGAL NAMED ENTITY RECOGNITION (NER) EVALUATION")
    print("=" * 65)

    evaluator = NEREvaluator()
    results = evaluator.evaluate(
        exact_span_match=True,
        experiment_name="Exp_07_Legal_NER",
    )

    metrics = results.get("metrics", {})
    print(f"Evaluated on {results.get('sample_count', 0)} annotated legal queries.")
    print("-" * 65)
    print(f"  Exact Span Micro-Precision : {metrics.get('micro_precision', 0.0):.4f}")
    print(f"  Exact Span Micro-Recall    : {metrics.get('micro_recall', 0.0):.4f}")
    print(f"  Exact Span Micro-F1        : {metrics.get('micro_f1', 0.0):.4f}")
    print(f"  Macro-F1 (across categories): {metrics.get('macro_f1', 0.0):.4f}")
    print("-" * 65)

    per_class = metrics.get("per_class", {})
    for cat, stats in per_class.items():
        print(f"  {cat:<18}: P={stats['precision']:.4f} | R={stats['recall']:.4f} | F1={stats['f1']:.4f} (support={stats['support']})")
    print("=" * 65)

    out_file = PROJECT_ROOT / "experiments" / "results" / "experiment_07_ner.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[SAVED] Results saved to {out_file}")

    # Also save CSV breakdown
    report_gen = ReportGenerator(output_dir=out_file.parent)
    report_gen.save_ner_csv(results, filename="ner_results.csv")

    return results


if __name__ == "__main__":
    run_experiment()
