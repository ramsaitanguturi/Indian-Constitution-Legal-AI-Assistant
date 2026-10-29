# Troubleshooting & Operational Guide

This document addresses common issues, recovery procedures, and edge cases encountered when running the **Indian Constitution Legal AI Assistant**.

---

## 1. Hardware & Environment Troubleshooting

### CUDA / GPU Availability
- **Symptom:** `CUDA Available: False` or `torch.cuda.is_available() == False`.
- **Resolution:** The system is engineered to run seamlessly on CPU without requiring an NVIDIA GPU. Deep learning models (`sentence-transformers`, `cross-encoder`, `bge-m3`) use optimized CPU multi-threading.
- **Tip:** If running on a system with an NVIDIA GPU and CUDA drivers installed, ensure `torch` with CUDA support is installed (`pip install torch --index-url https://download.pytorch.org/whl/cu121`).

### Memory (RAM) Management
- **Issue:** Memory consumption during dense indexing of large corpora.
- **Resolution:** The indexing script supports configurable batch sizes via `--batch-size 16` or `--batch-size 32`. Do not load entire unchunked corpora into RAM simultaneously; the pipeline streams documents in batches.

---

## 2. ChromaDB & Vector Store Issues

### SQLite Journal / File Lock Errors
- **Symptom:** `shutil.Error: chroma.sqlite3-journal not found` or `OperationalError: database is locked`.
- **Cause:** ChromaDB locks the SQLite database during active writes or concurrent connections.
- **Resolution:**
  1. Ensure no other instance of the CLI, evaluation script, or Streamlit app is running concurrently while rebuilding the index.
  2. If a lock persists after a crash, verify no zombie Python processes remain (`Get-Process python`).
  3. Safe backup tools in `scripts/update_corpus.py` automatically ignore ephemeral SQLite journal files (`*.lock`, `*-journal`, `*-wal`).

### Embedding Dimension Mismatch
- **Symptom:** `InvalidDimensionException: Embedding dimension 1024 does not match collection dimension 384`.
- **Resolution:** ChromaDB collections enforce a strict, immutable vector dimension:
  - `all-MiniLM-L6-v2` produces 384-dimensional vectors $\to$ collection `indian_legal_rag`.
  - `BAAI/bge-m3` produces 1024-dimensional vectors $\to$ collection `indian_legal_rag_bgem3`.
  The helper function `config.get_chroma_collection_name(model_name)` handles this dynamically. Never attempt to insert 1024-d vectors into a 384-d collection.

### Rebuilding Index from Scratch
To perform a safe, clean rebuild of ChromaDB:
```powershell
.\venv\Scripts\python scripts/build_index.py --rebuild --model sentence-transformers/all-MiniLM-L6-v2
```
or for BGE-M3:
```powershell
.\venv\Scripts\python scripts/build_index.py --rebuild --model BAAI/bge-m3
```

---

## 3. Offline Operation & Cache Management

### Offline Model Operation
- **Symptom:** Model download timeouts or network disconnections in air-gapped environments.
- **Resolution:**
  - Both `BAAI/bge-m3` and `sentence-transformers/all-MiniLM-L6-v2` are locally cached under `~/.cache/huggingface/hub/`.
  - In air-gapped or offline environments, set `export HF_HUB_OFFLINE=1` (or `$env:HF_HUB_OFFLINE=1` in PowerShell).
  - BM25 lexical search operates 100% offline with zero dependencies on remote endpoints or huggingface hub.

### Missing Parent Store
- **Symptom:** `FileNotFoundError: parent_store.json`.
- **Resolution:** Run the pipeline to regenerate parent store and indices:
  ```powershell
  .\venv\Scripts\python -c "from rag.ingestion import ProductionIngestor; ing = ProductionIngestor(); ing.process_parent_child_chunks(); ing.save_parent_store()"
  ```

---

## 4. Grounding & Abstention Behaviors

### Assistant Refuses to Answer Off-Topic Queries
- **Observation:** Assistant states *"I cannot answer this question as it falls outside Indian constitutional law and legal jurisprudence."*
- **Reason:** This is expected system behavior. The Multi-Stage Abstention Gate intercepts off-topic, non-legal queries before retrieval to prevent hallucinations.

### Assistant States Insufficient Authoritative Evidence
- **Observation:** Assistant states *"Authoritative evidence for this specific legal question is currently unavailable in the verified corpus."*
- **Reason:** This is intentional. When retrieved passages have low similarity (< 0.35) or fail cross-encoder reranker thresholds, the assistant abstains rather than inventing statutes, articles, or legal holdings.

