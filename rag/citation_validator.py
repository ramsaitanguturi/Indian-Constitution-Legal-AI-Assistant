"""
Citation Validator Module for Indian Constitution Legal RAG.
Validates generated answers and explicit citations against retrieved evidence.
Performs deterministic structural validation (existence, provenance, required metadata,
and detection of unsupported citations) while clearly separating structural validation
from heuristic claim verification.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple

from config import PARENT_STORE_PATH


class CitationValidator:
    """
    Validates structural integrity and evidence provenance of citations in RAG answers.
    Detects unretrieved documents, fabricated IDs, missing metadata, and unsupported references.
    """

    # Regex patterns for detecting inline citations and legal entity references in answer text
    DOC_KEY_PATTERN = re.compile(r"\[Doc:\s*([^\]]+)\]", re.IGNORECASE)
    ARTICLE_REF_PATTERN = re.compile(r"\bArticle\s*(\d+[A-Z]?|Preamble)\b", re.IGNORECASE)
    
    # Landmark case names for ungrounded mention detection
    CANONICAL_CASES = [
        "Kesavananda Bharati", "Kesavananda", "Maneka Gandhi", "Puttaswamy",
        "Minerva Mills", "S.R. Bommai", "Bommai", "A.K. Gopalan", "Gopalan",
        "Navtej Singh Johar", "Shreya Singhal", "Shayara Bano", "Indra Sawhney",
        "Golak Nath", "ADM Jabalpur", "Bachan Singh", "Vishaka"
    ]

    def __init__(self, parent_store: Optional[Dict[str, Dict[str, Any]]] = None):
        self.parent_store = parent_store if parent_store is not None else {}
        if not self.parent_store and os.path.exists(PARENT_STORE_PATH):
            try:
                with open(PARENT_STORE_PATH, "r", encoding="utf-8") as f:
                    self.parent_store = json.load(f)
            except Exception:
                self.parent_store = {}

        # Also load from expanded production corpus if available
        from config import CONSTITUTION_ARTICLES_PATH
        if len(self.parent_store) < 20 and os.path.exists(CONSTITUTION_ARTICLES_PATH):
            try:
                from rag.ingestion import ProductionIngestor
                ingestor = ProductionIngestor(use_full_corpus=True)
                full_parents, _ = ingestor.process_parent_child_chunks()
                for k, v in full_parents.items():
                    if k not in self.parent_store:
                        self.parent_store[k] = v
            except Exception:
                pass

    def _get_id_variants(self, raw_id: str) -> List[str]:
        """Returns standard ID variants for flexible matching (zero-padding, parent_ prefix)."""
        if not raw_id:
            return []
        variants = [raw_id]
        if raw_id.startswith("parent_"):
            variants.append(raw_id.replace("parent_", "", 1))
        else:
            variants.append(f"parent_{raw_id}")

        for v in list(variants):
            unpadded = re.sub(r"_0+(\d+)", r"_\1", v)
            variants.append(unpadded)
            padded = re.sub(r"_(\d+)", lambda m: f"_{int(m.group(1)):03d}", v)
            variants.append(padded)
        return list(dict.fromkeys(variants))

    def validate(
        self,
        generated_answer: str,
        citations: List[Dict[str, Any]],
        recovered_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validates citations and text claims against retrieved evidence.

        Args:
            generated_answer: Text of generated response.
            citations: List of structured citation dictionaries from GroundedGenerator.
            recovered_context: Output dictionary from ParentChildRecovery.recover().

        Returns:
            Structured validation result matching specification.
        """
        retrieved_parents = recovered_context.get("parents", [])
        retrieved_parent_ids: Set[str] = {p.get("document_id", "") for p in retrieved_parents}
        retrieved_variants: Set[str] = set()
        for rpid in retrieved_parent_ids:
            retrieved_variants.update(self._get_id_variants(rpid))

        retrieved_child_ids: Set[str] = {
            c.get("chunk_id", "") for c in recovered_context.get("child_evidence", [])
        }

        # Build corpus-level knowledge of articles and cases in retrieved set
        retrieved_articles: Set[str] = set()
        retrieved_case_names: Set[str] = set()
        all_retrieved_text: List[str] = []

        for p in retrieved_parents:
            if p.get("article_number"):
                art_clean = re.sub(r"[^\w]", "", p["article_number"].upper())
                retrieved_articles.add(art_clean)
            if p.get("case_name"):
                retrieved_case_names.add(p["case_name"].lower())

            # Accumulate all string/list content from parent record
            for val in p.values():
                if isinstance(val, str):
                    all_retrieved_text.append(val)
                elif isinstance(val, list):
                    for item in val:
                        if isinstance(item, str):
                            all_retrieved_text.append(item)

            for ch in p.get("supporting_children", []):
                if isinstance(ch, dict):
                    for val in ch.values():
                        if isinstance(val, str):
                            all_retrieved_text.append(val)

        combined_evidence_corpus = " ".join(all_retrieved_text).lower()

        valid_citations: List[Dict[str, Any]] = []
        invalid_citations: List[Dict[str, Any]] = []
        unsupported_claims: List[str] = []

        # -------------------------------------------------------------
        # 1. Structural Validation of Declared Citations
        # -------------------------------------------------------------
        for cit in citations:
            doc_id = cit.get("document_id", "")
            cit_key = cit.get("citation_key", f"[Doc: {doc_id}]")
            source_title = cit.get("source_title", "")
            doc_type = cit.get("doc_type", "")
            supporting_chunks = cit.get("supporting_chunk_ids", [])

            # Check 1: Required metadata exists
            if not doc_id or not source_title or not doc_type:
                invalid_citations.append({
                    "citation": cit,
                    "reason": "MISSING_REQUIRED_METADATA",
                    "details": f"Citation missing required metadata (doc_id='{doc_id}', title='{source_title}', type='{doc_type}').",
                })
                continue

            # Check 2: Document exists in parent_store / corpus
            doc_vars = self._get_id_variants(doc_id)
            if self.parent_store and not any(v in self.parent_store for v in doc_vars):
                invalid_citations.append({
                    "citation": cit,
                    "reason": "DOCUMENT_DOES_NOT_EXIST",
                    "details": f"Cited document ID '{doc_id}' does not exist in the verified legal database.",
                })
                continue

            # Check 3: Document was actually retrieved in supplied evidence
            if not any(v in retrieved_variants for v in doc_vars):
                invalid_citations.append({
                    "citation": cit,
                    "reason": "UNRETRIEVED_EVIDENCE_CITED",
                    "details": f"Document '{doc_id}' exists in database but was NOT part of the retrieved evidence for this query.",
                })
                continue

            # Check 4: Check supporting chunk IDs if present
            unmatched_chunks = [cid for cid in supporting_chunks if cid not in retrieved_child_ids]
            if unmatched_chunks and retrieved_child_ids:
                invalid_citations.append({
                    "citation": cit,
                    "reason": "INVALID_CHILD_CHUNK_REFERENCE",
                    "details": f"Chunks {unmatched_chunks} do not exist in retrieved child passages.",
                })
                continue

            valid_citations.append(cit)

        # -------------------------------------------------------------
        # 2. Text-Level Reference & Unsupported Mention Detection
        # -------------------------------------------------------------
        # A) Explicit [Doc: <id>] markers in generated text
        inline_doc_ids = self.DOC_KEY_PATTERN.findall(generated_answer)
        for inline_id in inline_doc_ids:
            clean_id = inline_id.strip()
            inline_vars = self._get_id_variants(clean_id)
            if not any(v in retrieved_variants for v in inline_vars):
                unsupported_claims.append(
                    f"Generated text explicitly cites [Doc: {clean_id}], which was not in retrieved evidence."
                )

        # B) Detect ungrounded article claims (e.g. text talks about Article 370 when only Art 21 was retrieved)
        if retrieved_articles:
            mentioned_articles = self.ARTICLE_REF_PATTERN.findall(generated_answer)
            for art in mentioned_articles:
                art_clean = "ARTICLE" + re.sub(r"[^\w]", "", art.upper())
                # Check if this article was retrieved
                matching = any(art_clean in ra or ra in art_clean for ra in retrieved_articles)
                if not matching and art.lower() not in combined_evidence_corpus:
                    unsupported_claims.append(
                        f"Generated text refers to 'Article {art}' which was not present in the retrieved evidence."
                    )

        # C) Detect ungrounded landmark case claims
        for case in self.CANONICAL_CASES:
            case_lower = case.lower()
            if case_lower in generated_answer.lower():
                # Check if this case was in retrieved parent cases or evidence text
                in_parents = any(case_lower in rc for rc in retrieved_case_names)
                in_evidence = case_lower in combined_evidence_corpus
                if not in_parents and not in_evidence:
                    unsupported_claims.append(
                        f"Generated text cites precedent '{case}' which was not in the retrieved evidence."
                    )

        # -------------------------------------------------------------
        # 3. Structural Integrity & Heuristic Claim Verification
        # -------------------------------------------------------------
        total_checked = len(citations)
        has_invalid = len(invalid_citations) > 0
        has_unsupported = len(unsupported_claims) > 0

        # Calculate validation score
        if total_checked == 0:
            # If no citations were expected (e.g. empty or abstention notice)
            if "insufficient evidence" in generated_answer.lower():
                validation_score = 1.0
                is_valid = True
            else:
                validation_score = 0.0
                is_valid = False
        else:
            struct_score = len(valid_citations) / total_checked
            penalty = 0.25 * len(unsupported_claims)
            validation_score = max(0.0, round(struct_score - penalty, 4))
            is_valid = (not has_invalid) and (not has_unsupported) and (validation_score >= 0.70)

        # Surface claim overlap check (Heuristic)
        claim_overlap_score = self._compute_surface_overlap(generated_answer, combined_evidence_corpus)

        summary_msg = (
            f"Validation passed ({len(valid_citations)}/{total_checked} valid citations)."
            if is_valid
            else f"Validation failed ({len(invalid_citations)} invalid citations, {len(unsupported_claims)} unsupported references detected)."
        )

        return {
            "valid": is_valid,
            "citations_checked": total_checked,
            "valid_citations": valid_citations,
            "invalid_citations": invalid_citations,
            "unsupported_claims": unsupported_claims,
            "validation_score": validation_score,
            "structural_validation": {
                "all_docs_exist": all(
                    c["document_id"] in self.parent_store for c in valid_citations
                ) if self.parent_store else True,
                "all_docs_in_retrieved_evidence": not any(
                    inv["reason"] == "UNRETRIEVED_EVIDENCE_CITED" for inv in invalid_citations
                ),
                "has_required_metadata": not any(
                    inv["reason"] == "MISSING_REQUIRED_METADATA" for inv in invalid_citations
                ),
            },
            "claim_verification": {
                "level": "surface_token_overlap",
                "overlap_score": claim_overlap_score,
                "disclaimer": (
                    "Structural citation validation verifies document existence and retrieval provenance. "
                    "Semantic factual verification is heuristic and does not guarantee complete legal correctness."
                ),
            },
            "summary": summary_msg,
        }

    def _compute_surface_overlap(self, text: str, evidence: str) -> float:
        """Heuristic surface token overlap between answer assertions and retrieved text."""
        if not text or not evidence:
            return 0.0
        words_text = set(re.findall(r"\b[a-zA-Z]{4,}\b", text.lower()))
        words_evidence = set(re.findall(r"\b[a-zA-Z]{4,}\b", evidence.lower()))
        if not words_text:
            return 0.0
        overlap = words_text.intersection(words_evidence)
        return round(len(overlap) / len(words_text), 4)
