"""
Confidence Estimation Module for Indian Constitutional Legal RAG.
Computes an explainable, multi-signal confidence estimate combining:
- Retrieval / reranker strength
- Supporting evidence count
- Entity alignment
- Agreement between retrieval methods
- Citation validation score
- Query evidence coverage

Explicitly transparent and uncalibrated (heuristic composite score).
"""

import math
import re
from typing import Dict, List, Any, Optional, Set

from config import CONFIDENCE_SIGNAL_WEIGHTS


class ConfidenceEstimator:
    """
    Computes transparent, explainable confidence estimates for RAG responses.
    Does NOT present scores as calibrated probabilities.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or CONFIDENCE_SIGNAL_WEIGHTS

    def estimate(
        self,
        query: str,
        ranked_chunks: List[Dict[str, Any]],
        recovered_context: Optional[Dict[str, Any]] = None,
        citation_validation: Optional[Dict[str, Any]] = None,
        query_entities: Optional[Dict[str, List[str]]] = None,
        linked_entities: Optional[List[Dict[str, Any]]] = None,
        bm25_candidates: Optional[List[Dict[str, Any]]] = None,
        dense_candidates: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Calculates explainable confidence estimate across 6 transparent signals.

        Returns:
            Dictionary containing:
            - confidence_score: float in [0.0, 1.0]
            - confidence_level: HIGH | MEDIUM | LOW | VERY_LOW
            - is_calibrated: False
            - signal_breakdown: Individual signal scores
            - signal_weights: Weight configuration applied
            - supporting_evidence_count: Number of chunks used
            - top_retrieval_score: Score of primary chunk
            - explanation: Textual explanation of score drivers
        """
        if not ranked_chunks:
            return {
                "confidence_score": 0.0,
                "confidence_level": "VERY_LOW",
                "is_calibrated": False,
                "disclaimer": (
                    "This confidence score is an explainable heuristic composite of retrieval, entity, "
                    "agreement, and citation signals, not a mathematically calibrated probability distribution."
                ),
                "signal_breakdown": {
                    "retrieval_strength": 0.0,
                    "evidence_count": 0.0,
                    "entity_alignment": 0.0,
                    "method_agreement": 0.0,
                    "citation_integrity": 0.0,
                    "evidence_coverage": 0.0,
                },
                "signal_weights": self.weights,
                "supporting_evidence_count": 0,
                "top_retrieval_score": 0.0,
                "explanation": "No evidence retrieved; confidence is 0.0.",
            }

        # -------------------------------------------------------------
        # Signal 1: Retrieval Strength (Reranker or Fusion Score)
        # -------------------------------------------------------------
        top_chunk = ranked_chunks[0]
        top_score = float(top_chunk.get("rerank_score", top_chunk.get("score", top_chunk.get("rrf_score", 0.0))))

        if "rerank_score" in top_chunk:
            # Cross-encoder logits: map via sigmoid to [0.0, 1.0]
            # Logit 0.0 -> 0.5, Logit 3.0 -> 0.95, Logit -3.0 -> 0.05
            try:
                retrieval_strength = 1.0 / (1.0 + math.exp(-top_score))
            except OverflowError:
                retrieval_strength = 1.0 if top_score > 0 else 0.0
        else:
            # RRF or dense score
            retrieval_strength = min(1.0, max(0.0, top_score * 30.0 if top_score < 0.05 else top_score))

        # -------------------------------------------------------------
        # Signal 2: Evidence Count
        # -------------------------------------------------------------
        evidence_count = len(ranked_chunks)
        count_signal = min(1.0, evidence_count / 3.0)

        # -------------------------------------------------------------
        # Signal 3: Entity Alignment
        # -------------------------------------------------------------
        extracted_entities = query_entities or {}
        article_mentions = extracted_entities.get("ARTICLE", []) or extracted_entities.get("articles", [])
        case_mentions = extracted_entities.get("CASE", []) or extracted_entities.get("cases", [])
        total_query_entities = len(article_mentions) + len(case_mentions)

        if total_query_entities == 0:
            # Query did not specify exact entities; neutral baseline
            entity_signal = 0.70
        else:
            # Check if any specified query entity appears in retrieved parents
            parents = (recovered_context or {}).get("parents", [])
            retrieved_titles = [
                (p.get("title", "") + " " + p.get("article_number", "") + " " + p.get("case_name", "")).lower()
                for p in parents
            ]
            matched = 0
            for art in article_mentions:
                art_num = re.sub(r"[^\w]", "", art.lower())
                if any(art_num in t for t in retrieved_titles):
                    matched += 1
            for c_name in case_mentions:
                if any(c_name.lower() in t for t in retrieved_titles):
                    matched += 1

            entity_signal = min(1.0, 0.20 + 0.80 * (matched / total_query_entities))

        # -------------------------------------------------------------
        # Signal 4: Method Agreement (BM25 vs Dense Overlap)
        # -------------------------------------------------------------
        if bm25_candidates and dense_candidates:
            bm25_ids = {c.get("chunk_id", c.get("child_id", "")) for c in bm25_candidates[:5]}
            dense_ids = {c.get("chunk_id", c.get("child_id", "")) for c in dense_candidates[:5]}
            intersection = len(bm25_ids.intersection(dense_ids))
            union = len(bm25_ids.union(dense_ids))
            jaccard = intersection / union if union > 0 else 0.0
            # Scale agreement: 0 overlap still has baseline hybrid value
            agreement_signal = round(0.50 + 0.50 * jaccard, 4)
        else:
            agreement_signal = 0.75  # Default when separate candidate lists not provided

        # -------------------------------------------------------------
        # Signal 5: Citation Integrity
        # -------------------------------------------------------------
        if citation_validation is not None:
            citation_signal = float(citation_validation.get("validation_score", 1.0))
        else:
            citation_signal = 1.0

        # -------------------------------------------------------------
        # Signal 6: Evidence Coverage of Query Terms
        # -------------------------------------------------------------
        coverage_signal = self._compute_coverage(query, ranked_chunks)

        # -------------------------------------------------------------
        # Weighted Composite Confidence Score
        # -------------------------------------------------------------
        w = self.weights
        composite_score = (
            w.get("retrieval", 0.25) * retrieval_strength
            + w.get("evidence_count", 0.15) * count_signal
            + w.get("entity_match", 0.20) * entity_signal
            + w.get("method_agreement", 0.15) * agreement_signal
            + w.get("citation_validity", 0.15) * citation_signal
            + w.get("evidence_coverage", 0.10) * coverage_signal
        )
        composite_score = min(1.0, max(0.0, round(composite_score, 4)))

        # Categorize confidence level
        if composite_score >= 0.70:
            level = "HIGH"
        elif composite_score >= 0.50:
            level = "MEDIUM"
        elif composite_score >= 0.30:
            level = "LOW"
        else:
            level = "VERY_LOW"

        explanation_parts = [
            f"Retrieval strength: {retrieval_strength:.2f}",
            f"Evidence count: {count_signal:.2f} ({evidence_count} chunks)",
            f"Entity alignment: {entity_signal:.2f}",
            f"Citation validity: {citation_signal:.2f}",
        ]

        return {
            "confidence_score": composite_score,
            "confidence_level": level,
            "is_calibrated": False,
            "disclaimer": (
                "This confidence score is an explainable heuristic composite of retrieval, entity, "
                "agreement, and citation signals, not a mathematically calibrated probability distribution."
            ),
            "signal_breakdown": {
                "retrieval_strength": round(retrieval_strength, 4),
                "evidence_count": round(count_signal, 4),
                "entity_alignment": round(entity_signal, 4),
                "method_agreement": round(agreement_signal, 4),
                "citation_integrity": round(citation_signal, 4),
                "evidence_coverage": round(coverage_signal, 4),
            },
            "signal_weights": self.weights,
            "supporting_evidence_count": evidence_count,
            "top_retrieval_score": round(top_score, 4),
            "explanation": " | ".join(explanation_parts),
        }

    def _compute_coverage(self, query: str, ranked_chunks: List[Dict[str, Any]]) -> float:
        """Calculates proportion of meaningful query terms present in retrieved passages."""
        if not query:
            return 0.0
        query_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", query.lower()))
        if not query_words:
            return 0.5
        all_chunk_text = " ".join(
            (c.get("text", "") or c.get("child_text", "")).lower() for c in ranked_chunks
        )
        covered = sum(1 for w in query_words if w in all_chunk_text)
        return round(covered / len(query_words), 4)
