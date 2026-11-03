# Complete Test Files Directory: `14_TESTING/test_files_explained.md`

[Back to Testing Overview](testing_overview.md) • [Back to Main Index](../README.md)

---

## 1. Directory Breakdown: All 28 Test Modules

Below is the comprehensive catalog of all 28 test files in `tests/`, detailing their test classes, functional coverage, and role in project reliability.

---

### 1. `test_baseline_regression.py` (27 Tests)
- **Classes**: `TestDatasetAndConfigBaseline`, `TestIngestionPipelineBaseline`, `TestLegalNERExtractorBaseline`, `TestRetrievalComponentsBaseline`, `TestHybridRetrievalBaseline`, `TestAgentsBaseline`.
- **Coverage**: Backward compatibility regression test verifying that refactored components maintain compatibility with baseline datasets (`sample_constitution.json`, `sample_judgments.json`).

### 2. `test_benchmark_integrity.py` (5 Tests)
- **Class**: `TestBenchmarkIntegrity`.
- **Coverage**: Asserts that all 100 queries in `legal_queries_gold.json` reference valid existing parent IDs in `parent_store.json`, verifies intent class balance, and checks NER span alignments.

### 3. `test_chunking.py` (14 Tests)
- **Classes**: `TestConstitutionalArticleChunking`, `TestJudgmentChunking`, `TestAmendmentChunking`, `TestTokenEstimationAndEdgeCases`, `TestExpandedCorpusIntegrity`.
- **Coverage**: Structure-aware chunking: verifies clauses are never split mid-sentence, tests sub-clause splitting on `(a)`, `(b)`, tests judgment section extraction (Facts, Issues, Ratio, Verdict), and tests token estimation.

### 4. `test_citation_validator.py` (10 Tests)
- **Class**: `TestCitationValidator`.
- **Coverage**: Tests structural citation verification: catches non-existent document IDs, catches unretrieved evidence cited from parametric memory, detects missing metadata, and flags ungrounded case mentions.

### 5. `test_confidence_abstention.py` (16 Tests)
- **Classes**: `TestConfidenceEstimator`, `TestAbstentionManager`, `TestEndToEndConfidenceAndAbstentionIntegration`.
- **Coverage**: Verifies all 6 confidence signals, tests sigmoid mapping of rerank logits, verifies 5-stage abstention gates, and tests safe refusal notices.

### 6. `test_corpus_integrity.py` (8 Tests)
- **Class**: `TestCorpusIntegrity`.
- **Coverage**: Cryptographic integrity: verifies SHA-256 hashes of raw and processed files against `corpus_manifest.json`, validates Pydantic `LegalDocument` schemas.

### 7. `test_embedding_dimensions.py` (4 Tests)
- **Class**: `TestEmbeddingDimensions`.
- **Coverage**: Tests dimension compatibility: asserts `BAAI/bge-m3` produces 1024-dimensional vectors in collection `indian_legal_rag_bgem3` and `all-MiniLM-L6-v2` produces 384-dimensional vectors in `indian_legal_rag`.

### 8. `test_end_to_end_rag.py` (8 Tests)
- **Class**: `TestEndToEndRAG`.
- **Coverage**: Full pipeline execution: tests query normalization, retrieval, parent recovery, grounded generation, citation validation, and confidence estimation.

### 9. `test_entity_linking.py` (10 Tests)
- **Class**: `TestEntityLinking`.
- **Coverage**: Tests canonical entity resolution: maps surface forms (`"art 21"`, `"puttaswamy case"`, `"habeas corpus"`) to canonical registry IDs (`art_21`, `case_puttaswamy_2017`).

### 10. `test_evaluation_framework.py` (12 Tests)
- **Class**: `TestEvaluationFramework`.
- **Coverage**: Evaluates benchmark suite runners, tests metric aggregation, and verifies report generation formatting.

### 11. `test_evaluation_metrics.py` (18 Tests)
- **Class**: `TestEvaluationMetrics`.
- **Coverage**: Exact mathematical testing: validates Hit@K, Recall@K, Precision@K, MRR, DCG@K, NDCG@K against known hand-computed numerical matrices; tests alias map deduplication.

### 12. `test_grounded_generator.py` (9 Tests)
- **Class**: `TestGroundedGenerator`.
- **Coverage**: Grounded generator tests: verifies prompt formatting, tests 3-part section separation (Evidence, Analysis, Citations), tests zero-temperature offline fallback synthesis.

### 13. `test_intent.py` (12 Tests)
- **Classes**: `TestRuleBasedClassifier`, `TestMLClassifier`, `TestHybridClassifier`.
- **Coverage**: Tests intent classification across all 8 classes; verifies spurious out-of-scope guard for queries containing legal entities.

### 14. `test_master_pipeline.py` (12 Tests)
- **Class**: `TestMasterPipeline`.
- **Coverage**: Tests `LegalRAGPipeline` end-to-end: verifies `PipelineResult` dataclass attributes, tests router parameter injection, and verifies early/late abstention.

### 15. `test_ner.py` (14 Tests)
- **Class**: `TestLegalNER`.
- **Coverage**: Tests extraction across all 10 legal entity categories, verifies span offsets `(start, end)`, tests overlapping span resolution (longer span wins).

### 16. `test_nli_verifier.py` (14 Tests)
- **Class**: `TestNLIVerifier`.
- **Coverage**: Natural Language Inference: tests sentence proposition splitting, tests deontic modal polarity clashes (`"permits"` vs `"prohibits"`), verifies `CONTRADICTION` and `ENTAILMENT` verdicts.

### 17. `test_nlp_components.py` (15 Tests)
- **Classes**: `TestPreprocessing`, `TestLanguageDetection`, `TestQueryExpansion`.
- **Coverage**: Tests Unicode cleaning, abbreviation expansion (`"Art."` $\to$ `"Article"`), Devanagari script detection, Hinglish detection, and max 3-term query expansion.

### 18. `test_parent_child.py` (10 Tests)
- **Class**: `TestParentChildRecovery`.
- **Coverage**: Tests parent hydration from `parent_store.json`, zero-padding resolution (`art_021` vs `art_21`), parent deduplication, and prompt context formatting.

### 19. `test_pipeline_inspector.py` (6 Tests)
- **Class**: `TestPipelineInspector`.
- **Coverage**: Tests white-box inspection utility logging intermediate representations for UI rendering.

### 20. `test_qa_flow_backward_compat.py` (8 Tests)
- **Class**: `TestQAFlowBackwardCompat`.
- **Coverage**: Verifies backward compatibility of question answering flows with legacy agent signatures.

### 21. `test_query_router.py` (12 Tests)
- **Class**: `TestQueryRouter`.
- **Coverage**: Deterministic routing: tests all 7 decision rules (`ARTICLE_SEARCH`, `CASE_SEARCH`, `COMPARISON_SEARCH`, `PROCEDURE_SEARCH`, `RIGHTS_SEARCH`, `HYBRID_SEARCH`, `OUT_OF_SCOPE`).

### 22. `test_reranker.py` (10 Tests)
- **Class**: `TestCrossEncoderReranker`.
- **Coverage**: Tests second-stage neural reranker: (query, text) pair creation, batch scoring, top-$K$ slicing, score sorting, and fallback when model is unavailable.

### 23. `test_research_dashboard.py` (8 Tests)
- **Class**: `TestResearchDashboard`.
- **Coverage**: Tests metric extraction and chart formatting for the Streamlit research dashboard view.

### 24. `test_retrieval.py` (22 Tests)
- **Classes**: `TestStandardResultSchema`, `TestBM25Retriever`, `TestDenseRetriever`, `TestReciprocalRankFusion`, `TestEntityAwareBoost`, `TestHybridRetrieverAblations`.
- **Coverage**: Complete retrieval subsystem tests: BM25 score ordering, dense collection search, Cormack RRF math ($k=60$), additive entity boost, and metadata filtering.

### 25. `test_retrieval_confidence_regression.py` (8 Tests)
- **Classes**: `TestScoreInterpretationAndAbstentionRegression`, `TestRouterAndIntentRegression`.
- **Coverage**: Regression suite ensuring negative cross-encoder logits don't cause false abstentions and queries with legal entities are never misrouted as out-of-scope.

### 26. `test_search_warrant_qa_regression.py` (6 Tests)
- **Classes**: `TestSearchWithoutWarrantRegression`, `TestSearchWithWarrantRegression`, `TestSupersededLegislationRegression`, `TestCitationValidatorSubstantiveSupport`.
- **Coverage**: Dedicated regression suite for search warrant procedures under Article 21 and Section 165 CrPC; verifies substantive citation validation.

### 27. `test_streamlit_smoke.py` (4 Tests)
- **Class**: `TestStreamlitSmoke`.
- **Coverage**: UI smoke tests: verifies all Streamlit imports load without crashing, tests offline dashboard rendering with zero external API calls.

### 28. `test_ui_formatter.py` (2 Tests)
- **Coverage**: Verifies `format_legal_pipeline_result()`: ensures clean creation of `FormattedProvision`, `FormattedJudgment`, and graceful abstention handling.

---

## 2. Total Summary

- **Total Test Files**: 28 modules
- **Total Test Cases**: 319 tests
- **Passing Status**: 319 passing (100%)

