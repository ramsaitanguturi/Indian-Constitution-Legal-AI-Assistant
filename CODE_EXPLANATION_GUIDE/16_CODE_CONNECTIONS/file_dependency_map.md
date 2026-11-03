# File Dependency and Import Matrix: `16_CODE_CONNECTIONS/file_dependency_map.md`

[Back to Main Index](../README.md)

---

## 1. System Dependency Overview

This document maps the inter-file dependencies and module import relationships across the entire codebase. It helps examiners and developers understand how code changes in one file propagate across the application.

```mermaid
graph TD
    CFG["config.py"]

    subgraph NLP["Stage 2: NLP Module"]
        PRE["nlp/preprocessing.py"]
        NER["nlp/legal_ner.py"]
        LNK["nlp/entity_linking.py"]
        INT["nlp/intent_classifier.py"]
        EXP["nlp/query_expansion.py"]
        LNG["nlp/language_detection.py"]
    end

    subgraph ROUTING["Stage 4: Query Routing"]
        RTR["routing/query_router.py"]
    end

    subgraph RETRIEVAL["Stage 3: Retrieval & Reranker"]
        EMB["retrieval/embeddings.py"]
        BM["retrieval/bm25_retriever.py"]
        DNS["retrieval/dense_retriever.py"]
        RRF["retrieval/rrf.py"]
        BST["retrieval/entity_boost.py"]
        RNK["retrieval/reranker.py"]
        HYB["retrieval/hybrid_retriever.py"]
    end

    subgraph RAG["Stage 4: Grounded RAG & Safety"]
        CHK["rag/chunking.py"]
        PC["rag/parent_child.py"]
        GEN["rag/generator.py"]
        NLI["rag/nli_verifier.py"]
        VAL["rag/citation_validator.py"]
        CNF["rag/confidence.py"]
        ABS["rag/abstention.py"]
        PIP["rag/pipeline.py"]
        UIF["rag/ui_formatter.py"]
    end

    subgraph APP["Stage 1: Main Application"]
        APP_PY["app.py"]
        AGN_PY["agents.py"]
    end

    CFG --> NLP & ROUTING & RETRIEVAL & RAG & APP
    NLP --> RTR & PIP
    ROUTING --> PIP
    RETRIEVAL --> PIP
    RAG --> PIP
    PIP --> UIF --> APP_PY
    RAG --> AGN_PY --> APP_PY
```

---

## 2. Detailed File Dependency Matrix

| File | Depends On (Imports) | Depended On By (Imported By) |
| :--- | :--- | :--- |
| **`config.py`** | *None* (Standard library `os`, `pathlib`) | Every single module in the repository. |
| **`nlp/preprocessing.py`** | `re`, `unicodedata` | `nlp/legal_ner.py`, `nlp/intent_classifier.py`, `retrieval/bm25_retriever.py`, `rag/pipeline.py` |
| **`nlp/language_detection.py`**| `re` | `routing/query_router.py`, `rag/pipeline.py` |
| **`nlp/legal_ner.py`** | `re`, `json`, `config.py`, `nlp/preprocessing.py` | `nlp/entity_linking.py`, `nlp/intent_classifier.py`, `routing/query_router.py`, `rag/pipeline.py` |
| **`nlp/entity_linking.py`** | `json`, `re`, `config.py` | `routing/query_router.py`, `retrieval/entity_boost.py`, `rag/pipeline.py` |
| **`nlp/intent_classifier.py`**| `re`, `json`, `config.py`, `nlp/preprocessing.py` | `routing/query_router.py`, `rag/pipeline.py`, `agents.py` |
| **`nlp/query_expansion.py`** | `re`, `json`, `config.py` | `routing/query_router.py`, `rag/pipeline.py` |
| **`routing/query_router.py`** | `config.py` | `rag/pipeline.py`, `rag/generator.py` |
| **`retrieval/embeddings.py`** | `sqlite3`, `hashlib`, `config.py`, `sentence_transformers` | `retrieval/dense_retriever.py`, `scripts/build_index.py`, `rag/ingestion.py` |
| **`retrieval/bm25_retriever.py`**| `math`, `re`, `config.py`, `rank_bm25` | `retrieval/hybrid_retriever.py`, `retriever.py`, `evaluation/retrieval_eval.py` |
| **`retrieval/dense_retriever.py`**| `chromadb`, `config.py`, `retrieval/embeddings.py`| `retrieval/hybrid_retriever.py`, `retriever.py`, `evaluation/retrieval_eval.py` |
| **`retrieval/rrf.py`** | `config.py` | `retrieval/hybrid_retriever.py`, `retriever.py` |
| **`retrieval/entity_boost.py`**| `re`, `config.py` | `retrieval/hybrid_retriever.py`, `retriever.py`, `rag/pipeline.py` |
| **`retrieval/reranker.py`** | `config.py`, `sentence_transformers.CrossEncoder` | `retrieval/hybrid_retriever.py`, `retriever.py`, `rag/pipeline.py` |
| **`retrieval/hybrid_retriever.py`**| All `retrieval/*` components | `rag/pipeline.py`, `retriever.py`, `evaluation/benchmark_runner.py` |
| **`rag/chunking.py`** | `re`, `config.py` | `rag/ingestion.py`, `ingestion.py`, `scripts/build_index.py` |
| **`rag/parent_child.py`** | `json`, `re`, `config.py` | `rag/pipeline.py`, `agents.py` |
| **`rag/generator.py`** | `re`, `config.py`, `google-genai` / `langchain_google_genai` | `rag/pipeline.py` |
| **`rag/nli_verifier.py`** | `re` | `rag/citation_validator.py` |
| **`rag/citation_validator.py`**| `re`, `json`, `config.py`, `rag/nli_verifier.py` | `rag/pipeline.py` |
| **`rag/confidence.py`** | `math`, `re`, `config.py` | `rag/pipeline.py` |
| **`rag/abstention.py`** | `config.py` | `rag/pipeline.py` |
| **`rag/pipeline.py`** | All `nlp/*`, `routing/*`, `retrieval/*`, and `rag/*` | `app.py` |
| **`rag/ui_formatter.py`** | `re` | `app.py` |
| **`agents.py`** | `config.py`, `retriever.py`, `rag/parent_child.py` | `app.py` |
| **`app.py`** | `streamlit`, `rag/pipeline.py`, `rag/ui_formatter.py`, `agents.py` | *User Interface Entry Point* |

---

## 3. Dependency Classification Taxonomy

To clearly understand how codebase files interact with each other and external systems, the dependencies are categorized into four distinct layers:

### A. Direct Function Calls (In-Memory Python Executions)
Direct, synchronous function and method invocations executed within the Python process:
- `app.py` $\to$ `rag.pipeline.LegalRAGPipeline.run(query)`
- `LegalRAGPipeline.run()` $\to$ `nlp.language_detection.detect_language(query)`
- `LegalRAGPipeline.run()` $\to$ `nlp.preprocessing.normalize_legal_text(query)`
- `LegalRAGPipeline.run()` $\to$ `nlp.legal_ner.LegalNER.extract_entities(norm_q)`
- `LegalRAGPipeline.run()` $\to$ `nlp.entity_linking.EntityLinker.link_all(entities)`
- `LegalRAGPipeline.run()` $\to$ `nlp.intent_classifier.HybridIntentClassifier.classify(norm_q)`
- `LegalRAGPipeline.run()` $\to$ `nlp.query_expansion.QueryExpander.expand(norm_q)`
- `LegalRAGPipeline.run()` $\to$ `routing.query_router.QueryRouter.route(...)`
- `LegalRAGPipeline.run()` $\to$ `retrieval.hybrid_retriever.HybridRetriever.retrieve(...)`
- `HybridRetriever.retrieve()` $\to$ `retrieval.bm25_retriever.BM25Retriever.retrieve(...)`
- `HybridRetriever.retrieve()` $\to$ `retrieval.dense_retriever.DenseRetriever.retrieve(...)`
- `HybridRetriever.retrieve()` $\to$ `retrieval.rrf.fuse(...)`
- `HybridRetriever.retrieve()` $\to$ `retrieval.entity_boost.apply_entity_boost(...)`
- `HybridRetriever.retrieve()` $\to$ `retrieval.reranker.CrossEncoderReranker.rerank(...)`
- `LegalRAGPipeline.run()` $\to$ `rag.parent_child.ParentChildRecovery.recover(...)`
- `LegalRAGPipeline.run()` $\to$ `rag.generator.GroundedGenerator.generate(...)`
- `LegalRAGPipeline.run()` $\to$ `rag.citation_validator.CitationValidator.validate(...)`
- `CitationValidator.validate()` $\to$ `rag.nli_verifier.NLIVerifier.verify_answer(...)`
- `LegalRAGPipeline.run()` $\to$ `rag.confidence.ConfidenceEstimator.estimate(...)`
- `LegalRAGPipeline.run()` $\to$ `rag.abstention.AbstentionManager.evaluate(...)`
- `app.py` $\to$ `rag.ui_formatter.format_legal_pipeline_result(pipeline_result)`

### B. Imported Dependencies (Packages & Third-Party Libraries)
External libraries declared in `requirements.txt` imported for computation:
- `rank_bm25`: BM25Okapi scoring in `retrieval/bm25_retriever.py`.
- `sentence_transformers`: BGE-M3 / MiniLM embeddings and CrossEncoder in `retrieval/embeddings.py` and `retrieval/reranker.py`.
- `chromadb`: Vector store client and persistent collection querying in `retrieval/dense_retriever.py`.
- `scikit-learn` / `joblib`: Logistic Regression intent classification in `nlp/intent_classifier.py`.
- `streamlit`: Web application framework in `app.py`.
- `google-genai` / `langchain_google_genai`: LLM generative synthesis API in `rag/generator.py` and `agents.py`.

### C. Runtime Interactions (IO, Cache, and Persistence Operations)
Data interactions occurring with filesystem, databases, and network services during execution:
- **SQLite Cache**: `retrieval/embeddings.py` connects to `embedding_cache.db` to check and insert precomputed vector hashes.
- **ChromaDB HNSW Graph**: `retrieval/dense_retriever.py` queries `chroma_db/` index for nearest neighbor cosine distances.
- **JSON File Store**: `rag/parent_child.py` loads and parses `parent_store.json` (1,734 records) into in-memory dictionaries.
- **LLM API Calls**: `rag/generator.py` makes secure HTTPS requests to Google Gemini endpoints when an API key is present.

### D. Optional & Conditional Components
Components that degrade gracefully or activate conditionally:
- **Linux SQLite Patch (`pysqlite3-binary`)**: Only imported if running on Linux systems where the default SQLite version is `< 3.35.0`.
- **Cross-Encoder Reranker**: Can be disabled via ablation flags (`enable_reranker=False`) or when low latency is required.
- **LLM Answer Generation**: Automatically falls back to offline, deterministic grounded synthesis (`HeuristicLegalSynthesizer`) if the Gemini API key is missing or quota is exhausted.
- **Multi-Agent Chat Module (`agents.py`)**: Legacy/exploratory multi-agent chat interface running in parallel with the canonical 16-stage `LegalRAGPipeline`.

---

## 4. Key Observations for Code Explanations

1. **Acyclic Directed Graph (DAG)**: There are **zero circular imports** in the repository. Dependencies strictly flow downwards from foundational modules (`config.py` $\to$ `nlp/*` $\to$ `retrieval/*` $\to$ `rag/*` $\to$ `app.py`).
2. **Lazy Loading**: Heavy neural modules (`sentence_transformers.CrossEncoder`, `ChatGoogleGenerativeAI`) are loaded lazily inside class methods rather than at module top-level. This prevents Streamlit import stalls and enables instant CLI start times.
3. **Pluggable Architecture**: `rag/pipeline.py` accepts pre-instantiated instances of retriever, parent store, and generator in its constructor, making it trivial to inject mock instances during unit testing.

