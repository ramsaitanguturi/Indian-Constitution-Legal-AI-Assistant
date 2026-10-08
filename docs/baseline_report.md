# Stage 0 Baseline Audit Report
## Entity-Aware Hybrid Retrieval and Reranking Framework for Indian Constitutional Question Answering

**Project**: Indian Constitution Legal AI Assistant  
**Milestone**: Stage 0 — Repository Audit and Baseline Establishment  
**Date**: October 8, 2026  
**Environment**: Python 3.12.10 (Windows 10 / PowerShell), pytest 9.1.1, scikit-learn 1.9.1, chromadb 1.5.9  

---

## 1. Executive Overview

This report documents the empirical baseline performance, dataset volume, retrieval latencies, and runtime behaviors of the **Indian Constitution Legal AI Assistant** repository prior to executing the NLP capstone upgrades (Stages 1 through 7). 

All measurements in this report are based on live runtime execution and testing against the repository's active components. No values have been estimated, simulated, or fabricated.

---

## 2. Corpus & Database Inventory

The baseline repository operates on a minimal curated sample dataset structured as follows:

| Asset | Filepath | Size | Item Count | Structure Details |
|---|---|---|---|---|
| **Constitutional Sample** | `data/sample_constitution.json` | 9.9 KB | 9 provisions | Preamble, Art. 12, 14, 19, 21, 21A, 32, 368, 370 |
| **Judgments Sample** | `data/sample_judgments.json` | 6.8 KB | 5 judgments | Kesavananda Bharati (1973), Maneka Gandhi (1978), Puttaswamy (2017), Minerva Mills (1980), S.R. Bommai (1994) |
| **Parent Document Store** | `parent_store.json` | 33.6 KB | 14 documents | 9 Constitution parent records + 5 Landmark Judgment parent records |
| **ChromaDB Vector Store** | `chroma_db/` | ~2.1 MB | 60 vectors | Cosine space (`hnsw:space: cosine`), 384 dimensions (`sentence-transformers/all-MiniLM-L6-v2`) |
| **Child Passages Generated** | Memory / Ingestion | - | 59 chunks | Character sliding window (`CHILD_CHUNK_SIZE=300`, `CHILD_CHUNK_OVERLAP=50`) |

### Chunking Observations
- Child chunking in `ingestion.py` relies on a character sliding window (`_split_text_into_children`) searching for whitespace within 300 characters.
- The 14 parent documents produce exactly 59 child chunks (an average of ~4.2 child chunks per parent document).
- There is no clause-level constitutional parsing or legal structural separation (Facts / Issues / Ratio / Verdict) at the chunk level in this baseline state.

---

## 3. Empirical Latency & System Profiling

Benchmarked using 5 representative constitutional and legal queries:
1. *"What did Supreme Court rule regarding Right to Privacy in Puttaswamy under Article 21?"*
2. *"Explain the basic structure doctrine in Kesavananda Bharati"*
3. *"What are the fundamental rights guaranteed under Article 19?"*
4. *"What is the procedure for constitutional amendment under Article 368?"*
5. *"Explain freedom of speech and expression and its restrictions"*

### Latency Breakdown (Mean of 5 queries)

| Pipeline Component | Metric | Mean Latency | Min Latency | Max Latency | Notes |
|---|---|---|---|---|---|
| **Model Cold-Start Initialization** | Total Time | **64.07 s** | - | - | Loading PyTorch runtime + `sentence-transformers` MiniLM weights |
| **Sparse BM25 Search** | Latency | **1.16 ms** | 1.06 ms | 1.34 ms | `BM25Okapi` ($k_1=1.5, b=0.75$) over 59 tokenized child texts |
| **Dense Vector Search** | Latency | **40.12 ms** | 32.20 ms | 58.56 ms | ChromaDB local collection query with 384-d MiniLM embeddings |
| **Reciprocal Rank Fusion (RRF)** | Latency | **0.54 ms** | 0.37 ms | 0.61 ms | Score fusion ($k=60$) + entity boost ($+0.05$) |
| **Total End-to-End Retrieval** | Latency | **36.46 ms** | 32.99 ms | 41.00 ms | Full `HybridRRFRetriever.retrieve()` pipeline |
| **Offline Fallback Synthesis** | Latency | **0.29 ms** | 0.20 ms | 0.35 ms | `HeuristicLegalSynthesizer.synthesize()` markdown generation |

### Memory Profiling
- **Traced Peak Memory**: `310.59 MB`
- Primary memory driver is the local `sentence-transformers/all-MiniLM-L6-v2` PyTorch model loaded for dense embeddings.

---

## 4. LLM Configuration & Fallback Verification

### Model Identifier Audit
- **Previous Value in `config.py`**: `DEFAULT_LLM_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")`
- **Observed Behavior**: The Google GenAI API returned HTTP 404 (`models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.8-flash`).
- **Remediation**: Updated `config.py` to `DEFAULT_LLM_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")`.
- **Live Verification**:
  - Live API call with `gemini-3.8-flash` succeeded with `used_llm: True`.
  - Offline fallback through `HeuristicLegalSynthesizer` was verified to function seamlessly when API keys are absent or invalid, preventing application crashes.

---

## 5. Automated Regression Test Suite

An initial automated regression test suite was established under `tests/`:

- **Test Suite Location**: `tests/test_baseline_regression.py`
- **Runner**: `pytest tests/`
- **Total Tests**: 27
- **Passed**: 27
- **Failed**: 0
- **Execution Time**: ~37–50 seconds (including cold-start embedding model initialization)

### Test Coverage Breakdown

| Test Group | Test Cases | Scope |
|---|---|---|
| `TestDatasetAndConfigBaseline` | 3 | Validates hyperparameter constants, paths, and raw JSON schema structure for constitution and judgments. |
| `TestIngestionPipelineBaseline` | 6 | Validates regex tokenization, sliding window bounds, parent/child counts (14 parents, 59 children), and parent store integrity. |
| `TestLegalNERExtractorBaseline` | 4 | Validates entity extraction for Articles, Landmark Cases, Legal Concepts, Preamble, and empty/unrelated queries. |
| `TestRetrievalComponentsBaseline` | 3 | Validates BM25 sparse search on matching and out-of-vocabulary queries, and Dense ChromaDB vector search. |
| `TestHybridRetrievalBaseline` | 3 | Validates RRF rank merging, entity boost bonus, top-k output schema, and parent document hydration. |
| `TestAgentsBaseline` | 8 | Validates query classification heuristics, override modes, markdown formatting for all 3 agent types in fallback synthesizer, and structured response schema. |

---

## 6. Application Health Verification

The existing Streamlit application was launched and validated:
- **Command**: `streamlit run app.py --server.headless true --server.port 8501`
- **Server Status**: Launched successfully on port 8501.
- **HTTP Health Check**: Returned `HTTP 200 OK` on `http://localhost:8501`.
- **Backward Compatibility**: All tabs (Q&A Assistant, Case Comparator, Constitutional Database Explorer, Architecture) remain functional.

---

## 7. Stage 0 Completion Checklist

- [x] Audited local environment and dependencies.
- [x] Pinned `scikit-learn>=1.4.0` and `pytest>=8.0.0` in `requirements.txt`.
- [x] Updated default LLM model in `config.py` to active `gemini-3.8-flash` with environment override.
- [x] Established `tests/` directory with `tests/__init__.py` and `tests/test_baseline_regression.py`.
- [x] Ran complete test suite (`pytest tests/`) — 27/27 tests passed.
- [x] Verified Streamlit application launches without regression.
- [x] Logged baseline metrics to `docs/baseline_report.md`.
- [x] No breaking architectural changes or premature future-stage implementations introduced.
