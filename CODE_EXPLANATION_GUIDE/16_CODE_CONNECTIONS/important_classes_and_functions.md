# Master Reference Directory of Important Classes and Functions: `16_CODE_CONNECTIONS/important_classes_and_functions.md`

[Back to Main Index](../README.md)

---

## 1. Overview

This document is the **Comprehensive Master Reference Directory** of all primary classes, functions, and data structures in the Indian Constitution Legal AI Assistant. Each entry provides the exact source file path, core responsibility, input parameters, and return types.

---

## 2. Core Orchestration & Pipeline

### `LegalRAGPipeline`
- **File**: [`rag/pipeline.py`](../../rag/pipeline.py#L74-L345)
- **Role**: Master end-to-end pipeline coordinator for question answering.
- **Key Methods**:
  - `__init__(retriever, parent_store, generator, strict_citation_validation)`: Initializes all Stage 2, 3, and 4 modular components.
  - `run(query, dynamic_api_key, override_top_k) -> PipelineResult`: Executes the full 16-stage pipeline.

### `PipelineResult`
- **File**: [`rag/pipeline.py`](../../rag/pipeline.py#L41-L73)
- **Role**: Strongly-typed, serializable dataclass encapsulating all 17 intermediate and final outputs of a query execution.
- **Key Fields**: `original_query`, `normalized_query`, `language`, `intent`, `entities`, `linked_entities`, `expanded_query`, `routing_decision`, `retrieved_chunks`, `reranked_chunks`, `parent_context`, `citations`, `generated_answer`, `citation_validation`, `confidence`, `abstained`, `abstention_reason`.

---

## 3. Natural Language Processing (Stage 2)

### `LegalNER`
- **File**: [`nlp/legal_ner.py`](../../nlp/legal_ner.py#L52-L210)
- **Role**: High-precision legal entity extractor for 10 legal entity categories.
- **Key Methods**:
  - `extract_entities(text: str) -> Dict[str, List[str]]`: Returns dictionary mapping entity labels (`ARTICLE`, `CASE`, `SECTION`, `AMENDMENT`, etc.) to lists of detected entity strings.
  - `extract_entity_spans(text: str) -> List[Dict[str, Any]]`: Returns exact `(start, end, text, label)` character offsets with collision resolution.

### `EntityLinker`
- **File**: [`nlp/entity_linking.py`](../../nlp/entity_linking.py#L48-L230)
- **Role**: Resolves informal surface mentions to canonical knowledge base entities.
- **Key Methods**:
  - `link_entity(mention: str, entity_type: str) -> Optional[Dict[str, Any]]`: Matches mention against alias index; returns canonical ID and metadata.
  - `link_all(extracted_entities: Dict[str, List[str]]) -> List[Dict[str, Any]]`: Batched linking across all extracted categories.

### `HybridIntentClassifier`
- **File**: [`nlp/intent_classifier.py`](../../nlp/intent_classifier.py#L182-L260)
- **Role**: Two-tier intent classification engine combining rule-based statutory patterns with machine learning fallback.
- **Key Methods**:
  - `classify(text: str, entities: Optional[Dict]) -> Dict[str, Any]`: Returns `{"intent": str, "confidence": float, "method": str, "is_out_of_scope": bool}`.

### `QueryExpander`
- **File**: [`nlp/query_expansion.py`](../../nlp/query_expansion.py#L22-L115)
- **Role**: Controlled legal synonym expansion with token drift guards.
- **Key Methods**:
  - `expand(query: str, max_expansions_per_term: int = 2) -> Dict[str, Any]`: Adds maximum 3 domain synonyms from `legal_synonyms.json`.

### `detect_language`
- **File**: [`nlp/language_detection.py`](../../nlp/language_detection.py#L18-L95)
- **Role**: Identifies language, Unicode script (Devanagari vs Latin), and Hinglish code-switching.
- **Signature**: `detect_language(text: str) -> Dict[str, Any]`

### `normalize_legal_text`
- **File**: [`nlp/preprocessing.py`](../../nlp/preprocessing.py#L42-L75)
- **Role**: Standardizes legal text, strips typographic quotes/dashes, and expands abbreviations.
- **Signature**: `normalize_legal_text(text: str) -> str`

---

## 4. Query Routing (Stage 4)

### `QueryRouter`
- **File**: [`routing/query_router.py`](../../routing/query_router.py#L51-L322)
- **Role**: Specialized deterministic NLP router deciding search strategies without stochastic LLMs.
- **Key Methods**:
  - `route(...) -> RoutingDecision`: Evaluates 7 deterministic decision rules over Stage 2 features.

### `RoutingDecision`
- **File**: [`routing/query_router.py`](../../routing/query_router.py#L25-L49)
- **Role**: Dataclass specifying strategy (`ARTICLE_SEARCH`, `CASE_SEARCH`, `OUT_OF_SCOPE`, etc.), candidate depth, and component weights.

---

## 5. Retrieval & Reranker Subsystem (Stage 3)

### `HybridRetriever`
- **File**: [`retrieval/hybrid_retrieval.py`](../../retrieval/hybrid_retrieval.py#L32-L368)
- **Role**: Coordinates BM25, Dense search, RRF fusion, Entity Boost, and Cross-Encoder reranking.
- **Key Methods**:
  - `retrieve(query, entities, top_k, filter_doc_type) -> List[Dict[str, Any]]`: Returns ranked top-$K$ child passages.

### `BM25Retriever`
- **File**: [`retrieval/bm25_retriever.py`](../../retrieval/bm25_retriever.py#L18-L156)
- **Role**: Sparse lexical search with compound legal identifier preservation.
- **Key Methods**:
  - `retrieve(query: str, top_k: int = 30) -> List[Dict[str, Any]]`: Scores passages using Rank-BM25 with min-max normalization.

### `DenseRetriever`
- **File**: [`retrieval/dense_retrieval.py`](../../retrieval/dense_retrieval.py#L17-L140)
- **Role**: Dense semantic vector search over ChromaDB collections.
- **Key Methods**:
  - `retrieve(query: str, top_k: int = 30) -> List[Dict[str, Any]]`: Queries HNSW index and converts cosine distance to similarity ($s = 1.0 - d$).

### `reciprocal_rank_fusion`
- **File**: [`retrieval/rrf.py`](../../retrieval/rrf.py#L15-L82)
- **Role**: Combines sparse and dense candidate lists using Cormack's RRF formula ($k=60$).
- **Signature**: `reciprocal_rank_fusion(ranked_lists: List[List[Dict]], k: int = 60) -> List[Dict]`

### `apply_entity_boost`
- **File**: [`retrieval/entity_boost.py`](../../retrieval/entity_boost.py#L104-L261)
- **Role**: Re-scores candidate passages by $+0.150$ when metadata matches query entities.
- **Signature**: `apply_entity_boost(candidates, linked_entities, boost_weight=0.15) -> List[Dict]`

### `CrossEncoderReranker`
- **File**: [`retrieval/reranker.py`](../../retrieval/reranker.py#L12-L121)
- **Role**: Second-stage neural reranker using full cross-attention (`ms-marco-MiniLM-L-6-v2`).
- **Key Methods**:
  - `rerank(query: str, candidates: List[Dict], top_k: int = 5) -> List[Dict[str, Any]]`

### `BGEM3EmbeddingFunction`
- **File**: [`retrieval/embeddings.py`](../../retrieval/embeddings.py#L22-L138)
- **Role**: Generates 1024-d dense embeddings with local SQLite disk caching.

---

## 6. Grounded RAG & Verification (Stage 4)

### `LegalStructureChunker`
- **File**: [`rag/chunking.py`](../../rag/chunking.py#L36-L565)
- **Role**: Structure-aware chunking for Articles (clauses), Amendments, Judgments (Facts/Ratio), and Acts (sections).

### `ParentChildRecovery`
- **File**: [`rag/parent_child.py`](../../rag/parent_child.py#L17-L290)
- **Role**: Hydrates full parent context from `parent_store.json`, deduplicates parent records, and constructs prompt context.

### `GroundedGenerator`
- **File**: [`rag/generator.py`](../../rag/generator.py#L44-L280)
- **Role**: Dual-mode generation: online Google Gemini (`temperature=0.0`) or deterministic offline legal synthesizer.

### `CitationValidator`
- **File**: [`rag/citation_validator.py`](../../rag/citation_validator.py#L19-L361)
- **Role**: Structural verification of declared citations (existence in DB, presence in retrieved evidence pool, metadata integrity).

### `NLIVerifier`
- **File**: [`rag/nli_verifier.py`](../../rag/nli_verifier.py#L65-L386)
- **Role**: Proposition-level Natural Language Inference detecting polarity conflicts and contradictory modals.

### `ConfidenceEstimator`
- **File**: [`rag/confidence.py`](../../rag/confidence.py#L21-L223)
- **Role**: Computes explainable multi-signal confidence composite score across 6 signals.

### `AbstentionManager`
- **File**: [`rag/abstention.py`](../../rag/abstention.py#L12-L229)
- **Role**: 5-stage defensive gating architecture withholding generation on ungrounded or low-confidence queries.

---

## 7. Data Ingestion & Evaluation

### `ProductionIngestor`
- **File**: [`rag/ingestion.py`](../../rag/ingestion.py#L30-L240)
- **Role**: Builds the 7,470 child passages, saves `parent_store.json`, and upserts vectors to ChromaDB.

### `BenchmarkRunner`
- **File**: [`evaluation/benchmark_runner.py`](../../evaluation/benchmark_runner.py#L53-L292)
- **Role**: Master CLI test runner executing all 6 ablation suites.

### `ReportGenerator`
- **File**: [`evaluation/report_generator.py`](../../evaluation/report_generator.py#L33-L327)
- **Role**: Serializes benchmark results to JSON, CSV, and Markdown.

### `hit_at_k`, `recall_at_k`, `ndcg_at_k`, `calculate_ner_metrics`
- **File**: [`evaluation/metrics.py`](../../evaluation/metrics.py#L21-L380)
- **Role**: Mathematical implementations of IR and NLP evaluation metrics.

