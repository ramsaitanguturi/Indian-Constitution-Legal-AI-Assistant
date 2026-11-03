# Utility and Ingestion Scripts: `13_SCRIPTS/scripts_explained.md`

[Back to Main Index](../README.md)

---

## 1. Overview of the `scripts/` Directory

The `scripts/` directory contains 26 operational, data processing, ingestion, and maintenance scripts. They are organized into four functional groups:

1. **Data Ingestion & Corpus Building Scripts** (Compiling articles, amendments, judgments, legislation, and manifests).
2. **Indexing & Embedding Caching Utilities** (ChromaDB index builder, BGE-M3 SQLite embedding cache).
3. **Benchmarking & Dataset Validation Utilities** (Gold benchmark creation, zero-leakage audits, corpus validation).
4. **Interactive Diagnostics & Regression Testing Tools** (Single-query pipeline tracer, priority query regression).

---

## 2. Master Functional Table of All 26 Scripts

| Script Name | Functional Group | Core Responsibility & Execution |
| :--- | :--- | :--- |
| `build_corpus.py` | Ingestion / Master | Orchestrates compilation of all 886 documents and generates `corpus_manifest.json`. |
| `ingest_constitution.py` | Ingestion | Parses Preamble, Articles 1–395+, and Schedules 1–12 into 477 structured records. |
| `ingest_amendments.py` | Ingestion | Structures all 106 Constitutional Amendment Acts (1951 to 2023) with Objects & Reasons. |
| `ingest_judgments.py` | Ingestion | Extracts 103 SCR PDFs via `pypdf`, 158 landmark briefs, and 25 parquet registry records. |
| `ingest_legislation.py` | Ingestion | Ingests 17 Central Acts (1,975 sections) from India Code (CrPC, IPC, IEA, CPC, RPA, etc.). |
| `ingest_data.py` | Ingestion / Legacy | Legacy ingestion script preserved for backward compatibility. |
| `update_corpus.py` | Maintenance | Incremental corpus updater for appending new statutes without rebuilding from scratch. |
| `download_sources.py` | Data Acquisition | Downloads official Supreme Court Reports (SCR) PDFs from AWS S3 Open Data archive. |
| `build_index.py` | Indexing / CLI | CLI utility to inspect (`--inspect`), verify, or safely rebuild (`--rebuild`) ChromaDB & BM25. |
| `cache_bgem3_embeddings.py` | Optimization | Pre-computes and caches BGE-M3 dense embeddings into `data/.cache/embeddings_cache.sqlite`. |
| `validate_corpus.py` | Quality Assurance | Validates JSON schemas and checks cryptographic SHA-256 hashes of all processed documents. |
| `validate_benchmark.py` | Quality Assurance | Verifies that all document IDs in `legal_queries_gold.json` actually exist in `parent_store.json`. |
| `audit_intent_leakage.py` | Verification | Mathematically asserts 0% data leakage between `intent_train.json` and `intent_test.json`. |
| `apply_canonical_retrieval_fixes.py` | Benchmarking | Applies canonical alias mappings to historical benchmark queries to eliminate ID mismatches. |
| `create_benchmark.py` | Benchmarking | Generates the initial 100 gold IR benchmark queries with graded relevance tags. |
| `build_full_benchmarks.py` | Benchmarking | Compiles multi-task benchmark partitions across IR, NER, intent, linking, and RAG. |
| `diagnose_query.py` | Diagnostics / CLI | Interactive debugging tool that runs a single query and prints a step-by-step 16-stage trace. |
| `evaluate_retrieval.py` | Evaluation | Standalone retrieval evaluation script measuring Hit@K, MRR, and NDCG. |
| `run_all_evaluations.py` | Evaluation | Shell orchestrator executing all benchmark evaluations in sequence. |
| `verify_queries.py` | Quality Assurance | Verifies that every query in the benchmark returns non-empty candidate lists. |
| `verify_unseen_queries.py` | Generalization | Evaluates generalization performance on a set of held-out real-world test queries. |
| `test_priority5_queries.py` | Regression | Regression test verifying that top 5 critical constitutional queries return accurate citations. |
| `capture_screenshots.py` | Documentation | Automated headless browser script (Playwright) capturing high-res Streamlit UI screenshots. |
| `corpus_data_articles.py` | Data Resource | Curated raw text dictionary of foundational constitutional provisions. |
| `corpus_data_amendments.py`| Data Resource | Curated legislative metadata and objects/reasons for all 106 constitutional amendments. |
| `corpus_data_judgments.py` | Data Resource | Curated analytical case briefs for landmark Supreme Court constitutional decisions. |

---

## 3. High-Value Scripts to Know for Your Demonstration

### 3.1 `diagnose_query.py`: The Ultimate Live Debugging Tool
During your viva presentation, your professor might ask: *"What happens under the hood when I type a specific query?"*
Instead of clicking around the UI, open a terminal and run:
```bash
python -m scripts.diagnose_query "Can police arrest without warrant under Article 21 and CrPC?"
```
**What it outputs:**
1. Language detected: `en`
2. Extracted Entities: `{"ARTICLE": ["Article 21"], "ACT": ["CrPC"]}`
3. Canonical Links: `art_21`, `act_crpc_1973`
4. Classified Intent: `CONSTITUTIONAL_PROCEDURE`
5. Strategy Selected: `PROCEDURE_SEARCH`
6. Top 5 Retrieved Passages with individual BM25, Dense, RRF, and Boost scores.
7. Parent Documents hydrated.
8. Generated Answer with NLI claim verification verdicts.

---

### 3.2 `audit_intent_leakage.py`: Proving Zero Data Leakage
Run this script to prove academic integrity to your examination committee:
```bash
python -m scripts.audit_intent_leakage
```
**Output:**
```text
=================================================================
INTENT DATASET ZERO-LEAKAGE INTEGRITY AUDIT
=================================================================
[*] Training queries count:   140
[*] Validation queries count: 30
[*] Test queries count:       30
[+] Train ∩ Test Overlap:     0 (PERFECT ZERO LEAKAGE)
[+] Train ∩ Val Overlap:      0 (PERFECT ZERO LEAKAGE)
[+] All 11 intent classes represented proportionally.
[+] Audit Status: PASSED (100% Contamination Free)
=================================================================
```

---

### 3.3 `build_index.py --inspect`: Live Database Health Audit
```bash
python -m scripts.build_index --inspect
```
Displays active collections, total indexed child chunks (7,470), parent documents (886), and active embedding models in under 1 second!

---

## 4. Viva Presentation & Defense Q&A

### Q1: What is the role of `scripts/diagnose_query.py`?
> **Student Answer**:
> *"It is our interactive diagnostic CLI tool. It takes any user query and prints a complete, terminal-based step-by-step execution trace across all 16 pipeline stages: showing the normalized query, detected entities, canonical IDs, intent classification, BM25 vs Dense candidate scores, RRF fusion math, parent hydration, and NLI verification. It provides 100% white-box observability into the system without needing a browser."*

### Q2: How did you verify that your training data didn't leak into your test benchmarks?
> **Student Answer**:
> *"We wrote an automated verification script: `scripts/audit_intent_leakage.py`. It computes the exact set intersection of token sequences between `intent_train.json` and `intent_test.json`. It confirms that the overlap is mathematically zero, proving that our classification Macro-F1 score of 0.8485 was achieved strictly on unseen out-of-sample data."*

