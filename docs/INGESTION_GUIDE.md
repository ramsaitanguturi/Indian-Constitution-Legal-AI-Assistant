# Data Ingestion & Corpus Operations Guide

This guide provides instructions for downloading, preprocessing, chunking, indexing, validating, and updating the legal corpus in the **Indian Constitution Legal AI Assistant**.

---

## 1. Directory Structure

```
data/
  raw/
    constitution/          # Official consolidated Constitution JSON / HTML
    amendments/            # Constitution Amendment Acts
    judgments/             # Supreme Court landmark judgments
    legislation/           # Statutory Central Acts (India Code)
  processed/
    constitution/          # Structured articles (articles_consolidated.json)
    amendments/            # Structured amendments (amendments_1_to_106.json)
    judgments/             # Structured landmark decisions (supreme_court_landmarks.json)
    legislation/           # Structured central statutes (central_acts.json)
    parent_store.json      # Primary parent document lookup store
  manifests/
    raw_downloads_manifest.json  # Checksums, URLs, and download status
    corpus_manifest.json         # Document counts, tokens, and build metadata
  reports/
    corpus_validation_report.json # Schema and integrity validation reports
    retrieval_evaluation_report.json # Information retrieval benchmark evaluation
```

---

## 2. Ingestion Pipeline Execution Order

Execute the pipeline in sequential order or run individual modules independently:

### Step 1: Download Raw Sources
Fetches source documents with exponential backoff and SHA-256 verification:
```powershell
.\venv\Scripts\python scripts/download_sources.py
```
Options:
- `--force`: Overwrite existing raw files even if checksums match.
- `--manifest-only`: Verify existing files and regenerate manifest without downloading.

### Step 2: Ingest Individual Corpora
Parse raw files into canonical structured schemas:
```powershell
# Constitutional Articles & Schedules (1–395+, Schedules 1–12)
.\venv\Scripts\python scripts/ingest_constitution.py

# Constitution Amendments (1st to 106th Amendment Acts)
.\venv\Scripts\python scripts/ingest_amendments.py

# Supreme Court Landmark Judgments
.\venv\Scripts\python scripts/ingest_judgments.py

# Statutory Central Acts
.\venv\Scripts\python scripts/ingest_legislation.py
```

### Step 3: Build Consolidated Corpus & Manifest
Consolidates all processed subsets into unified parent documents and generates the authoritative manifest:
```powershell
.\venv\Scripts\python scripts/build_corpus.py
```

### Step 4: Validate Corpus Integrity
Performs deep structural and schema validation across all documents:
```powershell
.\venv\Scripts\python scripts/validate_corpus.py --strict
```
Checks performed:
- All required fields populated (no hallucinated / mock fields).
- SHA-256 integrity checks against document content.
- Uniqueness and determinism of `document_id`.
- Part, Article, Clause, and Schedule structural hierarchy.

### Step 5: Build ChromaDB Vector Store & BM25 Index
Builds the vector store and BM25 index:
```powershell
# Fast baseline (MiniLM, 384-d)
.\venv\Scripts\python scripts/build_index.py --rebuild

# SOTA Multilingual Legal (BGE-M3, 1024-d)
.\venv\Scripts\python scripts/build_index.py --rebuild --model BAAI/bge-m3 --batch-size 32

# Inspect index health and chunk counts
.\venv\Scripts\python scripts/build_index.py --inspect
```

---

## 3. Freshness & Incremental Update Workflow

To maintain legal corpus currency without re-indexing unchanged documents:

```powershell
# Check remote sources for upstream amendments or new judgments
.\venv\Scripts\python scripts/update_corpus.py --check

# Backup current vector database and parent store before updates
.\venv\Scripts\python scripts/update_corpus.py --backup

# Execute complete incremental update and rebuild index
.\venv\Scripts\python scripts/update_corpus.py --full-update

# Rollback to the previous backup in case of upstream issues
.\venv\Scripts\python scripts/update_corpus.py --rollback backups/<backup_folder>
```

