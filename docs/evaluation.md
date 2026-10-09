# Indian Constitution Legal AI Assistant — Evaluation Methodology & Empirical Benchmarks

## 1. Evaluation Framework Overview

The quantitative evaluation suite of the **Indian Constitution Legal AI Assistant** provides empirical validation across all pipeline subsystems:
1. **Information Retrieval (IR)**: Multi-stage ablation across Lexical BM25, Dense Vector Search, Linear Hybrid, Reciprocal Rank Fusion (RRF), Legal Entity Boosting, and Cross-Encoder Neural Reranking.
2. **Domain-Specific Legal Named Entity Recognition (NER)**: Evaluated on 10 legal entity categories using strict exact-token and exact-span matching.
3. **Intent Classification**: Rule-based baseline vs. TF-IDF + Logistic Regression vs. Hybrid classifier, evaluated via holdout and 5-fold cross-validation.
4. **Canonical Entity Linking & Query Expansion**: Surface mention normalization, out-of-KB rejection, and controlled synonym drift prevention.
5. **RAG Grounding & Citation Integrity**: Structural citation provenance, ungrounded claim detection, and confidence-based automated abstention.

All metrics are computed deterministically (`EVAL_RANDOM_SEED = 42`) and serialized to machine-readable artifacts in `evaluation/results/` and `experiments/results/`.

---

## 2. Mathematical Metric Definitions

### 2.1 Information Retrieval Metrics

Let $Q$ be the set of evaluation queries, and for query $q \in Q$, let $\text{Rel}_q$ be the ground truth set of relevant parent document IDs. Let $R_{q, K} = [d_1, d_2, \dots, d_K]$ be the ranked list of top-$K$ retrieved documents.

#### Hit@K
Measures whether at least one relevant document appears in the top-$K$ results:
$$\text{Hit@K} = \frac{1}{|Q|} \sum_{q \in Q} \mathbb{I}\left( |\text{Rel}_q \cap \{d_1, \dots, d_K\}| > 0 \right)$$

#### Recall@K
Measures the proportion of all relevant documents captured in the top-$K$ results:
$$\text{Recall@K} = \frac{1}{|Q|} \sum_{q \in Q} \frac{|\text{Rel}_q \cap \{d_1, \dots, d_K\}|}{|\text{Rel}_q|}$$

#### Precision@K
Measures the fraction of retrieved top-$K$ documents that are relevant:
$$\text{Precision@K} = \frac{1}{|Q|} \sum_{q \in Q} \frac{|\text{Rel}_q \cap \{d_1, \dots, d_K\}|}{K}$$

#### Mean Reciprocal Rank (MRR)
Evaluates the reciprocal rank of the first relevant document:
$$\text{MRR} = \frac{1}{|Q|} \sum_{q \in Q} \frac{1}{\text{rank}_q^*}$$
where $\text{rank}_q^*$ is the 1-based index of the first relevant document in $R_q$ (and 0 if no relevant document is retrieved).

#### Normalized Discounted Cumulative Gain (NDCG@K)
Accounts for the graded position of all relevant documents:
$$\text{DCG@K} = \sum_{i=1}^K \frac{2^{\text{rel}(d_i)} - 1}{\log_2(i + 1)}, \quad \text{IDCG@K} = \sum_{i=1}^{\min(K, |\text{Rel}_q|)} \frac{2^1 - 1}{\log_2(i + 1)}, \quad \text{NDCG@K} = \frac{1}{|Q|} \sum_{q \in Q} \frac{\text{DCG@K}}{\text{IDCG@K}}$$
where $\text{rel}(d_i) \in \{0, 1\}$ denotes binary ground truth relevance.

---

### 2.2 NLP Classification & NER Metrics

For an entity class or intent category $c \in C$:
$$\text{Precision}_c = \frac{\text{TP}_c}{\text{TP}_c + \text{FP}_c}, \quad \text{Recall}_c = \frac{\text{TP}_c}{\text{TP}_c + \text{FN}_c}, \quad \text{F1}_c = \frac{2 \cdot \text{Precision}_c \cdot \text{Recall}_c}{\text{Precision}_c + \text{Recall}_c}$$

- **Macro-F1**: Unweighted arithmetic mean across all classes (crucial for evaluating minority legal classes):
  $$\text{Macro-F1} = \frac{1}{|C|} \sum_{c \in C} \text{F1}_c$$
- **Micro-F1**: Globally aggregated counts across all classes:
  $$\text{Micro-F1} = \frac{2 \cdot \sum_c \text{TP}_c}{2 \cdot \sum_c \text{TP}_c + \sum_c \text{FP}_c + \sum_c \text{FN}_c}$$

---

## 3. Information Retrieval Empirical Findings

Evaluated across the 200-query benchmark (`data/benchmark/retrieval_queries.json`) against both Original Shorthand Labels and Canonical Ground Truth (`data/annotations/relevance_labels_v2_canonicalized.json`):

| Method | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Recall@5 | Recall@10 | MRR | NDCG@5 | NDCG@10 | Avg Latency |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Exp 1: BM25 Only** | 0.7900 | 0.8750 | 0.8850 | 0.8950 | 0.6724 | 0.7003 | 0.8271 | 0.7208 | 0.7197 | 3.75 ms |
| **Exp 2: Dense Only** | 0.8100 | 0.8800 | 0.8900 | 0.8950 | 0.6811 | 0.7131 | 0.8385 | 0.7416 | 0.7432 | 17.73 ms |
| **Exp 3: Linear Hybrid** | 0.8100 | 0.8800 | 0.8900 | 0.8950 | 0.6789 | 0.7076 | 0.8411 | 0.7335 | 0.7333 | 22.01 ms |
| **Exp 4: BM25 + Dense + RRF** | 0.8100 | 0.8800 | 0.8900 | 0.8950 | 0.6750 | 0.7005 | 0.8396 | 0.7279 | 0.7262 | 21.89 ms |
| **Exp 5: RRF + Entity Boost** | 0.8200 | 0.8800 | 0.8900 | 0.8950 | 0.6980 | 0.7229 | 0.8421 | 0.7511 | 0.7493 | 68.03 ms |
| **Exp 6: Full Pipeline (+ Cross-Encoder)** | **0.8400** | **0.8850** | **0.9000** | **0.9050** | **0.7214** | **0.7478** | **0.8583** | **0.7810** | **0.7787** | 625.10 ms |

*(Metrics computed using Canonical Ground Truth. On original unpadded labels, Recall@10 is 0.5064 for BM25 and 0.5526 for Cross-Encoder due to shorthand ID mismatches).*

---

## 4. Legal Named Entity Recognition (NER) Findings

Evaluated on 105 annotated legal queries (211 entity spans) under strict exact-span matching (`exact_span_match=True`):

- **Overall Micro-F1**: **0.8714** (Precision: 0.8756, Recall: 0.8673)
- **Overall Macro-F1**: **0.8496** (Precision: 0.8991, Recall: 0.8435)

| Category | Support | TP | FP | FN | Precision | Recall | F1 Score | Resolution & Error Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| `ARTICLE` | 40 | 40 | 0 | 0 | **1.0000** | **1.0000** | **1.0000** | Perfect extraction via statutory regex |
| `AMENDMENT` | 15 | 15 | 0 | 0 | **1.0000** | **1.0000** | **1.0000** | Perfect extraction via ordinal regex |
| `SECTION` | 11 | 11 | 0 | 0 | **1.0000** | **1.0000** | **1.0000** | Perfect extraction via Section regex |
| `DATE` | 38 | 38 | 0 | 0 | **1.0000** | **1.0000** | **1.0000** | Perfect extraction via calendar regex |
| `PERSON` | 14 | 13 | 2 | 1 | **0.8667** | **0.9286** | **0.8966** | Resolved from 0.0000 via judicial title extraction |
| `CASE` | 31 | 23 | 1 | 8 | **0.9583** | **0.7419** | **0.8364** | High precision; misses uncataloged abbreviations |
| `ACT` | 15 | 10 | 0 | 5 | **1.0000** | **0.6667** | **0.8000** | High precision; uncataloged statutory Acts missed |
| `COURT` | 23 | 14 | 1 | 9 | **0.9333** | **0.6087** | **0.7368** | Institutional entities captured |
| `RIGHT` | 9 | 5 | 1 | 4 | **0.8333** | **0.5556** | **0.6667** | Core Fundamental Rights captured |
| `LEGAL_CONCEPT` | 15 | 14 | 21 | 1 | **0.4000** | **0.9333** | **0.5600** | High recall; conversational over-triggering FP |

---

## 5. Intent Classification Model Comparison

Evaluated on 220 queries across 11 balanced intent classes:

### 5.1 80/20 Holdout Split (187 Train / 33 Test)
- **rule_based_baseline**: Accuracy = 0.6970, Macro-F1 = 0.6290
- **hybrid_classifier**: Accuracy = 0.6970, Macro-F1 = 0.6301
- **tfidf_logistic_regression**: Accuracy = **0.8485**, Macro-F1 = **0.8331**, Macro-Precision = **0.8727**

### 5.2 5-Fold Stratified Cross-Validation (TF-IDF + LogReg)
- **Mean Accuracy**: **0.7591** ($\pm 0.0422$)
- **Mean Macro-F1**: **0.7444** ($\pm 0.0417$)

---

## 6. Entity Linking, Query Expansion & RAG Reliability

- **Canonical Entity Linking Accuracy**: **0.8667** (26/30 correct on aliased queries).
- **Out-of-KB Rejection**: **1.0000** (3/3 non-constitutional queries cleanly rejected).
- **Query Expansion Term Precision**: **0.7500** with **0.0% semantic drift rate**.
- **Structural Citation Validity Rate**: **1.0000** (All generated citations map to retrieved context).
- **Automated Abstention Accuracy**: **1.0000** on adversarial out-of-scope queries.

---

## 7. Execution Commands to Reproduce Evaluations

```powershell
# Run all evaluations and update evaluation/results/
python scripts/run_all_evaluations.py

# Run all automated test cases (254 passing)
.\venv\Scripts\pytest -q
```
