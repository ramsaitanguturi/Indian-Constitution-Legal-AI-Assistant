"""
Master CLI script to run all Stage 5 evaluations and save results.
Saves outputs to both evaluation/results/ and experiments/results/.
"""

import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.benchmark_runner import BenchmarkRunner
from config import EVALUATION_RESULTS_DIR


def main():
    print("=" * 70)
    print("INDIAN CONSTITUTION LEGAL AI — MASTER EVALUATION RUNNER")
    print("=" * 70)

    runner = BenchmarkRunner(results_dir=EVALUATION_RESULTS_DIR)
    summary = runner.run_all()

    # Mirror to experiments/results/ for plan compatibility
    exp_results_dir = PROJECT_ROOT / "experiments" / "results"
    exp_results_dir.mkdir(parents=True, exist_ok=True)

    for item in EVALUATION_RESULTS_DIR.iterdir():
        if item.is_file():
            shutil.copy2(item, exp_results_dir / item.name)

    print(f"\n[SYNC] Mirrored evaluation artifacts to {exp_results_dir}")
    print("Master evaluation completed successfully.")


if __name__ == "__main__":
    main()
