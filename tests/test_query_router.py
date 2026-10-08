"""
Unit tests for Specialized NLP Query Router (Stage 4).
Verifies deterministic routing decisions, parameter configuration,
and handling of various legal intent types and out-of-scope queries.
"""

import pytest
from routing.query_router import QueryRouter, RoutingDecision, get_query_router


@pytest.fixture
def router():
    return QueryRouter()


class TestQueryRouter:
    """Verifies deterministic NLP Query Routing behavior."""

    def test_router_singleton_factory(self):
        """Ensure get_query_router returns a valid QueryRouter singleton."""
        r1 = get_query_router()
        r2 = get_query_router()
        assert isinstance(r1, QueryRouter)
        assert r1 is r2

    def test_route_article_lookup_query(self, router):
        """Article lookup query routes to ARTICLE_SEARCH with constitutional filtering."""
        decision = router.route(
            normalized_query="What is Article 21 of the Constitution?",
            language="en",
            legal_entities={"ARTICLE": ["Article 21"], "CASE": []},
            linked_entities=[{"entity_id": "ARTICLE_21", "canonical_name": "Article 21"}],
            intent="ARTICLE_LOOKUP",
            expanded_query="Article 21 life liberty procedure established by law",
        )

        assert isinstance(decision, RoutingDecision)
        assert decision.strategy == "ARTICLE_SEARCH"
        assert decision.filter_doc_type == "constitution"
        assert decision.recommended_agent == "article_agent"
        assert decision.is_out_of_scope is False
        assert decision.use_bm25 is True
        assert decision.use_dense is True
        assert decision.use_reranker is True
        assert decision.entity_boost_weight >= 0.15
        assert any("constitutional provisions" in r for r in decision.reasons)

    def test_route_case_law_query(self, router):
        """Case law query routes to CASE_SEARCH with judgment filtering."""
        decision = router.route(
            normalized_query="Explain Puttaswamy privacy judgment",
            language="en",
            legal_entities={"ARTICLE": [], "CASE": ["Puttaswamy"]},
            linked_entities=[{"entity_id": "CASE_PUTTASWAMY_2017", "canonical_name": "Puttaswamy"}],
            intent="CASE_LAW_QUERY",
            expanded_query="Puttaswamy privacy judgment right to privacy",
        )

        assert decision.strategy == "CASE_SEARCH"
        assert decision.filter_doc_type == "judgment"
        assert decision.recommended_agent == "case_law_agent"
        assert decision.is_out_of_scope is False
        assert decision.use_entity_boost is True

    def test_route_case_comparison_query(self, router):
        """Comparison query routes to COMPARISON_SEARCH with expanded candidate pool."""
        decision = router.route(
            normalized_query="Compare Kesavananda Bharati and Minerva Mills",
            language="en",
            legal_entities={"ARTICLE": [], "CASE": ["Kesavananda Bharati", "Minerva Mills"]},
            linked_entities=[
                {"entity_id": "CASE_KESAVANANDA_1973"},
                {"entity_id": "CASE_MINERVA_1980"}
            ],
            intent="CASE_COMPARISON",
            expanded_query="Compare Kesavananda Bharati Minerva Mills basic structure",
        )

        assert decision.strategy == "COMPARISON_SEARCH"
        assert decision.filter_doc_type == "judgment"
        assert decision.recommended_agent == "case_law_agent"
        assert decision.requires_comparison is True
        assert decision.top_k_candidates >= 35
        assert decision.final_top_k >= 6

    def test_route_rights_and_explanation_query(self, router):
        """Rights inquiry routes to RIGHTS_SEARCH with cross-corpus search and expanded query."""
        decision = router.route(
            normalized_query="Explain the right to clean environment",
            language="en",
            legal_entities={"ARTICLE": [], "CASE": [], "RIGHT": ["right to clean environment"]},
            linked_entities=[],
            intent="RIGHTS_QUERY",
            expanded_query="Explain right to clean environment Article 21 life liberty pollution",
        )

        assert decision.strategy == "RIGHTS_SEARCH"
        assert decision.filter_doc_type is None  # Cross-corpus
        assert decision.recommended_agent == "explanation_agent"
        assert decision.retrieval_query == "Explain right to clean environment Article 21 life liberty pollution"

    def test_route_out_of_scope_query(self, router):
        """Out of scope queries immediately route to OUT_OF_SCOPE with retrieval disabled."""
        decision = router.route(
            normalized_query="How do I bake a chocolate cake?",
            language="en",
            legal_entities={"ARTICLE": [], "CASE": []},
            linked_entities=[],
            intent="OUT_OF_SCOPE",
            expanded_query="How do I bake a chocolate cake?",
        )

        assert decision.strategy == "OUT_OF_SCOPE"
        assert decision.is_out_of_scope is True
        assert decision.use_bm25 is False
        assert decision.use_dense is False
        assert decision.use_reranker is False

    def test_route_empty_query(self, router):
        """Empty query routes safely to OUT_OF_SCOPE."""
        decision = router.route(
            normalized_query="",
            language="en",
        )
        assert decision.strategy == "OUT_OF_SCOPE"
        assert decision.is_out_of_scope is True

    def test_route_unsupported_language(self, router):
        """Unsupported language routes to OUT_OF_SCOPE."""
        decision = router.route(
            normalized_query="Some foreign language text",
            language={"language": "unknown", "is_supported": False},
            intent="LEGAL_EXPLANATION",
        )
        assert decision.strategy == "OUT_OF_SCOPE"
        assert decision.is_out_of_scope is True

    def test_route_from_nlp_context_dict(self, router):
        """Convenience method accepts consolidated NLP dictionary."""
        nlp_ctx = {
            "normalized_query": "Procedure to amend the Constitution under Article 368",
            "language": "en",
            "entities": {"ARTICLE": ["Article 368"], "CASE": []},
            "linked_entities": [{"entity_id": "ARTICLE_368"}],
            "intent": "CONSTITUTIONAL_PROCEDURE",
            "expanded_query": "Procedure to amend Constitution Article 368 amendment power",
        }
        decision = router.route_from_nlp_context(nlp_ctx)
        assert decision.strategy == "ARTICLE_SEARCH"
        assert decision.filter_doc_type == "constitution"
        assert decision.to_dict()["strategy"] == "ARTICLE_SEARCH"
