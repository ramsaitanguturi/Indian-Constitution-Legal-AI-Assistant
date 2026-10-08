"""
Reciprocal Rank Fusion (RRF) Module for Hybrid Search.
Combines multiple ranked candidate lists strictly via rank reciprocity:
    RRF_score(d) = sum_{L in rank_lists} (1.0 / (k + rank_L(d)))
"""

from typing import Dict, List, Any
from config import RRF_K


def get_candidate_key(candidate: Dict[str, Any]) -> str:
    """Extract a unique key identifying the candidate chunk."""
    return str(
        candidate.get("chunk_id")
        or candidate.get("child_id")
        or candidate.get("document_id")
        or candidate.get("id", "")
    )


def fuse(
    rank_lists: List[List[Dict[str, Any]]],
    k: int = RRF_K
) -> List[Dict[str, Any]]:
    """
    Merge multiple ranked candidate lists using Reciprocal Rank Fusion (RRF).

    Args:
        rank_lists: List of ranked lists, where each inner list contains
                    candidate dictionaries ordered by relevance (1-indexed rank).
        k: Smoothing constant preventing high-ranked outliers from dominating (default: 60).

    Returns:
        List of fused candidate dictionaries, sorted descending by fused RRF score,
        with updated 1-indexed ranks.
    """
    if not rank_lists:
        return []

    effective_k = k if k > 0 else 60

    rrf_scores: Dict[str, float] = {}
    candidate_records: Dict[str, Dict[str, Any]] = {}
    source_ranks: Dict[str, Dict[str, int]] = {}

    for list_idx, rank_list in enumerate(rank_lists):
        if not rank_list:
            continue

        for item_idx, item in enumerate(rank_list):
            cand_key = get_candidate_key(item)
            if not cand_key:
                continue

            # Use explicit 'rank' if provided, otherwise derive from 1-indexed list position
            item_rank = item.get("rank")
            if not isinstance(item_rank, int) or item_rank < 1:
                item_rank = item_idx + 1

            reciprocal_rank = 1.0 / (effective_k + item_rank)
            rrf_scores[cand_key] = rrf_scores.get(cand_key, 0.0) + reciprocal_rank

            if cand_key not in source_ranks:
                source_ranks[cand_key] = {}
            source_ranks[cand_key][f"list_{list_idx}"] = item_rank

            # Record or merge candidate attributes
            if cand_key not in candidate_records:
                # Shallow copy to avoid mutating caller data
                candidate_records[cand_key] = dict(item)
            else:
                existing = candidate_records[cand_key]
                # Merge metadata dictionaries if needed
                if "metadata" in item and isinstance(item["metadata"], dict):
                    merged_meta = dict(existing.get("metadata", {}))
                    merged_meta.update(item["metadata"])
                    existing["metadata"] = merged_meta

                # Keep longer text if one was truncated
                if len(item.get("text", "")) > len(existing.get("text", "")):
                    existing["text"] = item.get("text", "")
                    existing["child_text"] = item.get("text", "")

                # Propagate specific rank indicators if available
                if "bm25_rank" in item and item["bm25_rank"] != "N/A":
                    existing["bm25_rank"] = item["bm25_rank"]
                if "vector_rank" in item and item["vector_rank"] != "N/A":
                    existing["vector_rank"] = item["vector_rank"]

    if not rrf_scores:
        return []

    # Sort descending by fused RRF score
    sorted_items = sorted(rrf_scores.items(), key=lambda kv: kv[1], reverse=True)

    fused_results: List[Dict[str, Any]] = []
    for rank, (cand_key, score) in enumerate(sorted_items, start=1):
        record = dict(candidate_records[cand_key])
        final_score = round(score, 6)

        record["score"] = final_score
        record["rrf_score"] = final_score
        record["rank"] = rank

        # Ensure metadata has source ranks
        meta = record.setdefault("metadata", {})
        if isinstance(meta, dict):
            meta["source_ranks"] = source_ranks.get(cand_key, {})
            meta["rrf_score"] = final_score

        fused_results.append(record)

    return fused_results
