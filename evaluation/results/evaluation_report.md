# Indian Constitution Legal AI Assistant — Empirical Evaluation Report
**Generated:** 2026-10-09 13:40:09 | **Corpus Version:** 1.0.0-capstone | **Random Seed:** 42

> **Research Purpose:** Quantitative empirical evaluation of NLP query understanding, entity-aware hybrid retrieval, and grounded RAG reliability.

## 1. Information Retrieval Empirical Evaluation
Evaluated across standard Information Retrieval metrics using verified relevance judgments.

| Retrieval Configuration | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Recall@5 | Recall@10 | MRR | NDCG@5 | NDCG@10 | Latency (ms) |
|---|---|---|---|---|---|---|---|---|---|---|
| **Exp 1: BM25 Only** | 0.7500 | 0.8400 | 0.8500 | 0.8600 | 0.5018 | 0.5064 | 0.7962 | 0.6166 | 0.6157 | 4.1 ms |
| **Exp 2: Dense Only** | 0.7750 | 0.8400 | 0.8500 | 0.8500 | 0.5096 | 0.5250 | 0.8072 | 0.6413 | 0.6429 | 18.0 ms |
| **Exp 3: BM25 + Dense (Linear)** | 0.7700 | 0.8450 | 0.8550 | 0.8600 | 0.5050 | 0.5150 | 0.8099 | 0.6297 | 0.6298 | 22.8 ms |
| **Exp 4: BM25 + Dense + RRF** | 0.7700 | 0.8400 | 0.8550 | 0.8550 | 0.5056 | 0.5106 | 0.8071 | 0.6261 | 0.6244 | 22.4 ms |
| **Exp 5: RRF + Entity Boost** | 0.7800 | 0.8400 | 0.8450 | 0.8450 | 0.5285 | 0.5348 | 0.8096 | 0.6513 | 0.6492 | 66.4 ms |
| **Exp 6: Full Pipeline (+ Cross-Encoder)** | 0.8000 | 0.8450 | 0.8600 | 0.8650 | 0.5476 | 0.5526 | 0.8263 | 0.6752 | 0.6730 | 623.9 ms |

*Configuration Details:*
- BM25: Okapi ($k_1=1.5, b=0.75$)
- Dense Model: `sentence-transformers/all-MiniLM-L6-v2`
- Fusion: Reciprocal Rank Fusion ($k=60$)
- Entity Boost Weight: $+0.15$
- Neural Reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2`

## 2. Legal Named Entity Recognition (NER) Evaluation
**Exact Span Match:** True | **Micro-F1:** 0.8148 | **Macro-F1:** 0.7408 | **Gold Entities:** 211

| Entity Category | Precision | Recall | F1 Score | Support | TP | FP | FN |
|---|---|---|---|---|---|---|---|
| `ACT` | 1.0000 | 0.6667 | **0.8000** | 15 | 10 | 0 | 5 |
| `AMENDMENT` | 1.0000 | 1.0000 | **1.0000** | 15 | 15 | 0 | 0 |
| `ARTICLE` | 1.0000 | 1.0000 | **1.0000** | 40 | 40 | 0 | 0 |
| `CASE` | 0.9200 | 0.7419 | **0.8214** | 31 | 23 | 2 | 8 |
| `COURT` | 0.9333 | 0.6087 | **0.7368** | 23 | 14 | 1 | 9 |
| `DATE` | 1.0000 | 1.0000 | **1.0000** | 38 | 38 | 0 | 0 |
| `LEGAL_CONCEPT` | 0.2812 | 0.6000 | **0.3830** | 15 | 9 | 23 | 6 |
| `PERSON` | 0.0000 | 0.0000 | **0.0000** | 14 | 0 | 2 | 14 |
| `RIGHT` | 0.8333 | 0.5556 | **0.6667** | 9 | 5 | 1 | 4 |
| `SECTION` | 1.0000 | 1.0000 | **1.0000** | 11 | 11 | 0 | 0 |

## 3. Intent Classification Model Comparison
**Partitioning:** 85/15 Stratified Split (187 Train / 33 Test) | **Random Seed:** 42

| Model Architecture | Accuracy | Macro Precision | Macro Recall | Macro F1 | Weighted F1 |
|---|---|---|---|---|---|
| **rule_based_baseline** | 0.6970 | 0.5939 | 0.6970 | **0.6290** | 0.6290 |
| **tfidf_logistic_regression** | 0.8485 | 0.8727 | 0.8485 | **0.8331** | 0.8331 |
| **hybrid_classifier** | 0.6970 | 0.6000 | 0.6970 | **0.6301** | 0.6301 |

*5-Fold Stratified Cross-Validation (TF-IDF + Logistic Regression):* Accuracy = 0.7591 (±0.0422), Macro-F1 = 0.7444 (±0.0417)

> [!NOTE]
> DATASET LIMITATION: Total benchmark contains 220 examples across 11 classes (~20 samples/class). The held-out test set contains 33 samples (~3 per class). Class distributions have variance; 5-fold cross-validation is reported to provide confidence intervals.

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
**Citation Validity Rate:** 0.9456 | **Citation Precision:** 0.9456 | **Evidence Coverage:** 0.9456 | **Abstention Accuracy:** 1.0000

> [!IMPORTANT]
> Notice: Structural citation validation verifies evidence provenance and prevents fabricated citations. It does NOT claim semantic or substantive legal truth.

## 6. Controlled Query Expansion Evaluation
**Expansion Precision:** 0.7500 | **Semantic Drift Rate:** 0.0000 | **Average Terms Appended:** 3.0

## 7. Benchmark Integrity & Human Annotation Audit
Records requiring ongoing human annotation are strictly tracked to prevent fabricated scores:

- **Retrieval Benchmark:** 200 verified queries, 0 queued for future annotation.
- **NER Benchmark:** 105 verified queries, 0 queued.
- **Entity Linking Benchmark:** 30 verified mentions, 1 queued.
- **RAG Benchmark:** 100 verified test cases, 0 queued.

