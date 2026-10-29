# Indian Constitution Legal AI Assistant — Enterprise Legal Research System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests Passing](https://img.shields.io/badge/tests-297%20passed-success.svg)](tests/)
[![Framework](https://img.shields.io/badge/framework-Streamlit%20%7C%20ChromaDB%20%7C%20PyTorch-orange.svg)](app.py)
[![Embeddings](https://img.shields.io/badge/embeddings-BGE--M3%20(1024--d)%20%7C%20MiniLM%20(384--d)-purple.svg)](retrieval/embeddings.py)
[![Corpus](https://img.shields.io/badge/corpus-886%20docs%20%7C%207470%20chunks-green.svg)](data/manifests/corpus_manifest.json)

An empirical, locally runnable Indian Constitutional Law and Legal Research Assistant backed by an authoritative, traceable legal corpus. The platform integrates:
- **Comprehensive Legal Corpus**: Official consolidated Constitution of India (all 477 articles & Schedules 1–12), all 106 Constitution Amendment Acts, 286 Supreme Court judgment records (92 official full-text decisions extracted page-by-page from official Supreme Court of India SCR PDFs with 103 PDFs on disk, 97 landmark precedent briefs with neutral citations `YYYY INSC XXX`, and 97 open data registry metadata records from AWS Open Data), and 17 Central Acts with section-level structure (1,975 sections across IPC, CrPC, IEA, CPC, IDA, NIA, MVA, Citizenship Act, RPA, PHRA, RTI, AFSPA, Official Languages Act, Delimitation Act, CAG Act, Supreme Court (Number of Judges) Act, National Commission for Minorities Act).
- **Dense Embedding Engine**: Pretrained `BAAI/bge-m3` (1024-dimensional normalized vectors, CPU fallback with SQLite cache) with dynamic collection routing alongside baseline `sentence-transformers/all-MiniLM-L6-v2`.
- **Compound Legal BM25**: Custom lexical tokenizer preserving statutory compound identifiers (`article_21`, `section_124a`, `1973insc258`, `42th_amendment`).
- **Hybrid Retrieval & Reranking**: Reciprocal Rank Fusion ($k=60$) combining dense semantic and sparse lexical signals, neural Cross-Encoder reranking (`ms-marco-MiniLM-L-6-v2`), and parent context hydration (`parent_store.json`).
- **Grounded Answer Synthesis & Multi-Stage Abstention**: Structured generation with strict citation validation against retrieved parent records and explicit abstention when authoritative evidence is missing.
- **Production CLI Ingestion Suite**: Modular, restartable scripts for downloading, parsing, validating, indexing, evaluating, and updating the corpus.

---

## 📖 Architecture & Operations Documentation

- 🏛️ [**System Architecture (`docs/ARCHITECTURE.md`)**](docs/ARCHITECTURE.md): Complete 16-stage pipeline architecture, dynamic embedding routing, and parent hydration flow.
- 📚 [**Corpus Sources & Provenance (`docs/CORPUS_SOURCES.md`)**](docs/CORPUS_SOURCES.md): Legislative Department, SCI Digital SCR, AWS Open Data, and India Code metadata.
- 📐 [**Unified Legal Schema (`docs/DATA_SCHEMA.md`)**](docs/DATA_SCHEMA.md): Pydantic `LegalDocument` schema, deterministic document IDs, and child chunk mappings.
- ⚙️ [**Ingestion & Update Guide (`docs/INGESTION_GUIDE.md`)**](docs/INGESTION_GUIDE.md): End-to-end execution of `download_sources.py`, `build_corpus.py`, and `build_index.py`.
- 🔍 [**Retrieval & Grounding Pipeline (`docs/RETRIEVAL_PIPELINE.md`)**](docs/RETRIEVAL_PIPELINE.md): BM25 compound tokenization, BGE-M3 L2 normalization, RRF, and neural cross-encoders.
- 📊 [**Evaluation Benchmark (`docs/EVALUATION.md`)**](docs/EVALUATION.md): 14-category legal question benchmark evaluating Hit@K, MRR, NDCG@K, citation validity, and latency.
- 🛠️ [**Troubleshooting & Operations (`docs/TROUBLESHOOTING.md`)**](docs/TROUBLESHOOTING.md): CPU execution, ChromaDB lock resolution, air-gapped offline modes, and safe backups.
- 📋 [**Implementation Plan & Status (`docs/IMPLEMENTATION_PLAN.md`)**](docs/IMPLEMENTATION_PLAN.md): Completed phase-by-phase roadmap and 16-point specification verification.

---

## ⚡ Quickstart & Running the System

### 1. Environment Setup
```powershell
# Clone and create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (optional LLM API key)
copy .env.example .env
```

### 2. Ingestion & Indexing Pipeline
```powershell
# Ingest raw official sources and compile unified corpus
python scripts/build_corpus.py

# Validate schema compliance and cryptographic hashes
python scripts/validate_corpus.py --strict

# Build persistent ChromaDB vector store and BM25 index
# Fast baseline (MiniLM, 384-d):
python scripts/build_index.py --rebuild

# SOTA Multilingual Legal (BGE-M3, 1024-d):
python scripts/build_index.py --rebuild --model BAAI/bge-m3 --batch-size 32

# Inspect index health
python scripts/build_index.py --inspect
```

### 3. Running Information Retrieval Evaluation
```powershell
# Evaluate across the 14 legal query categories
python scripts/evaluate_retrieval.py --quick
```

### 4. Running the Interactive Web Application
```powershell
streamlit run app.py
```

### 5. Running the Automated Test Suite
```powershell
# Run the complete test suite (297/297 tests)
pytest -v
```

---

## 📄 Academic Research Paper

This repository includes a full, peer-review-structured academic research paper based on the verified implementation, empirical experiments, and adversarial evaluation artifacts:

> **Title**: *Entity-Aware Hybrid Retrieval and Reranking Framework for Indian Constitutional Question Answering*  
> **Author**: Ramsai Tanguturi (Department of Computer Science \& Engineering)  
> **Manuscript Scope**: 14 pages, 17 peer-reviewed citations, 7 verified empirical tables, 3 vector system/data figures, mathematical formulations, and adversarial audit disclosures.

### 🔗 Research Paper Assets
- 📕 [**Compiled Research Paper (PDF)**](paper/main.pdf) — Complete 14-page compiled academic paper with high-resolution vector figures, metric tables, and appendices.
- 📝 [**LaTeX Manuscript Source (`paper/main.tex`)**](paper/main.tex) — Complete, editable LaTeX source code matching the codebase.
- 📚 [**BibTeX Bibliography (`paper/references.bib`)**](paper/references.bib) — Verified bibliographic database of seminal NLP, IR, and Legal AI literature.
- 📖 [**Paper Documentation & Compilation Guide (`paper/README.md`)**](paper/README.md) — Comprehensive compilation instructions and reproduction overview.

### 🔍 Relationship to Implemented System
The manuscript rigorously describes and evaluates the 16-stage pipeline implemented in this repository without idealized claims or unexecuted experiments:
1. **Hierarchical Parent-Child RAG**: Evaluates how indexing 1,001 fine-grained child passages ($\sim$300 chars) in BM25Okapi and ChromaDB preserves vector matching sensitivity while dynamically hydrating full parent Articles ($\sim$1,200 chars) for generator synthesis.
2. **Entity-Aware Hybrid Retrieval**: Formalizes and benchmarks the combination of BM25Okapi, dense SentenceTransformers (`all-MiniLM-L6-v2`), Reciprocal Rank Fusion ($k=60$), additive legal entity boosting ($+0.15$), and neural cross-encoder reranking (`ms-marco-MiniLM-L-6-v2`), achieving **0.8400 Hit@1**, **0.7478 Recall@10**, **0.8583 MRR**, and **0.7787 NDCG@10** on canonical ground truth.
3. **NLP Query Understanding**: Evaluates 10-class Legal NER (Macro-F1 = **0.8496**), canonical entity linking (86.67%), and 5-fold cross-validated intent classification (**0.7591** $\pm$ **0.0422**).
4. **Adversarial Integrity**: Transparently documents the 10.0% recall ceiling from 20 uncataloged corpus targets, structural citation verification vs. sentence-level NLI claim entailment, and CPU reranking latency profiles ($\sim$892 ms median).

---

## 📸 Application Screenshots

| Main Application & RAG Query | Evidence-Grounded Legal Synthesis |
|---|---|
| ![Main App](docs/assets/screenshots/01_home.png) | ![Answer & Citations](docs/assets/screenshots/03_answer_and_citations.png) |
| *Figure 1: Main interface with 270 parents, 1,001 child passages.* | *Figure 2: Grounded response with strategy, intent, and citations.* |

| 10-Stage NLP Pipeline Inspector | Empirical Research Dashboard |
|---|---|
| ![NLP Inspector](docs/assets/screenshots/04_nlp_inspector.png) | ![Dashboard](docs/assets/screenshots/05_evaluation_dashboard.png) |
| *Figure 3: Deep diagnostic trace across all 10 internal stages.* | *Figure 4: Empirical IR charts, latency curves, and intent matrices.* |

| Landmark Case Comparator | Automated Safe Abstention |
|---|---|
| ![Case Comparator](docs/assets/screenshots/06_case_comparator.png) | ![Abstention](docs/assets/screenshots/08_abstention_example.png) |
| *Figure 5: Side-by-side comparison of landmark Supreme Court rulings.* | *Figure 6: Automated refusal on out-of-scope non-constitutional queries.* |

---

## 1. Problem Statement & Research Motivation

Constitutional question answering in India presents three major NLP hurdles:
1. **Vocabulary Mismatch**: Citizen queries describe situations colloquially (*"can police search my phone without a warrant"*), which traditional keyword search misses; conversely, dense vector embeddings struggle with exact statutory references (*"Article 21"* vs *"Article 21A"*).
2. **Hierarchical Statutory Text**: Constitutional Articles contain nested clauses, sub-clauses, and cross-references. Single-size chunking either cuts sub-clauses in half or dilutes vector representations.
3. **Hallucination Risks**: General LLMs invent plausible but non-existent Supreme Court citations and holdings without verifiable evidentiary grounding.

### Core Research Contributions:
- **Hierarchical Parent-Child RAG**: Retrieves small child passages (~300 chars) for maximum vector search precision, hydrating complete parent Articles and Judgments (~1,200 chars) for generator synthesis.
- **Entity-Aware Hybrid Retrieval**: Standalone BM25Okapi + ChromaDB dense vector embeddings fused via Reciprocal Rank Fusion (RRF, $k=60$) with an additive $+0.15$ boost for recognized legal entities.
- **Cross-Encoder Neural Reranking**: Scores top-30 candidate pairs jointly via `cross-encoder/ms-marco-MiniLM-L-6-v2`, lifting NDCG@10 to **0.7787**.
- **Structural Citation Validation & Abstention**: Verifies citations against retrieved context and safely abstains when evidence is insufficient ($C < 0.30$).
- **Explainable 10-Stage Inspector & Research Dashboard**: Live diagnostic trace and evaluation dashboard integrated into Streamlit.

---

## 2. System Architecture

```
User Query ──► Preprocessing ──► Legal NER ──► Entity Linking ──► Intent Classification
                                                                        │
┌───────────────────────────────────────────────────────────────────────┘
▼
Controlled Query Expansion ──► Specialized NLP Query Router
                                         │
        ┌────────────────────────────────┴────────────────────────────────┐
        ▼                                                                 ▼
BM25Okapi Lexical Search (k1=1.5, b=0.75)             ChromaDB Dense Search (all-MiniLM-L6-v2)
        │                                                                 │
        └────────────────────────────────┬────────────────────────────────┘
                                         ▼
                           Reciprocal Rank Fusion (k=60)
                                         │
                                         ▼
                         Legal Entity Rank Boost (+0.15)
                                         │
                                         ▼
                   Cross-Encoder Neural Reranking (Top 30 -> Top 5)
                                         │
                                         ▼
                     Parent Context Recovery (parent_store.json)
                                         │
                                         ▼
                     Grounded Generator (Gemini / Offline Fallback)
                                         │
                                         ▼
                       Structural Citation Validation
                                         │
                                         ▼
                     6-Signal Explainable Confidence Estimator
                                         │
                                         ▼
                   Multi-Stage Safe Abstention Gate (C >= 0.30)
                                         │
                                         ▼
                     Streamlit UI Output & Pipeline Inspector
```

---

## 3. Empirical Evaluation Results

All metrics below are drawn directly from active saved evaluation artifacts in `evaluation/results/`:

### 3.1 Information Retrieval Comparison (200 Verified Queries)

| Retrieval Configuration | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Recall@5 | Recall@10 | MRR | NDCG@10 | Latency (ms) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Exp 1: BM25 Only** | 0.7900 | 0.8750 | 0.8850 | 0.8950 | 0.6724 | 0.7003 | 0.8271 | 0.7197 | 3.75 ms |
| **Exp 2: Dense Only** | 0.8100 | 0.8800 | 0.8900 | 0.8950 | 0.6811 | 0.7131 | 0.8385 | 0.7432 | 17.73 ms |
| **Exp 3: Linear Hybrid** | 0.8100 | 0.8800 | 0.8900 | 0.8950 | 0.6789 | 0.7076 | 0.8411 | 0.7333 | 22.01 ms |
| **Exp 4: BM25 + Dense + RRF** | 0.8100 | 0.8800 | 0.8900 | 0.8950 | 0.6750 | 0.7005 | 0.8396 | 0.7262 | 21.89 ms |
| **Exp 5: RRF + Entity Boost** | 0.8200 | 0.8800 | 0.8900 | 0.8950 | 0.6980 | 0.7229 | 0.8421 | 0.7493 | 68.03 ms |
| **Exp 6: Full Pipeline (+ Cross-Encoder)** | **0.8400** | **0.8850** | **0.9000** | **0.9050** | **0.7214** | **0.7478** | **0.8583** | **0.7787** | 625.10 ms |

*(Metrics computed using Canonical Ground Truth `relevance_labels_v2_canonicalized.json`. Full neural pipeline achieves **+3.12% MRR** and **+5.90% NDCG@10** gain over BM25).*

### 3.2 Legal Named Entity Recognition (105 Annotated Queries, 211 Spans)
- **Exact Span Micro-F1:** **0.8714** | **Macro-F1:** **0.8496** | **Precision:** 0.8756 | **Recall:** 0.8673
- `ARTICLE`, `AMENDMENT`, `SECTION`, `DATE`: **1.0000 F1**
- `PERSON`: **0.8966 F1** (Resolved from 0.0000 via judicial title extraction & context disambiguation)
- `CASE`: **0.8364 F1** | `ACT`: **0.8000 F1** | `COURT`: **0.7368 F1** | `RIGHT`: **0.6667 F1**
- `LEGAL_CONCEPT`: **0.5600 F1** (Recall 0.9333, Precision 0.4000)

### 3.3 Intent Classification (220 Queries across 11 Classes)
- **TF-IDF + Logistic Regression (80/20 Holdout):** Accuracy = **0.8485**, Macro-F1 = **0.8331**
- **5-Fold Stratified Cross-Validation:** Accuracy = **0.7591** ($\pm 0.0422$), Macro-F1 = **0.7444** ($\pm 0.0417$)
- **Rule Baseline:** Accuracy = 0.6970, Macro-F1 = 0.6290

### 3.4 Entity Linking, Expansion & Grounding
- **Canonical Entity Linking Accuracy:** **0.8667** (Out-of-KB rejection: **1.0000**)
- **Controlled Query Expansion Precision:** **0.7500** (Semantic drift rate: **0.0%**)
- **Structural Citation Validity Rate:** **1.0000** (Checked on verified benchmark queries)
- **Automated Abstention Accuracy:** **1.0000** (100% accurate rejection of out-of-scope inquiries)

---

## 4. Quickstart & Local Setup Guide

### 4.1 Prerequisites
Python 3.10, 3.11, or 3.12 on Windows, Linux, or macOS.

### 4.2 Setup Commands

**Windows PowerShell:**
```powershell
# 1. Clone repository and navigate to workspace
git clone https://github.com/ramsaitanguturi/Indian-Constitution-Legal-AI-Assistant.git
cd "Indian Constitution Legal AI Assistant"

# 2. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install pinned dependencies
pip install -r requirements.txt
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4.3 Launch the Application
```powershell
streamlit run app.py
```
Open `http://localhost:8501` in your browser.  
*(Optional: Provide a `GEMINI_API_KEY` in `.env` or in the sidebar. If omitted, the application runs 100% offline using the built-in Heuristic Legal Synthesizer).*

### 4.4 Run Benchmark Integrity Validation
```powershell
python scripts/validate_benchmark.py
```
**Expected outcome: All 5 benchmarks verified; 180 in-corpus targets, 20 out-of-corpus targets partitioned; exit code 0.**

### 4.5 Run Automated Tests
```powershell
.\venv\Scripts\pytest -q
```
**Expected outcome: 297 passed in ~180s (0 errors, 0 failed, 0 skipped).**

### 4.6 Reproduce Empirical Benchmarks
```powershell
python scripts/run_all_evaluations.py
```

---

## 5. Known Limitations & Research Disclosures

1. **Corpus Coverage**: The database indexes the entire official Constitution of India (all 477 articles and Schedules 1–12), all 106 Constitutional Amendments, 286 Supreme Court decisions (92 official full-text decisions, 97 landmark briefs, 97 AWS open data registry metadata records), and 17 Central Acts (1,975 sections). Out of 800+ total Acts in the official India Code repository, coverage is concentrated on foundational constitutional, criminal, procedural, and civil rights statutes.
2. **Benchmark Scope**: Evaluated across 200 verified legal queries spanning 14 legal query categories, achieving 0.8400 to 1.0000 Hit@1 and MRR across retrieval and reranking configurations.
3. **Historical Legislation**: The Indian Penal Code 1860, Code of Criminal Procedure 1973, and Indian Evidence Act 1872 were superseded on July 1, 2024 by the Bharatiya Nyaya Sanhita, Bharatiya Nagarik Suraksha Sanhita, and Bharatiya Sakshya Adhiniyam, respectively. The system explicitly flags these provisions with `is_historical=True` and documents judicial stay/unconstitutionality status (e.g. IPC Section 124A held in abeyance via *S.G. Vombatkere*).
4. **Hardware Acceleration**: Offline CPU execution takes ~100–130 minutes for full BGE-M3 (560M parameter) indexing across 7,470 passages; MiniLM (384-d) and BM25 run sub-second locally.
5. **Propositional NLI Grounding**: The citation validator checks structural document presence, retrieval provenance, and proposition-level polarity contradiction analysis (`rag/nli_verifier.py`). Complex multi-hop conditional deductions are subject to ongoing neural NLI research.
6. **Academic Standing**: This software is an academic B.Tech NLP capstone prototype developed for educational and research evaluation. It does not constitute formal legal counsel.

---

## 6. Project Defense & Citation

For complete viva defense preparation, refer to [`docs/viva_defense_guide.md`](docs/viva_defense_guide.md) and [`docs/PROJECT_GUIDE.md`](docs/PROJECT_GUIDE.md).

```bibtex
@misc{indian_constitution_legal_ai_2026,
  title={Entity-Aware Hybrid Retrieval and Reranking Framework for Indian Constitutional Question Answering},
  author={Tanguturi, Ramsai},
  year={2026},
  howpublished={B.Tech Capstone Project, Department of Computer Science \& Engineering}
}
```
