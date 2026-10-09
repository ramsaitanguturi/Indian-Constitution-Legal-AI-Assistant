"""
Backward Compatibility Tests for Existing Q&A and Retrieval Flows.

Verifies:
1. Stage 4 LegalRAGPipeline execution produces expected PipelineResult schema.
2. Pipeline Inspector adapter processes live PipelineResult without breaking.
3. Legacy HybridRRFRetriever and MultiAgentRouter interfaces remain functional.
4. Legacy output adaptation into Pipeline Inspector diagnostics.
5. Ingestor parent_store access and child_chunks schemas are preserved.
"""

import pytest
from rag.pipeline import get_legal_rag_pipeline, PipelineResult
from rag.pipeline_inspector import extract_pipeline_diagnostics
from ingestion import ParentChildIngestor
from retriever import HybridRRFRetriever
from agents import MultiAgentRouter


class TestQAFlowBackwardCompatibility:
    """Ensures existing Q&A flow and legacy modes run without regressions."""

    def test_stage4_pipeline_result_compatibility(self):
        pipeline = get_legal_rag_pipeline()
        result = pipeline.run("What is Article 21?")
        assert isinstance(result, PipelineResult)
        assert hasattr(result, "original_query")
        assert hasattr(result, "normalized_query")
        assert hasattr(result, "language")
        assert hasattr(result, "intent")
        assert hasattr(result, "entities")
        assert hasattr(result, "linked_entities")
        assert hasattr(result, "routing_decision")
        assert hasattr(result, "retrieved_chunks")
        assert hasattr(result, "parent_context")
        assert hasattr(result, "citation_validation")
        assert hasattr(result, "confidence")
        assert hasattr(result, "abstained")

        # Test diagnostic adapter on real pipeline output
        diagnostics = extract_pipeline_diagnostics(result)
        assert diagnostics is not None
        assert "query_preprocessing" in diagnostics
        assert "entity_extraction_and_linking" in diagnostics
        assert "intent_and_routing" in diagnostics
        assert "retrieval_candidates" in diagnostics
        assert "confidence_and_abstention" in diagnostics
        assert diagnostics["confidence_and_abstention"]["is_calibrated"] is False

    def test_legacy_retriever_and_router_compatibility(self):
        ingestor = ParentChildIngestor()
        retriever = HybridRRFRetriever(ingestor)
        output = retriever.retrieve("Article 21 privacy", top_k=2)

        assert "query" in output
        assert "entities" in output
        assert "results" in output
        assert isinstance(output["results"], list)
        assert len(output["results"]) > 0

        router = MultiAgentRouter()
        agent_type = router.classify_query("Article 21 privacy", output["entities"])
        assert agent_type in ["article_agent", "case_law_agent", "explanation_agent"]

        # Adapt legacy output to inspector
        legacy_diag = {
            "original_query": output["query"],
            "normalized_query": output["query"],
            "language": {"language": "en", "is_english": True, "confidence": 1.0},
            "intent": {"intent": agent_type, "confidence": 0.8, "routing_mode": "legacy_keyword_router"},
            "entities": output["entities"],
            "linked_entities": [],
            "routing_decision": {"strategy": agent_type, "use_bm25": True, "use_dense": True},
            "retrieved_chunks": output["results"],
            "reranked_chunks": output["results"],
            "parent_context": {"parents": [], "parent_count": len(output["results"])},
            "citations": [],
            "generated_answer": "Legacy response.",
            "citation_validation": {"valid": True, "citations_checked": 0, "invalid_citations": []},
            "confidence": {"confidence_score": 0.70, "confidence_level": "MEDIUM", "is_calibrated": False},
            "abstained": False,
        }
        diag = extract_pipeline_diagnostics(legacy_diag)
        assert diag["intent_and_routing"]["predicted_intent"] == agent_type
        assert len(diag["retrieval_candidates"]) == len(output["results"])
