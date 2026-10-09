# Adversarial Reproducibility & Latency Profiling Report

**Project**: Indian Constitution Legal AI Assistant  
**Role**: Senior NLP Researcher & Adversarial Evaluator  
**Audit Date**: October 2026  
**Status**: **PASS for Software & Experiment Reproducibility**  

---

## 1. System Environment & Execution Context

All evaluations and latency profiles were measured directly on the host development machine:

- **Operating System**: Microsoft Windows 10/11 x64 (PowerShell 5.1/7.x)
- **Python Version**: `3.12.10` located at `.\venv\Scripts\python.exe`
- **Execution Target**: Multi-core CPU (`torch 2.10.0+cpu` without GPU acceleration)
- **Core Dependencies**:
  - `pytest`: 9.1.1
  - `scikit-learn`: 1.9.1
  - `chromadb`: 1.5.9
  - `sentence-transformers`: 5.4.1 (`all-MiniLM-L6-v2` embeddings, `ms-marco-MiniLM-L-6-v2` cross-encoder)
  - `rank-bm25`: 0.2.2
  - `streamlit`: 1.55.0

---

## 2. Rigorous Latency Profiling (Warm-up + 20 Repeated Trials)

Previous reports quoted average cross-encoder latency as "644 ms" without warm-up protocols or variance reporting. Here, a rigorous benchmark was conducted with 3 warm-up passes followed by 20 repeated trials on representative constitutional queries:

| Pipeline Subsystem | Mean Latency | Median Latency | P95 Latency | Min Latency | Max Latency | Adversarial Finding |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **Sparse BM25 Search** | **3.36 ms** | **3.02 ms** | **4.43 ms** | 2.68 ms | 4.77 ms | Negligible overhead; deterministic inverted index lookup. |
| **Dense Vector Search** | **24.04 ms** | **19.79 ms** | **63.83 ms** | 15.92 ms | 73.31 ms | Occasional spikes due to ChromaDB HNSW cache misses. |
| **Cross-Encoder Reranker** (Top 20 $\to$ Top 5) | **1320.70 ms** | **891.64 ms** | **1390.67 ms** | 793.56 ms | 9931.38 ms | Cold-start spike on CPU; **steady-state median is ~892 ms**. |
| **Generation (Offline Fallback)** | **555.03 ms** | **566.45 ms** | **589.35 ms** | 502.68 ms | 609.21 ms | Markdown synthesis and parent-child hydration. |
| **End-to-End Pipeline** | **~1.90 s** | **~1.48 s** | **~2.05 s** | 1.32 s | 10.55 s | Feasible for interactive use, but CPU-bound. |

*Critical Finding on Latency Claims*: Theoretical conjectures regarding "ONNX quantization bringing latency below 50 ms" are unsupported by empirical data on this CPU architecture. In reality, steady-state CPU cross-encoder reranking requires **~890 ms**.

---

## 3. Dual Retrieval Ablation Benchmark (Original vs. Canonical Labels)

Evaluated across all 200 retrieval queries in `data/benchmark/retrieval_queries.json`:

| Configuration | Hit@1 (Orig) | Hit@1 (Canon) | Recall@10 (Orig) | Recall@10 (Canon) | MRR (Orig) | MRR (Canon) | NDCG@10 (Orig) | NDCG@10 (Canon) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Exp 1: BM25 Only** | 0.7500 | **0.7900** | 0.5064 | **0.7003** | 0.7962 | **0.8271** | 0.6157 | **0.7197** |
| **Exp 2: Dense Only** | 0.7750 | **0.8100** | 0.5250 | **0.7131** | 0.8072 | **0.8385** | 0.6429 | **0.7432** |
| **Exp 3: Linear Hybrid** | 0.7700 | **0.8100** | 0.5150 | **0.7076** | 0.8099 | **0.8411** | 0.6298 | **0.7333** |
| **Exp 4: RRF (k=60)** | 0.7700 | **0.8100** | 0.5106 | **0.7005** | 0.8071 | **0.8396** | 0.6244 | **0.7262** |
| **Exp 5: Entity Boost** | 0.7800 | **0.8200** | 0.5352 | **0.7229** | 0.8096 | **0.8421** | 0.6482 | **0.7493** |
| **Exp 6: Cross-Encoder** | **0.8000** | **0.8400** | **0.5526** | **0.7478** | **0.8263** | **0.8583** | **0.6730** | **0.7787** |

---

## 4. Sequential Execution Record of All 8 Experiments

Every individual experiment script in `experiments/` was executed sequentially from the virtual environment. Artifact log saved to [`evaluation/results/adversarial_experiment_execution_log.json`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/evaluation/results/adversarial_experiment_execution_log.json):

| Script | Command | Exit Code | Duration | Output Artifact Path |
|---|---|:---:|:---:|---|
| **Exp 01: BM25** | `.\venv\Scripts\python.exe experiments/experiment_01_bm25.py` | **0** | 6.84s | `experiments/results/experiment_01_bm25.json` |
| **Exp 02: Dense** | `.\venv\Scripts\python.exe experiments/experiment_02_dense.py` | **0** | 42.48s | `experiments/results/experiment_02_dense.json` |
| **Exp 03: Hybrid** | `.\venv\Scripts\python.exe experiments/experiment_03_hybrid.py` | **0** | 41.90s | `experiments/results/experiment_03_hybrid.json` |
| **Exp 04: RRF** | `.\venv\Scripts\python.exe experiments/experiment_04_rrf.py` | **0** | 36.96s | `experiments/results/experiment_04_rrf.json` |
| **Exp 05: Entity Boost** | `.\venv\Scripts\python.exe experiments/experiment_05_entity_boost.py` | **0** | 40.83s | `experiments/results/experiment_05_entity_boost.json` |
| **Exp 06: Reranker** | `.\venv\Scripts\python.exe experiments/experiment_06_reranker.py` | **0** | 159.02s | `experiments/results/experiment_06_reranker.json` |
| **Exp 07: NER** | `.\venv\Scripts\python.exe experiments/experiment_07_ner.py` | **0** | 8.40s | `experiments/results/experiment_07_ner.json` |
| **Exp 08: Intent** | `.\venv\Scripts\python.exe experiments/experiment_08_intent.py` | **0** | 4.59s | `experiments/results/experiment_08_intent.json` |

---

## 5. Automated Test Suite Execution Record

Executed via pytest:
```powershell
.\venv\Scripts\pytest.exe -v
```
- **Total Tests Collected**: 254
- **Passed**: **254**
- **Failed**: 0
- **Skipped**: 0
- **Errors**: 0
- **Execution Time**: **108.81s**
- **Status**: **PASS**
