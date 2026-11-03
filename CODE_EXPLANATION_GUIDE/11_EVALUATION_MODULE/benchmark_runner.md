# Master Benchmark Runner: `evaluation/benchmark_runner.py`

[Back to Evaluation Overview](README.md) • [Back to Main Index](../README.md)

---

## 1. Basic Introduction

### What is this file?
`evaluation/benchmark_runner.py` is the **Master Evaluation CLI and Orchestrator**. It executes all Stage 5 quantitative evaluation suites across information retrieval, legal NER, intent classification, entity linking, and grounded RAG, automatically generating CSV results, JSON summaries, and Markdown reports.

### Why does this file exist?
Instead of running separate ad-hoc evaluation scripts, `benchmark_runner.py` provides a unified, repeatable testing harness:
- Single command execution for the entire project: `python -m evaluation.benchmark_runner --suite all`.
- Coordinated multi-stage ablation: runs BM25, Dense, Hybrid, RRF, Entity Boost, and Cross-Encoder back-to-back under identical test conditions.
- Quick evaluation mode (`--quick`) for fast validation during development.
- Automatic report serialization via `ReportGenerator`.

---

## 2. Imports and Dependencies

```python
# evaluation/benchmark_runner.py L21-L51
import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from config import (
    EVALUATION_RESULTS_DIR,
    PARENT_STORE_PATH,
    BGE_M3_MODEL_NAME,
)
from evaluation.retrieval_eval import RetrievalEvaluator
from evaluation.ner_eval import NEREvaluator
from evaluation.intent_eval import IntentEvaluator
from evaluation.entity_linking_eval import EntityLinkingEvaluator
from evaluation.rag_eval import RAGEvaluator
from evaluation.report_generator import ReportGenerator
```

---

## 3. Class: `BenchmarkRunner`

```python
class BenchmarkRunner:
    """
    Orchestrates execution of the entire Stage 5 evaluation suite.
    """
```

### 3.1 Method: `run_retrieval_suite() -> List[Dict[str, Any]]`

Executes the 6-stage Information Retrieval ablation study across all 100 gold benchmark queries:

```
Configuration 1: BM25 Only (Lexical Baseline)
Configuration 2: Dense Only (BGE-M3 / MiniLM Semantic Baseline)
Configuration 3: BM25 + Dense (Linear Score Combination without RRF)
Configuration 4: BM25 + Dense + RRF (Cormack Reciprocal Rank Fusion, k=60)
Configuration 5: RRF + Legal Entity Boost (+0.15 additive metadata uplift)
Configuration 6: Full Pipeline (+ Cross-Encoder Neural Reranker)
```

For each configuration, it evaluates:
- `Hit@1`, `Hit@3`, `Hit@5`, `Hit@10`
- `Recall@5`, `Recall@10`
- `Precision@5`, `Precision@10`
- `Mean Reciprocal Rank (MRR)`
- `NDCG@5`, `NDCG@10`

---

### 3.2 Method: `run_ner_suite() -> Dict[str, Any]`
Invokes `NEREvaluator` over `data/annotations/legal_ner_gold.json`. Computes Micro and Macro Precision, Recall, and F1 across all 10 legal entity categories using exact character span matching.

---

### 3.3 Method: `run_intent_suite() -> Dict[str, Any]`
Invokes `IntentEvaluator` on the zero-leakage test partition (`data/benchmarks/intent_test.json`). Compares three classifiers:
1. `RuleBasedIntentClassifier`
2. `MLIntentClassifier` (TF-IDF + Logistic Regression)
3. `HybridIntentClassifier` (Rule-first with ML fallback)

Outputs per-class accuracy, Macro-F1, Weighted-F1, and Confusion Matrices.

---

### 3.4 Method: `run_linking_suite() -> Dict[str, Any]`
Evaluates canonical entity linking accuracy against `data/annotations/entity_linking_gold.json`, measuring exact link matches for constitutional articles, landmark cases, and legal doctrines.

---

### 3.5 Method: `run_rag_suite() -> Dict[str, Any]`
Evaluates grounded answer generation, calculating:
- **Citation Structural Validity**: Percentage of generated citations that match existing retrieved documents.
- **NLI Claim Grounding**: Percentage of generated propositions entailed by retrieved evidence.
- **Abstention Accuracy**: Verification that out-of-scope and unanswerable queries were safely refused.

---

## 4. Command-Line Interface (CLI) & Usage Options

```bash
# Run all benchmark suites (Retrieval, NER, Intent, Linking, RAG)
python -m evaluation.benchmark_runner --suite all

# Run only the Information Retrieval ablation suite
python -m evaluation.benchmark_runner --suite retrieval

# Run fast quick-mode evaluation (uses 10 sample queries)
python -m evaluation.benchmark_runner --suite all --quick

# Specify custom embedding model
python -m evaluation.benchmark_runner --suite retrieval --model BAAI/bge-m3

# Specify custom output directory
python -m evaluation.benchmark_runner --suite all --output-dir evaluation/custom_results
```

---

## 5. Actual Code Walkthrough

### Code Excerpt: Master Suite Execution (Lines 230-265)
```python
    def run_all(self) -> Dict[str, Any]:
        """Runs all evaluation suites and generates comprehensive report."""
        start_time = time.time()
        print("\n" + "=" * 65)
        print("STARTING COMPLETE LEGAL AI BENCHMARK EVALUATION")
        print("=" * 65)

        retrieval_res = self.run_retrieval_suite()
        ner_res = self.run_ner_suite()
        intent_res = self.run_intent_suite()
        linking_res = self.run_linking_suite()
        rag_res = self.run_rag_suite()

        elapsed = time.time() - start_time
        print(f"\n[BENCHMARK] All suites completed in {elapsed:.2f} seconds.")

        # Generate reports
        print("[BENCHMARK] Generating summary reports and CSV tables...")
        report_files = self.report_generator.generate_all_reports(
            retrieval_results=retrieval_res,
            ner_results=ner_res,
            intent_results=intent_res,
            linking_results=linking_res,
            rag_results=rag_res,
        )
        return {"elapsed_seconds": elapsed, "reports": report_files}
```
- **Why this design is ideal for viva demonstration**: During a live examination, running `python -m evaluation.benchmark_runner --quick` executes the complete evaluation across all 5 subcomponents in under 8 seconds, printing live tables and saving reports directly to `evaluation/results/`.

---

## 6. Viva Presentation & Defense Q&A

### Q1: How do you run the evaluation suite during the project demonstration?
> **Student Answer**:
> *"We execute `python -m evaluation.benchmark_runner --suite all --quick` from the terminal. The runner initializes the 6-stage retrieval ablation, tests the 10-class Legal NER extractor, evaluates intent classification on holdout test queries, tests entity linking, and validates RAG citation integrity. In less than 10 seconds, it prints comparative tables to the terminal and updates `evaluation/results/evaluation_report.md`."*

### Q2: What are the 6 retrieval configurations compared by the benchmark runner?
> **Student Answer**:
> *"The runner evaluates: (1) BM25 baseline, (2) Dense BGE-M3 baseline, (3) Naive linear combination, (4) Hybrid search with Cormack Reciprocal Rank Fusion, (5) RRF with statutory Entity Boosting, and (6) Full pipeline with cross-encoder neural reranking. Comparing these 6 steps quantifies the exact contribution of each architectural innovation, proving that the full pipeline improves NDCG@10 from 0.5484 to 0.7787—a 41.9% gain over BM25."*

