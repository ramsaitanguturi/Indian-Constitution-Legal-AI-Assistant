# Complete Data Directory Walkthrough: `15_DATA_AND_DATABASE/data_directory_explained.md`

[Back to Main Index](../README.md)

---

## 1. Overview of the `data/` Directory

The `data/` directory is the central data store of the Indian Constitution Legal AI Assistant. It contains raw legal archives, standardized processed datasets, ground-truth evaluation benchmarks, cryptographic audit manifests, parent document caches, and the persistent vector database.

```
data/
├── raw/                      # Original, unedited source files
│   ├── constitution/         # Official Constitution of India raw text
│   ├── judgments/            # 103 Official Supreme Court Reports (SCR) PDFs (1950–1952)
│   └── legislation/          # 7 Central Codes JSON (IPC, CrPC, IEA, CPC, IDA, MVA, NIA)
│
├── processed/                # Schema-validated, consolidated datasets (886 documents)
│   ├── constitution/         # articles_consolidated.json (477 articles & schedules)
│   ├── amendments/           # amendments_1_to_106.json (106 Amendment Acts)
│   ├── judgments/            # supreme_court_landmarks.json (286 decisions)
│   └── legislation/          # central_acts.json (17 Central Acts / 1,975 sections)
│
├── benchmarks/               # Gold standard evaluation benchmarks
│   ├── legal_queries_gold.json   # 100 expert IR queries with graded relevance
│   ├── intent_train.json         # Zero-leakage intent training set (70%)
│   ├── intent_val.json           # Zero-leakage intent validation set (15%)
│   ├── intent_test.json          # Zero-leakage intent holdout test set (15%)
│   └── alias_map.json            # Canonical document ID alias dictionary
│
├── annotations/              # Fine-grained token & entity annotations
│   ├── legal_ner_gold.json       # Gold character spans for 10 entity types
│   └── entity_linking_gold.json  # Surface form to canonical entity ID mappings
│
├── manifests/                # Cryptographic audit & provenance records
│   ├── corpus_manifest.json      # Master SHA-256 manifest for all 886 documents
│   └── raw_downloads_manifest.json # Acquisition timestamps and official source URLs
│
├── parent_store.json         # Hydration cache containing all 886 full parent records
├── chroma_db/                # ChromaDB vector store (HNSW graph + SQLite metadata)
└── .cache/                   # Persistent embeddings cache (embeddings_cache.sqlite)
```

---

## 2. Detailed Subdirectory Descriptions

### 2.1 `data/raw/` (Raw Source Archives)
Stores pristine, unaltered legal documents as acquired from government repositories:
- `data/raw/constitution/constitution_of_india.json`: Raw consolidated text from the Legislative Department, Ministry of Law and Justice.
- `data/raw/judgments/*.pdf`: 103 official Supreme Court Reports (SCR) decision PDFs downloaded from AWS Open Data (`s3://indian-supreme-court-judgments`), spanning the formative years 1950 to 1952 (*A.K. Gopalan*, *Romesh Thappar*, *Brij Bhushan*, *Chintaman Rao*, *Chiranjit Lal*, *Shankari Prasad*).
- `data/raw/legislation/*.json`: Complete central codes downloaded from India Code: IPC (1860), CrPC (1973), Indian Evidence Act (1872), CPC (1908), Industrial Disputes Act (1947), Motor Vehicles Act (1988), and Negotiable Instruments Act (1881).

---

### 2.2 `data/processed/` (Standardized Canonical Datasets)
Contains clean, schema-compliant JSON documents validated by Pydantic's `LegalDocument` model. All 886 documents possess mandatory `document_id`, `document_type`, `source_url`, and `source_hash` fields:
1. **`articles_consolidated.json` (477 docs)**: Preamble, Articles 1 through 395+ (including 21A, 51A, 243A-ZG, 300A), and Schedules 1 through 12.
2. **`amendments_1_to_106.json` (106 docs)**: 1st Amendment (1951) through 106th Amendment (*Nari Shakti Vandan Adhiniyam*, 2023).
3. **`supreme_court_landmarks.json` (286 docs)**: 103 full-text PDF rulings, 158 structured landmark briefs (Facts, Issues, Ratio, Verdict), and 25 registry records.
4. **`central_acts.json` (17 Acts / 1,975 Sections)**: Constitutional framework enactments (Citizenship, RPA, RTI, AFSPA, PHRA, etc.) plus major legal codes.

---

### 2.3 `data/benchmarks/` and `data/annotations/` (Evaluation Gold Standards)
The ground-truth datasets powering the Stage 5 evaluation suite:
- **`legal_queries_gold.json`**: 100 diverse queries annotated with graded relevance ($3, 2, 1, 0$), expected statutory articles, and landmark case names.
- **`intent_train.json` / `val.json` / `test.json`**: Zero-data-leakage splits for intent classification.
- **`legal_ner_gold.json`**: Exact start and end character offsets for 10 entity types.
- **`entity_linking_gold.json`**: Mapping of informal surface names to canonical IDs.

---

### 2.4 `data/parent_store.json` (Parent Hydration Store)
A 12 MB JSON dictionary mapping canonical `parent_id` strings (e.g., `parent_const_art_021`) to full parent document records.
- Enables asymmetric RAG: child chunks (~300 chars) are searched in ChromaDB; full parent documents (~1,200 chars) are hydrated from `parent_store.json` for LLM prompt context.

---

### 2.5 `data/chroma_db/` (Persistent Vector Store)
The embedded ChromaDB database:
- `chroma.sqlite3`: SQLite relational database storing chunk text, document metadata, and collection IDs.
- Binary vector index folders containing the HNSW hierarchical graphs used for fast approximate nearest neighbor (ANN) vector lookup.

---

### 2.6 `data/.cache/embeddings_cache.sqlite` (Persistent Embedding Cache)
A local SQLite database caching 1024-dimensional BGE-M3 embedding vectors keyed by MD5 text hashes.
- Prevents re-computing neural embeddings when the same query or chunk is processed repeatedly.

---

## 3. Viva Presentation & Defense Q&A

### Q1: Why do you separate raw data from processed data?
> **Student Answer**:
> *"Separating raw from processed data is a core data engineering best practice (the medallion architecture). Raw files (`data/raw/`) preserve pristine historical artifacts like government PDFs and unedited statutes. Processed files (`data/processed/`) contain cleaned, schema-validated records where text is normalized, clauses are structured, and SHA-256 hashes are verified. If parsing logic ever changes, we can re-process from raw data without re-downloading anything from the web."*

### Q2: What is stored in `data/.cache/embeddings_cache.sqlite`?
> **Student Answer**:
> *"It is our local SQLite vector cache. Generating 1024-dimensional embeddings for BGE-M3 on CPU requires neural forward passes. By caching computed vectors in SQLite keyed by query text hashes, identical queries or repeated evaluation runs execute instantaneously from disk cache in under 1 millisecond, dramatically accelerating response times."*

