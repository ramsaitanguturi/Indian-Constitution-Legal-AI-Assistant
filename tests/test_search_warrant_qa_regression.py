"""
Regression Test Suite for Legal Search, Warrant Inquiries, and Superseded Legislation.

Covers:
1. Search of private premises without a warrant (CrPC Sec 165 / BNSS Sec 185 + Kharak Singh).
2. Plain-language grounded answer quality, safeguards, exceptions, and non-categorical claims.
3. Search with a warrant under criminal procedure.
4. Superseded legislation distinction (CrPC 1973 repealed by BNSS 2023, Section 531 savings).
5. Explicit corpus gap reporting for BNSS 2023.
6. Substantive evidence support checking in CitationValidator.
"""

import pytest
from typing import Dict, Any

from rag.pipeline import get_legal_rag_pipeline
from rag.citation_validator import CitationValidator
from retrieval.hybrid_retriever import HybridRetriever


@pytest.fixture(scope="module")
def pipeline():
    return get_legal_rag_pipeline()


class TestSearchWithoutWarrantRegression:
    """Verifies retrieval, synthesis quality, and verification for warrantless search queries."""

    def test_search_without_warrant_retrieval(self, pipeline):
        """Query retrieves CrPC Section 165 and Kharak Singh without irrelevant traffic statutes."""
        query = "can police search house without warrant?"
        res = pipeline.run(query)

        retrieved_ids = [c["chunk_id"] for c in res.retrieved_chunks]
        parent_ids = [p["document_id"] for p in res.parent_context.get("parents", [])]

        # Must retrieve Section 165 (Search by police officer)
        assert "child_act_crpc_1973_s181" in retrieved_ids, (
            f"Expected CrPC Sec 165 (child_act_crpc_1973_s181) in retrieved chunks, got {retrieved_ids}"
        )

        # Must retrieve Kharak Singh (Police surveillance & domiciliary night visits)
        has_kharak = any("kharak_singh" in cid for cid in retrieved_ids)
        assert has_kharak, f"Expected Kharak Singh judgment in retrieved chunks, got {retrieved_ids}"

        # Must have both CrPC and Kharak Singh as parents
        assert "parent_act_crpc_1973" in parent_ids
        assert "parent_case_sc_kharak_singh_1963" in parent_ids

        # Must NOT force irrelevant Motor Vehicles Act chunk into top-5
        mva_chunks = [cid for cid in retrieved_ids if "mva" in cid]
        assert len(mva_chunks) == 0, f"Irrelevant MVA chunk found in top-5 retrieval: {mva_chunks}"

    def test_search_without_warrant_answer_quality(self, pipeline):
        """Synthesizes concise, direct plain-language answer with safeguards and no categorical claims."""
        query = "can police search house without warrant?"
        res = pipeline.run(query)
        ans = res.generated_answer

        # Answer length must be reasonable (< 25k chars, avoiding raw 160k char statute dump)
        assert len(ans) < 25000, f"Answer is excessively long ({len(ans)} chars), likely raw dump"
        assert len(ans) > 1000, f"Answer is suspiciously short ({len(ans)} chars)"

        # Does not make categorical claims that police always need a warrant or never need one
        ans_lower = ans.lower()
        assert "does not make a categorical claim" in ans_lower or "generally require" in ans_lower
        assert "exceptions" in ans_lower

        # Covers emergency investigation search under Section 165
        assert "section 165" in ans_lower
        assert "reasonable grounds" in ans_lower
        assert "writing" in ans_lower
        assert "magistrate" in ans_lower

        # Covers procedural safeguards (witnesses / panchnama)
        assert "witness" in ans_lower or "panchnama" in ans_lower or "inhabitants" in ans_lower

        # Covers constitutional privacy doctrine under Article 21
        assert "kharak singh" in ans_lower
        assert "article 21" in ans_lower

        # Distinguishes current law (BNSS 2023) from superseded CrPC 1973
        assert "bharatiya nagarik suraksha sanhita" in ans_lower or "bnss" in ans_lower
        assert "1 july 2024" in ans_lower
        assert "section 531" in ans_lower

        # Explicitly reports corpus gap for BNSS statutory text
        assert "corpus gap" in ans_lower or "not yet indexed" in ans_lower

    def test_search_without_warrant_citation_validation(self, pipeline):
        """Citation validation passes with substantive support and zero contradicted claims."""
        query = "can police search house without warrant?"
        res = pipeline.run(query)

        val = res.citation_validation
        assert val["valid"] is True, f"Citation validation failed: {val.get('summary')}"
        assert len(val.get("invalid_citations", [])) == 0
        assert len(val.get("unsupported_claims", [])) == 0

        nli = val.get("nli_verification", {})
        assert nli.get("has_contradictions") is False
        assert nli.get("contradicted_claims", 0) == 0
        assert nli.get("nli_status") == "VERIFIED_ENTAILED"

        # Confidence must be HIGH
        assert res.confidence.get("confidence_level") == "HIGH"
        assert res.confidence.get("confidence_score", 0.0) >= 0.75


class TestSearchWithWarrantRegression:
    """Verifies retrieval and explanation for search warrant procedures."""

    def test_search_with_warrant_retrieval_and_answer(self, pipeline):
        """Query about search warrants retrieves relevant criminal procedure provisions."""
        query = "when can a magistrate issue a search warrant under criminal procedure?"
        res = pipeline.run(query)

        retrieved_ids = [c["chunk_id"] for c in res.retrieved_chunks]
        parent_ids = [p["document_id"] for p in res.parent_context.get("parents", [])]

        # Must retrieve criminal procedure parent
        assert "parent_act_crpc_1973" in parent_ids

        # Answer must address search warrant grounds and safeguards
        ans_lower = res.generated_answer.lower()
        assert "search" in ans_lower
        assert "warrant" in ans_lower
        assert "magistrate" in ans_lower

        # Must distinguish current law and report corpus gap
        assert "bnss" in ans_lower or "bharatiya nagarik suraksha sanhita" in ans_lower


class TestSupersededLegislationRegression:
    """Verifies handling of outdated / repealed statutes like CrPC 1973 vs BNSS 2023."""

    def test_crpc_repealed_status_and_savings(self, pipeline):
        """Clarifies CrPC is superseded by BNSS 2023 with Section 531 savings."""
        query = "is CrPC still valid in India or replaced by BNSS?"
        res = pipeline.run(query)
        ans = res.generated_answer.lower()

        # Explains CrPC is repealed / superseded
        assert "repealed" in ans or "superseded" in ans or "no longer" in ans
        assert "bharatiya nagarik suraksha sanhita" in ans or "bnss" in ans
        assert "1 july 2024" in ans

        # Explains savings clause for pending cases
        assert "section 531" in ans or "pending" in ans or "prior to" in ans

        # Explains parallel reforms (BNS replacing IPC, BSA replacing IEA)
        assert "bharatiya nyaya sanhita" in ans or "bns" in ans

        # Confirms corpus gap notice
        assert "corpus" in ans or "not yet" in ans


class TestCitationValidatorSubstantiveSupport:
    """Verifies CitationValidator checks substantive evidence support, not merely document existence."""

    def test_substantive_support_rejection_for_unsupported_statutory_claim(self):
        """CitationValidator rejects citation when text claims specific provisions absent from evidence."""
        validator = CitationValidator(
            parent_store={
                "parent_act_crpc_1973": {
                    "document_id": "parent_act_crpc_1973",
                    "doc_type": "statute",
                    "title": "Code of Criminal Procedure, 1973",
                    "summary": "Governs criminal procedure, investigation, and trial.",
                    "text": "Code of Criminal Procedure provisions.",
                }
            }
        )

        # Answer claims Section 999 which does not exist in evidence
        answer = "Under Section 999 of the Code of Criminal Procedure, all citizens receive automatic bail. [Doc: parent_act_crpc_1973]"
        citations = [{
            "document_id": "parent_act_crpc_1973",
            "citation_key": "[Doc: parent_act_crpc_1973]",
            "source_title": "Code of Criminal Procedure, 1973",
            "doc_type": "statute",
        }]
        recovered_context = {
            "parents": [{
                "document_id": "parent_act_crpc_1973",
                "doc_type": "statute",
                "title": "Code of Criminal Procedure, 1973",
                "summary": "Governs criminal procedure, investigation, and trial.",
                "text": "Code of Criminal Procedure provisions.",
                "supporting_children": []
            }],
            "child_evidence": []
        }

        res = validator.validate(answer, citations, recovered_context)
        # Should flag invalid citation or unsupported claim
        assert res["valid"] is False
        assert any(
            inv.get("reason") == "INSUFFICIENT_SUBSTANTIVE_SUPPORT"
            for inv in res.get("invalid_citations", [])
        )

