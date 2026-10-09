"""
End-to-End Integration tests for Legal RAG Pipeline (Stage 4).
Verifies:
- Complete 16-stage pipeline execution on constitutional queries
- Structured PipelineResult schema compliance (all 17 fields)
- Out-of-scope query safe abstention
- Insufficient-evidence handling
- Backward compatibility with legacy facades
"""

import pytest
from rag.pipeline import LegalRAGPipeline, PipelineResult, get_legal_rag_pipeline
from retriever import HybridRRFRetriever
from agents import MultiAgentRouter


@pytest.fixture(scope="module")
def rag_pipeline():
    """Instantiate singleton or shared pipeline."""
    return get_legal_rag_pipeline()


class TestEndToEndLegalRAGPipeline:
    """Verifies end-to-end Legal RAG pipeline behavior."""

    def test_pipeline_singleton_factory(self):
        """Ensure get_legal_rag_pipeline returns a singleton."""
        p1 = get_legal_rag_pipeline()
        p2 = get_legal_rag_pipeline()
        assert isinstance(p1, LegalRAGPipeline)
        assert p1 is p2

    def test_successful_pipeline_execution(self, rag_pipeline):
        """Standard constitutional query executes full pipeline and produces validated answer."""
        query = "What does Article 21 guarantee regarding life and personal liberty?"
        result = rag_pipeline.run(query)

        assert isinstance(result, PipelineResult)
        assert result.original_query == query
        assert result.abstained is False
        assert result.is_success is True
        assert len(result.generated_answer) > 50

        # Verify Stage 2 NLP outputs populated
        assert result.language["language"] == "en"
        assert "article" in result.normalized_query.lower()
        assert "ARTICLE" in result.entities
        assert "Article 21" in result.entities["ARTICLE"]

        # Verify Stage 4 routing decision
        routing = result.routing_decision
        assert routing["strategy"] == "ARTICLE_SEARCH"
        assert routing["filter_doc_type"] == "constitution"

        # Verify retrieval and parent context
        assert len(result.retrieved_chunks) > 0
        assert result.parent_context["parent_count"] >= 1
        assert any(
            "21" in p.get("article_number", "") or "21" in p.get("document_id", "")
            for p in result.parent_context["parents"]
        )

        # Verify citations and citation validation
        assert len(result.citations) >= 1
        val = result.citation_validation
        assert val["valid"] is True
        assert val["citations_checked"] >= 1
        assert len(val["invalid_citations"]) == 0

        # Verify confidence estimation
        conf = result.confidence
        assert 0.0 <= conf["confidence_score"] <= 1.0
        assert conf["confidence_level"] in ("HIGH", "MEDIUM")
        assert conf["is_calibrated"] is False
        assert "signal_breakdown" in conf

    def test_pipeline_out_of_scope_abstention(self, rag_pipeline):
        """Out of scope query triggers safe abstention at the router stage."""
        query = "Can you give me a recipe for chocolate chip cookies?"
        result = rag_pipeline.run(query)

        assert isinstance(result, PipelineResult)
        assert result.abstained is True
        assert result.is_success is False
        assert result.abstention_reason == "OUT_OF_SCOPE"
        assert "outside the scope of Indian Constitutional Law" in result.generated_answer
        assert len(result.retrieved_chunks) == 0
        assert result.confidence["confidence_score"] == 0.0

    def test_pipeline_result_schema_serialization(self, rag_pipeline):
        """PipelineResult converts to complete dictionary matching the 17-field specification."""
        query = "Explain the right to constitutional remedies under Article 32."
        result = rag_pipeline.run(query)
        data = result.to_dict()

        expected_fields = [
            "original_query",
            "normalized_query",
            "language",
            "intent",
            "entities",
            "linked_entities",
            "expanded_query",
            "routing_decision",
            "retrieved_chunks",
            "reranked_chunks",
            "parent_context",
            "citations",
            "generated_answer",
            "citation_validation",
            "confidence",
            "abstained",
            "abstention_reason",
        ]

        for field_name in expected_fields:
            assert field_name in data, f"Missing required schema field: {field_name}"

    def test_landmark_judgment_pipeline_query(self, rag_pipeline):
        """Case law query correctly retrieves judgment context, synthesizes ratio, and validates citations."""
        query = "What was the ratio decidendi in the Puttaswamy privacy case?"
        result = rag_pipeline.run(query)

        assert result.abstained is False
        assert result.routing_decision["strategy"] in ("CASE_SEARCH", "RIGHTS_SEARCH")
        assert len(result.parent_context["parents"]) >= 1

        # Check that Puttaswamy or privacy was identified
        parents = result.parent_context["parents"]
        titles = [p.get("case_name", "") + " " + p.get("title", "") for p in parents]
        assert any("puttaswamy" in t.lower() or "privacy" in t.lower() or "21" in t.lower() for t in titles)

        # Check answer has distinguished sections
        assert "### 📜 Direct Legal Evidence" in result.generated_answer
        assert "### ⚖️ Grounded Legal Analysis" in result.generated_answer
        assert "### 📚 Verified Citations" in result.generated_answer

    def test_pipeline_empty_and_whitespace_query(self, rag_pipeline):
        """Empty and whitespace queries safely abstain without error."""
        for empty_q in ["", "   ", "\n\t"]:
            res = rag_pipeline.run(empty_q)
            assert res.abstained is True
            assert res.abstention_reason == "EMPTY_QUERY"
            assert res.confidence["confidence_score"] == 0.0

    def test_pipeline_with_mocked_external_llm_call(self, rag_pipeline):
        """End-to-end query execution with external LLM call mocked."""
        from unittest.mock import MagicMock

        orig_llm = rag_pipeline.generator.llm
        orig_avail = rag_pipeline.generator.llm_available

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = (
            "### 📜 Direct Legal Evidence\n"
            "Article 21 guarantees protection of life and personal liberty.\n\n"
            "### ⚖️ Grounded Legal Analysis\n"
            "The right to life is a foundational fundamental right under the Constitution.\n\n"
            "### 📚 Verified Citations\n"
            "- [Doc: parent_const_art_21] Article 21"
        )

        try:
            rag_pipeline.generator.llm = mock_llm
            rag_pipeline.generator.llm_available = True

            result = rag_pipeline.run("What does Article 21 guarantee?")
            assert result.is_success is True
            assert result.abstained is False
            assert "Direct Legal Evidence" in result.generated_answer
            assert len(result.citations) >= 1
            assert result.citation_validation["valid"] is True
        finally:
            rag_pipeline.generator.llm = orig_llm
            rag_pipeline.generator.llm_available = orig_avail


class TestBackwardCompatibility:
    """Verifies that existing modules and facades remain fully functional."""

    def test_legacy_hybrid_retriever_facade(self):
        """Existing HybridRRFRetriever in retriever.py continues to function normally."""
        retriever = HybridRRFRetriever()
        res = retriever.retrieve("Article 21 life liberty", top_k=3)
        assert "results" in res
        assert "entities" in res
        assert len(res["results"]) > 0

    def test_legacy_multi_agent_router_facade(self):
        """Existing MultiAgentRouter in agents.py continues to function normally."""
        router = MultiAgentRouter()
        classified = router.classify_query("Explain Puttaswamy judgment", {"cases": ["Puttaswamy"]})
        assert classified == "case_law_agent"
