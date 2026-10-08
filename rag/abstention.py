"""
Abstention Decision Module for Indian Constitutional Legal RAG.
Refuses to generate speculative or ungrounded responses when evidence is insufficient,
retrieval confidence is below threshold, citations fail validation, or query is out-of-scope.
"""

from typing import Dict, List, Any, Optional

from config import CONFIDENCE_ABSTENTION_THRESHOLD, MIN_RETRIEVAL_SCORE_THRESHOLD


class AbstentionManager:
    """
    Evaluates multi-stage criteria to decide whether the system should safely abstain.
    """

    def __init__(
        self,
        confidence_threshold: float = CONFIDENCE_ABSTENTION_THRESHOLD,
        min_retrieval_score: float = MIN_RETRIEVAL_SCORE_THRESHOLD,
        strict_citation_validation: bool = False,
    ):
        self.confidence_threshold = confidence_threshold
        self.min_retrieval_score = min_retrieval_score
        self.strict_citation_validation = strict_citation_validation

    def evaluate(
        self,
        query: str,
        routing_decision: Optional[Any] = None,
        retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
        recovered_context: Optional[Dict[str, Any]] = None,
        citation_validation: Optional[Dict[str, Any]] = None,
        confidence_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Determines whether the pipeline should abstain from answering.

        Args:
            query: Raw user query string.
            routing_decision: RoutingDecision object or dict.
            retrieved_chunks: Candidate retrieved/reranked chunks.
            recovered_context: Output from ParentChildRecovery.
            citation_validation: Output from CitationValidator.
            confidence_result: Output from ConfidenceEstimator.

        Returns:
            Dictionary specifying:
            - should_abstain: bool
            - abstention_reason: str or None
            - safe_response: str or None
            - abstention_stage: str or None
            - thresholds_applied: Dict of applied thresholds
        """
        thresholds = {
            "confidence_threshold": self.confidence_threshold,
            "min_retrieval_score": self.min_retrieval_score,
            "strict_citation_validation": self.strict_citation_validation,
        }

        # -------------------------------------------------------------
        # 1. Routing Stage: Out-of-Scope or Unsupported Language
        # -------------------------------------------------------------
        if routing_decision is not None:
            is_oos = getattr(routing_decision, "is_out_of_scope", False)
            strategy = getattr(routing_decision, "strategy", "")
            if isinstance(routing_decision, dict):
                is_oos = routing_decision.get("is_out_of_scope", False)
                strategy = routing_decision.get("strategy", "")

            if is_oos or strategy == "OUT_OF_SCOPE":
                return {
                    "should_abstain": True,
                    "abstention_reason": "OUT_OF_SCOPE",
                    "safe_response": (
                        "**Scope Notice**: This inquiry falls outside the scope of Indian Constitutional Law. "
                        "The assistant is specialized exclusively in the provisions of the Constitution of India, "
                        "its amendments, and landmark Supreme Court judicial precedents. "
                        "Please submit an inquiry regarding constitutional rights, articles, or case law."
                    ),
                    "abstention_stage": "ROUTER",
                    "thresholds_applied": thresholds,
                }

        # -------------------------------------------------------------
        # 2. Retrieval Stage: Empty Results & Low Relevance
        # -------------------------------------------------------------
        if retrieved_chunks is not None:
            if not retrieved_chunks:
                return {
                    "should_abstain": True,
                    "abstention_reason": "NO_RETRIEVAL_RESULTS",
                    "safe_response": (
                        "**Abstention Notice**: No relevant constitutional articles or landmark judgments "
                        "were found in the verified legal database for your inquiry. "
                        "To prevent hallucination, generation has been safely withheld. "
                        "Please verify Article numbers or case citations and try again."
                    ),
                    "abstention_stage": "RETRIEVAL",
                    "thresholds_applied": thresholds,
                }

            # Check for very low retrieval score
            top_score = float(retrieved_chunks[0].get("score", retrieved_chunks[0].get("rrf_score", 1.0)))
            if "rerank_score" in retrieved_chunks[0]:
                top_score = float(retrieved_chunks[0]["rerank_score"])
                # Severe cross-encoder negative logit check (e.g. < -8.0 indicates extreme irrelevance)
                if top_score < -8.0:
                    return {
                        "should_abstain": True,
                        "abstention_reason": "LOW_RETRIEVAL_CONFIDENCE",
                        "safe_response": (
                            "**Low Relevance Notice**: The closest retrieved legal passages exhibited very low "
                            f"semantic relevance (score: {top_score:.2f}). To ensure reliable legal assistance, "
                            "the assistant abstains from answering. Please rephrase with specific constitutional terms."
                        ),
                        "abstention_stage": "RERANKER",
                        "thresholds_applied": thresholds,
                    }
            elif top_score < self.min_retrieval_score:
                return {
                    "should_abstain": True,
                    "abstention_reason": "LOW_RETRIEVAL_CONFIDENCE",
                    "safe_response": (
                        "**Low Relevance Notice**: Retrieval fusion score was below the minimum confidence threshold "
                        f"({top_score:.4f} < {self.min_retrieval_score:.4f}). Generation withheld."
                    ),
                    "abstention_stage": "RETRIEVAL",
                    "thresholds_applied": thresholds,
                }

        # -------------------------------------------------------------
        # 3. Context Recovery Stage: Insufficient Evidence
        # -------------------------------------------------------------
        if recovered_context is not None:
            parents = recovered_context.get("parents", [])
            if not parents:
                return {
                    "should_abstain": True,
                    "abstention_reason": "INSUFFICIENT_EVIDENCE",
                    "safe_response": (
                        "**Insufficient Evidence Notice**: Retrieved child passages could not be anchored to "
                        "verified parent constitutional documents in the knowledge base. Generation withheld."
                    ),
                    "abstention_stage": "CONTEXT_RECOVERY",
                    "thresholds_applied": thresholds,
                }

        # -------------------------------------------------------------
        # 4. Citation Validation Stage: Structural Failures
        # -------------------------------------------------------------
        if citation_validation is not None:
            is_valid = citation_validation.get("valid", True)
            invalid_citations = citation_validation.get("invalid_citations", [])
            unsupported_claims = citation_validation.get("unsupported_claims", [])

            # If strict citation validation is enabled or completely invalid
            if (not is_valid and self.strict_citation_validation) or (len(invalid_citations) > 0 and len(citation_validation.get("valid_citations", [])) == 0):
                return {
                    "should_abstain": True,
                    "abstention_reason": "CITATION_VALIDATION_FAILURE",
                    "safe_response": (
                        "**Citation Integrity Notice**: The synthesized response contained citations that could not be "
                        "structurally validated against the retrieved source evidence. To maintain legal accuracy, "
                        "the response has been withheld."
                    ),
                    "abstention_stage": "CITATION_VALIDATOR",
                    "thresholds_applied": thresholds,
                }

        # -------------------------------------------------------------
        # 5. Confidence Stage: Low Composite Confidence
        # -------------------------------------------------------------
        if confidence_result is not None:
            conf_score = float(confidence_result.get("confidence_score", 1.0))
            if conf_score < self.confidence_threshold:
                return {
                    "should_abstain": True,
                    "abstention_reason": "LOW_CONFIDENCE",
                    "safe_response": (
                        f"**Low Confidence Abstention**: The overall composite confidence for this query ({conf_score:.2f}) "
                        f"fell below the safety threshold ({self.confidence_threshold:.2f}). "
                        "The assistant refuses to generate an unverified response. "
                        "Please consider referencing specific Articles (e.g., Article 21) or landmark cases."
                    ),
                    "abstention_stage": "CONFIDENCE_ESTIMATOR",
                    "thresholds_applied": thresholds,
                }

        # No abstention triggered
        return {
            "should_abstain": False,
            "abstention_reason": None,
            "safe_response": None,
            "abstention_stage": None,
            "thresholds_applied": thresholds,
        }
