"""
Unit tests for NLP preprocessing, language detection, and query expansion modules.
"""

import pytest
from nlp.preprocessing import (
    clean_unicode_and_quotes,
    expand_legal_abbreviations,
    normalize_legal_text,
    tokenize_query,
    extract_keywords,
)
from nlp.language_detection import (
    detect_language,
    detect_script,
)
from nlp.query_expansion import (
    QueryExpander,
    get_query_expander,
)


class TestNLPPreprocessing:
    """Verifies text normalization, abbreviation expansion, and tokenization."""

    def test_unicode_and_quotes_cleaning(self):
        text = "“Article 21” protects ‘life’ and – liberty…"
        cleaned = clean_unicode_and_quotes(text)
        assert '"Article 21"' in cleaned
        assert "'life'" in cleaned
        assert "-" in cleaned
        assert "..." in cleaned

    def test_legal_abbreviations_expansion(self):
        query = "What did the SC and CJI hold in Art. 21 u/a COI vs. UOI?"
        expanded = expand_legal_abbreviations(query)
        assert "Supreme Court" in expanded
        assert "Chief Justice of India" in expanded
        assert "Article 21" in expanded
        assert "under Article" in expanded
        assert "Constitution of India" in expanded
        assert "Union of India" in expanded
        assert "v." in expanded

    def test_normalize_legal_text(self):
        text = "   Art. 19(1)(a)   guarantees  freedom of speech.   \n\n\n  "
        normalized = normalize_legal_text(text)
        assert normalized.startswith("Article 19(1)(a)")
        assert "  " not in normalized

    def test_tokenize_query(self):
        tokens = tokenize_query("Article 19(1)(a) and Section 66A v. State")
        assert "Article" in tokens
        assert "19(1)(a)" in tokens or "19(1)(a)" in " ".join(tokens)
        assert "Section" in tokens
        assert "66A" in tokens

    def test_extract_keywords(self):
        kws = extract_keywords("What is the basic structure doctrine under Article 368?")
        assert "basic" in kws
        assert "structure" in kws
        assert "doctrine" in kws
        assert "article" in kws
        assert "368" in kws
        # Common stopwords removed
        assert "what" not in kws
        assert "is" not in kws
        assert "the" not in kws


class TestLanguageDetection:
    """Verifies language identification for English vs Indic/Unknown queries."""

    def test_detect_english_query(self):
        res = detect_language("What is the fundamental right to personal liberty under Article 21?")
        assert res["is_english"] is True
        assert res["language"] == "en"
        assert res["script"] == "latin"
        assert res["confidence"] >= 0.8

    def test_detect_devanagari_hindi(self):
        res = detect_language("अनुच्छेद 21 के तहत जीवन और व्यक्तिगत स्वतंत्रता का अधिकार क्या है?")
        assert res["is_english"] is False
        assert res["language"] == "hi"
        assert res["script"] == "devanagari"
        assert res["confidence"] >= 0.9

    def test_detect_tamil(self):
        res = detect_language("அரசியலமைப்பு சட்டம் பிரிவு 21")
        assert res["is_english"] is False
        assert res["script"] == "tamil"

    def test_detect_empty_string(self):
        res = detect_language("")
        assert res["is_english"] is False
        assert res["language"] == "unknown"


class TestQueryExpansion:
    """Verifies controlled, deterministic legal query expansion."""

    @pytest.fixture
    def expander(self):
        return get_query_expander()

    def test_expand_privacy_concept(self, expander):
        res = expander.expand("Can the state infringe on privacy?", max_terms=3, enabled=True)
        assert res["was_expanded"] is True
        assert len(res["expanded_terms"]) <= 3
        assert any("Article 21" in t or "privacy" in t.lower() or "liberty" in t.lower() for t in res["expanded_terms"])
        assert "infringe on privacy" in res["expanded_query"]

    def test_expand_disabled_toggle(self, expander):
        res = expander.expand("Can the state infringe on privacy?", enabled=False)
        assert res["was_expanded"] is False
        assert res["expanded_terms"] == []
        assert res["expanded_query"] == "Can the state infringe on privacy?"

    def test_no_circular_duplication(self, expander):
        query = "Article 21 right to privacy personal liberty"
        res = expander.expand(query, max_terms=2, enabled=True)
        # Terms already present in query should not be duplicated
        for term in res["expanded_terms"]:
            assert term.lower() not in query.lower()

    def test_expand_empty_query(self, expander):
        res = expander.expand("")
        assert res["was_expanded"] is False
        assert res["expanded_terms"] == []
