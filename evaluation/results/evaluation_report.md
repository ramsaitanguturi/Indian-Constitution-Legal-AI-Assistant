# Indian Constitution Legal AI Assistant — Empirical Evaluation Report
**Generated:** 2026-10-09 11:48:16 | **Corpus Version:** 1.0.0-capstone | **Random Seed:** 42

> **Research Purpose:** Quantitative empirical evaluation of NLP query understanding, entity-aware hybrid retrieval, and grounded RAG reliability.

## 1. Information Retrieval Empirical Evaluation
Evaluated across standard Information Retrieval metrics using verified relevance judgments.

| Retrieval Configuration | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Recall@5 | Recall@10 | MRR | NDCG@5 | NDCG@10 | Latency (ms) |
|---|---|---|---|---|---|---|---|---|---|---|
| **Exp 1: BM25 Only** | 0.7500 | 0.9000 | 0.9500 | 0.9500 | 0.5488 | 0.5488 | 0.8375 | 0.5895 | 0.5811 | 3.5 ms |
| **Exp 2: Dense Only** | 0.8500 | 1.0000 | 1.0000 | 1.0000 | 0.7738 | 0.8279 | 0.9250 | 0.7977 | 0.8086 | 22.8 ms |
| **Exp 3: BM25 + Dense (Linear)** | 0.8000 | 1.0000 | 1.0000 | 1.0000 | 0.6325 | 0.6325 | 0.9000 | 0.6661 | 0.6545 | 22.6 ms |
| **Exp 4: BM25 + Dense + RRF** | 0.8000 | 1.0000 | 1.0000 | 1.0000 | 0.6138 | 0.6388 | 0.9000 | 0.6449 | 0.6429 | 21.9 ms |
| **Exp 5: RRF + Entity Boost** | 0.8500 | 1.0000 | 1.0000 | 1.0000 | 0.8050 | 0.8342 | 0.9250 | 0.8127 | 0.8154 | 65.1 ms |
| **Exp 6: Full Pipeline (+ Cross-Encoder)** | 0.9500 | 1.0000 | 1.0000 | 1.0000 | 0.8962 | 0.8962 | 0.9750 | 0.9183 | 0.9041 | 1001.5 ms |

*Configuration Details:*
- BM25: Okapi ($k_1=1.5, b=0.75$)
- Dense Model: `sentence-transformers/all-MiniLM-L6-v2`
- Fusion: Reciprocal Rank Fusion ($k=60$)
- Entity Boost Weight: $+0.15$
- Neural Reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2`

## 2. Legal Named Entity Recognition (NER) Evaluation
**Exact Span Match:** True | **Micro-F1:** 0.8468 | **Macro-F1:** 0.8011 | **Gold Entities:** 53

| Entity Category | Precision | Recall | F1 Score | Support | TP | FP | FN |
|---|---|---|---|---|---|---|---|
| `ACT` | 1.0000 | 1.0000 | **1.0000** | 4 | 4 | 0 | 0 |
| `AMENDMENT` | 1.0000 | 1.0000 | **1.0000** | 3 | 3 | 0 | 0 |
| `ARTICLE` | 1.0000 | 1.0000 | **1.0000** | 13 | 13 | 0 | 0 |
| `CASE` | 0.8571 | 0.8571 | **0.8571** | 7 | 6 | 1 | 1 |
| `COURT` | 0.8750 | 1.0000 | **0.9333** | 7 | 7 | 1 | 0 |
| `DATE` | 1.0000 | 1.0000 | **1.0000** | 5 | 5 | 0 | 0 |
| `LEGAL_CONCEPT` | 0.3636 | 0.6667 | **0.4706** | 6 | 4 | 7 | 2 |
| `PERSON` | 0.0000 | 0.0000 | **0.0000** | 2 | 0 | 1 | 2 |
| `RIGHT` | 0.7500 | 0.7500 | **0.7500** | 4 | 3 | 1 | 1 |
| `SECTION` | 1.0000 | 1.0000 | **1.0000** | 2 | 2 | 0 | 0 |

## 3. Intent Classification Model Comparison
**Partitioning:** 85/15 Stratified Split (155 Train / 28 Test) | **Random Seed:** 42

| Model Architecture | Accuracy | Macro Precision | Macro Recall | Macro F1 | Weighted F1 |
|---|---|---|---|---|---|
| **rule_based_baseline** | 0.7857 | 0.9123 | 0.8182 | **0.8123** | 0.7986 |
| **tfidf_logistic_regression** | 0.6429 | 0.6970 | 0.6591 | **0.6487** | 0.6378 |
| **hybrid_classifier** | 0.8214 | 0.9432 | 0.8636 | **0.8647** | 0.8287 |

*5-Fold Stratified Cross-Validation (TF-IDF + Logistic Regression):* Accuracy = 0.6180 (±0.0700), Macro-F1 = 0.5888 (±0.0831)

> [!NOTE]
> DATASET LIMITATION: Total benchmark contains 183 examples across 11 classes (~16 samples/class). The held-out test set contains 28 samples (~2 per class). Class distributions have variance; 5-fold cross-validation is reported to provide confidence intervals.

## 4. Canonical Entity Linking Evaluation
**Overall Canonical Linking Accuracy:** 0.8667 | **Out-of-KB Rejection Accuracy:** 1.0000 | **Evaluated Mentions:** 30

| Entity Type | Linking Accuracy | Correct | Total |
|---|---|---|---|
| `ARTICLE` | **0.8889** | 8 | 9 |
| `CASE` | **1.0000** | 12 | 12 |
| `AMENDMENT` | **0.6667** | 2 | 3 |
| `LEGAL_CONCEPT` | **0.5000** | 1 | 2 |
| `RIGHT` | **0.0000** | 0 | 1 |
| `UNKNOWN` | **1.0000** | 3 | 3 |

## 5. RAG Grounding & Citation Validation
**Citation Validity Rate:** 1.0000 | **Citation Precision:** 1.0000 | **Evidence Coverage:** 1.0000 | **Abstention Accuracy:** 1.0000

> [!IMPORTANT]
> Notice: Structural citation validation verifies evidence provenance and prevents fabricated citations. It does NOT claim semantic or substantive legal truth.

## 6. Controlled Query Expansion Evaluation
**Expansion Precision:** 0.7500 | **Semantic Drift Rate:** 0.0000 | **Average Terms Appended:** 3.0

## 7. Benchmark Integrity & Human Annotation Audit
Records requiring ongoing human annotation are strictly tracked to prevent fabricated scores:

- **Retrieval Benchmark:** 20 verified queries, 3 queued for future annotation.
- **NER Benchmark:** 20 verified queries, 2 queued.
- **Entity Linking Benchmark:** 30 verified mentions, 1 queued.
- **RAG Benchmark:** 8 verified test cases, 1 queued.

