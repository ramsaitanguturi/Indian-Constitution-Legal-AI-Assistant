# Indian Constitution Legal AI Assistant — NLP Capstone

An empirical Natural Language Processing (NLP) and Information Retrieval (IR) framework for Question Answering over Indian Constitutional Law. Integrates domain-specific Legal Named Entity Recognition (NER), canonical entity linking, hybrid retrieval with Reciprocal Rank Fusion (RRF), Cross-Encoder neural reranking, evidence-grounded generation, structural citation validation, explainable confidence estimation, an interactive Research Dashboard, and a 10-stage NLP Pipeline Inspector.

---

## 1. Problem Statement & Research Motivation

Constitutional question answering in India presents significant NLP challenges:
- **Hierarchical Statutory Text**: Constitutional Articles contain nested clauses, sub-clauses, and cross-references to other Parts and Schedules.
- **Judicial Precedents**: Landmark Supreme Court judgments interpret constitutional doctrines (e.g., the *Basic Structure Doctrine* from *Kesavananda Bharati*, or the *Right to Privacy* under *Article 21* from *Puttaswamy*).
- **Lexical vs. Semantic Mismatch**: Citizen queries frequently use conversational language (*"can police search my phone without a warrant"*), which traditional keyword search misses; conversely, purely dense vector search struggles with exact statutory references (*"Article 21A"* vs *"Article 21"*).
- **Hallucination Risks**: General-purpose LLMs generate convincing but fabricated citations, statutes, and legal holdings without verifiable evidentiary grounding.

**Research Contribution:**
This project designs, implements, and empirically evaluates an end-to-end framework combining:
1. **Domain-Specific Legal NER & Canonical Entity Linking** across 10 categories.
2. **Entity-Aware Hybrid Retrieval**: Standalone BM25Okapi + Dense vector embeddings (ChromaDB) fused via Reciprocal Rank Fusion (RRF, $k=60$) with an entity rank boost ($+0.15$).
3. **Cross-Encoder Neural Reranking**: `cross-encoder/ms-marco-MiniLM-L-6-v2` reordering candidate passages.
4. **Hierarchical Parent-Child Context Recovery**: Preserves fine-grained retrieval precision while hydrating full parent Articles and Judgments for generation.
5. **Grounded RAG with Structural Citation Validation**: Validates that all citations correspond to retrieved context.
6. **Explainable Confidence & Multi-Stage Abstention**: Refuses out-of-scope queries and sub-threshold evidence.
7. **Empirical Research Dashboard & Diagnostic Pipeline Inspector**: Built into the Streamlit interface for live demonstration and defense.

---

## 2. Target Architecture & Component Responsibilities

The system consists of modular, independently testable subpackages:

```
                            USER QUERY
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Language Detection   │  nlp/language_detection.py
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Query Preprocessing  │  nlp/preprocessing.py
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Domain Legal NER    │  nlp/legal_ner.py (10 categories)
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Canonical Entity Link │  nlp/entity_linking.py (KB normalization)
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Intent Classification │  nlp/intent_classifier.py (Hybrid)
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Controlled Expansion  │  nlp/query_expansion.py
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Specialized Router    │  routing/query_router.py
                    └───────────┬───────────┘
                                │
    ┌───────────────────────────┴───────────────────────────┐
    ▼                                                       ▼
┌──────────────┐ BM25Okapi                               ┌──────────────┐ ChromaDB
│ Sparse Search│ k1=1.5, b=0.75                          │ Dense Search │ all-MiniLM-L6-v2
└──────┬───────┘                                         └──────┬───────┘
       │                                                        │
       └───────────────────────────┬────────────────────────────┘
                                   ▼
                       ┌───────────────────────┐
                       │ Reciprocal Rank Fusion│  retrieval/rrf.py (k=60)
                       └───────────┬───────────┘
                                   │
                                   ▼
                       ┌───────────────────────┐
                       │  Entity Rank Boosting │  retrieval/entity_boost.py (+0.15)
                       └───────────┬───────────┘
                                   │
                                   ▼
                       ┌───────────────────────┐
                       │ Cross-Encoder Rerank  │  retrieval/reranker.py
                       │ ms-marco-MiniLM-L-6-v2│  Top 20 -> Top 5
                       └───────────┬───────────┘
                                   │
                                   ▼
                       ┌───────────────────────┐
                       │ Context Recovery      │  rag/parent_child.py
                       │  (Parent-Child RAG)   │  Full Articles & Judgments
                       └───────────┬───────────┘
                                   │
                                   ▼
                       ┌───────────────────────┐
                       │ Grounded Generator    │  rag/generator.py
                       │ Gemini / Offline Fall │  Evidence-bounded prompt
                       └───────────┬───────────┘
                                   │
                                   ▼
                       ┌───────────────────────┐
                       │ Structural Citation   │  rag/citation_validator.py
                       │      Validation       │  Verify provenance against context
                       └───────────┬───────────┘
                                   │
                                   ▼
                       ┌───────────────────────┐
                       │ Confidence Estimator  │  rag/confidence.py
                       │ 6 Weighted Signals    │  Uncalibrated heuristic
                       └───────────┬───────────┘
                                   │
                                   ▼
                       ┌───────────────────────┐
                       │ Multi-Stage Abstention│  rag/abstention.py
                       │ Router/IR/Post-Gen    │  Safe refusal
                       └───────────────────────┘
```

---

## 3. NLP Query Understanding Pipeline

- **Language Detection** (`nlp/language_detection.py`): Identifies query language, validating English inputs while flagging non-English queries for safe handling.
- **Legal Preprocessing** (`nlp/preprocessing.py`): Normalizes statutory legal formatting, case citations, legal abbreviations (`"Art."` $\to$ `"Article"`, `"v."` $\to$ `"versus"`), and whitespace.
- **Legal NER** (`nlp/legal_ner.py`): Hybrid extractor identifying 10 legal categories: `ARTICLE`, `CASE`, `AMENDMENT`, `ACT`, `SECTION`, `COURT`, `DATE`, `RIGHT`, `LEGAL_CONCEPT`, `PERSON`.
- **Canonical Entity Linking** (`nlp/entity_linking.py`): Resolves surface mentions (e.g., *"Puttaswamy privacy case"*, *"Art 21"*) to unambiguous corpus IDs (`parent_case_sc_puttaswamy_privacy_2017`, `parent_const_art_021`), rejecting out-of-knowledge-base entities cleanly.
- **Intent Classification** (`nlp/intent_classifier.py`): Classifies user queries across 11 intent classes using a rule-based baseline, a TF-IDF + Logistic Regression model, and a confidence-calibrated hybrid classifier.
- **Controlled Query Expansion** (`nlp/query_expansion.py`): Maps conversational citizen phrases to formal constitutional terms using a curated legal ontology, preventing semantic drift.

---

## 4. Hybrid Retrieval & Neural Reranking Methodology

The retrieval pipeline executes a multi-stage fusion and reranking workflow:

1. **Lexical Sparse Retrieval** (`retrieval/bm25_retriever.py`):
   - Algorithm: **BM25Okapi** ($k_1=1.5, b=0.75$).
   - Tokenization: Legal punctuation-preserving regex.
2. **Dense Vector Retrieval** (`retrieval/dense_retriever.py`):
   - Model: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions).
   - Vector Database: **ChromaDB** with cosine distance converted to similarity ($1 - \text{distance}$).
3. **Reciprocal Rank Fusion** (`retrieval/rrf.py`):
   $$RRF\_Score(d) = \sum_{m \in \{\text{BM25}, \text{Dense}\}} \frac{1}{k + r_m(d)} \quad (k = 60)$$
4. **Legal Entity Score Boost** (`retrieval/entity_boost.py`):
   Adds $+0.15$ to candidate scores when candidate metadata matches extracted and linked legal entities.
5. **Cross-Encoder Neural Reranking** (`retrieval/reranker.py`):
   - Model: `cross-encoder/ms-marco-MiniLM-L-6-v2`.
   - Takes top-20 fused candidates, scores `(query, passage)` pairs jointly via full cross-attention, and returns the top 5 candidates.

---

## 5. Grounded RAG, Citations, Confidence & Abstention

- **Parent-Child Context Recovery** (`rag/parent_child.py`): Hydrates granular child chunks (~300 characters) into full parent documents (`parent_store.json`), providing the generator with complete constitutional context.
- **Evidence-Grounded Generator** (`rag/generator.py`): Generates answers strictly from retrieved evidence, with fallback to an offline **Heuristic Legal Synthesizer** when no API key is available.
- **Structural Citation Validation** (`rag/citation_validator.py`): Checks that every cited Article, Case, or Bench reference exists in the legal database and was present in retrieved evidence.
  > **Important Scientific Notice:** Structural citation validation checks source references and provenance against retrieved context passages. It does NOT establish semantic support, legal interpretation correctness, or legal advice reliability. Do not represent a small benchmark's results as proof of legal correctness.
- **Explainable Confidence Estimator** (`rag/confidence.py`): Transparent weighted composite across 6 signals (retrieval strength, evidence volume, entity alignment, retrieval agreement, citation validity, query coverage). *Explicitly disclosed as an explainable heuristic, not a mathematically calibrated probability.*
- **Multi-Stage Automated Abstention** (`rag/abstention.py`): Refuses out-of-scope queries, zero-retrieval outcomes, and sub-threshold evidence.

---

## 6. Empirical Evaluation Results

All metrics below are drawn directly from active saved evaluation artifacts in `evaluation/results/`:

### 6.1 Information Retrieval Empirical Evaluation (200 Verified Queries)

| Retrieval Configuration | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Recall@5 | Recall@10 | MRR | NDCG@5 | NDCG@10 | Avg Latency |
|---|---|---|---|---|---|---|---|---|---|---|
| **Exp 1: BM25 Only** | 0.7500 | 0.8400 | 0.8500 | 0.8600 | 0.5018 | 0.5064 | 0.7962 | 0.6166 | 0.6157 | 4.1 ms |
| **Exp 2: Dense Only** | 0.7750 | 0.8400 | 0.8500 | 0.8500 | 0.5096 | 0.5250 | 0.8072 | 0.6413 | 0.6429 | 18.0 ms |
| **Exp 3: BM25 + Dense (Linear)** | 0.7700 | 0.8450 | 0.8550 | 0.8600 | 0.5050 | 0.5150 | 0.8099 | 0.6297 | 0.6298 | 22.8 ms |
| **Exp 4: BM25 + Dense + RRF** | 0.7700 | 0.8400 | 0.8550 | 0.8550 | 0.5056 | 0.5106 | 0.8071 | 0.6261 | 0.6244 | 22.4 ms |
| **Exp 5: RRF + Entity Boost** | 0.7800 | 0.8400 | 0.8450 | 0.8450 | 0.5285 | 0.5348 | 0.8096 | 0.6513 | 0.6492 | 66.4 ms |
| **Exp 6: Full Pipeline (+ Cross-Encoder)** | **0.8000** | **0.8450** | **0.8600** | **0.8650** | **0.5476** | **0.5526** | **0.8263** | **0.6752** | **0.6730** | 623.9 ms |

> *Empirical Ablation Insight:* Progressing from lexical BM25 baseline to full neural reranking yields a **+3.01% MRR improvement** (0.7962 -> 0.8263) and a **+5.73% NDCG@10 gain** (0.6157 -> 0.6730), empirically confirming the complementary power of domain-specific entity boosting and cross-attention reranking.

### 6.2 Legal Named Entity Recognition (NER) (105 Annotated Queries)
- **Exact Span Micro-F1:** 0.8148 | **Macro-F1:** 0.7408 | **Gold Entities:** 211
- Structured categories (`ARTICLE`, `AMENDMENT`, `SECTION`, `DATE`): **1.0000 F1**
- `CASE`: **0.8214 F1** | `ACT`: **0.8000 F1** | `COURT`: **0.7368 F1** | `RIGHT`: **0.6667 F1**
- `LEGAL_CONCEPT`: **0.3830 F1** (boundary variance across abstract multi-word doctrines)

### 6.3 Intent Classification (220 Queries across 11 Classes)
- **rule_based_baseline:** Accuracy = 0.6970, Macro-F1 = 0.6290
- **tfidf_logistic_regression:** Accuracy = **0.8485**, Macro-F1 = **0.8331**
- **hybrid_classifier:** Accuracy = 0.6970, Macro-F1 = 0.6301
- **5-Fold Stratified Cross-Validation (TF-IDF + LogReg):** Accuracy = 0.7591 (±0.0422), Macro-F1 = 0.7444 (±0.0417)

### 6.4 Entity Linking, Expansion & Grounding
- **Canonical Entity Linking Accuracy:** 0.8667 (Out-of-KB rejection: 1.0000)
- **Controlled Query Expansion Precision:** 0.7500 (Drift rate: 0.0%)
- **Structural Citation Validity Rate:** 0.9456 (Evaluated on 100 benchmark questions)
- **Automated Abstention Accuracy:** 1.0000 (100% accurate rejection of out-of-scope inquiries)

---

## 7. Interactive Streamlit Application

The Streamlit user interface (`app.py`) provides 5 dedicated tabs:

1. **💬 Ask Assistant & RAG Query**:
   - Primary interface with preset benchmark queries and live query input.
   - Strategy, intent, language, confidence, and citation validation badges.
   - Hydrated parent-child context inspection.
   - **🔬 10-Stage NLP Pipeline Inspector**: Expandable diagnostic trace displaying query preprocessing, entity linking, intent classification, retrieval candidate scoring, reranking contributions, citation validation, and confidence signals. Toggleable via sidebar.
2. **⚖️ Case Comparator**: Side-by-side comparative analysis of landmark Supreme Court judgments.
3. **📜 Constitution & Cases Database**: Interactive data table explorer for constitutional Articles and landmark cases.
4. **🏗️ RAG Architecture & Methodology**: System architecture overview and technical specifications.
5. **📊 Empirical Research Dashboard**:
   - Information Retrieval comparison charts (Hit@K, NDCG@10 vs. latency) and query-level audit log browser.
   - Intent classification model comparison, 5-fold CV results, and interactive confusion matrices.
   - NLP component breakdown (NER per-category F1, Entity Linking, Query Expansion).
   - RAG citation grounding and evidence coverage audit.
   - Benchmark integrity manifest and reproducibility hyperparameters.

---

## 8. Quickstart & Local Setup Guide

### 8.1 Prerequisites
Python 3.10+ on Windows, Linux, or macOS.

### 8.2 Environment Setup

**Windows PowerShell:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 8.3 Launching the Application
```powershell
streamlit run app.py
```
Open your browser to `http://localhost:8501`.

*(Optional: Set `GEMINI_API_KEY` in `.env` or input it via the sidebar. If omitted, the application operates 100% offline using the built-in Heuristic Legal Synthesizer).*

### 8.4 Running the Automated Test Suite
```powershell
.\venv\Scripts\pytest -q
```

### 8.5 Reproducing Empirical Benchmarks
```powershell
python scripts/run_all_evaluations.py
```

---

## 9. Known Limitations & Future Research Directions

1. **Benchmark Scale**: The retrieval benchmark evaluates 200 verified queries across constitutional provisions and judgments, the intent classification suite evaluates 220 queries across 11 classes, and NER evaluates 105 annotated legal queries (211 gold entities). 5-fold cross-validation is reported to provide confidence intervals across class distributions.
2. **Entity Recognition on Abstract Concepts**: Rule-based regexes achieve high precision on structured categories (`ARTICLE`, `AMENDMENT`, `SECTION`, `DATE`), but abstract concepts (`LEGAL_CONCEPT`) show lower precision (0.2812) due to lexical boundary variance. Integrating domain-fine-tuned transformers (e.g., *InLegalBERT*) represents a valuable future extension.
3. **Structural vs. Semantic Citation Grounding**: The current validator confirms structural presence, valid document identifiers, and evidence provenance within retrieved passages. Natural language inference (NLI) for semantic claim entailment is an ongoing research direction.
4. **Legal Disclaimer**: This software is an academic NLP capstone project for educational and research purposes. It does not constitute formal legal advice.
