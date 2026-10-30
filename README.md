# Indian Constitution Legal AI Assistant — Enterprise Legal Research System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests Passing](https://img.shields.io/badge/tests-319%20passed-success.svg)](tests/)
[![Framework](https://img.shields.io/badge/framework-Streamlit%20%7C%20ChromaDB%20%7C%20PyTorch-orange.svg)](app.py)
[![Embeddings](https://img.shields.io/badge/embeddings-BGE--M3%20(1024--d)%20%7C%20MiniLM%20(384--d)-purple.svg)](retrieval/embeddings.py)
[![Corpus](https://img.shields.io/badge/corpus-886%20docs%20%7C%207470%20chunks-green.svg)](data/manifests/corpus_manifest.json)

An empirical, locally runnable Indian Constitutional Law and Legal Research Assistant backed by an authoritative, traceable legal corpus. The platform integrates:
- **Comprehensive Legal Corpus**: Official consolidated Constitution of India (all 477 articles & Schedules 1–12), all 106 Constitution Amendment Acts, 286 Supreme Court judgment records (92 official full-text decisions extracted page-by-page from official Supreme Court of India SCR PDFs with 103 PDFs on disk, 97 landmark precedent briefs with neutral citations `YYYY INSC XXX`, and 97 open data registry metadata records from AWS Open Data), and 17 Central Acts with section-level structure (1,975 sections across IPC, CrPC, IEA, CPC, IDA, NIA, MVA, Citizenship Act, RPA, PHRA, RTI, AFSPA, Official Languages Act, Delimitation Act, CAG Act, Supreme Court (Number of Judges) Act, National Commission for Minorities Act).
- **Dense Embedding Engine**: Pretrained `BAAI/bge-m3` (1024-dimensional normalized vectors, CPU fallback with SQLite cache) with dynamic collection routing alongside baseline `sentence-transformers/all-MiniLM-L6-v2` (384-d). Includes runtime dimension mismatch validation to protect collection integrity.
- **Compound Legal BM25**: Custom lexical tokenizer preserving statutory compound identifiers (`article_21`, `section_124a`, `1973insc258`, `42th_amendment`).
- **Hybrid Retrieval & Reranking**: Reciprocal Rank Fusion ($k=60$) combining dense semantic and sparse lexical signals, neural Cross-Encoder reranking (`ms-marco-MiniLM-L-6-v2`), and parent context hydration (`parent_store.json`).
- **Grounded Answer Synthesis & Multi-Stage Abstention**: Structured generation with strict citation validation against retrieved parent records, atomic Natural Language Inference (NLI) polarity checking, and explicit abstention when authoritative evidence is missing.
- **Minimal High-Density Web Interface**: Streamlit UI (`app.py`) providing structured extraction of Direct Answers, Relevant Legal Provisions, Relevant Judgments, Important Exceptions, and Verified Citations with full expandable source texts and a 10-stage diagnostic inspection audit.
- **Production CLI Ingestion Suite**: Modular, restartable scripts for downloading, parsing, validating, indexing, evaluating, and updating the corpus.

---

## 🎯 Demonstration & Evaluation Guide

> [!IMPORTANT]
> For faculty review committees, examiners, and project evaluators: A dedicated, beginner-friendly live demonstration walkthrough, viva defense preparation guide, and code explanation is provided in:
>
> 📖 [**`DEMONSTRATION_GUIDE.md`**](DEMONSTRATION_GUIDE.md)

---

## 📖 Architecture & Operations Documentation

- 🏛️ [**System Architecture (`docs/architecture.md`)**](docs/architecture.md): Complete 16-stage pipeline architecture, dynamic embedding routing, and parent hydration flow.
- 📚 [**Corpus Sources & Provenance (`docs/CORPUS_SOURCES.md`)**](docs/CORPUS_SOURCES.md): Legislative Department, SCI Digital SCR, AWS Open Data, and India Code metadata.
- 📐 [**Unified Legal Schema (`docs/DATA_SCHEMA.md`)**](docs/DATA_SCHEMA.md): Pydantic `LegalDocument` schema, deterministic document IDs, and child chunk mappings.
- ⚙️ [**Ingestion & Update Guide (`docs/INGESTION_GUIDE.md`)**](docs/INGESTION_GUIDE.md): End-to-end execution of `download_sources.py`, `build_corpus.py`, and `build_index.py`.
- 🔍 [**Retrieval & Grounding Pipeline (`docs/RETRIEVAL_PIPELINE.md`)**](docs/RETRIEVAL_PIPELINE.md): BM25 compound tokenization, BGE-M3 L2 normalization, RRF, and neural cross-encoders.
- 📊 [**Evaluation Benchmark (`docs/evaluation.md`)**](docs/evaluation.md): 14-category legal question benchmark evaluating Hit@K, MRR, NDCG@K, citation validity, and latency.
- 🛠️ [**Troubleshooting & Operations (`docs/TROUBLESHOOTING.md`)**](docs/TROUBLESHOOTING.md): CPU execution, ChromaDB lock resolution, air-gapped offline modes, and safe backups.
- 📋 [**Implementation Plan & Status (`docs/IMPLEMENTATION_PLAN.md`)**](docs/IMPLEMENTATION_PLAN.md): Completed phase-by-phase roadmap and specification verification.
- 🎓 [**Viva Defense Guide (`docs/viva_defense_guide.md`)**](docs/viva_defense_guide.md): 60-second elevator pitch, slide outline, examiner Q&A, and live demo script.

---

## 📸 Application Screenshots

Genuine interface screenshots captured from the running application:

| Main Application & RAG Query | Evidence-Grounded Legal Synthesis |
|---|---|
| ![Main App](docs/assets/screenshots/01_home.png) | ![Answer & Citations](docs/assets/screenshots/03_answer_and_citations.png) |
| *Figure 1: Main interface with research settings sidebar, dark legal theme, and question input.* | *Figure 2: Grounded response with Direct Answer, provisions, ratio decidendi, and citations.* |

| 10-Stage NLP Pipeline Inspector | Empirical Research Dashboard |
|---|---|
| ![NLP Inspector](docs/assets/screenshots/04_nlp_inspector.png) | ![Dashboard](docs/assets/screenshots/05_evaluation_dashboard.png) |
| *Figure 3: Deep diagnostic trace across all internal stages (NER, linking, RRF, reranker).* | *Figure 4: Empirical IR charts, latency curves, and intent confusion matrices.* |

| Landmark Case Comparator | Automated Safe Abstention |
|---|---|
| ![Case Comparator](docs/assets/screenshots/06_case_comparator.png) | ![Abstention](docs/assets/screenshots/08_abstention_example.png) |
| *Figure 5: Side-by-side comparative analysis of landmark Supreme Court rulings.* | *Figure 6: Automated refusal on out-of-scope non-constitutional / commercial queries.* |

| Question Input & Autocomplete | Constitution & Cases Database Explorer |
|---|---|
| ![Question Input](docs/assets/screenshots/02_question_input.png) | ![Database Explorer](docs/assets/screenshots/07_database_explorer.png) |
| *Figure 7: Example constitutional question input.* | *Figure 8: Filterable statutory provision and judicial case database explorer.* |

---

## 1. Problem Statement & Objectives

### 1.1 The Problem
Constitutional question answering in India presents three major NLP challenges:
1. **Vocabulary Mismatch**: Citizen queries describe situations colloquially (*"can police search my phone without a warrant"*), which traditional keyword search misses; conversely, dense vector embeddings struggle with exact statutory references (*"Article 21"* vs *"Article 21A"*).
2. **Hierarchical Statutory Text**: Constitutional Articles contain nested clauses, sub-clauses, and cross-references. Single-size chunking either cuts sub-clauses in half or dilutes vector representations.
3. **Hallucination Risks**: General LLMs invent plausible but non-existent Supreme Court citations and holdings without verifiable evidentiary grounding.

### 1.2 Project Objectives
- Build an authoritative, unified corpus of Indian Constitutional law, amendments, Supreme Court decisions, and core statutory legislation with cryptographic provenance tracking.
- Implement an Entity-Aware Hybrid Retrieval system fusing lexical BM25 and dense semantic representations via Reciprocal Rank Fusion ($k=60$), entity boosting, and neural Cross-Encoder reranking.
- Prevent legal hallucinations via hierarchical Parent-Child context recovery, structural citation validation, claim-level NLI contradiction detection, and multi-stage automated abstention.
- Deliver an offline-capable, locally runnable Streamlit application backed by empirical evaluation and a 100% passing automated test suite (319/319 tests).

---

## 2. Main Features Currently Implemented

| Subsystem | Implemented Capabilities | Status |
|---|---|:---:|
| **Official Corpus** | 886 documents: 477 Articles & Schedules 1–12, 106 Amendment Acts, 286 Judgments (92 official full-text SCR PDF, 97 landmark briefs, 97 AWS registry records), 17 Central Acts (1,975 sections). | **COMPLETED** |
| **NLP Query Understanding** | Language detection (EN/HI), legal text normalization, 10-class Legal NER (Macro-F1 0.8496), canonical entity linking (86.67%), TF-IDF + Logistic Regression intent classifier (84.85%), and controlled synonym expansion. | **COMPLETED** |
| **Hybrid Retrieval** | BM25Okapi with compound statutory tokenization + Dense vector retrieval (`BAAI/bge-m3` 1024-d / `all-MiniLM-L6-v2` 384-d) with collection dimension protection. | **COMPLETED** |
| **Rank Fusion & Reranking** | Reciprocal Rank Fusion ($k=60$) + Additive Entity Boost ($+0.15$) + Neural Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) reranking top 30 to top 5. | **COMPLETED** |
| **Reliability & Grounding** | Parent-child hydration (`parent_store.json`), Grounded legal synthesis (Gemini API / Offline deterministic fallback), Structural citation validator, Claim-level NLI polarity verifier, and 6-signal confidence abstention gate. | **COMPLETED** |
| **User Interface** | Sleek, dark-themed Streamlit UI (`app.py`) with Direct Answer card, Provisions, Judgments, Exceptions, Verified Sources with excerpts, and Technical Verification Audit. | **COMPLETED** |
| **Automated Testing** | 319 unit, integration, regression, and smoke tests in pytest with 100% pass rate. | **COMPLETED** |

---

## 3. Technology Stack

- **Application Framework**: Streamlit ($\ge 1.30.0$)
- **Vector Database**: ChromaDB ($\ge 0.4.22$) with SQLite persistent storage
- **Sparse Information Retrieval**: `rank-bm25` (BM25Okapi, $k_1=1.5, b=0.75$)
- **Dense Embedding Models**: `BAAI/bge-m3` (1024-d) & `sentence-transformers/all-MiniLM-L6-v2` (384-d)
- **Neural Reranker**: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- **Machine Learning**: `scikit-learn` ($\ge 1.4.0$) for TF-IDF vectorization and Logistic Regression intent classification
- **Data Engineering**: Pandas ($\ge 2.0.0$), NumPy ($\ge 1.24.0$), Pydantic ($\ge 2.0.0$)
- **Generative AI & LLM**: Google Gemini API (`gemini-3.8-flash` via `google-generativeai` & `langchain-google-genai`) with offline deterministic fallback
- **Testing & Verification**: Pytest ($\ge 8.0.0$)

---

## 4. System Architecture & Workflow

```text
User Query ──► Preprocessing ──► Legal NER ──► Entity Linking ──► Intent Classification
                                                                        │
┌───────────────────────────────────────────────────────────────────────┘
▼
Controlled Query Expansion ──► Specialized NLP Query Router
                                         │
        ┌────────────────────────────────┴────────────────────────────────┐
        ▼                                                                 ▼
BM25Okapi Lexical Search (k1=1.5, b=0.75)             ChromaDB Dense Search (BGE-M3 / MiniLM)
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
                        Claim-Level NLI Polarity Verification
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

## 5. Repository Directory Structure

```text
Indian Constitution Legal AI Assistant/
├── .env.example                     # Environment variables template (API keys, models)
├── .gitignore                       # Git ignore definitions
├── app.py                           # Minimal, high-density Streamlit web application
├── config.py                        # Centralized configuration, paths, model settings
├── ingestion.py                     # Baseline parent-child ingestion & tokenizer facade
├── retriever.py                     # Baseline hybrid retriever & regex NER facade
├── agents.py                        # Multi-agent router & heuristic synthesizer facade
├── parent_store.json                # Hydrated parent document store
├── requirements.txt                 # Pinned dependencies
├── README.md                        # Primary project documentation
├── DEMONSTRATION_GUIDE.md           # Step-by-step viva & live demonstration guide
├── data/
│   ├── constitution/                # Canonical articles and amendments
│   ├── judgments/                   # Supreme Court landmark decisions
│   ├── benchmark/                   # 5 benchmark suites (retrieval, intent, NER, RAG)
│   ├── annotations/                 # Ground-truth relevance and NER span annotations
│   ├── manifests/                   # corpus_manifest.json & raw_downloads_manifest.json
│   ├── reports/                     # Validation reports
│   ├── raw/                         # Raw downloads (PDFs, JSONs, Parquet)
│   └── processed/                   # Consolidated and normalized JSON files
├── docs/                            # Deep-dive architecture and audit documentation
│   ├── assets/screenshots/          # Genuine application interface screenshots
│   ├── architecture.md              # System architecture specification
│   ├── CORPUS_SOURCES.md            # Official source provenance and URLs
│   ├── DATA_SCHEMA.md               # LegalDocument Pydantic schema
│   ├── INGESTION_GUIDE.md           # Pipeline execution and rebuild runbook
│   ├── RETRIEVAL_PIPELINE.md        # Mathematical details of BM25, RRF, Reranking
│   ├── evaluation.md                # Evaluation framework and metrics
│   ├── experiments.md               # Full empirical experiments log (Exp 1 to Exp 8)
│   ├── LIMITATIONS.md               # Honest limitations and boundaries
│   ├── TROUBLESHOOTING.md           # Operational troubleshooting guide
│   └── viva_defense_guide.md        # Comprehensive viva defense questions & answers
├── evaluation/                      # Stage 5 evaluation framework
│   ├── benchmark_runner.py          # Master evaluation runner
│   ├── metrics.py                   # IR metrics: Hit@K, Recall@K, MRR, NDCG@K
│   ├── retrieval_eval.py            # Retrieval ablation evaluator
│   ├── ner_eval.py                  # NER exact-span evaluator
│   ├── intent_eval.py               # Intent classifier evaluator
│   ├── dashboard_view.py            # Streamlit empirical evaluation dashboard
│   └── results/                     # Saved CSV/JSON evaluation artifacts
├── experiments/                     # Individual experiment scripts (Exp 01 to Exp 08)
├── nlp/                             # NLP Query Understanding Subsystem
│   ├── preprocessing.py             # Normalization and compound tokens
│   ├── language_detection.py        # English/Hindi detection
│   ├── legal_ner.py                 # 10-class Legal NER engine
│   ├── entity_linking.py            # Canonical KB entity linker
│   ├── intent_classifier.py         # TF-IDF + Logistic Regression
│   └── query_expansion.py           # Controlled synonym expansion
├── rag/                             # RAG Generation, Grounding & Reliability
│   ├── pipeline.py                  # Master LegalRAGPipeline orchestrator
│   ├── parent_child.py              # Parent context hydration
│   ├── generator.py                 # Grounded generator with offline fallback
│   ├── citation_validator.py        # Structural citation validation
│   ├── nli_verifier.py              # Claim-level polarity & conflict verifier
│   ├── confidence.py                # 6-signal confidence estimator
│   ├── abstention.py                # Multi-stage abstention gate
│   └── ui_formatter.py              # Presentation-ready answer formatting
├── retrieval/                       # Information Retrieval Subsystem
│   ├── bm25_retriever.py            # Lexical BM25Okapi search
│   ├── dense_retriever.py           # ChromaDB dense vector search
│   ├── embeddings.py                # BGE-M3 / MiniLM embedding engine
│   ├── rrf.py                       # Reciprocal Rank Fusion ($k=60$)
│   ├── entity_boost.py              # Additive entity score boost ($+0.15$)
│   ├── reranker.py                  # Neural Cross-Encoder reranker
│   └── hybrid_retriever.py          # Unified hybrid retrieval coordinator
├── routing/                         # Query routing subsystem
├── scripts/                         # CLI execution and ingestion scripts
└── tests/                           # 319 passing automated tests
```

---

## 6. Empirical Evaluation Results

All metrics below are drawn directly from active saved evaluation artifacts in `evaluation/results/`:

### 6.1 Information Retrieval Comparison (200 Verified Queries)

| Retrieval Configuration | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Recall@5 | Recall@10 | MRR | NDCG@10 | Latency (ms) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Exp 1: BM25 Only** | 0.7900 | 0.8750 | 0.8850 | 0.8950 | 0.6724 | 0.7003 | 0.8271 | 0.7197 | 3.75 ms |
| **Exp 2: Dense Only** | 0.8100 | 0.8800 | 0.8900 | 0.8950 | 0.6811 | 0.7131 | 0.8385 | 0.7432 | 17.73 ms |
| **Exp 3: Linear Hybrid** | 0.8100 | 0.8800 | 0.8900 | 0.8950 | 0.6789 | 0.7076 | 0.8411 | 0.7333 | 22.01 ms |
| **Exp 4: BM25 + Dense + RRF** | 0.8100 | 0.8800 | 0.8900 | 0.8950 | 0.6750 | 0.7005 | 0.8396 | 0.7262 | 21.89 ms |
| **Exp 5: RRF + Entity Boost** | 0.8200 | 0.8800 | 0.8900 | 0.8950 | 0.6980 | 0.7229 | 0.8421 | 0.7493 | 68.03 ms |
| **Exp 6: Full Pipeline (+ Cross-Encoder)** | **0.8400** | **0.8850** | **0.9000** | **0.9050** | **0.7214** | **0.7478** | **0.8583** | **0.7787** | 625.10 ms |

*(Metrics computed using Canonical Ground Truth `relevance_labels_v2_canonicalized.json`. Full neural pipeline achieves **+3.12% MRR** and **+5.90% NDCG@10** gain over BM25).*

### 6.2 Legal Named Entity Recognition (105 Annotated Queries, 211 Spans)
- **Exact Span Micro-F1:** **0.8714** | **Macro-F1:** **0.8496** | **Precision:** 0.8756 | **Recall:** 0.8673
- `ARTICLE`, `AMENDMENT`, `SECTION`, `DATE`: **1.0000 F1**
- `PERSON`: **0.8966 F1** (Resolved from 0.0000 via judicial title extraction & context disambiguation)
- `CASE`: **0.8364 F1** | `ACT`: **0.8000 F1** | `COURT`: **0.7368 F1** | `RIGHT`: **0.6667 F1**
- `LEGAL_CONCEPT`: **0.5600 F1** (Recall 0.9333, Precision 0.4000)

### 6.3 Intent Classification (220 Queries across 11 Classes)
- **TF-IDF + Logistic Regression (80/20 Holdout):** Accuracy = **0.8485**, Macro-F1 = **0.8331**
- **5-Fold Stratified Cross-Validation:** Accuracy = **0.7591** ($\pm 0.0422$), Macro-F1 = **0.7444** ($\pm 0.0417$)
- **Rule Baseline:** Accuracy = 0.6970, Macro-F1 = 0.6290

### 6.4 Entity Linking, Expansion & Grounding
- **Canonical Entity Linking Accuracy:** **0.8667** (Out-of-KB rejection: **1.0000**)
- **Controlled Query Expansion Precision:** **0.7500** (Semantic drift rate: **0.0%**)
- **Structural Citation Validity Rate:** **1.0000** (Checked on verified benchmark queries)
- **Automated Abstention Accuracy:** **1.0000** (100% accurate rejection of out-of-scope inquiries)

---

## 7. Quickstart & Local Setup Guide

### 7.1 Prerequisites
- Python 3.10, 3.11, or 3.12 on Windows, Linux, or macOS.
- 4 GB RAM minimum (8 GB recommended for BGE-M3 dense indexing).

### 7.2 Setup Commands

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

# 4. Configure environment variables (optional LLM API key)
copy .env.example .env
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 7.3 Launch the Interactive Web Application
```powershell
streamlit run app.py
```
Open `http://localhost:8501` in your browser.  
*(Optional: Provide a `GEMINI_API_KEY` in `.env` or in the sidebar. If omitted, the application runs 100% offline using the built-in Grounded Legal Engine).*

### 7.4 Run Automated Test Suite
```powershell
pytest -v
```
**Verified Outcome: 319 passed, 0 failed in ~213s.**

### 7.5 Run Benchmark Integrity Validation
```powershell
python scripts/validate_benchmark.py
```
**Expected outcome: All 5 benchmarks verified; 180 in-corpus targets, 20 out-of-corpus targets partitioned; exit code 0.**

### 7.6 Run Information Retrieval Evaluation
```powershell
# Quick evaluation (smoke mode)
python scripts/evaluate_retrieval.py --quick

# Full 200-query benchmark
python scripts/evaluate_retrieval.py
```

---

## 8. Known Limitations & Research Disclosures

1. **Corpus Coverage**: The database indexes the entire official Constitution of India (all 477 articles and Schedules 1–12), all 106 Constitutional Amendments, 286 Supreme Court decisions (92 official full-text decisions, 97 landmark briefs, 97 AWS open data registry metadata records), and 17 Central Acts (1,975 sections). Out of 800+ total Acts in the official India Code repository, coverage is concentrated on foundational constitutional, criminal, procedural, and civil rights statutes.
2. **Benchmark Scope**: Evaluated across 200 verified legal queries spanning 14 legal query categories, achieving 0.8400 to 1.0000 Hit@1 and MRR across retrieval and reranking configurations.
3. **Historical Legislation**: The Indian Penal Code 1860, Code of Criminal Procedure 1973, and Indian Evidence Act 1872 were superseded on July 1, 2024 by the Bharatiya Nyaya Sanhita, Bharatiya Nagarik Suraksha Sanhita, and Bharatiya Sakshya Adhiniyam, respectively. The system explicitly flags these provisions with `is_historical=True` and documents judicial stay/unconstitutionality status (e.g. IPC Section 124A held in abeyance via *S.G. Vombatkere*).
4. **Hardware Acceleration**: Offline CPU execution takes ~100–130 minutes for full BGE-M3 (560M parameter) indexing across 7,470 passages; MiniLM (384-d) and BM25 run sub-second locally.
5. **Propositional NLI Grounding**: The citation validator checks structural document presence, retrieval provenance, and proposition-level polarity contradiction analysis (`rag/nli_verifier.py`). Complex multi-hop conditional deductions are subject to ongoing neural NLI research.
6. **Academic Standing**: This software is an academic B.Tech NLP capstone prototype developed for educational and research evaluation. It does not constitute formal legal counsel.

---

## 9. Project Defense & Citation

For complete viva defense preparation, refer to [`DEMONSTRATION_GUIDE.md`](DEMONSTRATION_GUIDE.md), [`docs/viva_defense_guide.md`](docs/viva_defense_guide.md), and [`docs/PROJECT_GUIDE.md`](docs/PROJECT_GUIDE.md).

```bibtex
@misc{indian_constitution_legal_ai_2026,
  title={Entity-Aware Hybrid Retrieval and Reranking Framework for Indian Constitutional Question Answering},
  author={Tanguturi, Ramsai},
  year={2026},
  howpublished={B.Tech Capstone Project, Department of Computer Science \& Engineering}
}
```
