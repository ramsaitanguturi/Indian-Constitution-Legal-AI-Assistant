"""
Unit Tests for the NLP Pipeline Diagnostic Inspector.

Verifies:
1. Extraction of all 10 diagnostic pipeline stages.
2. Graceful handling of complete, abstained, partial, and empty results.
3. Security scrubbing of API keys and private secrets.
4. Explicit disclosure of uncalibrated heuristic confidence vs posterior probabilities.
5. Legacy agent dictionary compatibility.
"""

import pytest
from rag.pipeline import PipelineResult
from rag.pipeline_inspector import extract_pipeline_diagnostics, scrub_sensitive_text


@pytest.fixture
def sample_pipeline_result():
    """Provides a realistic complete PipelineResult object for testing."""
    return PipelineResult(
        original_query="What does Article 21 guarantee?",
        normalized_query="what does article 21 guarantee",
        language={"language": "en", "is_english": True, "confidence": 0.99},
        intent={"intent": "ARTICLE_LOOKUP", "confidence": 0.92, "routing_mode": "hybrid_classifier"},
        entities={"ARTICLE": ["Article 21"]},
        linked_entities=[{
            "surface_text": "Article 21",
            "canonical_id": "parent_const_art_021",
            "entity_type": "ARTICLE",
            "score": 1.0,
            "is_nil": False,
        }],
        expanded_query="what does article 21 guarantee (due process, life, personal liberty)",
        routing_decision={
            "strategy": "ARTICLE_SEARCH",
            "use_bm25": True,
            "use_dense": True,
            "use_rrf": True,
            "use_entity_boost": True,
            "entity_boost_weight": 0.15,
            "use_reranker": True,
            "final_top_k": 5,
        },
        retrieved_chunks=[{
            "chunk_id": "child_const_art_021_0",
            "parent_id": "parent_const_art_021",
            "score": 0.88,
            "rank": 1,
            "doc_type": "constitution",
            "text": "No person shall be deprived of his life or personal liberty except according to procedure established by law.",
            "metadata": {"bm25_rank": 1, "vector_rank": 2, "entity_boosted": True},
        }],
        reranked_chunks=[{
            "chunk_id": "child_const_art_021_0",
            "parent_id": "parent_const_art_021",
            "score": 0.95,
            "rank": 1,
            "doc_type": "constitution",
            "text": "No person shall be deprived of his life or personal liberty except according to procedure established by law.",
            "rerank_score": 0.95,
        }],
        parent_context={
            "parent_count": 1,
            "parents": [{
                "parent_id": "parent_const_art_021",
                "doc_type": "constitution",
                "title": "Protection of life and personal liberty",
                "article_number": "Article 21",
                "supporting_children": [{"chunk_id": "child_const_art_021_0"}],
            }],
        },
        citations=[{"citation_text": "Article 21 of the Constitution"}],
        generated_answer="Article 21 protects life and personal liberty.",
        citation_validation={
            "valid": True,
            "citations_checked": 1,
            "valid_citations": ["Article 21 of the Constitution"],
            "invalid_citations": [],
            "unsupported_claims": [],
            "summary": "All citations verified.",
        },
        confidence={
            "confidence_score": 0.92,
            "confidence_level": "HIGH",
            "is_calibrated": False,
            "explanation": "High confidence based on strong retrieval and verified citation.",
            "signal_breakdown": {
                "retrieval_strength": {
                    "weight": 0.25,
                    "score": 0.95,
                    "weighted_value": 0.2375,
                    "details": "Strong top candidate score",
                }
            },
        },
        abstained=False,
        abstention_reason=None,
    )


class TestPipelineInspectorExtraction:
    """Verifies diagnostic extraction from PipelineResult and dictionaries."""

    def test_extract_all_10_stages(self, sample_pipeline_result):
        diag = extract_pipeline_diagnostics(sample_pipeline_result)
        assert diag is not None

        # 1. Query Preprocessing
        assert diag["query_preprocessing"]["original_query"] == "What does Article 21 guarantee?"
        assert diag["query_preprocessing"]["normalized_query"] == "what does article 21 guarantee"

        # 2. Language Identification
        assert diag["query_preprocessing"]["language_code"] == "en"
        assert diag["query_preprocessing"]["is_english"] is True

        # 3. Entity Extraction & Linking
        assert "ARTICLE" in diag["entity_extraction_and_linking"]["entities_by_category"]
        assert len(diag["entity_extraction_and_linking"]["linked_entities"]) == 1
        assert diag["entity_extraction_and_linking"]["linked_entities"][0]["canonical_id"] == "parent_const_art_021"

        # 4. Intent & Routing
        assert diag["intent_and_routing"]["predicted_intent"] == "ARTICLE_LOOKUP"
        assert diag["intent_and_routing"]["routing_strategy"] == "ARTICLE_SEARCH"
        assert diag["intent_and_routing"]["use_bm25"] is True
        assert diag["intent_and_routing"]["use_reranker"] is True

        # 5. Query Expansion
        assert diag["query_expansion"]["is_expanded"] is True

        # 6. Retrieval Candidates & Scores
        assert len(diag["retrieval_candidates"]) == 1
        assert diag["retrieval_candidates"][0]["parent_id"] == "parent_const_art_021"

        # 7. Entity Boost & Reranking Info
        assert diag["reranking_and_boost_info"]["entity_boost_enabled"] is True
        assert diag["reranking_and_boost_info"]["boost_weight"] == 0.15

        # 8. Recovered Parent Context
        assert diag["parent_recovery"]["parent_count"] == 1

        # 9. Citation Validation Outcome
        assert diag["citation_validation"]["valid"] is True
        assert diag["citation_validation"]["citations_checked"] == 1

        # 10. Confidence & Abstention
        assert diag["confidence_and_abstention"]["confidence_score"] == 0.92
        assert diag["confidence_and_abstention"]["confidence_level"] == "HIGH"
        assert diag["confidence_and_abstention"]["is_calibrated"] is False
        assert diag["confidence_and_abstention"]["abstained"] is False
        assert len(diag["confidence_and_abstention"]["signals"]) == 1

    def test_extract_abstained_result(self):
        abstained_res = PipelineResult(
            original_query="How do I bake bread?",
            normalized_query="how do i bake bread",
            language={"language": "en", "is_english": True, "confidence": 1.0},
            intent={"intent": "OUT_OF_SCOPE", "confidence": 0.95, "routing_mode": "hybrid_classifier"},
            entities={},
            linked_entities=[],
            expanded_query="how do i bake bread",
            routing_decision={"strategy": "OUT_OF_SCOPE"},
            retrieved_chunks=[],
            reranked_chunks=[],
            parent_context={"parents": [], "parent_count": 0},
            citations=[],
            generated_answer="This system only answers queries related to the Constitution of India.",
            citation_validation={"valid": True, "citations_checked": 0, "invalid_citations": [], "unsupported_claims": [], "summary": "Abstained."},
            confidence={"confidence_score": 0.0, "confidence_level": "VERY_LOW", "is_calibrated": False, "explanation": "Out of scope."},
            abstained=True,
            abstention_reason="QUERY_OUT_OF_SCOPE",
        )
        diag = extract_pipeline_diagnostics(abstained_res)
        assert diag["confidence_and_abstention"]["abstained"] is True
        assert diag["confidence_and_abstention"]["abstention_reason"] == "QUERY_OUT_OF_SCOPE"
        assert diag["intent_and_routing"]["predicted_intent"] == "OUT_OF_SCOPE"
        assert len(diag["retrieval_candidates"]) == 0

    def test_extract_partial_dict(self):
        partial = {"original_query": "Test partial query"}
        diag = extract_pipeline_diagnostics(partial)
        assert diag["query_preprocessing"]["original_query"] == "Test partial query"
        assert diag["confidence_and_abstention"]["is_calibrated"] is False
        assert diag["confidence_and_abstention"]["abstained"] is False

    def test_extract_float_signal_breakdown(self):
        result_with_floats = {
            "original_query": "Article 21",
            "confidence": {
                "confidence_score": 0.88,
                "confidence_level": "HIGH",
                "is_calibrated": False,
                "signal_breakdown": {
                    "retrieval_strength": 0.95,
                    "evidence_count": 0.80,
                },
                "signal_weights": {
                    "retrieval_strength": 0.25,
                    "evidence_count": 0.15,
                },
            },
        }
        diag = extract_pipeline_diagnostics(result_with_floats)
        signals = diag["confidence_and_abstention"]["signals"]
        assert len(signals) == 2
        assert signals[0]["Signal"] == "Retrieval Strength"
        assert signals[0]["Raw Score"] == 0.95
        assert signals[0]["Weight"] == 0.25
        assert signals[0]["Contribution"] == 0.2375

    def test_scrub_sensitive_api_keys(self):
        sensitive_text = "Query mentioning AIzaSyB1234567890abcdef1234567890abcdef and sk-1234567890abcdef12345678"
        scrubbed = scrub_sensitive_text(sensitive_text)
        assert "AIzaSyB1234567890abcdef1234567890abcdef" not in scrubbed
        assert "[REDACTED_API_KEY]" in scrubbed

        diag = extract_pipeline_diagnostics({
            "original_query": "What is AIzaSyB1234567890abcdef1234567890abcdef?",
        })
        assert "AIzaSyB" not in diag["query_preprocessing"]["original_query"]
