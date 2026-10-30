# Reproducibility Guide & Execution Runbook

**Project:** Indian Constitution Legal AI Assistant  
**Research Focus:** Entity-Aware Hybrid Retrieval and Reranking Framework for Indian Constitutional Question Answering  
**Document:** `docs/REPRODUCIBILITY.md`  
**Evaluation Random Seed:** `EVAL_RANDOM_SEED = 42`  
**Python Environment:** Python 3.12.10 (Windows x64 / Linux x64)  

---

## 1. Quick Start Single Commands

To verify the repository in clean room conditions:

### 1.1 Run Benchmark Integrity Validation
```powershell
# Standard partition validation (exits 0)
python scripts/validate_benchmark.py

# Strict uncataloged partition verification (exits 1 if uncataloged remain)
python scripts/validate_benchmark.py --strict
```

### 1.2 Run Full Automated Test Suite
```powershell
# Run all 319 unit, integration, and regression tests (verified 319 passed in ~213s)
pytest -v
```

### 1.3 Launch Web Application
```powershell
streamlit run app.py
```

### 1.4 Live Demonstration Guide
For comprehensive step-by-step viva defense walkthroughs and evaluation scripts, see [**`DEMONSTRATION_GUIDE.md`**](../DEMONSTRATION_GUIDE.md).

---

## 2. Environment Setup & Determinism

### 2.1 Dependencies Installation
```powershell
# Clone or navigate to the repository
cd "Indian Constitution Legal AI Assistant"

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install locked dependencies
pip install -r requirements.txt
```

### 2.2 Random Seed & Determinism
All randomized operations (such as train-test splitting and k-fold cross-validation in `evaluation/evaluator.py` and `experiments/experiment_08_intent.py`) enforce:
```python
EVAL_RANDOM_SEED = 42
```
This guarantees identical split boundaries and evaluation metrics across repeated runs.

---

## 3. Core Experiment Reproduction Suite (Exp 1 – Exp 8)

Every experiment script reads verified benchmark datasets and writes structured output JSON artifacts to `experiments/results/`:

| Experiment | Target | Command | Primary Reported Metric | Output Artifact Path |
|---|---|---|---|---|
| **Exp 01** | BM25 Sparse Baseline | `python experiments/experiment_01_bm25.py` | Recall@10: 0.7003 / NDCG@10: 0.7197 | `experiments/results/experiment_01_bm25.json` |
| **Exp 02** | Dense Vector Baseline | `python experiments/experiment_02_dense.py` | Recall@10: 0.7131 / NDCG@10: 0.7432 | `experiments/results/experiment_02_dense.json` |
| **Exp 03** | Linear Hybrid Fusion | `python experiments/experiment_03_hybrid.py` | Recall@10: 0.7076 / NDCG@10: 0.7333 | `experiments/results/experiment_03_hybrid.json` |
| **Exp 04** | Reciprocal Rank Fusion | `python experiments/experiment_04_rrf.py` | Recall@10: 0.7005 / NDCG@10: 0.7262 | `experiments/results/experiment_04_rrf.json` |
| **Exp 05** | Entity-Aware Boost | `python experiments/experiment_05_entity_boost.py` | Recall@10: 0.7229 / NDCG@10: 0.7493 | `experiments/results/experiment_05_entity_boost.json` |
| **Exp 06** | Cross-Encoder Reranker | `python experiments/experiment_06_reranker.py` | Recall@10: 0.7478 / NDCG@10: 0.7787 | `experiments/results/experiment_06_reranker.json` |
| **Exp 07** | Legal Named Entity Recognition | `python experiments/experiment_07_ner.py` | Micro-F1: 0.8714 / Macro-F1: 0.8496 | `experiments/results/experiment_07_ner.json` |
| **Exp 08** | Intent Classification | `python experiments/experiment_08_intent.py` | Holdout Acc: 0.8485 / 5-Fold Acc: 0.7591 | `experiments/results/experiment_08_intent.json` |

---

## 4. Master Evaluation Runner

To run all evaluation modules and re-generate the full research suite:
```powershell
python evaluation/evaluator.py
```
This generates:
- `evaluation/results/retrieval_evaluation_results.json`
- `evaluation/results/retrieval_comparison_table.csv`
- `evaluation/results/classification_evaluation_results.json`
- `evaluation/results/intent_comparison_table.csv`
- `evaluation/results/ner_evaluation_results.json`
- `evaluation/results/entity_linking_evaluation_results.json`
- `evaluation/results/rag_citation_evaluation_results.json`
- `evaluation/results/evaluation_summary.json`
- `evaluation/results/RESEARCH_REPORT.md`

---

## 5. System Latency & Hardware Expectations

Measurements taken on host Intel Core CPU without GPU acceleration:
- **BM25 Search**: ~3.0 ms
- **Dense Vector Search**: ~19.8 ms
- **Entity Linking & Expansion**: ~2.5 ms
- **Cross-Encoder Reranking**: ~891.6 ms (steady-state median for top-20 candidates)
- **Grounded Offline Synthesis**: ~566.5 ms
- **Total End-to-End Latency**: ~1.48 s (median)

On GPU-enabled hardware (`CUDA`), end-to-end latency drops below ~350 ms.
