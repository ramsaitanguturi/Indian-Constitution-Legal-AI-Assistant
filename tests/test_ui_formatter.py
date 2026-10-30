"""
Unit tests for ui_formatter module.
Validates that:
1. FormattedLegalAnswer is correctly created for standard query results.
2. Sections are structured into Direct Answer, Legal Provisions, Judgments, and Exceptions.
3. No empty sections are forced.
4. Abstentions are handled gracefully.
5. Excerpts are compact and do not exceed limits.
"""

import pytest
from rag.ui_formatter import format_legal_pipeline_result, FormattedLegalAnswer
from rag.pipeline import PipelineResult


def test_format_legal_pipeline_result_with_parents():
    dummy_res = PipelineResult(
        original_query="What is Article 21?",
        normalized_query="what is article 21",
        language={"language": "en", "is_english": True, "confidence": 1.0},
        intent={"intent": "ARTICLE_LOOKUP", "confidence": 0.9},
        entities={"ARTICLE": ["Article 21"]},
        linked_entities=[],
        expanded_query="what is article 21",
        routing_decision={"strategy": "ARTICLE_SEARCH"},
        retrieved_chunks=[],
        reranked_chunks=[],
        parent_context={
            "parents": [
                {
                    "document_id": "parent_const_art_021",
                    "doc_type": "constitution",
                    "article_number": "Article 21",
                    "title": "Protection of life and personal liberty",
                    "part": "Part III",
                    "category": "Fundamental Rights",
                    "raw_text": "No person shall be deprived of his life or personal liberty except according to procedure established by law.",
                    "explanation": "Guarantees that no person's life or liberty can be encroached upon arbitrarily.",
                    "supporting_children": [
                        {"text": "No person shall be deprived of his life or personal liberty...", "chunk_id": "c1", "score": 0.9}
                    ]
                }
            ],
            "parent_count": 1
        },
        citations=[{"document_id": "parent_const_art_021", "citation_key": "[Doc: parent_const_art_021]"}],
        generated_answer="### 📜 Direct Legal Evidence\n\nArticle 21\n\n### ⚖️ Grounded Legal Analysis\n\nAnalysis of Article 21\n\n### 📚 Verified Citations\n\n[Doc: parent_const_art_021]",
        citation_validation={"valid": True, "citations_checked": 1, "invalid_citations": []},
        confidence={"confidence_score": 0.88, "confidence_level": "HIGH"},
        abstained=False
    )

    formatted = format_legal_pipeline_result(dummy_res)
    assert isinstance(formatted, FormattedLegalAnswer)
    assert not formatted.is_abstained
    assert "Article 21" in formatted.direct_answer
    assert len(formatted.provisions) == 1
    assert formatted.provisions[0].article_or_section == "Article 21"
    assert formatted.provisions[0].document_id == "parent_const_art_021"
    assert len(formatted.provisions[0].excerpt) > 0
    assert len(formatted.provisions[0].excerpt) <= 280
    assert len(formatted.judgments) == 0  # Not forced!
    assert formatted.confidence_level == "HIGH"
    assert formatted.citations_valid is True


def test_format_legal_pipeline_result_abstention():
    dummy_res = PipelineResult(
        original_query="What is the weather today?",
        normalized_query="what is the weather today",
        language={"language": "en", "is_english": True, "confidence": 1.0},
        intent={"intent": "OUT_OF_SCOPE", "confidence": 0.95},
        entities={},
        linked_entities=[],
        expanded_query="what is the weather today",
        routing_decision={"strategy": "OUT_OF_SCOPE"},
        retrieved_chunks=[],
        reranked_chunks=[],
        parent_context={"parents": [], "parent_count": 0},
        citations=[],
        generated_answer="I cannot answer this query.",
        citation_validation={"valid": True, "citations_checked": 0, "invalid_citations": []},
        confidence={"confidence_score": 0.0, "confidence_level": "VERY_LOW"},
        abstained=True,
        abstention_reason="OUT_OF_SCOPE"
    )

    formatted = format_legal_pipeline_result(dummy_res)
    assert formatted.is_abstained
    assert formatted.abstention_reason == "OUT_OF_SCOPE"
    assert len(formatted.provisions) == 0
    assert len(formatted.judgments) == 0
    assert len(formatted.exceptions) == 0

