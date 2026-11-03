# Experimental Ablation Suite: `12_EXPERIMENTS/experiments_explained.md`

[Back to Main Index](../README.md)

---

## 1. Overview of the Experiments Directory

The `experiments/` directory contains standalone, reproducible Python scripts corresponding to the 8 core empirical experiments conducted during the development of the Indian Constitution Legal AI Assistant.

Each script:
- Evaluates a single specific component or retrieval ablation in complete isolation.
- Measures standardized metrics (Hit@1, Hit@5, Hit@10, Recall@5, MRR, NDCG@10, Macro-F1).
- Operates on the verified benchmark queries and gold annotations.
- Outputs machine-readable results to `experiments/results/experiment_XX_*.json`.

```
experiments/
├── experiment_01_bm25.py          # Exp 1: BM25 Lexical Retrieval Baseline
├── experiment_02_dense.py         # Exp 2: Dense Semantic Vector Baseline (BGE-M3)
├── experiment_03_hybrid.py        # Exp 3: Naive Linear Hybrid Combination
├── experiment_04_rrf.py           # Exp 4: Reciprocal Rank Fusion (RRF, k=60)
├── experiment_05_entity_boost.py  # Exp 5: Statutory Entity-Aware Ranking Boost
├── experiment_06_reranker.py      # Exp 6: Cross-Encoder Neural Reranking (Full Pipeline)
├── experiment_07_ner.py           # Exp 7: Legal Named Entity Recognition (10 Classes)
├── experiment_08_intent.py        # Exp 8: Intent Classification (Zero-Leakage Split)
└── results/                       # Persisted JSON experiment artifacts
```

---

## 2. Detailed Breakdown of the 8 Experiments

### Experiment 01: BM25 Lexical Baseline (`experiment_01_bm25.py`)
- **Hypothesis**: Pure keyword matching will achieve high precision on exact numeric queries (`"Article 21"`) but will fail on semantic paraphrases (*"right to clean drinking water"*).
- **Implementation**: Runs `BM25Retriever` (Rank-BM25 with compound legal tokenization) across all benchmark queries.
- **Empirical Results**:
  - `Hit@5`: **0.6800** | `Hit@10`: **0.7700** | `MRR`: **0.4912** | `NDCG@10`: **0.5484**
- **Findings**: Strong on exact section lookups, but misses landmark case law where judicial vocabulary diverges from statutory text.

---

### Experiment 02: Dense Vector Baseline (`experiment_02_dense.py`)
- **Hypothesis**: Dense semantic search with `BAAI/bge-m3` will capture high-level conceptual similarities that BM25 misses.
- **Implementation**: Runs `DenseRetriever` over ChromaDB collection `indian_legal_rag_bgem3` (1024-dimensional embeddings, cosine distance).
- **Empirical Results**:
  - `Hit@5`: **0.7200** | `Hit@10`: **0.8100** | `MRR`: **0.5240** | `NDCG@10`: **0.5739** (+4.6% over BM25)
- **Findings**: Captures broad constitutional doctrines, but occasionally suffers from statutory anchor confusion (e.g. retrieving Article 19 when Article 21 was queried because both discuss liberty).

---

### Experiment 03: Naive Linear Hybrid Combination (`experiment_03_hybrid.py`)
- **Hypothesis**: Taking a simple linear combination of normalized scores ($\text{Score} = 0.5 \cdot s_{\text{BM25}} + 0.5 \cdot s_{\text{Dense}}$) will outperform either baseline.
- **Implementation**: Min-max normalizes BM25 and cosine scores into $[0, 1]$ and takes their weighted average.
- **Empirical Results**:
  - `Hit@5`: **0.7600** | `Hit@10`: **0.8400** | `MRR`: **0.5620** | `NDCG@10`: **0.6120** (+11.6% over BM25)
- **Findings**: Outperforms single models, but min-max normalization is vulnerable to outlier score spikes that distort rankings across diverse query lengths.

---

### Experiment 04: Reciprocal Rank Fusion (`experiment_04_rrf.py`)
- **Hypothesis**: Rank-based fusion using Cormack's RRF ($k=60$) will eliminate the scale-distortion problem of score combination.
- **Implementation**:
  $$\text{RRF Score}(d) = \frac{1}{60 + \text{rank}_{\text{BM25}}(d)} + \frac{1}{60 + \text{rank}_{\text{Dense}}(d)}$$
- **Empirical Results**:
  - `Hit@5`: **0.8100** | `Hit@10`: **0.8800** | `MRR`: **0.6150** | `NDCG@10`: **0.6558** (+19.6% over BM25)
- **Findings**: Scale-invariant and robust. Eliminates score calibration issues entirely. Documents appearing in the top 10 of both lists are decisively promoted.

---

### Experiment 05: Statutory Entity-Aware Ranking Boost (`experiment_05_entity_boost.py`)
- **Hypothesis**: Adding an explicit additive boost ($\Delta s = +0.15$) when candidate metadata matches extracted statutory articles or case names will eliminate anchor confusion.
- **Implementation**: Runs `apply_entity_boost()` after RRF fusion, checking candidate `article_number`, `case_name`, and doc IDs against query entities.
- **Empirical Results**:
  - `Hit@5`: **0.8400** | `Hit@10`: **0.9000** | `MRR`: **0.6580** | `NDCG@10`: **0.6994** (+27.5% over BM25)
- **Findings**: Successfully pushes authoritative statutory provisions to Rank 1 and 2 when specifically requested by the user.

---

### Experiment 06: Full Pipeline with Cross-Encoder Reranker (`experiment_06_reranker.py`)
- **Hypothesis**: Re-scoring the top 30 candidate passages using full Transformer cross-attention (`cross-encoder/ms-marco-MiniLM-L-6-v2`) will maximize contextual precision.
- **Implementation**: Concatenates `[CLS] Query [SEP] Passage [SEP]` through all 6 transformer layers, reranking top 30 to final top 5.
- **Empirical Results**:
  - `Hit@5`: **0.8900** | `Hit@10`: **0.9400** | `MRR`: **0.7420** | `NDCG@10`: **0.7787** (**+41.9% gain over BM25!** 🚀)
- **Findings**: The definitive architecture. Captures subtle legal conditions, exceptions, and negations with superior relevance.

---

### Experiment 07: Legal Named Entity Recognition (`experiment_07_ner.py`)
- **Hypothesis**: Rule-based regex combined with dynamic corpus gazetteers and span collision resolution will outperform general-purpose NER (e.g. standard Spacy `en_core_web_sm`).
- **Implementation**: Evaluates `LegalNER` across all 10 entity categories on `data/annotations/legal_ner_gold.json`.
- **Empirical Results**:
  - `Micro-Precision`: **0.8812** | `Micro-Recall`: **0.8420** | `Micro-F1`: **0.8611**
  - `Macro-Precision`: **0.8650** | `Macro-Recall`: **0.8350** | `Macro-F1`: **0.8496**
- **Findings**: 100% precision on numeric articles and amendments; high precision on landmark cases via dynamic gazetteers.

---

### Experiment 08: Zero-Leakage Intent Classification (`experiment_08_intent.py`)
- **Hypothesis**: A Hybrid classifier (Rule-based statutory patterns + ML TF-IDF fallback) trained on `intent_train.json` will outperform either model on unseen `intent_test.json`.
- **Implementation**: Fits TF-IDF Logistic Regression model solely on training partition and evaluates on unseen holdout test partition across 8 legal intent classes.
- **Empirical Results**:
  - `Rule-Based Classifier`: Macro-F1 = **0.8120**
  - `Pure ML (Logistic Regression)`: Macro-F1 = **0.7410**
  - `Hybrid Classifier`: Macro-F1 = **0.8485** | Accuracy = **87.5%**
- **Findings**: The hybrid architecture achieves the highest accuracy by resolving obvious statutory queries deterministically and relying on ML statistical patterns for ambiguous natural language inquiries.

---

## 3. Master Summary Table of Retrieval Ablations

| Exp | Method / Architecture | Hit@5 | Hit@10 | MRR | NDCG@10 | Gain over BM25 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **01** | BM25 Baseline | 0.6800 | 0.7700 | 0.4912 | 0.5484 | — |
| **02** | Dense Vector Baseline (BGE-M3) | 0.7200 | 0.8100 | 0.5240 | 0.5739 | +4.6% |
| **03** | Naive Linear Hybrid Combination | 0.7600 | 0.8400 | 0.5620 | 0.6120 | +11.6% |
| **04** | Hybrid + Reciprocal Rank Fusion (RRF) | 0.8100 | 0.8800 | 0.6150 | 0.6558 | +19.6% |
| **05** | RRF + Statutory Entity Boost (+0.15) | 0.8400 | 0.9000 | 0.6580 | 0.6994 | +27.5% |
| **06** | **Full Pipeline (+ Cross-Encoder Reranker)** | **0.8900** | **0.9400** | **0.7420** | **0.7787** | **+41.9%** 🚀 |

---

## 4. How to Run Any Experiment from the Terminal

```bash
# Run any individual experiment
python -m experiments.experiment_01_bm25
python -m experiments.experiment_02_dense
python -m experiments.experiment_03_hybrid
python -m experiments.experiment_04_rrf
python -m experiments.experiment_05_entity_boost
python -m experiments.experiment_06_reranker
python -m experiments.experiment_07_ner
python -m experiments.experiment_08_intent
```

---

## 5. Viva Presentation & Defense Q&A

### Q1: What was the purpose of creating 8 separate experiment scripts?
> **Student Answer**:
> *"Scientific research requires empirical ablations to prove that every proposed architectural component adds genuine value. Instead of presenting the final pipeline as a black box, our 8 experiment scripts systematically test each layer in isolation: starting with BM25, adding BGE-M3 dense embeddings, introducing RRF fusion, adding entity boosting, and finally adding neural reranking. The results prove step-by-step how our engineering decisions improved NDCG@10 from 0.5484 to 0.7787."*

