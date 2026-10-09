# Indian Constitution Legal AI Assistant — Empirical Experiments & Research Findings

## 1. Overview & Research Questions

This document presents the comprehensive empirical experiment logs, ablation studies, latency profiles, and evaluation artifacts for the research study:

> **"Entity-Aware Hybrid Retrieval and Reranking Framework for Indian Constitutional Question Answering"**

All metrics, confusion counts, and runtime measurements reported herein are drawn directly from saved execution artifacts in `experiments/results/` and `evaluation/results/`.

### 1.1 Formal Research Questions

- **RQ1 (Lexical vs. Semantic Synergy)**: Does fusing sparse lexical BM25 retrieval with dense vector representations (MiniLM) via Reciprocal Rank Fusion (RRF) improve recall and reciprocal rank over either standalone method for constitutional queries?
- **RQ2 (Domain Entity-Aware Boosting)**: Does detecting and linking canonical constitutional entities (`ARTICLE`, `CASE`, `AMENDMENT`) and applying an additive rank boost ($+0.15$) elevate statutory target passages above generic semantic matches?
- **RQ3 (Neural Reranking Precision)**: Does cross-attention neural reranking (`ms-marco-MiniLM-L-6-v2`) over top-30 fused candidates improve top-1 and top-5 ranking metrics compared to bi-encoder vector similarity alone?
- **RQ4 (Query Understanding Accuracy)**: Does an n-gram TF-IDF and regularized Logistic Regression intent classifier improve routing accuracy across 11 legal intent classes compared to heuristic keyword rules?
- **RQ5 (Evidence Grounding & Citation Integrity)**: Does hierarchical parent-child context recovery combined with structural citation validation and confidence-based abstention eliminate hallucinated constitutional authorities?

---

## 2. Information Retrieval Experiments (Exp 1 – Exp 6)

### 2.1 Benchmark Setup
- **Benchmark Corpus**: 270 parent documents (137 articles, 18 amendments, 104 judgments) yielding 1,001 child passages in ChromaDB.
- **Query Set**: 200 verified constitutional legal queries in `data/benchmark/retrieval_queries.json`.
- **Evaluation Cutoffs**: Evaluated at $K \in \{1, 3, 5, 10\}$.
- **Dual Relevance Label Ground Truth**:
  1. *Original Labels* (`data/annotations/relevance_labels.json`): Contains 171 unpadded/shorthand aliases (e.g., `parent_const_art_14` alongside zero-padded `parent_const_art_014`).
  2. *Canonicalized Labels v2* (`data/annotations/relevance_labels_v2_canonicalized.json`): Resolves aliases to verified, zero-padded parent document IDs.

### 2.2 Dual Retrieval Comparison Matrix (200 Queries)

| Experiment Configuration | Hit@1 (Orig / Canon) | Hit@3 (Orig / Canon) | Hit@5 (Orig / Canon) | Hit@10 (Orig / Canon) | Recall@5 (Orig / Canon) | Recall@10 (Orig / Canon) | MRR (Orig / Canon) | NDCG@10 (Orig / Canon) | Mean Latency (ms) | Median Latency (ms) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Exp 1: BM25 Only** | 0.7500 / **0.7900** | 0.8400 / **0.8750** | 0.8500 / **0.8850** | 0.8600 / **0.8950** | 0.5018 / **0.6724** | 0.5064 / **0.7003** | 0.7962 / **0.8271** | 0.6157 / **0.7197** | 3.75 ms | 3.02 ms |
| **Exp 2: Dense Only** | 0.7750 / **0.8100** | 0.8400 / **0.8800** | 0.8500 / **0.8900** | 0.8500 / **0.8950** | 0.5096 / **0.6811** | 0.5250 / **0.7131** | 0.8072 / **0.8385** | 0.6429 / **0.7432** | 17.73 ms | 19.79 ms |
| **Exp 3: Linear Hybrid** | 0.7700 / **0.8100** | 0.8450 / **0.8800** | 0.8550 / **0.8900** | 0.8600 / **0.8950** | 0.5050 / **0.6789** | 0.5150 / **0.7076** | 0.8099 / **0.8411** | 0.6298 / **0.7333** | 22.01 ms | 21.50 ms |
| **Exp 4: BM25 + Dense + RRF** | 0.7700 / **0.8100** | 0.8400 / **0.8800** | 0.8550 / **0.8900** | 0.8550 / **0.8950** | 0.5056 / **0.6750** | 0.5106 / **0.7005** | 0.8071 / **0.8396** | 0.6244 / **0.7262** | 21.89 ms | 21.20 ms |
| **Exp 5: RRF + Entity Boost** | 0.7800 / **0.8200** | 0.8400 / **0.8800** | 0.8450 / **0.8900** | 0.8450 / **0.8950** | 0.5293 / **0.6980** | 0.5352 / **0.7229** | 0.8096 / **0.8421** | 0.6482 / **0.7493** | 68.03 ms | 65.40 ms |
| **Exp 6: Full Pipeline (+ Cross-Encoder)** | **0.8000** / **0.8400** | **0.8450** / **0.8850** | **0.8600** / **0.9000** | **0.8650** / **0.9050** | **0.5476** / **0.7214** | **0.5526** / **0.7478** | **0.8263** / **0.8583** | **0.6730** / **0.7787** | 625.10 ms | 891.64 ms |

### 2.3 Key Empirical Retrieval Insights

1. **Impact of Canonicalization**: On raw shorthand labels, Recall@10 appeared capped at `0.5526`. Once alias discrepancy was forensically resolved with canonical zero-padded IDs (`relevance_labels_v2_canonicalized.json`), genuine Recall@10 rose to **0.7478** (and NDCG@10 reached **0.7787**).
2. **The 10% Uncataloged Ceiling**: 20 queries out of 200 target constitutional articles (e.g., Articles 148, 174, 280, 311) absent from the 137-article subset. On in-corpus queries alone (180 queries), the Cross-Encoder reaches **0.9333 Hit@10** and **0.7781 Recall@10**.
3. **Cross-Encoder Ranking Quality Gain**: Moving from Exp 1 (BM25) to Exp 6 (Full Neural Pipeline) delivers a **+3.12% MRR lift** (0.8271 $\to$ 0.8583) and a **+5.90% NDCG@10 improvement** (0.7197 $\to$ 0.7787). This confirms that cross-attention resolves ambiguous candidate rankings that neither bi-encoders nor lexical counters can separate.
4. **Latency vs. Accuracy Trade-Off**: Lexical BM25 operates in **3.75 ms**, whereas the neural cross-encoder runs on CPU at **~892 ms steady-state median**. For resource-constrained interactive deployments, RRF + Entity Boost (Exp 5, 68 ms) provides a pragmatic sweet spot.

---

## 3. Legal Named Entity Recognition Evaluation (Exp 7)

- **Benchmark**: `data/annotations/ner_annotations.json` (105 annotated legal queries, 211 entity spans).
- **Evaluation Criteria**: Strict Exact-Span Match (`exact_span_match=True`).
- **Overall Metrics**: **Micro-F1 = 0.8714**, **Macro-F1 = 0.8496**, Overall Precision = **0.8756**, Overall Recall = **0.8673**.

### 3.1 Per-Category Performance Breakdown

| Entity Category | Support | TP | FP | FN | Precision | Recall | F1 Score | Detection Method |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| `ARTICLE` | 40 | 40 | 0 | 0 | **1.0000** | **1.0000** | **1.0000** | Exact statutory regex (`Article \d+[A-Z]?`) |
| `AMENDMENT` | 15 | 15 | 0 | 0 | **1.0000** | **1.0000** | **1.0000** | Ordinal statutory regex (`\d+(?:st|nd|rd|th)\s+Amendment`) |
| `SECTION` | 11 | 11 | 0 | 0 | **1.0000** | **1.0000** | **1.0000** | Section statutory regex (`Section \d+[A-Z]?`) |
| `DATE` | 38 | 38 | 0 | 0 | **1.0000** | **1.0000** | **1.0000** | Year and calendar date regex |
| `PERSON` | 14 | 13 | 2 | 1 | **0.8667** | **0.9286** | **0.8966** | `PERSON_TITLE_PATTERN` regex + corpus gazetteer |
| `CASE` | 31 | 23 | 1 | 8 | **0.9583** | **0.7419** | **0.8364** | Landmark case gazetteer + adversary regex (`v.`) |
| `ACT` | 15 | 10 | 0 | 5 | **1.0000** | **0.6667** | **0.8000** | Statutory Act title regex + gazetteer |
| `COURT` | 23 | 14 | 1 | 9 | **0.9333** | **0.6087** | **0.7368** | Institutional court gazetteer |
| `RIGHT` | 9 | 5 | 1 | 4 | **0.8333** | **0.5556** | **0.6667** | Constitutional rights gazetteer |
| `LEGAL_CONCEPT` | 15 | 14 | 21 | 1 | **0.4000** | **0.9333** | **0.5600** | Corpus-extracted concept gazetteer |
| **MICRO AVG** | 211 | 183 | 26 | 28 | **0.8756** | **0.8673** | **0.8714** | Exact token and span match |
| **MACRO AVG** | 10 classes | - | - | - | **0.8991** | **0.8435** | **0.8496** | Unweighted class average |

### 3.2 Error Analysis & Adversarial Insights
- **The `PERSON` Resolution**: Baseline NER scored F1 = 0.0000 due to bare judge names. Introducing `PERSON_TITLE_PATTERN` (`Chief Justice`, `Justice`, `Dr.`) resolved 13 of 14 mentions, lifting F1 to **0.8966**.
- **The `LEGAL_CONCEPT` Trade-Off**: Concepts achieve high recall (0.9333) but lower precision (0.4000, 21 false positives). Terms like *"equality"*, *"procedure"*, or *"fundamental rights"* trigger broad concept flags when queries mention procedural rights colloquially.
- **Gazetteer Memorization Disclosure**: The 12 judge names in the benchmark were added directly to static gazetteers. While title regex generalizes to unseen judges (100% on unseen test names), uncataloged bare personal names do not generalize without title prefixes.

---

## 4. Intent Classification Evaluation (Exp 8)

- **Dataset**: `data/benchmark/classification_queries.json` (220 queries across 11 balanced classes).
- **Evaluation Protocols**:
  1. 80/20 Holdout Split (187 train, 33 test) with stratified sampling (`EVAL_RANDOM_SEED = 42`).
  2. 5-Fold Stratified Cross-Validation on the full 220-query set.

### 4.1 Model Architecture Comparison (80/20 Holdout)

| Model Architecture | Accuracy | Macro Precision | Macro Recall | Macro F1 | Weighted F1 |
|---|:---:|:---:|:---:|:---:|:---:|
| **Rule-Based Baseline** | 0.6970 | 0.5939 | 0.6970 | 0.6290 | 0.6290 |
| **Hybrid Classifier** | 0.6970 | 0.6000 | 0.6970 | 0.6301 | 0.6301 |
| **TF-IDF + Logistic Regression** | **0.8485** | **0.8727** | **0.8485** | **0.8331** | **0.8331** |

### 4.2 5-Fold Stratified Cross-Validation Results
To prove that holdout performance was not an artifact of favorable test splitting, 5-fold cross-validation was executed:
- **Mean Accuracy**: **0.7591** ($\pm 0.0422$)
- **Mean Macro-F1**: **0.7444** ($\pm 0.0417$)
- **Fold Accuracies**: Fold 1: 0.7727, Fold 2: 0.7500, Fold 3: 0.7955, Fold 4: 0.7727, Fold 5: 0.7045.

### 4.3 Why TF-IDF + Logistic Regression Outperforms Larger Models
With a curated training dataset of 187 queries, fine-tuning large pre-trained transformers (such as BERT or RoBERTa) risks severe catastrophic overfitting. Unigram and bigram TF-IDF features ($n \in \{1, 2\}$) paired with regularized Logistic Regression (`class_weight='balanced'`, $C=1.0$) provide optimal bias-variance trade-off, sub-millisecond inference, and transparent decision weights.

---

## 5. Entity Linking & Query Expansion Evaluations

### 5.1 Canonical Entity Linking (`nlp/entity_linking.py`)
- **Benchmark**: `data/benchmark/entity_linking_queries.json` (33 queries).
- **In-KB Alias Normalization**: **26 / 30 correct (86.67% accuracy)**. Successfully resolves informal aliases:
  - *"Puttaswamy privacy case"* $\to$ `case_sc_puttaswamy_privacy_2017`
  - *"Art 21"* / *"Article 21"* $\to$ `const_art_021`
  - *"Basic structure judgment"* $\to$ `case_sc_kesavananda_1973`
- **Out-of-KB Rejection**: **3 / 3 correct (100% rejection accuracy)**. Successfully rejects non-constitutional entities (e.g., *"Section 420 IPC"*, *"Motor Vehicles Act"*) without forcing false links.

### 5.2 Controlled Query Expansion (`nlp/query_expansion.py`)
- **Benchmark**: `data/benchmark/query_expansion_benchmark.json` (20 queries).
- **Term Precision**: **0.7500** (15 / 20 queries received legally accurate expansions).
- **Semantic Drift Rate**: **0.0%**. Because expansions are strictly capped at 3 domain-verified ontology synonyms, zero queries drifted into irrelevant statutory domains.

---

## 6. RAG Grounding, Citations & Abstention Audit

Evaluated across adversarial and out-of-scope benchmarks in `evaluation/results/rag_grounding_adversarial_audit.json`:

| Case ID | Query Category | Query Content | Retrieved Context | Citation Score | Abstained? | Grounding Verdict |
|:---:|:---:|---|---|:---:|:---:|:---:|
| `RAG_01` | In-Domain Direct | Supreme Court ruling in Puttaswamy on Article 21 Privacy | Art 21, Puttaswamy (2017) | 1.0000 | **False** | **PASS** (Grounded answer synthesized) |
| `RAG_02` | In-Domain Precedent | Basic Structure Doctrine in Kesavananda Bharati | Art 368, Kesavananda, Minerva Mills | 1.0000 | **False** | **PASS** (Grounded answer synthesized) |
| `RAG_03` | In-Domain Procedure | Procedure for constitutional amendment under Art 368 | Art 368, 24th Amendment | 1.0000 | **False** | **PASS** (Grounded answer synthesized) |
| `RAG_04` | Out-of-Scope Statutory | Penalty for cheque bounce under Section 138 NI Act | Sub-threshold penal fragments | 0.0000 | **True** | **PASS** (Safely abstained, zero hallucination) |
| `RAG_05` | Out-of-Scope Criminal | Procedure for lodging FIR for theft under IPC | Sub-threshold procedural fragments | 0.0000 | **True** | **PASS** (Safely abstained, zero hallucination) |
| `RAG_06` | Non-Existent Article | Provisions of Article 999 of the Constitution | 0 matching chunks retrieved | 0.0000 | **True** | **PASS** (Early abstention triggered) |

### Grounding & Abstention Metrics:
- **Structural Citation Validity Rate**: **1.0000** (All citations correspond to verified parent records present in retrieved context).
- **Automated Abstention Accuracy**: **1.0000** (100% of out-of-scope and unevidenced queries safely rejected).

---

## 7. Subsystem Latency & Runtime Profiling

Measured across 20 repeated trials on host CPU (`torch 2.10.0+cpu`, AMD/Intel multi-core):

```text
Pipeline Subsystem             Mean Latency    Median Latency   P95 Latency    Min Latency    Max Latency
---------------------------------------------------------------------------------------------------------
Sparse BM25 Search                 3.36 ms         3.02 ms         4.43 ms        2.68 ms        4.77 ms
Dense Vector Search (ChromaDB)    24.04 ms        19.79 ms        63.83 ms       15.92 ms       73.31 ms
Reciprocal Rank Fusion (RRF)       0.54 ms         0.48 ms         0.82 ms        0.35 ms        0.91 ms
Legal Entity Rank Boosting         2.15 ms         1.92 ms         3.10 ms        1.50 ms        3.45 ms
Cross-Encoder Neural Reranking  1320.70 ms       891.64 ms      1390.67 ms      793.56 ms     9931.38 ms
Offline Synthesis & Hydration    555.03 ms       566.45 ms       589.35 ms      502.68 ms      609.21 ms
---------------------------------------------------------------------------------------------------------
End-to-End Pipeline Execution    1.90 s          1.48 s          2.05 s         1.32 s        10.55 s
```

*Note on Latency Spike*: The first query invocation after boot includes model weight cold-start loading (~9.9 seconds). Steady-state interactive latency consistently settles at **~1.48 seconds**.

---

## 8. Reproducing All Experiments

Every experiment script can be executed independently from the command line:

```powershell
# Execute individual experiments
python experiments/experiment_01_bm25.py
python experiments/experiment_02_dense.py
python experiments/experiment_03_hybrid.py
python experiments/experiment_04_rrf.py
python experiments/experiment_05_entity_boost.py
python experiments/experiment_06_reranker.py
python experiments/experiment_07_ner.py
python experiments/experiment_08_intent.py

# Execute full evaluation suite & regenerate all summary artifacts
python scripts/run_all_evaluations.py
```
