"""
Unit tests for Parent-Child Context Recovery (Stage 4).
Verifies:
- Parent document recovery from winning child chunks
- Deduplication of parent contexts when multiple child chunks share a parent
- Granular provenance tracking
- Structured prompt context rendering
"""

import pytest
from rag.parent_child import ParentChildRecovery


@pytest.fixture
def mock_parent_store():
    return {
        "constitution_art_21": {
            "document_id": "constitution_art_21",
            "doc_type": "constitution",
            "article_number": "Article 21",
            "title": "Protection of life and personal liberty",
            "part": "Part III",
            "category": "Right to Freedom",
            "raw_text": "No person shall be deprived of his life or personal liberty except according to procedure established by law.",
            "explanation": "Guarantees fundamental right to life and liberty.",
        },
        "judgment_puttaswamy_2017": {
            "document_id": "judgment_puttaswamy_2017",
            "doc_type": "judgment",
            "case_name": "Justice K.S. Puttaswamy v. Union of India",
            "citation": "(2017) 10 SCC 1",
            "year": 2017,
            "bench": "9-Judge Bench",
            "facts": "Challenge to biometric Aadhaar identity scheme.",
            "ratio_decidendi": "Right to privacy is an intrinsic part of life and personal liberty under Article 21.",
            "verdict": "Unanimously affirmed privacy as a Fundamental Right.",
        },
    }


class TestParentChildRecovery:
    """Verifies ParentChildRecovery behavior."""

    def test_recover_empty_chunks(self):
        """Recovery handles empty chunk list safely."""
        recovery = ParentChildRecovery(parent_store={})
        res = recovery.recover([])
        assert res["parents"] == []
        assert res["parent_count"] == 0
        assert res["child_count"] == 0
        assert res["formatted_context"] == ""

    def test_recover_single_parent_multiple_children(self, mock_parent_store):
        """Multiple child chunks belonging to the same parent are deduplicated cleanly."""
        recovery = ParentChildRecovery(parent_store=mock_parent_store)

        ranked_chunks = [
            {
                "chunk_id": "art_21_chunk_0",
                "document_id": "constitution_art_21",
                "text": "No person shall be deprived of his life...",
                "rerank_score": 2.5,
                "rank": 1,
            },
            {
                "chunk_id": "art_21_chunk_1",
                "document_id": "constitution_art_21",
                "text": "...or personal liberty except according to procedure established by law.",
                "rerank_score": 1.8,
                "rank": 2,
            },
        ]

        res = recovery.recover(ranked_chunks)

        # Crucial check: Only ONE parent record must exist
        assert res["parent_count"] == 1
        assert len(res["parents"]) == 1

        parent = res["parents"][0]
        assert parent["document_id"] == "constitution_art_21"
        assert parent["article_number"] == "Article 21"
        assert parent["best_rank"] == 1
        assert parent["best_score"] == 2.5

        # Both children must be preserved as supporting evidence
        assert len(parent["supporting_children"]) == 2
        child_ids = [c["chunk_id"] for c in parent["supporting_children"]]
        assert "art_21_chunk_0" in child_ids
        assert "art_21_chunk_1" in child_ids

        # Total child count preserved
        assert res["child_count"] == 2

    def test_provenance_preservation(self, mock_parent_store):
        """Provenance mapping accurately associates each child chunk with its parent document."""
        recovery = ParentChildRecovery(parent_store=mock_parent_store)

        ranked_chunks = [
            {
                "chunk_id": "chunk_art21",
                "document_id": "constitution_art_21",
                "text": "No person shall be deprived of his life",
                "score": 0.03,
                "rank": 1,
            },
            {
                "chunk_id": "chunk_putta",
                "document_id": "judgment_puttaswamy_2017",
                "text": "Privacy is an intrinsic part of life and liberty",
                "score": 0.02,
                "rank": 2,
            },
        ]

        res = recovery.recover(ranked_chunks)

        assert res["parent_count"] == 2
        assert res["child_to_parent_map"]["chunk_art21"] == "constitution_art_21"
        assert res["child_to_parent_map"]["chunk_putta"] == "judgment_puttaswamy_2017"

        prov_records = res["provenance_records"]
        assert len(prov_records) == 2
        assert prov_records[0]["chunk_id"] == "chunk_art21"
        assert prov_records[0]["parent_id"] == "constitution_art_21"
        assert prov_records[0]["rank"] == 1

    def test_format_context_for_prompt(self, mock_parent_store):
        """Prompt context includes document ID markers, full text, and exact child passages."""
        recovery = ParentChildRecovery(parent_store=mock_parent_store)

        ranked_chunks = [
            {
                "chunk_id": "c1",
                "document_id": "constitution_art_21",
                "text": "Evidence snippet Article 21",
                "score": 1.0,
                "rank": 1,
            }
        ]

        res = recovery.recover(ranked_chunks)
        ctx = res["formatted_context"]

        assert "[DocID: constitution_art_21]" in ctx
        assert "Article 21" in ctx
        assert "Protection of life and personal liberty" in ctx
        assert "Evidence snippet Article 21" in ctx
        assert "Exact Retrieved Child Evidence Passages" in ctx

    def test_missing_parent_fallback(self):
        """If a parent_id is not in parent_store, builds a graceful fallback parent record."""
        recovery = ParentChildRecovery(parent_store={})

        ranked_chunks = [
            {
                "chunk_id": "unknown_chunk_1",
                "document_id": "unregistered_doc_123",
                "text": "Some constitutional provision text",
                "score": 0.5,
                "rank": 1,
            }
        ]

        res = recovery.recover(ranked_chunks)
        assert res["parent_count"] == 1
        assert res["parents"][0]["document_id"] == "unregistered_doc_123"
        assert len(res["parents"][0]["supporting_children"]) == 1
