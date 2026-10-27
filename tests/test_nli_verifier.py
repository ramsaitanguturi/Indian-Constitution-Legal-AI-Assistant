"""
Unit and Regression Tests for Claim-Level Natural Language Inference (NLI) Verifier.
Validates:
1. Sentence and proposition decomposition.
2. Direct entailment of supported constitutional assertions.
3. Detection of statutory contradictions and negative polarity inversions.
4. Neutral classification of ungrounded or out-of-scope assertions.
5. End-to-end integration with CitationValidator and abstention triggers.
"""

import pytest
from rag.nli_verifier import NLIVerifier, get_nli_verifier
from rag.citation_validator import CitationValidator


@pytest.fixture
def nli_instance():
    return NLIVerifier(entailment_threshold=0.60, contradiction_threshold=0.50, use_neural_model=False)


@pytest.fixture
def sample_evidence_context():
    return {
        "parents": [
            {
                "document_id": "parent_const_art_021",
                "article_number": "Article 21",
                "title": "Protection of life and personal liberty",
                "doc_type": "constitution",
                "raw_text": (
                    "No person shall be deprived of his life or personal liberty except according to procedure "
                    "established by law. The right to life includes the right to live with human dignity and privacy."
                ),
                "text": "No person shall be deprived of his life or personal liberty except according to procedure established by law.",
                "explanation": "Guarantees protection against arbitrary executive and legislative deprivation of life and personal liberty.",
                "supporting_children": []
            },
            {
                "document_id": "parent_const_art_017",
                "article_number": "Article 17",
                "title": "Abolition of Untouchability",
                "doc_type": "constitution",
                "raw_text": (
                    "Untouchability is abolished and its practice in any form is forbidden. "
                    "The enforcement of any disability arising out of Untouchability shall be an offence punishable in accordance with law."
                ),
                "text": "Untouchability is abolished and its practice in any form is forbidden.",
                "explanation": "Absolute abolition of untouchability with zero exceptions.",
                "supporting_children": []
            }
        ],
        "child_evidence": [
            {
                "chunk_id": "child_art_21_0",
                "text": "No person shall be deprived of his life or personal liberty except according to procedure established by law."
            }
        ]
    }


class TestNLIVerifier:
    """Verifies proposition splitting, entailment scoring, and contradiction detection."""

    def test_split_into_claims_clean_sentences(self, nli_instance):
        """Verifies decomposition into atomic factual claims while filtering headers and citations."""
        answer = (
            "### Constitutional Analysis\n"
            "Article 21 guarantees protection of life and personal liberty [Doc: parent_const_art_021]. "
            "In Puttaswamy, the Supreme Court held that the right to privacy is intrinsic to life and liberty. "
            "* Key Takeaways:\n"
            "- The State cannot arbitrarily deprive citizens of personal liberty without law."
        )
        claims = nli_instance.split_into_claims(answer)
        assert len(claims) >= 2
        for c in claims:
            assert "[Doc:" not in c
            assert not c.startswith("#")
            assert len(c) > 15

    def test_supported_claim_is_entailed(self, nli_instance, sample_evidence_context):
        """Supported claim that matches statutory evidence is classified as ENTAILMENT."""
        claim = "No person shall be deprived of his life or personal liberty except according to procedure established by law."
        passages = [p["raw_text"] for p in sample_evidence_context["parents"]]
        res = nli_instance.evaluate_claim(claim, passages)

        assert res["verdict"] == "ENTAILMENT"
        assert res["confidence"] >= 0.60
        assert "parent_const_art_021" in sample_evidence_context["parents"][0]["document_id"]

    def test_contradicted_claim_is_detected(self, nli_instance, sample_evidence_context):
        """Claim stating untouchability is permitted directly contradicts Article 17 text."""
        # Evidence states: "Untouchability is abolished and its practice in any form is forbidden"
        contradicted_claim = "The practice of untouchability is permitted in certain private institutions under Article 17."
        passages = [p["raw_text"] for p in sample_evidence_context["parents"]]
        res = nli_instance.evaluate_claim(contradicted_claim, passages)

        assert res["verdict"] == "CONTRADICTION"
        assert res["confidence"] > 0.70

    def test_unsupported_claim_is_neutral(self, nli_instance, sample_evidence_context):
        """Claim about commercial tax rates has zero overlap and is classified as NEUTRAL."""
        unrelated_claim = "The Goods and Services Tax council levied an eighteen percent slab rate on manufacturing goods."
        passages = [p["raw_text"] for p in sample_evidence_context["parents"]]
        res = nli_instance.evaluate_claim(unrelated_claim, passages)

        assert res["verdict"] == "NEUTRAL"

    def test_verify_answer_aggregates_breakdown(self, nli_instance, sample_evidence_context):
        """Full answer verification correctly aggregates entailed, neutral, and contradicted claims."""
        answer = (
            "Article 21 guarantees that no person shall be deprived of life or personal liberty except according to procedure established by law. "
            "Furthermore, commercial tax rates under GST were set at 18 percent for all manufactured products."
        )
        report = nli_instance.verify_answer(answer, sample_evidence_context)

        assert report["total_claims"] == 2
        assert report["entailed_claims"] == 1
        assert report["neutral_claims"] == 1
        assert report["contradicted_claims"] == 0
        assert report["has_contradictions"] is False
        assert report["nli_status"] in ["PARTIALLY_GROUNDED", "VERIFIED_ENTAILED"]

    def test_contradiction_fails_citation_validation(self, sample_evidence_context):
        """A generated response containing an overt contradiction fails citation validation."""
        validator = CitationValidator(
            parent_store={p["document_id"]: p for p in sample_evidence_context["parents"]}
        )
        answer = (
            "Article 17 allows the practice of untouchability under certain customary exceptions. [Doc: parent_const_art_017]"
        )
        citations = [{
            "document_id": "parent_const_art_017",
            "citation_key": "[Doc: parent_const_art_017]",
            "source_title": "Abolition of Untouchability",
            "doc_type": "constitution"
        }]

        result = validator.validate(answer, citations, sample_evidence_context)

        # Must fail because claim contradicts Article 17 statutory text
        assert result["valid"] is False
        assert any("contradicted" in u.lower() for u in result["unsupported_claims"])
        assert result["nli_verification"]["has_contradictions"] is True
