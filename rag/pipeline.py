"""
End-to-End Legal RAG Pipeline for Indian Constitutional Question Answering.
Orchestrates:
1. Language Detection
2. Preprocessing
3. Legal NER
4. Entity Linking
5. Intent Classification
6. Query Expansion
7. Specialized NLP Query Router
8. BM25 + Dense Retrieval
9. Reciprocal Rank Fusion (RRF)
10. Legal Entity-Aware Boost
11. Cross-Encoder Reranking
12. Parent Context Recovery
13. Grounded Generator
14. Citation Validator
15. Confidence Estimation
16. Multi-Stage Abstention Decision
"""

import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional

from nlp.language_detection import detect_language
from nlp.preprocessing import normalize_legal_text
from nlp.legal_ner import get_legal_ner
from nlp.entity_linking import get_entity_linker
from nlp.intent_classifier import get_intent_classifier
from nlp.query_expansion import get_query_expander
from routing.query_router import get_query_router, RoutingDecision
from retrieval.hybrid_retriever import HybridRetriever
from rag.parent_child import ParentChildRecovery
from rag.generator import GroundedGenerator
from rag.citation_validator import CitationValidator
from rag.confidence import ConfidenceEstimator
from rag.abstention import AbstentionManager


@dataclass
class PipelineResult:
    """
    Structured outcome of the end-to-end Legal RAG pipeline.
    """
    original_query: str
    normalized_query: str
    language: Dict[str, Any]
    intent: Dict[str, Any]
    entities: Dict[str, List[str]]
    linked_entities: List[Dict[str, Any]]
    expanded_query: str
    routing_decision: Dict[str, Any]
    retrieved_chunks: List[Dict[str, Any]]
    reranked_chunks: List[Dict[str, Any]]
    parent_context: Dict[str, Any]
    citations: List[Dict[str, Any]]
    generated_answer: str
    citation_validation: Dict[str, Any]
    confidence: Dict[str, Any]
    abstained: bool
    abstention_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert pipeline result to a fully serializable dictionary."""
        return asdict(self)

    @property
    def is_success(self) -> bool:
        """True if pipeline produced a validated answer without abstention."""
        return not self.abstained and bool(self.generated_answer)


class LegalRAGPipeline:
    """
    Unified end-to-end Legal RAG pipeline orchestrator.
    Directly leverages modular Stage 2 and Stage 3 components.
    """

    def __init__(
        self,
        retriever: Optional[HybridRetriever] = None,
        parent_store: Optional[Dict[str, Dict[str, Any]]] = None,
        generator: Optional[GroundedGenerator] = None,
        strict_citation_validation: bool = False,
    ):
        # NLP Understanding components (Stage 2)
        self.legal_ner = get_legal_ner()
        self.entity_linker = get_entity_linker()
        self.intent_classifier = get_intent_classifier()
        self.query_expander = get_query_expander()

        # Routing component (Stage 4)
        self.query_router = get_query_router()

        # Retrieval & Reranker component (Stage 3)
        self.retriever = retriever or HybridRetriever()

        # Context Recovery & Grounding components (Stage 4)
        self.parent_store = parent_store or getattr(self.retriever, "parent_store", {})
        self.parent_recovery = ParentChildRecovery(parent_store=self.parent_store)
        self.generator = generator or GroundedGenerator()
        self.citation_validator = CitationValidator(parent_store=self.parent_store)
        self.confidence_estimator = ConfidenceEstimator()
        self.abstention_manager = AbstentionManager(
            strict_citation_validation=strict_citation_validation
        )

    def run(
        self,
        query: str,
        dynamic_api_key: Optional[str] = None,
        override_top_k: Optional[int] = None,
    ) -> PipelineResult:
        """
        Executes the full end-to-end 16-stage Legal RAG pipeline.

        Args:
            query: User's raw question string.
            dynamic_api_key: Optional Google Gemini API key.
            override_top_k: Optional custom top_k override.

        Returns:
            PipelineResult structured object.
        """
        raw_query = query or ""

        # Step 1: Language Detection
        lang_info = detect_language(raw_query)

        # Step 2: Preprocessing
        norm_q = normalize_legal_text(raw_query)

        # Step 3: Legal NER
        entities = self.legal_ner.extract_entities(norm_q)

        # Step 4: Entity Linking
        linked_entities = self.entity_linker.link_all(entities)

        # Step 5: Intent Classification
        intent_info = self.intent_classifier.classify(norm_q, entities=entities)

        # Step 6: Query Expansion
        expansion_info = self.query_expander.expand(norm_q)
        exp_q = expansion_info.get("expanded_query", norm_q)

        # Step 7: Query Router
        routing_obj = self.query_router.route(
            normalized_query=norm_q,
            language=lang_info,
            legal_entities=entities,
            linked_entities=linked_entities,
            intent=intent_info,
            expanded_query=exp_q,
        )
        routing_dict = routing_obj.to_dict()

        # Step 8: Early Abstention Check (Router Stage)
        router_abstain = self.abstention_manager.evaluate(
            query=raw_query,
            routing_decision=routing_obj,
        )
        if router_abstain["should_abstain"]:
            return PipelineResult(
                original_query=raw_query,
                normalized_query=norm_q,
                language=lang_info,
                intent=intent_info,
                entities=entities,
                linked_entities=linked_entities,
                expanded_query=exp_q,
                routing_decision=routing_dict,
                retrieved_chunks=[],
                reranked_chunks=[],
                parent_context={"parents": [], "parent_count": 0, "child_count": 0},
                citations=[],
                generated_answer=router_abstain["safe_response"],
                citation_validation={
                    "valid": True,
                    "citations_checked": 0,
                    "invalid_citations": [],
                    "unsupported_claims": [],
                    "summary": "Abstained at router stage.",
                },
                confidence={
                    "confidence_score": 0.0,
                    "confidence_level": "VERY_LOW",
                    "is_calibrated": False,
                    "explanation": "Out of scope; confidence 0.0.",
                },
                abstained=True,
                abstention_reason=router_abstain["abstention_reason"],
            )

        # Step 9-11: Retrieval & Reranking (Configured by Router)
        retrieval_query = routing_obj.retrieval_query
        target_top_k = override_top_k or routing_obj.final_top_k

        # Dynamic parameter injection based on router decision
        orig_bm25 = self.retriever.use_bm25
        orig_dense = self.retriever.use_dense
        orig_rrf = self.retriever.use_rrf
        orig_eb = self.retriever.use_entity_boost
        orig_eb_wt = self.retriever.entity_boost_weight
        orig_reranker = self.retriever.use_reranker

        try:
            self.retriever.use_bm25 = routing_obj.use_bm25
            self.retriever.use_dense = routing_obj.use_dense
            self.retriever.use_rrf = routing_obj.use_rrf
            self.retriever.use_entity_boost = routing_obj.use_entity_boost
            self.retriever.entity_boost_weight = routing_obj.entity_boost_weight
            self.retriever.use_reranker = routing_obj.use_reranker

            reranked_chunks = self.retriever.retrieve(
                query=retrieval_query,
                entities=linked_entities or entities,
                top_k=target_top_k,
            )
        finally:
            # Restore retriever defaults
            self.retriever.use_bm25 = orig_bm25
            self.retriever.use_dense = orig_dense
            self.retriever.use_rrf = orig_rrf
            self.retriever.use_entity_boost = orig_eb
            self.retriever.entity_boost_weight = orig_eb_wt
            self.retriever.use_reranker = orig_reranker

        # Apply doc_type filtering if router specified and candidate set permits
        if routing_obj.filter_doc_type:
            filtered = [
                c for c in reranked_chunks
                if c.get("doc_type") == routing_obj.filter_doc_type
                or c.get("metadata", {}).get("doc_type") == routing_obj.filter_doc_type
            ]
            # Only apply if filter doesn't completely wipe out all candidates
            if filtered:
                reranked_chunks = filtered

        # Step 12: Abstention Check (Retrieval Stage)
        retrieval_abstain = self.abstention_manager.evaluate(
            query=raw_query,
            routing_decision=routing_obj,
            retrieved_chunks=reranked_chunks,
        )
        if retrieval_abstain["should_abstain"]:
            return PipelineResult(
                original_query=raw_query,
                normalized_query=norm_q,
                language=lang_info,
                intent=intent_info,
                entities=entities,
                linked_entities=linked_entities,
                expanded_query=exp_q,
                routing_decision=routing_dict,
                retrieved_chunks=reranked_chunks,
                reranked_chunks=reranked_chunks,
                parent_context={"parents": [], "parent_count": 0, "child_count": 0},
                citations=[],
                generated_answer=retrieval_abstain["safe_response"],
                citation_validation={
                    "valid": True,
                    "citations_checked": 0,
                    "invalid_citations": [],
                    "unsupported_claims": [],
                    "summary": "Abstained at retrieval stage.",
                },
                confidence={
                    "confidence_score": 0.0,
                    "confidence_level": "VERY_LOW",
                    "is_calibrated": False,
                    "explanation": "No relevant chunks retrieved.",
                },
                abstained=True,
                abstention_reason=retrieval_abstain["abstention_reason"],
            )

        # Step 13: Parent Context Recovery
        recovered_context = self.parent_recovery.recover(reranked_chunks)

        # Step 14: Grounded Generation
        generation_result = self.generator.generate(
            query=raw_query,
            recovered_context=recovered_context,
            routing_decision=routing_obj,
            dynamic_api_key=dynamic_api_key,
        )

        # Step 15: Citation Validation
        citation_validation = self.citation_validator.validate(
            generated_answer=generation_result["answer"],
            citations=generation_result["citations"],
            recovered_context=recovered_context,
        )

        # Step 16: Confidence Estimation
        confidence_result = self.confidence_estimator.estimate(
            query=raw_query,
            ranked_chunks=reranked_chunks,
            recovered_context=recovered_context,
            citation_validation=citation_validation,
            query_entities=entities,
            linked_entities=linked_entities,
        )

        # Step 17: Post-Generation Abstention Check
        final_abstain = self.abstention_manager.evaluate(
            query=raw_query,
            routing_decision=routing_obj,
            retrieved_chunks=reranked_chunks,
            recovered_context=recovered_context,
            citation_validation=citation_validation,
            confidence_result=confidence_result,
        )

        if final_abstain["should_abstain"]:
            final_answer = final_abstain["safe_response"]
            is_abstained = True
            abstain_reason = final_abstain["abstention_reason"]
        else:
            final_answer = generation_result["answer"]
            is_abstained = False
            abstain_reason = None

        return PipelineResult(
            original_query=raw_query,
            normalized_query=norm_q,
            language=lang_info,
            intent=intent_info,
            entities=entities,
            linked_entities=linked_entities,
            expanded_query=exp_q,
            routing_decision=routing_dict,
            retrieved_chunks=reranked_chunks,
            reranked_chunks=reranked_chunks,
            parent_context=recovered_context,
            citations=generation_result["citations"],
            generated_answer=final_answer,
            citation_validation=citation_validation,
            confidence=confidence_result,
            abstained=is_abstained,
            abstention_reason=abstain_reason,
        )


# Global singleton pipeline instance
_PIPELINE_INSTANCE: Optional[LegalRAGPipeline] = None


def get_legal_rag_pipeline() -> LegalRAGPipeline:
    """Returns or lazily initializes the singleton LegalRAGPipeline."""
    global _PIPELINE_INSTANCE
    if _PIPELINE_INSTANCE is None:
        _PIPELINE_INSTANCE = LegalRAGPipeline()
    return _PIPELINE_INSTANCE
