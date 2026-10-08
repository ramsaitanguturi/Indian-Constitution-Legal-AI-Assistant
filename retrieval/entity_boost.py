"""
Legal Entity-Aware Ranking Boost Module.
Increments candidate retrieval scores when candidate metadata matches
extracted or linked legal entities (e.g. Article numbers, Case names, Doctrines),
with transparent explainability logs.
"""

import re
from typing import Dict, List, Any, Optional
from config import ENTITY_BOOST_WEIGHT


def _normalize_token(text: str) -> str:
    """Lowercase and strip punctuation for entity token matching."""
    if not text:
        return ""
    return re.sub(r"[^\w\s]", "", str(text).lower()).strip()


def _parse_entities(entities_input: Any) -> Dict[str, List[str]]:
    """
    Normalizes entities from various formats (dict from NER, list of linked records, etc.)
    into a structured map:
        {
            "articles": [...],
            "cases": [...],
            "concepts": [...],
            "entity_ids": [...]
        }
    """
    parsed: Dict[str, List[str]] = {
        "articles": [],
        "cases": [],
        "concepts": [],
        "entity_ids": [],
    }

    if not entities_input:
        return parsed

    # Format 1: List of linked entity dictionaries from EntityLinker
    if isinstance(entities_input, list):
        for item in entities_input:
            if isinstance(item, dict):
                eid = item.get("entity_id", "")
                if eid:
                    parsed["entity_ids"].append(eid)

                etype = item.get("entity_type", "").upper()
                cname = item.get("canonical_name", "")
                surface = item.get("surface_form", "")

                if etype in ("ARTICLE", "CONSTITUTION_ARTICLE"):
                    parsed["articles"].extend([cname, surface])
                elif etype in ("CASE", "JUDGMENT"):
                    parsed["cases"].extend([cname, surface])
                elif etype in ("LEGAL_CONCEPT", "RIGHT", "AMENDMENT"):
                    parsed["concepts"].extend([cname, surface])
            elif isinstance(item, str):
                parsed["concepts"].append(item)

    # Format 2: Dict mapping categories to entity lists (from LegalNER / LegalNERExtractor)
    elif isinstance(entities_input, dict):
        # Extract articles
        for k in ("articles", "ARTICLE"):
            if k in entities_input and isinstance(entities_input[k], list):
                parsed["articles"].extend(entities_input[k])

        # Extract cases
        for k in ("cases", "CASE"):
            if k in entities_input and isinstance(entities_input[k], list):
                parsed["cases"].extend(entities_input[k])

        # Extract concepts, rights, amendments
        for k in ("concepts", "LEGAL_CONCEPT", "RIGHT", "rights", "AMENDMENT", "amendments"):
            if k in entities_input and isinstance(entities_input[k], list):
                parsed["concepts"].extend(entities_input[k])

        # Extract canonical entity IDs if present
        for k in ("entity_ids", "linked_entities"):
            if k in entities_input:
                val = entities_input[k]
                if isinstance(val, list):
                    for v in val:
                        if isinstance(v, dict) and "entity_id" in v:
                            parsed["entity_ids"].append(v["entity_id"])
                        elif isinstance(v, str):
                            parsed["entity_ids"].append(v)

    # Clean up empty strings and duplicates
    for cat in parsed:
        seen = set()
        cleaned = []
        for term in parsed[cat]:
            term_clean = term.strip()
            if term_clean and term_clean.lower() not in seen:
                seen.add(term_clean.lower())
                cleaned.append(term_clean)
        parsed[cat] = cleaned

    return parsed


def apply_entity_boost(
    candidates: List[Dict[str, Any]],
    linked_entities: Any,
    boost_weight: float = ENTITY_BOOST_WEIGHT,
) -> List[Dict[str, Any]]:
    """
    Apply legal entity-aware ranking boost to retrieved candidate chunks.

    Args:
        candidates: List of candidate dictionaries (e.g. output from RRF or retrieval).
        linked_entities: Extracted or linked legal entities (dict or list of dicts).
        boost_weight: Multiplier applied per matching entity class (default: 0.15).

    Returns:
        List of candidate dictionaries re-sorted by boosted score with updated ranks
        and transparent explainability logs in each candidate's metadata.
    """
    if not candidates:
        return []

    # If no entities or zero weight, preserve candidates
    if not linked_entities or boost_weight <= 0.0:
        boosted = []
        for rank, c in enumerate(candidates, start=1):
            cand_copy = dict(c)
            cand_copy["rank"] = rank
            cand_copy["boost_applied"] = 0.0
            cand_copy["boost_reasons"] = []
            cand_copy["base_score"] = cand_copy.get("score", 0.0)
            boosted.append(cand_copy)
        return boosted

    parsed_entities = _parse_entities(linked_entities)
    has_any_entities = any(bool(v) for v in parsed_entities.values())

    if not has_any_entities:
        boosted = []
        for rank, c in enumerate(candidates, start=1):
            cand_copy = dict(c)
            cand_copy["rank"] = rank
            cand_copy["boost_applied"] = 0.0
            cand_copy["boost_reasons"] = []
            cand_copy["base_score"] = cand_copy.get("score", 0.0)
            boosted.append(cand_copy)
        return boosted

    boosted_candidates: List[Dict[str, Any]] = []

    for item in candidates:
        cand = dict(item)
        metadata = dict(cand.get("metadata", {}))
        meta_parent = cand.get("parent_data", {})

        base_score = float(cand.get("score", 0.0))
        boost_applied = 0.0
        boost_reasons: List[str] = []

        cand_art = _normalize_token(metadata.get("article_number") or meta_parent.get("article_number", ""))
        cand_case = _normalize_token(metadata.get("case_name") or meta_parent.get("case_name", ""))
        cand_title = _normalize_token(metadata.get("title") or meta_parent.get("title", ""))
        cand_doc_id = _normalize_token(cand.get("document_id") or cand.get("parent_id", ""))
        cand_text = _normalize_token(cand.get("text", "")[:300])

        # 1. Article Matching (Full Weight)
        for ent_art in parsed_entities["articles"]:
            norm_art = _normalize_token(ent_art)
            if not norm_art:
                continue

            # Exact article number match (e.g. "article 21" or "21")
            art_digits = re.findall(r"\d+[a-z]?", norm_art)
            cand_digits = re.findall(r"\d+[a-z]?", cand_art) + re.findall(r"\d+[a-z]?", cand_doc_id)

            is_match = False
            if art_digits and cand_digits and any(d in cand_digits for d in art_digits):
                is_match = True
            elif cand_art and (norm_art in cand_art or cand_art in norm_art):
                is_match = True
            elif cand_title and norm_art in cand_title:
                is_match = True

            if is_match:
                match_boost = boost_weight * 1.0
                boost_applied += match_boost
                boost_reasons.append(f"Matched Article: {ent_art} (+{match_boost:.3f})")
                break  # Count each entity type once per candidate

        # 2. Landmark Case Law Matching (Full Weight)
        for ent_case in parsed_entities["cases"]:
            norm_case = _normalize_token(ent_case)
            if not norm_case:
                continue

            if cand_case and (norm_case in cand_case or cand_case in norm_case):
                match_boost = boost_weight * 1.0
                boost_applied += match_boost
                boost_reasons.append(f"Matched Case: {ent_case} (+{match_boost:.3f})")
                break
            if cand_doc_id and len(norm_case) > 4 and norm_case in cand_doc_id:
                match_boost = boost_weight * 1.0
                boost_applied += match_boost
                boost_reasons.append(f"Matched Case: {ent_case} (+{match_boost:.3f})")
                break
            # Split into significant lead names (e.g. "Kesavananda" or "Puttaswamy")
            lead_tokens = [w for w in norm_case.split() if len(w) > 4 and w not in ("state", "union", "india", "kerala")]
            if cand_case and any(lt in cand_case for lt in lead_tokens):
                match_boost = boost_weight * 1.0
                boost_applied += match_boost
                boost_reasons.append(f"Matched Case Lead: {ent_case} (+{match_boost:.3f})")
                break

        # 3. Canonical Entity ID Matching (Full Weight)
        for eid in parsed_entities["entity_ids"]:
            norm_eid = _normalize_token(eid)
            if not norm_eid:
                continue
            if (cand_doc_id and norm_eid in cand_doc_id) or (cand_case and norm_eid in cand_case) or (cand_art and norm_eid in cand_art):
                match_boost = boost_weight * 1.0
                boost_applied += match_boost
                boost_reasons.append(f"Matched Entity ID: {eid} (+{match_boost:.3f})")
                break

        # 4. Legal Concept / Right Matching (Half Weight)
        for concept in parsed_entities["concepts"]:
            norm_concept = _normalize_token(concept)
            if not norm_concept or len(norm_concept) < 4:
                continue
            if (cand_title and norm_concept in cand_title) or (cand_text and norm_concept in cand_text):
                concept_boost = boost_weight * 0.5
                boost_applied += concept_boost
                boost_reasons.append(f"Matched Concept: {concept} (+{concept_boost:.3f})")
                break

        # Compute new boosted score
        final_score = round(base_score + boost_applied, 5)

        # Update candidate fields
        cand["base_score"] = round(base_score, 5)
        cand["boost_applied"] = round(boost_applied, 5)
        cand["boost_reasons"] = boost_reasons
        cand["score"] = final_score

        # Maintain metadata transparency
        metadata["boost_applied"] = round(boost_applied, 5)
        metadata["boost_reasons"] = boost_reasons
        metadata["base_score"] = round(base_score, 5)
        cand["metadata"] = metadata

        boosted_candidates.append(cand)

    # Re-sort descending by boosted score
    boosted_candidates.sort(key=lambda c: c["score"], reverse=True)

    # Re-index ranks 1..N
    for new_rank, cand in enumerate(boosted_candidates, start=1):
        cand["rank"] = new_rank

    return boosted_candidates
