"""
Unit tests for Citation Validator (Stage 4).
Verifies:
- Structural validation of declared citations
- Detection of non-existent documents, unretrieved evidence, and missing metadata
- Detection of ungrounded references in generated text
- Explicit separation of structural validation from heuristic claim verification
"""

import pytest
from rag.citation_validator import CitationValidator


@pytest.fixture
def mock_parent_store():
    return {
        "constitution_art_21": {
            "document_id": "constitution_art_21",
            "article_number": "Article 21",
            "title": "Protection of life and personal liberty",
            "doc_type": "constitution",
        },
        "constitution_art_14": {
            "document_id": "constitution_art_14",
            "article_number": "Article 14",
            "title": "Equality before law",
            "doc_type": "constitution",
        },
        "judgment_puttaswamy_2017": {
            "document_id": "judgment_puttaswamy_2017",
            "case_name": "Justice K.S. Puttaswamy v. Union of India",
            "citation": "(2017) 10 SCC 1",
            "doc_type": "judgment",
        },
    }


@pytest.fixture
def mock_recovered_context():
    return {
        "parents": [
            {
                "document_id": "constitution_art_21",
                "article_number": "Article 21",
                "title": "Protection of life and personal liberty",
                "doc_type": "constitution",
                "full_text": "No person shall be deprived of his life or personal liberty.",
                "supporting_children": [{"chunk_id": "c_21_0", "text": "No person shall be deprived"}],
            }
        ],
        "child_evidence": [{"chunk_id": "c_21_0", "text": "No person shall be deprived"}],
    }


class TestCitationValidator:
    """Verifies CitationValidator behavior."""

    def test_valid_citations_pass(self, mock_parent_store, mock_recovered_context):
        """Citations that exist in parent store and were retrieved pass validation."""
        validator = CitationValidator(parent_store=mock_parent_store)

        citations = [
            {
                "citation_key": "[Doc: constitution_art_21]",
                "document_id": "constitution_art_21",
                "source_title": "Article 21",
                "doc_type": "constitution",
                "supporting_chunk_ids": ["c_21_0"],
            }
        ]
        answer = "Under Article 21, life and liberty are protected [Doc: constitution_art_21]."

        res = validator.validate(answer, citations, mock_recovered_context)
        assert res["valid"] is True
        assert res["citations_checked"] == 1
        assert len(res["valid_citations"]) == 1
        assert len(res["invalid_citations"]) == 0
        assert len(res["unsupported_claims"]) == 0
        assert res["validation_score"] >= 0.70

    def test_nonexistent_document_fails(self, mock_parent_store, mock_recovered_context):
        """Citation with a fabricated document ID fails validation."""
        validator = CitationValidator(parent_store=mock_parent_store)

        citations = [
            {
                "citation_key": "[Doc: fake_doc_999]",
                "document_id": "fake_doc_999",
                "source_title": "Fake Law",
                "doc_type": "constitution",
            }
        ]
        answer = "Fake claim [Doc: fake_doc_999]."

        res = validator.validate(answer, citations, mock_recovered_context)
        assert res["valid"] is False
        assert len(res["invalid_citations"]) == 1
        assert res["invalid_citations"][0]["reason"] == "DOCUMENT_DOES_NOT_EXIST"

    def test_unretrieved_evidence_fails(self, mock_parent_store, mock_recovered_context):
        """Citation to a document that exists in corpus but was NOT retrieved fails."""
        validator = CitationValidator(parent_store=mock_parent_store)

        citations = [
            {
                "citation_key": "[Doc: constitution_art_14]",
                "document_id": "constitution_art_14",  # In parent store, but NOT in recovered_context!
                "source_title": "Article 14",
                "doc_type": "constitution",
            }
        ]
        answer = "Equality under Article 14 [Doc: constitution_art_14]."

        res = validator.validate(answer, citations, mock_recovered_context)
        assert res["valid"] is False
        assert len(res["invalid_citations"]) == 1
        assert res["invalid_citations"][0]["reason"] == "UNRETRIEVED_EVIDENCE_CITED"

    def test_missing_metadata_detected(self, mock_parent_store, mock_recovered_context):
        """Citation missing required metadata fails validation."""
        validator = CitationValidator(parent_store=mock_parent_store)

        citations = [
            {
                "citation_key": "[Doc: constitution_art_21]",
                "document_id": "constitution_art_21",
                # missing source_title and doc_type!
            }
        ]
        answer = "Claim."

        res = validator.validate(answer, citations, mock_recovered_context)
        assert res["valid"] is False
        assert len(res["invalid_citations"]) == 1
        assert res["invalid_citations"][0]["reason"] == "MISSING_REQUIRED_METADATA"

    def test_unsupported_case_mention_in_text(self, mock_parent_store, mock_recovered_context):
        """Detects ungrounded mentions of landmark cases not present in retrieved context."""
        validator = CitationValidator(parent_store=mock_parent_store)

        citations = [
            {
                "citation_key": "[Doc: constitution_art_21]",
                "document_id": "constitution_art_21",
                "source_title": "Article 21",
                "doc_type": "constitution",
            }
        ]
        # Text mentions Kesavananda Bharati, but Kesavananda was NOT retrieved!
        answer = "Under Article 21 [Doc: constitution_art_21], and the court held in Kesavananda Bharati that..."

        res = validator.validate(answer, citations, mock_recovered_context)
        assert len(res["unsupported_claims"]) > 0
        assert any("Kesavananda" in c for c in res["unsupported_claims"])
        assert res["valid"] is False

    def test_claim_verification_disclaimer_present(self, mock_parent_store, mock_recovered_context):
        """Ensures structural validation is clearly separated from heuristic claim verification."""
        validator = CitationValidator(parent_store=mock_parent_store)
        res = validator.validate("Safe answer", [], mock_recovered_context)

        claim_ver = res["claim_verification"]
        assert "disclaimer" in claim_ver
        assert "Semantic factual verification is heuristic" in claim_ver["disclaimer"]
        assert "Structural citation validation" in claim_ver["disclaimer"]
