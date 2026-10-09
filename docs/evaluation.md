# Indian Constitution Legal AI Assistant — Evaluation Methodology & Empirical Results

## 1. Overview & Research Objectives

The Stage 5 evaluation framework quantitatively evaluates:
1. **Information Retrieval (IR)**: Lexical (BM25) vs Dense vs Fusion vs Cross-Encoder reranking.
2. **Legal Named Entity Recognition (NER)**: 10 legal categories on exact token and span match.
3. **Intent Classification**: Rule-based vs TF-IDF + Logistic Regression vs Hybrid model.
4. **Canonical Entity Linking**: Normalizing aliases to canonical corpus IDs and out-of-KB rejection.
5. **RAG Grounding & Citation Integrity**: Structural validation of citations and safe abstention.

All results reported below are drawn directly from active saved evaluation artifacts in `evaluation/results/`.

---

## 2. Information Retrieval Empirical Findings

**Benchmark:** 20 verified legal queries, evaluated against gold relevance judgments.

| Retrieval Configuration | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Recall@5 | Recall@10 | MRR | NDCG@5 | NDCG@10 | Latency (ms) |
|---|---|---|---|---|---|---|---|---|---|---|
| **Exp 1: BM25 Only** | 0.7500 | 0.9000 | 0.9500 | 0.9500 | 0.5488 | 0.5488 | 0.8375 | 0.5895 | 0.5811 | 3.5 ms |
| **Exp 2: Dense Only** | 0.8500 | 1.0000 | 1.0000 | 1.0000 | 0.7738 | 0.8279 | 0.9250 | 0.7977 | 0.8086 | 22.8 ms |
| **Exp 3: BM25 + Dense (Linear)** | 0.8000 | 1.0000 | 1.0000 | 1.0000 | 0.6325 | 0.6325 | 0.9000 | 0.6661 | 0.6545 | 22.6 ms |
| **Exp 4: BM25 + Dense + RRF** | 0.8000 | 1.0000 | 1.0000 | 1.0000 | 0.6138 | 0.6388 | 0.9000 | 0.6449 | 0.6429 | 21.9 ms |
| **Exp 5: RRF + Entity Boost** | 0.8500 | 1.0000 | 1.0000 | 1.0000 | 0.8050 | 0.8342 | 0.9250 | 0.8127 | 0.8154 | 65.1 ms |
| **Exp 6: Full Pipeline (+ Cross-Encoder)** | **0.9500** | **1.0000** | **1.0000** | **1.0000** | **0.8962** | **0.8962** | **0.9750** | **0.9183** | **0.9041** | 1001.5 ms |

> **Scientific Disclosure:** Differences across configurations reflect observational performance on the 20-query verified benchmark. Sample sizes are constrained; no claim of formal statistical significance (e.g. paired t-test at p < 0.05) is asserted without expanded sample testing.

---

## 3. Legal Named Entity Recognition (NER) Findings

**Exact Span Match:** True | **Micro-F1:** 0.8468 | **Macro-F1:** 0.8011 | **Gold Entities:** 53

| Category | Precision | Recall | F1 Score | Support | TP | FP | FN |
|---|---|---|---|---|---|---|---|
| `ACT` | 1.0000 | 1.0000 | 1.0000 | 4 | 4 | 0 | 0 |
| `AMENDMENT` | 1.0000 | 1.0000 | 1.0000 | 3 | 3 | 0 | 0 |
| `ARTICLE` | 1.0000 | 1.0000 | 1.0000 | 13 | 13 | 0 | 0 |
| `CASE` | 0.8571 | 0.8571 | 0.8571 | 7 | 6 | 1 | 1 |
| `COURT` | 0.8750 | 1.0000 | 0.9333 | 7 | 7 | 1 | 0 |
| `DATE` | 1.0000 | 1.0000 | 1.0000 | 5 | 5 | 0 | 0 |
| `LEGAL_CONCEPT` | 0.3636 | 0.6667 | 0.4706 | 6 | 4 | 7 | 2 |
| `PERSON` | 0.0000 | 0.0000 | 0.0000 | 2 | 0 | 1 | 2 |
| `RIGHT` | 0.7500 | 0.7500 | 0.7500 | 4 | 3 | 1 | 1 |
| `SECTION` | 1.0000 | 1.0000 | 1.0000 | 2 | 2 | 0 | 0 |

---

## 4. Intent Classification Model Comparison

**Split:** 85/15 Stratified Split (155 Train / 28 Test) | **Random Seed:** 42

| Model Architecture | Accuracy | Macro Precision | Macro Recall | Macro F1 | Weighted F1 |
|---|---|---|---|---|---|
| **rule_based_baseline** | 0.7857 | 0.9123 | 0.8182 | 0.8123 | 0.7986 |
| **tfidf_logistic_regression** | 0.6429 | 0.6970 | 0.6591 | 0.6487 | 0.6378 |
| **hybrid_classifier** | **0.8214** | **0.9432** | **0.8636** | **0.8647** | **0.8287** |

**5-Fold Cross-Validation (TF-IDF + LogReg):** Accuracy = 0.6180 (±0.0700), Macro-F1 = 0.5888 (±0.0831).

---

## 5. Entity Linking, Expansion & RAG Grounding

- **Canonical Linking Accuracy:** 0.8667 (26/30 correct)
- **Out-of-KB Rejection Accuracy:** 1.0000 (3/3 unknown entities rejected)
- **Controlled Query Expansion Precision:** 0.7500 (Drift rate: 0.0%)
- **Structural Citation Validity Rate:** 1.0000 (9/9 verified)
- **Automated Abstention Accuracy:** 1.0000 on out-of-scope / sub-threshold inputs

---

## 6. Reproducing Experiments

To reproduce all experiments and regenerate report artifacts:

```powershell
# Run the complete benchmark suite
python scripts/run_all_evaluations.py

# Run the test suite
.\venv\Scripts\pytest -q
```
