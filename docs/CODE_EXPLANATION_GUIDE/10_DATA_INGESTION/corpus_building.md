# Master Corpus Compilation & Manifest: `scripts/build_corpus.py`

[Back to Ingestion Overview](README.md) • [Back to Main Index](../README.md)

---

## 1. Basic Introduction

### What is this file?
`scripts/build_corpus.py` is the **Master Corpus Compilation and Validation Script**. It orchestrates the ingestion of all four legal data categories (Articles, Amendments, Judgments, and Central Acts), validates each record against strict schema rules, and generates a comprehensive cryptographic audit manifest (`data/processed/corpus_manifest.json`).

### Why is this file needed?
In production AI research, data reproducibility and auditability are mandatory:
- How do we prove that none of the 886 documents were corrupted during ingestion?
- How do we verify that every document contains mandatory metadata (provenance URL, SHA-256 hash, non-empty legal text)?
- How do we provide a smoke-test partition for fast continuous integration (CI) testing without parsing 5.8 million characters?

`scripts/build_corpus.py` solves all of these requirements by providing a centralized command-line interface with automated schema assertions and manifest generation.

---

## 2. Imports and Dependencies

```python
# scripts/build_corpus.py L10-L42
import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any

from config import (
    CONSTITUTION_ARTICLES_PATH,
    CONSTITUTION_AMENDMENTS_PATH,
    JUDGMENTS_LANDMARKS_PATH,
    LEGISLATION_ACTS_PATH,
    CORPUS_MANIFEST_PATH,
    # ... directory paths
)
from scripts.ingest_constitution import ingest_constitution
from scripts.ingest_amendments import build_amendments_dataset
from scripts.ingest_judgments import ingest_judgments
from scripts.ingest_legislation import ingest_legislation
from rag.schema import LegalDocument
```

---

## 3. Core Functions in `scripts/build_corpus.py`

### 3.1 `validate_document_records(docs: List[Dict], expected_type: str) -> None`

```python
# Lines 44-55
def validate_document_records(docs: List[Dict[str, Any]], expected_type: str) -> None:
    """Validate that every document complies with LegalDocument schema without missing keys."""
    for idx, doc in enumerate(docs):
        assert "document_id" in doc, f"Missing document_id in document {idx} of {expected_type}"
        assert "document_type" in doc, f"Missing document_type in {doc.get('document_id')}"
        assert doc["document_type"] == expected_type, (
            f"Type mismatch: expected {expected_type}, got {doc['document_type']} in {doc.get('document_id')}"
        )
        assert "text" in doc and doc["text"].strip(), f"Empty legal text in {doc.get('document_id')}"
        assert "source_url" in doc, f"Missing source_url in {doc.get('document_id')}"
        assert "source_hash" in doc, f"Missing source_hash in {doc.get('document_id')}"
```
- **Why fail-fast assertions are used**: If any scraping or parsing script introduces an empty text string or forgets the source URL, `assert` immediately halts execution, preventing corrupt records from contaminating the vector database.

---

### 3.2 `build_corpus(smoke_test: bool = False) -> Dict[str, Any]`

#### Step-by-Step Execution:
1. **Directory Preparation (Lines 65-70)**: Ensures all 8 target directories exist using `mkdir(parents=True, exist_ok=True)`.
2. **Stage 1: Constitution & Schedules (Lines 73-80)**: Calls `ingest_constitution()`, validates records, and writes to `constitution_articles.json`. (Slices to 25 items if `--smoke-test`).
3. **Stage 2: Amendments 1 to 106 (Lines 83-90)**: Calls `build_amendments_dataset()`, validates records, and writes to `constitution_amendments.json`. (Slices to 10 items if `--smoke-test`).
4. **Stage 3: Supreme Court Decisions (Lines 93-100)**: Calls `ingest_judgments()`, validates records, and writes to `supreme_court_judgments.json`. (Slices to 15 items if `--smoke-test`).
5. **Stage 4: Central Legislation (Lines 103-110)**: Calls `ingest_legislation()`, validates records, and writes to `constitutional_legislation.json`. (Slices to 2 acts if `--smoke-test`).
6. **Stage 5: Cryptographic Audit Manifest Generation (Lines 112-184)**:
   - Sums total character counts and estimates token counts ($\approx \text{chars} / 4$).
   - Computes document-level granularity (full-text vs summary judgments, statutory section counts).
   - Records official government source citations, licensing, and amendment version.
   - Saves final JSON manifest to `data/processed/corpus_manifest.json`.

---

## 4. Manifest Structure: `corpus_manifest.json`

```json
{
  "manifest_version": "2.1.0-production",
  "generated_at": "2024-01-01T00:00:00Z",
  "is_smoke_test": false,
  "counts_by_document_type": {
    "constitution_article": 477,
    "constitution_amendment": 106,
    "judgment": 286,
    "statute": 17
  },
  "judgment_granularity": {
    "official_full_text": 103,
    "structured_summary_briefs": 158,
    "registry_metadata_only": 25
  },
  "statute_granularity": {
    "total_acts": 17,
    "total_sections_parsed": 1975
  },
  "total_documents": 886,
  "total_character_count": 5824190,
  "estimated_total_tokens": 1456048
}
```

---

## 5. CLI Execution & Flags

```bash
# Full production corpus build (all 886 documents)
python -m scripts.build_corpus

# Fast smoke-test partition (for quick validation & testing)
python -m scripts.build_corpus --smoke-test
```

---

## 6. Viva Presentation & Defense Q&A

### Q1: What is the purpose of `build_corpus.py`?
> **Student Answer**:
> *"It is the single entry point for our data pipeline. It coordinates the ingestion of constitutional articles, 106 amendments, 286 Supreme Court judgments, and 17 Central Acts. Before writing any data to disk, it executes strict schema assertions to ensure non-empty text, valid types, and source provenance. Finally, it generates `corpus_manifest.json`, an audit file recording exact document counts, character sizes, and cryptographic SHA-256 integrity details."*

### Q2: Why is the `--smoke-test` flag useful?
> **Student Answer**:
> *"A full corpus build parses 5.8 million characters, including dozens of full-text Supreme Court PDFs. On a standard laptop, parsing everything takes several minutes. The `--smoke-test` flag builds a small representative partition (25 articles, 10 amendments, 15 judgments, 2 acts) in under 5 seconds. This allows developers and examiners to verify that the end-to-end ingestion pipeline runs without errors before committing to a full build."*

