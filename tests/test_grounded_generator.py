"""
Unit tests for Grounded Generator (Stage 4).
Verifies:
- Grounded generation derived exclusively from supplied evidence
- Distinct separation between direct evidence and legal analysis
- Structured citation generation without hallucination
- Safe handling of missing/insufficient evidence
"""

import pytest
from rag.generator import GroundedGenerator


@pytest.fixture
def mock_recovered_context():
    return {
        "parents": [
            {
                "document_id": "constitution_art_21",
                "doc_type": "constitution",
                "article_number": "Article 21",
                "title": "Protection of life and personal liberty",
                "part": "Part III",
                "category": "Fundamental Rights",
                "full_text": "No person shall be deprived of his life or personal liberty except according to procedure established by law.",
                "explanation": "Guarantees that no person's life or personal liberty can be encroached upon arbitrarily.",
                "supporting_children": [
                    {
                        "chunk_id": "art_21_chunk_0",
                        "text": "No person shall be deprived of his life or personal liberty except according to procedure established by law.",
                        "rank": 1,
                        "score": 0.95,
                    }
                ],
            },
            {
                "document_id": "judgment_puttaswamy_2017",
                "doc_type": "judgment",
                "case_name": "Justice K.S. Puttaswamy v. Union of India",
                "citation": "(2017) 10 SCC 1",
                "year": 2017,
                "bench": "9-Judge Bench",
                "facts": "Aadhaar scheme challenge.",
                "ratio_decidendi": "Privacy is an intrinsic element of life and liberty guaranteed under Article 21.",
                "verdict": "Unanimously affirmed privacy as a Fundamental Right.",
                "key_takeaways": ["Paved way for data protection regime."],
                "supporting_children": [
                    {
                        "chunk_id": "putta_chunk_0",
                        "text": "Privacy is an intrinsic element of life and liberty.",
                        "rank": 2,
                        "score": 0.88,
                    }
                ],
            },
        ],
        "formatted_context": "=== SOURCE DOCUMENT 1 ===...",
    }


class TestGroundedGenerator:
    """Verifies GroundedGenerator behavior."""

    def test_offline_grounded_generation_structure(self, mock_recovered_context):
        """Offline synthesizer produces structured sections distinguishing evidence and analysis."""
        generator = GroundedGenerator()  # Offline by default when test runs without API call
        res = generator.generate(
            query="What does Article 21 guarantee and how does privacy relate to it?",
            recovered_context=mock_recovered_context,
        )

        assert "answer" in res
        assert "citations" in res
        assert res["has_insufficient_evidence"] is False

        # Verify distinguished sections exist
        sections = res["distinguished_sections"]
        assert "evidence" in sections
        assert "analysis" in sections
        assert "citations" in sections

        # Evidence section contains exact quotes
        assert "Article 21" in sections["evidence"]
        assert "[Doc: constitution_art_21]" in sections["evidence"]
        assert "[Doc: judgment_puttaswamy_2017]" in sections["evidence"]

        # Analysis section contains legal synthesis
        assert "Analysis of Article 21" in sections["analysis"]
        assert "Legal Doctrine in Justice K.S. Puttaswamy" in sections["analysis"]

        # Citations list contains structured objects
        citations = res["citations"]
        assert len(citations) == 2
        assert citations[0]["document_id"] == "constitution_art_21"
        assert citations[0]["citation_key"] == "[Doc: constitution_art_21]"
        assert citations[1]["document_id"] == "judgment_puttaswamy_2017"

    def test_insufficient_evidence_handling(self):
        """Empty context triggers safe insufficient evidence notice rather than hallucination."""
        generator = GroundedGenerator()
        res = generator.generate(
            query="Explain Article 9999",
            recovered_context={"parents": []},
        )

        assert res["has_insufficient_evidence"] is True
        assert res["citations"] == []
        assert "Insufficient Evidence" in res["answer"]
        assert "generation has been safely withheld" in res["answer"]

    def test_citation_metadata_integrity(self, mock_recovered_context):
        """Structured citations retain complete metadata fields for downstream validator."""
        generator = GroundedGenerator()
        res = generator.generate("Test query", mock_recovered_context)
        for cit in res["citations"]:
            assert "document_id" in cit
            assert "source_title" in cit
            assert "doc_type" in cit
            assert "citation_key" in cit
            assert "supporting_chunk_ids" in cit
            assert isinstance(cit["supporting_chunk_ids"], list)

    def test_api_failure_and_timeout_fallback(self, mock_recovered_context):
        """Simulate external LLM API failure/timeout; ensure graceful fallback to deterministic synthesis."""
        from unittest.mock import MagicMock

        generator = GroundedGenerator()
        generator.llm_available = True
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = TimeoutError("Simulated Gemini API network timeout")
        generator.llm = mock_llm

        res = generator.generate(
            query="What is Article 21?",
            recovered_context=mock_recovered_context,
        )

        assert res["used_llm"] is False
        assert "Article 21" in res["answer"]
        assert len(res["citations"]) > 0
        assert res["has_insufficient_evidence"] is False
