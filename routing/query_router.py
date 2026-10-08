"""
Specialized NLP Query Router for Indian Constitutional Legal AI.
Deterministically decides retrieval strategy, candidate depth, and component weights
based on Stage 2 NLP query understanding outputs:
- normalized query
- language
- legal entities
- linked entities
- intent classification
- expanded query

This is a specialized, deterministic NLP routing component, not an LLM agent.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Union

from config import (
    RETRIEVAL_CANDIDATE_POOL,
    FINAL_TOP_K,
    ENTITY_BOOST_WEIGHT,
)


@dataclass
class RoutingDecision:
    """
    Deterministic routing decision dictating retrieval and generation execution.
    """
    strategy: str  # ARTICLE_SEARCH, CASE_SEARCH, COMPARISON_SEARCH, RIGHTS_SEARCH, PROCEDURE_SEARCH, HYBRID_SEARCH, OUT_OF_SCOPE
    retrieval_query: str
    filter_doc_type: Optional[str]  # "constitution", "judgment", or None
    use_bm25: bool = True
    use_dense: bool = True
    use_rrf: bool = True
    use_entity_boost: bool = True
    use_reranker: bool = True
    entity_boost_weight: float = ENTITY_BOOST_WEIGHT
    top_k_candidates: int = RETRIEVAL_CANDIDATE_POOL
    final_top_k: int = FINAL_TOP_K
    recommended_agent: str = "explanation_agent"
    requires_comparison: bool = False
    is_out_of_scope: bool = False
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert decision to serializable dictionary."""
        return asdict(self)


class QueryRouter:
    """
    Deterministic, rule-driven NLP router for constitutional queries.
    Maps fine-grained intent, entity distributions, and linguistic signals to
    optimal retrieval parameters without stochastic LLM invocations.
    """

    def __init__(
        self,
        default_candidate_pool: int = RETRIEVAL_CANDIDATE_POOL,
        default_final_top_k: int = FINAL_TOP_K,
        default_entity_boost_weight: float = ENTITY_BOOST_WEIGHT,
    ):
        self.default_candidate_pool = default_candidate_pool
        self.default_final_top_k = default_final_top_k
        self.default_entity_boost_weight = default_entity_boost_weight

    def route(
        self,
        normalized_query: str = "",
        language: Union[str, Dict[str, Any]] = "en",
        legal_entities: Optional[Dict[str, List[str]]] = None,
        linked_entities: Optional[List[Dict[str, Any]]] = None,
        intent: Union[str, Dict[str, Any]] = "LEGAL_EXPLANATION",
        expanded_query: str = "",
    ) -> RoutingDecision:
        """
        Deterministically produces a RoutingDecision from Stage 2 NLP signals.

        Args:
            normalized_query: Cleaned, preprocessed query text.
            language: Language code string or dictionary from language_detection.
            legal_entities: Extracted entity category map from legal_ner.
            linked_entities: List of canonical linked entity records from entity_linking.
            intent: Intent label string or dictionary from intent_classifier.
            expanded_query: Query expanded with controlled domain synonyms.

        Returns:
            RoutingDecision specifying the exact retrieval configuration.
        """
        reasons: List[str] = []

        # 1. Parse language signal
        lang_code = language.get("language", "en") if isinstance(language, dict) else str(language or "en")
        is_supported_lang = language.get("is_supported", True) if isinstance(language, dict) else (lang_code in ["en", "hi", "hinglish"])

        # 2. Parse intent label
        if isinstance(intent, dict):
            intent_label = intent.get("intent", "LEGAL_EXPLANATION")
            is_out_of_scope_flag = intent.get("is_out_of_scope", False)
        else:
            intent_label = str(intent or "LEGAL_EXPLANATION")
            is_out_of_scope_flag = (intent_label == "OUT_OF_SCOPE")

        entities = legal_entities or {}
        linked = linked_entities or []
        norm_q = normalized_query.strip()
        exp_q = expanded_query.strip() if expanded_query else norm_q

        # Extract counts of prominent entity types
        article_mentions = entities.get("ARTICLE", []) or entities.get("articles", [])
        case_mentions = entities.get("CASE", []) or entities.get("cases", [])
        amendment_mentions = entities.get("AMENDMENT", [])
        right_mentions = entities.get("RIGHT", [])
        concept_mentions = entities.get("LEGAL_CONCEPT", []) or entities.get("concepts", [])

        # 3. Guard against Empty Query or Out-of-Scope / Unsupported Language
        if not norm_q:
            reasons.append("Empty query received; routed to OUT_OF_SCOPE abstention.")
            return RoutingDecision(
                strategy="OUT_OF_SCOPE",
                retrieval_query=norm_q,
                filter_doc_type=None,
                use_bm25=False,
                use_dense=False,
                use_rrf=False,
                use_entity_boost=False,
                use_reranker=False,
                is_out_of_scope=True,
                recommended_agent="explanation_agent",
                reasons=reasons,
            )

        if is_out_of_scope_flag or intent_label == "OUT_OF_SCOPE" or not is_supported_lang:
            reasons.append(f"Query classified as OUT_OF_SCOPE (intent='{intent_label}', lang='{lang_code}').")
            return RoutingDecision(
                strategy="OUT_OF_SCOPE",
                retrieval_query=norm_q,
                filter_doc_type=None,
                use_bm25=False,
                use_dense=False,
                use_rrf=False,
                use_entity_boost=False,
                use_reranker=False,
                is_out_of_scope=True,
                recommended_agent="explanation_agent",
                reasons=reasons,
            )

        # 4. Decision: CASE COMPARISON
        if intent_label == "CASE_COMPARISON" or (len(case_mentions) >= 2):
            reasons.append("Case comparison intent or multiple landmark cases identified.")
            # For comparison, we need wider candidate pool and slightly more final results
            return RoutingDecision(
                strategy="COMPARISON_SEARCH",
                retrieval_query=exp_q,
                filter_doc_type="judgment",
                use_bm25=True,
                use_dense=True,
                use_rrf=True,
                use_entity_boost=True,
                use_reranker=True,
                entity_boost_weight=0.20,
                top_k_candidates=max(self.default_candidate_pool, 35),
                final_top_k=max(self.default_final_top_k, 6),
                recommended_agent="case_law_agent",
                requires_comparison=True,
                is_out_of_scope=False,
                reasons=reasons,
            )

        # 5. Decision: ARTICLE LOOKUP / AMENDMENT QUERY
        if (
            intent_label in ("ARTICLE_LOOKUP", "AMENDMENT_QUERY")
            or (article_mentions and not case_mentions and intent_label != "CASE_LAW_QUERY")
            or (amendment_mentions and not case_mentions)
        ):
            reasons.append(f"Query targets constitutional provisions or amendments (intent='{intent_label}', articles={article_mentions}).")
            # For exact article lookup, keep normalized query to avoid diluting specific article token
            target_q = norm_q if article_mentions else exp_q
            return RoutingDecision(
                strategy="ARTICLE_SEARCH",
                retrieval_query=target_q,
                filter_doc_type="constitution",
                use_bm25=True,
                use_dense=True,
                use_rrf=True,
                use_entity_boost=True,
                use_reranker=True,
                entity_boost_weight=0.20,
                top_k_candidates=self.default_candidate_pool,
                final_top_k=self.default_final_top_k,
                recommended_agent="article_agent",
                requires_comparison=False,
                is_out_of_scope=False,
                reasons=reasons,
            )

        # 6. Decision: CASE LAW / PRECEDENT QUERY
        if (
            intent_label in ("CASE_LAW_QUERY", "PRECEDENT_QUERY")
            or (case_mentions and not article_mentions)
        ):
            reasons.append(f"Query targets judicial precedent or case law (intent='{intent_label}', cases={case_mentions}).")
            target_q = norm_q if case_mentions else exp_q
            return RoutingDecision(
                strategy="CASE_SEARCH",
                retrieval_query=target_q,
                filter_doc_type="judgment",
                use_bm25=True,
                use_dense=True,
                use_rrf=True,
                use_entity_boost=True,
                use_reranker=True,
                entity_boost_weight=0.20,
                top_k_candidates=self.default_candidate_pool,
                final_top_k=self.default_final_top_k,
                recommended_agent="case_law_agent",
                requires_comparison=False,
                is_out_of_scope=False,
                reasons=reasons,
            )

        # 7. Decision: CONSTITUTIONAL PROCEDURE
        if intent_label == "CONSTITUTIONAL_PROCEDURE":
            reasons.append("Procedural constitutional query targeting governing state mechanisms.")
            return RoutingDecision(
                strategy="PROCEDURE_SEARCH",
                retrieval_query=exp_q,
                filter_doc_type="constitution",
                use_bm25=True,
                use_dense=True,
                use_rrf=True,
                use_entity_boost=bool(linked or article_mentions),
                use_reranker=True,
                entity_boost_weight=self.default_entity_boost_weight,
                top_k_candidates=self.default_candidate_pool,
                final_top_k=self.default_final_top_k,
                recommended_agent="article_agent",
                requires_comparison=False,
                is_out_of_scope=False,
                reasons=reasons,
            )

        # 8. Decision: RIGHTS / DEFINITION / LEGAL EXPLANATION
        if intent_label in ("RIGHTS_QUERY", "DEFINITION_QUERY", "LEGAL_EXPLANATION"):
            reasons.append(f"Conceptual inquiry into constitutional rights or doctrines (intent='{intent_label}').")
            # Cross-corpus search: both constitutional articles and precedent are essential
            return RoutingDecision(
                strategy="RIGHTS_SEARCH",
                retrieval_query=exp_q,
                filter_doc_type=None,
                use_bm25=True,
                use_dense=True,
                use_rrf=True,
                use_entity_boost=bool(linked or right_mentions or concept_mentions),
                use_reranker=True,
                entity_boost_weight=self.default_entity_boost_weight,
                top_k_candidates=self.default_candidate_pool,
                final_top_k=self.default_final_top_k,
                recommended_agent="explanation_agent",
                requires_comparison=False,
                is_out_of_scope=False,
                reasons=reasons,
            )

        # 9. Default: HYBRID SEARCH (Multi-document / general inquiry)
        reasons.append(f"General or multi-document constitutional question routed to full hybrid retrieval (intent='{intent_label}').")
        return RoutingDecision(
            strategy="HYBRID_SEARCH",
            retrieval_query=exp_q,
            filter_doc_type=None,
            use_bm25=True,
            use_dense=True,
            use_rrf=True,
            use_entity_boost=bool(linked or entities),
            use_reranker=True,
            entity_boost_weight=self.default_entity_boost_weight,
            top_k_candidates=self.default_candidate_pool,
            final_top_k=self.default_final_top_k,
            recommended_agent="explanation_agent",
            requires_comparison=False,
            is_out_of_scope=False,
            reasons=reasons,
        )

    def route_from_nlp_context(self, nlp_context: Dict[str, Any]) -> RoutingDecision:
        """
        Convenience router accepting the consolidated output dictionary of Stage 2.
        """
        return self.route(
            normalized_query=nlp_context.get("normalized_query", nlp_context.get("query", "")),
            language=nlp_context.get("language", "en"),
            legal_entities=nlp_context.get("entities", nlp_context.get("legal_entities")),
            linked_entities=nlp_context.get("linked_entities"),
            intent=nlp_context.get("intent", "LEGAL_EXPLANATION"),
            expanded_query=nlp_context.get("expanded_query", ""),
        )


# Global singleton instance
_ROUTER_INSTANCE: Optional[QueryRouter] = None


def get_query_router() -> QueryRouter:
    """Returns or lazily instantiates the singleton QueryRouter instance."""
    global _ROUTER_INSTANCE
    if _ROUTER_INSTANCE is None:
        _ROUTER_INSTANCE = QueryRouter()
    return _ROUTER_INSTANCE
