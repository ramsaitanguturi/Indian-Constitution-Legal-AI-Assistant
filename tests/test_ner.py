"""
Unit tests for NLP Legal Named Entity Recognition (NER) module.
Verifies extraction across all 10 entity categories, span boundaries,
confidence scoring, conflict resolution, edge cases, and legacy compatibility.
"""

import pytest
from nlp.legal_ner import LegalNER, get_legal_ner


@pytest.fixture(scope="module")
def ner_instance():
    return get_legal_ner()


class TestLegalNERCategories:
    """Verifies that all 10 legal entity categories are properly identified."""

    def test_extract_article_entities(self, ner_instance):
        text = "What is the scope of Article 21, Art. 14, and Article 19(1)(a)?"
        entities = ner_instance.extract_entities(text)
        assert any("Article 21" in a for a in entities["ARTICLE"])
        assert any("Article 14" in a for a in entities["ARTICLE"])
        assert any("Article 19(1)(A)" in a for a in entities["ARTICLE"])

    def test_extract_preamble_as_article(self, ner_instance):
        text = "Did Kesavananda Bharati hold that the Preamble is an integral part of the Constitution?"
        entities = ner_instance.extract_entities(text)
        assert "Preamble" in entities["ARTICLE"]

    def test_extract_case_entities(self, ner_instance):
        text = "Compare the rulings in Kesavananda Bharati and Justice K.S. Puttaswamy v. Union of India."
        entities = ner_instance.extract_entities(text)
        assert any("Kesavananda Bharati" in c for c in entities["CASE"])
        assert any("Puttaswamy" in c for c in entities["CASE"])

    def test_extract_person_entities(self, ner_instance):
        text = "Dr. B.R. Ambedkar and Justice D.Y. Chandrachud articulated fundamental rights."
        entities = ner_instance.extract_entities(text)
        assert any("Ambedkar" in p for p in entities["PERSON"])
        assert any("Chandrachud" in p for p in entities["PERSON"])

    def test_extract_court_entities(self, ner_instance):
        text = "The Supreme Court of India and the High Court of Delhi have writ jurisdiction."
        entities = ner_instance.extract_entities(text)
        assert any("Supreme Court" in c for c in entities["COURT"])
        assert any("High Court" in c for c in entities["COURT"])

    def test_extract_legal_concept_entities(self, ner_instance):
        text = "Explain the basic structure doctrine, judicial review, and the proportionality test."
        entities = ner_instance.extract_entities(text)
        assert any("basic structure" in c.lower() for c in entities["LEGAL_CONCEPT"])
        assert any("judicial review" in c.lower() for c in entities["LEGAL_CONCEPT"])
        assert any("proportionality" in c.lower() for c in entities["LEGAL_CONCEPT"])

    def test_extract_right_entities(self, ner_instance):
        text = "Does the right to privacy and freedom of speech exist under personal liberty?"
        entities = ner_instance.extract_entities(text)
        assert any("privacy" in r.lower() for r in entities["RIGHT"])
        assert any("speech" in r.lower() for r in entities["RIGHT"])

    def test_extract_amendment_entities(self, ner_instance):
        text = "The 42nd Amendment Act and 44th Constitutional Amendment modified the emergency provisions."
        entities = ner_instance.extract_entities(text)
        assert len(entities["AMENDMENT"]) >= 2
        assert any("42" in a for a in entities["AMENDMENT"])
        assert any("44" in a for a in entities["AMENDMENT"])

    def test_extract_act_entities(self, ner_instance):
        text = "The challenge to the Aadhaar Act and the Information Technology Act under the Constitution of India."
        entities = ner_instance.extract_entities(text)
        assert any("Aadhaar Act" in a for a in entities["ACT"])
        assert any("Information Technology Act" in a for a in entities["ACT"])
        assert any("Constitution of India" in a for a in entities["ACT"])

    def test_extract_section_entities(self, ner_instance):
        text = "The Supreme Court struck down Section 66A and read down Section 377."
        entities = ner_instance.extract_entities(text)
        assert any("Section 66A" in s for s in entities["SECTION"])
        assert any("Section 377" in s for s in entities["SECTION"])

    def test_extract_date_entities(self, ner_instance):
        text = "The judgment was delivered in 1973 and reaffirmed in 2017."
        entities = ner_instance.extract_entities(text)
        assert "1973" in entities["DATE"]
        assert "2017" in entities["DATE"]


class TestLegalNERSpansAndStructure:
    """Verifies span extraction mechanics, character offsets, and conflict handling."""

    def test_span_offsets_and_substring_accuracy(self, ner_instance):
        query = "What did Puttaswamy decide about privacy under Article 21 in 2017?"
        spans = ner_instance.extract_spans(query)
        assert len(spans) >= 4

        for span in spans:
            start = span["start"]
            end = span["end"]
            surface_text = span["text"]
            # Ensure character slices match exact input
            assert query[start:end] == surface_text
            assert span["confidence"] > 0.0
            assert span["label"] in [
                "ARTICLE", "CASE", "PERSON", "COURT", "LEGAL_CONCEPT",
                "RIGHT", "AMENDMENT", "ACT", "SECTION", "DATE"
            ]

    def test_spans_do_not_overlap(self, ner_instance):
        query = "Kesavananda Bharati basic structure doctrine under Article 368"
        spans = ner_instance.extract_spans(query)
        # Check no two spans overlap
        for i in range(len(spans) - 1):
            assert spans[i]["end"] <= spans[i + 1]["start"]


class TestLegalNEREdgeCases:
    """Verifies robustness on edge cases, empty queries, and legacy adapter."""

    def test_empty_string(self, ner_instance):
        entities = ner_instance.extract_entities("")
        assert all(len(items) == 0 for items in entities.values())
        assert ner_instance.extract_spans("") == []

    def test_whitespace_and_punctuation(self, ner_instance):
        entities = ner_instance.extract_entities("   ??? !!! ... ,,,   ")
        assert all(len(items) == 0 for items in entities.values())

    def test_non_legal_query(self, ner_instance):
        entities = ner_instance.extract_entities("How to cook delicious pasta in 10 minutes?")
        assert all(len(items) == 0 for items in entities.values())

    def test_legacy_extractor_format(self, ner_instance):
        query = "Article 21 and Puttaswamy regarding right to privacy"
        legacy = ner_instance.extract_legacy_entities(query)
        assert "articles" in legacy
        assert "cases" in legacy
        assert "concepts" in legacy
        assert any("Article 21" in a for a in legacy["articles"])
        assert any("Puttaswamy" in c for c in legacy["cases"])
        assert any("privacy" in cp for cp in legacy["concepts"])
