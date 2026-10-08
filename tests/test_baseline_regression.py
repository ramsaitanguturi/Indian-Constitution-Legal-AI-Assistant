"""
Baseline regression tests for Indian Constitution Legal AI Assistant.
Validates existing ingestion pipeline, BM25 search, dense vector retrieval,
Reciprocal Rank Fusion (RRF), Legal NER extraction, and Agent routing/fallback.
"""

import json
import os
import pytest
from pathlib import Path

from config import (
    BASE_DIR,
    CONSTITUTION_DATA_PATH,
    JUDGMENTS_DATA_PATH,
    PARENT_STORE_PATH,
    CHROMA_PERSIST_DIR,
    CHROMA_COLLECTION_NAME,
    DEFAULT_EMBEDDING_MODEL,
    CHILD_CHUNK_SIZE,
    BM25_K1,
    BM25_B,
    RRF_K,
    DEFAULT_TOP_K,
    DEFAULT_LLM_MODEL
)
from ingestion import ParentChildIngestor, simple_tokenize
from retriever import HybridRRFRetriever, LegalNERExtractor
from agents import MultiAgentRouter, HeuristicLegalSynthesizer


@pytest.fixture(scope="module")
def ingestor_instance():
    """Instantiate and run ParentChildIngestor processing."""
    ing = ParentChildIngestor()
    ing.process_parent_child_chunks()
    return ing


@pytest.fixture(scope="module")
def retriever_instance():
    """Shared retriever instance to avoid re-loading embedding model per test."""
    return HybridRRFRetriever()


@pytest.fixture(scope="module")
def router_instance():
    """Shared MultiAgentRouter instance."""
    return MultiAgentRouter()


# =========================================================================
# 1. Configuration & Dataset Integrity Tests
# =========================================================================

class TestDatasetAndConfigBaseline:
    """Verifies existing datasets and configuration values."""

    def test_config_constants_valid(self):
        """Ensure all required hyperparameters and path constants are defined."""
        assert BASE_DIR.exists()
        assert CHILD_CHUNK_SIZE > 0
        assert BM25_K1 == 1.5
        assert BM25_B == 0.75
        assert RRF_K == 60
        assert DEFAULT_TOP_K == 4
        assert DEFAULT_EMBEDDING_MODEL == "sentence-transformers/all-MiniLM-L6-v2"
        assert CHROMA_COLLECTION_NAME == "indian_legal_rag"
        assert isinstance(DEFAULT_LLM_MODEL, str) and len(DEFAULT_LLM_MODEL) > 0

    def test_sample_constitution_data_schema(self):
        """Verify data/sample_constitution.json has 9 valid articles."""
        assert os.path.exists(CONSTITUTION_DATA_PATH)
        with open(CONSTITUTION_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 9

        for item in data:
            assert "id" in item
            assert "article_number" in item
            assert "title" in item
            assert "part" in item
            assert "category" in item
            assert "text" in item
            assert len(item["text"]) > 0

    def test_sample_judgments_data_schema(self):
        """Verify data/sample_judgments.json has 5 valid judgments."""
        assert os.path.exists(JUDGMENTS_DATA_PATH)
        with open(JUDGMENTS_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 5

        for item in data:
            assert "id" in item
            assert "case_name" in item
            assert "citation" in item
            assert "year" in item
            assert "bench" in item
            assert "facts" in item
            assert "ratio_decidendi" in item
            assert "verdict" in item
            assert len(item["facts"]) > 0
            assert len(item["ratio_decidendi"]) > 0


# =========================================================================
# 2. Ingestion & Chunking Pipeline Tests
# =========================================================================

class TestIngestionPipelineBaseline:
    """Verifies chunking, parent store creation, and BM25 index building."""

    def test_simple_tokenize(self):
        """Test basic tokenization behavior."""
        tokens = simple_tokenize("Article 21: Protection of Life and Personal Liberty!")
        assert "article" in tokens
        assert "21" in tokens
        assert "protection" in tokens
        assert "liberty" in tokens

    def test_simple_tokenize_empty(self):
        """Test tokenization of empty and punctuation-only inputs."""
        assert simple_tokenize("") == []
        assert simple_tokenize("!@#$%^&*()") == []

    def test_split_text_into_children_bounds(self, ingestor_instance):
        """Verify child chunking sliding window obeys chunk boundaries."""
        sample_text = (
            "The Constitution of India is the supreme law of India. "
            "The document lays down the framework that demarcates fundamental political code, "
            "structure, procedures, powers, and duties of government institutions and sets out "
            "fundamental rights, directive principles, and the duties of citizens. It is the longest "
            "written constitution of any country on earth. B. R. Ambedkar is widely considered to be its chief architect."
        )
        chunks = ingestor_instance._split_text_into_children(sample_text, chunk_size=100, overlap=20)
        assert len(chunks) > 1
        for ch in chunks:
            assert len(ch) <= 100
            assert len(ch) > 0

    def test_split_text_into_children_empty(self, ingestor_instance):
        """Verify child chunking on empty string."""
        assert ingestor_instance._split_text_into_children("") == []
        assert ingestor_instance._split_text_into_children(None) == []

    def test_process_parent_child_chunks_counts(self, ingestor_instance):
        """Verify exact parent and child counts for baseline dataset."""
        parent_store = ingestor_instance.parent_store
        child_chunks = ingestor_instance.child_chunks

        # 9 articles + 5 judgments = 14 parents
        assert len(parent_store) == 14
        const_parents = [p for p in parent_store.values() if p["doc_type"] == "constitution"]
        judg_parents = [p for p in parent_store.values() if p["doc_type"] == "judgment"]
        assert len(const_parents) == 9
        assert len(judg_parents) == 5

        # Exactly 59 child chunks generated from character sliding window
        assert len(child_chunks) == 59

        # Verify child metadata links to parent
        for child in child_chunks:
            assert child["parent_id"] in parent_store
            assert len(child["text"]) > 0
            assert child["doc_type"] in ["constitution", "judgment"]

    def test_parent_store_file_integrity(self):
        """Verify existing parent_store.json file is intact and readable."""
        assert os.path.exists(PARENT_STORE_PATH)
        with open(PARENT_STORE_PATH, "r", encoding="utf-8") as f:
            store = json.load(f)
        assert isinstance(store, dict)
        assert len(store) == 14


# =========================================================================
# 3. Legal Named Entity Recognition (NER) Tests
# =========================================================================

class TestLegalNERExtractorBaseline:
    """Verifies rule-based entity extraction from user queries."""

    def test_extract_article_and_case(self):
        """Extract explicit Article reference and landmark Case name."""
        query = "What did Supreme Court hold in Puttaswamy regarding Article 21 and right to privacy?"
        entities = LegalNERExtractor.extract_entities(query)
        assert "Article 21" in entities["articles"]
        assert "Puttaswamy" in entities["cases"]
        assert any(c in entities["concepts"] for c in ["privacy", "right to privacy"])

    def test_extract_preamble(self):
        """Extract Preamble reference."""
        query = "Explain secularism under the Preamble of the Constitution"
        entities = LegalNERExtractor.extract_entities(query)
        assert "Preamble" in entities["articles"]
        assert "secularism" in entities["concepts"]

    def test_extract_multiple_cases(self):
        """Extract multiple landmark cases."""
        query = "Compare Kesavananda Bharati with Minerva Mills regarding basic structure"
        entities = LegalNERExtractor.extract_entities(query)
        assert "Kesavananda Bharati" in entities["cases"]
        assert "Minerva Mills" in entities["cases"]
        assert "basic structure" in entities["concepts"]

    def test_extract_empty_or_unrelated_query(self):
        """Verify extractor returns clean empty lists for queries with no legal entities."""
        entities_empty = LegalNERExtractor.extract_entities("")
        assert entities_empty == {"articles": [], "cases": [], "concepts": []}

        entities_random = LegalNERExtractor.extract_entities("What is the weather in Delhi today?")
        assert entities_random == {"articles": [], "cases": [], "concepts": []}


# =========================================================================
# 4. Sparse (BM25) and Dense (ChromaDB) Retrieval Tests
# =========================================================================

class TestRetrievalComponentsBaseline:
    """Verifies BM25 sparse search and ChromaDB dense search."""

    def test_bm25_sparse_search_matching_query(self, retriever_instance):
        """BM25 search returns ranked results for keywords in corpus."""
        results = retriever_instance.sparse_search_bm25("Article 21 privacy", top_k=5)
        assert len(results) > 0
        for child_id, score, rank in results:
            assert isinstance(child_id, str)
            assert isinstance(score, float)
            assert score > 0.0
            assert rank >= 1

    def test_bm25_sparse_search_unmatched_query(self, retriever_instance):
        """BM25 search returns empty list for out-of-vocabulary queries."""
        results = retriever_instance.sparse_search_bm25("xyznonsensewordnotincorpus12345", top_k=5)
        assert results == []

    def test_dense_vector_search(self, retriever_instance):
        """Dense search queries ChromaDB and returns top-k nearest neighbors."""
        results = retriever_instance.dense_search_vector("Article 21 privacy", top_k=5)
        assert len(results) == 5
        for child_id, dist, rank in results:
            assert isinstance(child_id, str)
            assert isinstance(dist, float)
            assert rank >= 1


# =========================================================================
# 5. RRF Fusion and Hybrid Retrieval End-to-End Tests
# =========================================================================

class TestHybridRetrievalBaseline:
    """Verifies Reciprocal Rank Fusion, entity boost, and full retrieve pipeline."""

    def test_rrf_scoring_and_entity_boost(self, retriever_instance):
        """Verify RRF fusion combines rankings and adds entity boost."""
        bm25_mock = [("child_const_art_21_0", 5.0, 1), ("child_const_art_19_0", 3.0, 2)]
        vector_mock = [("child_const_art_21_0", 0.2, 1), ("child_const_art_14_0", 0.4, 2)]
        entities = {"articles": ["Article 21"], "cases": [], "concepts": []}

        fused = retriever_instance.reciprocal_rank_fusion(bm25_mock, vector_mock, entities, k_constant=60)
        assert len(fused) == 3

        # child_const_art_21_0 should be top ranked due to appearing in both + entity boost
        top_item = fused[0]
        assert "art_21" in top_item["child_id"]
        assert top_item["rrf_score"] > 0.05  # Has entity boost added

    def test_retrieve_pipeline_top_k(self, retriever_instance):
        """Test full HybridRRFRetriever.retrieve pipeline on 'Article 21 privacy'."""
        output = retriever_instance.retrieve("Article 21 privacy", top_k=4)

        assert "query" in output
        assert output["query"] == "Article 21 privacy"
        assert "entities" in output
        assert "results" in output

        results = output["results"]
        assert len(results) == 4

        # Validate schema of each retrieved item
        for item in results:
            assert "child_id" in item
            assert "child_text" in item
            assert len(item["child_text"]) > 0
            assert "parent_id" in item
            assert "parent_data" in item
            assert isinstance(item["parent_data"], dict)
            assert len(item["parent_data"]) > 0
            assert "rrf_score" in item
            assert "bm25_rank" in item
            assert "vector_rank" in item
            assert "doc_type" in item

    def test_retrieve_parent_hydration(self, retriever_instance):
        """Ensure retrieved results hydrate full parent documents."""
        output = retriever_instance.retrieve("basic structure doctrine Kesavananda Bharati", top_k=3)
        assert len(output["results"]) > 0
        first_doc = output["results"][0]
        pdata = first_doc["parent_data"]
        assert "full_text" in pdata
        assert len(pdata["full_text"]) > 50


# =========================================================================
# 6. MultiAgentRouter & HeuristicLegalSynthesizer Baseline Tests
# =========================================================================

class TestAgentsBaseline:
    """Verifies query classification, fallback synthesizer, and agent execution."""

    def test_classify_query_case_law(self, router_instance):
        """Query with case name or precedent keyword routes to case_law_agent."""
        entities = {"articles": [], "cases": ["Kesavananda Bharati"], "concepts": []}
        agent = router_instance.classify_query("Explain the judgment in Kesavananda Bharati", entities)
        assert agent == "case_law_agent"

    def test_classify_query_article(self, router_instance):
        """Query with constitutional article routes to article_agent."""
        entities = {"articles": ["Article 21"], "cases": [], "concepts": []}
        agent = router_instance.classify_query("State the constitutional text of Article 21", entities)
        assert agent == "article_agent"

    def test_classify_query_explanation(self, router_instance):
        """Query requesting simple explanation routes to explanation_agent."""
        entities = {"articles": [], "cases": [], "concepts": []}
        agent = router_instance.classify_query("Explain in simple terms what right to liberty means", entities)
        assert agent == "explanation_agent"

    def test_classify_query_override_mode(self, router_instance):
        """Override mode explicitly chooses designated agent."""
        entities = {"articles": [], "cases": [], "concepts": []}
        assert router_instance.classify_query("any query", entities, override_mode="Case-Law Agent") == "case_law_agent"
        assert router_instance.classify_query("any query", entities, override_mode="Article Agent") == "article_agent"
        assert router_instance.classify_query("any query", entities, override_mode="Explanation Agent") == "explanation_agent"

    def test_heuristic_synthesizer_article_mode(self):
        """HeuristicLegalSynthesizer generates structured markdown for article_agent."""
        mock_docs = [{
            "child_text": "Article 21: Protection of life and personal liberty",
            "parent_data": {
                "doc_type": "constitution",
                "article_number": "Article 21",
                "title": "Protection of Life and Personal Liberty",
                "part": "Part III",
                "category": "Fundamental Right",
                "raw_text": "No person shall be deprived of his life or personal liberty except according to procedure established by law.",
                "explanation": "Guarantees right to live with dignity.",
                "historical_context": "Drafted by Constituent Assembly."
            }
        }]
        entities = {"articles": ["Article 21"], "cases": [], "concepts": []}
        synth_text = HeuristicLegalSynthesizer.synthesize("article_agent", "What is Article 21?", mock_docs, entities)

        assert "Constitutional Article Analysis" in synth_text
        assert "Article 21" in synth_text
        assert "Guarantees right to live with dignity." in synth_text

    def test_heuristic_synthesizer_case_mode(self):
        """HeuristicLegalSynthesizer generates structured markdown for case_law_agent."""
        mock_docs = [{
            "child_text": "Puttaswamy privacy judgment",
            "parent_data": {
                "doc_type": "judgment",
                "case_name": "Justice K.S. Puttaswamy v. Union of India",
                "citation": "(2017) 10 SCC 1",
                "year": 2017,
                "bench": "9-Judge Bench",
                "articles_referred": ["Article 21"],
                "facts": "Aadhaar challenge.",
                "ratio_decidendi": "Privacy is fundamental under Article 21.",
                "verdict": "Unanimous declaration.",
                "key_takeaways": ["Milestone for informational privacy."]
            }
        }]
        entities = {"articles": [], "cases": ["Puttaswamy"], "concepts": ["privacy"]}
        synth_text = HeuristicLegalSynthesizer.synthesize("case_law_agent", "Explain Puttaswamy", mock_docs, entities)

        assert "Supreme Court Case-Law & Precedents Analysis" in synth_text
        assert "Puttaswamy" in synth_text
        assert "Ratio Decidendi" in synth_text

    def test_heuristic_synthesizer_empty_context(self):
        """HeuristicLegalSynthesizer returns graceful notice when context is empty."""
        synth_text = HeuristicLegalSynthesizer.synthesize("article_agent", "unknown query", [], {})
        assert "Context Notice" in synth_text
        assert "No matching constitutional articles" in synth_text

    def test_agent_execution_returns_expected_structure(self, router_instance):
        """Execute agent returns valid dictionary with all metadata fields."""
        mock_docs = [{
            "child_text": "Sample passage",
            "parent_data": {
                "doc_type": "constitution",
                "article_number": "Article 14",
                "title": "Equality before law",
                "part": "Part III",
                "category": "Fundamental Right",
                "raw_text": "The State shall not deny to any person equality before the law."
            }
        }]
        entities = {"articles": ["Article 14"], "cases": [], "concepts": []}
        res = router_instance.execute_agent("article_agent", "What is Article 14?", mock_docs, entities)

        assert isinstance(res, dict)
        assert res["agent_type"] == "article_agent"
        assert "agent_name" in res
        assert "response" in res and len(res["response"]) > 0
        assert "query" in res
        assert "entities" in res
        assert "source_docs" in res
        assert "used_llm" in res
        assert "model_name" in res
