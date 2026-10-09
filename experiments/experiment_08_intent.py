"""
Experiment 08: Legal Query Intent Classification Comparative Evaluation.
Evaluates Rule-Based Baseline, ML Classifier (TF-IDF + Logistic Regression),
and Hybrid Orchestrator across 11 intent classes with zero data leakage.
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.intent_eval import IntentEvaluator
from evaluation.report_generator import ReportGenerator


def run_experiment():
    print("=" * 65)
    print("EXPERIMENT 08: INTENT CLASSIFICATION COMPARATIVE EVALUATION")
    print("=" * 65)

    evaluator = IntentEvaluator()
    results = evaluator.run_comparative_evaluation()

    models = results.get("models", {})
    print(f"Evaluated on {results.get('total_samples', 0)} queries (Test set size: {results.get('test_samples', 0)}).")
    print("-" * 65)
    for name, stats in models.items():
        print(f"  {name:<25}: Accuracy = {stats.get('accuracy', 0.0):.4f} | Macro-F1 = {stats.get('macro_f1', 0.0):.4f}")
    print("=" * 65)

    out_file = PROJECT_ROOT / "experiments" / "results" / "experiment_08_intent.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[SAVED] Results saved to {out_file}")

    # Also save CSV breakdown
    report_gen = ReportGenerator(output_dir=out_file.parent)
    report_gen.save_classification_csv(results, filename="classification_results.csv")

    return results


if __name__ == "__main__":
    run_experiment()
