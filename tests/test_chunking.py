"""
Comprehensive unit tests for Structure-Aware Legal Chunking and Corpus Datasets.
Verifies clause-level preservation (no mid-clause splits), judgment sectioning,
metadata inheritance, character/token metrics, edge cases, and dataset integrity.
"""

import json
import os
import pytest
from pathlib import Path

from config import (
    CONSTITUTION_ARTICLES_PATH,
    CONSTITUTION_AMENDMENTS_PATH,
    JUDGMENTS_LANDMARKS_PATH,
    MAX_CLAUSE_CHUNK_CHARS,
    MIN_CHUNK_CHARS
)
from rag.chunking import LegalStructureChunker, estimate_tokens
from rag.ingestion import ProductionIngestor


@pytest.fixture(scope="module")
def chunker():
    """Shared LegalStructureChunker instance."""
    return LegalStructureChunker()


# =========================================================================
# 1. Constitutional Article Chunking Tests
# =========================================================================

class TestConstitutionalArticleChunking:
    """Verifies clause-level structure-aware chunking of Constitutional Articles."""

    def test_clause_integrity_no_mid_clause_split(self, chunker):
        """Verifies clauses remain intact without arbitrary character slicing."""
        sample_article = {
            "id": "test_art_21",
            "document_id": "const_art_021",
            "document_type": "constitution_article",
            "article_number": "Article 21",
            "title": "Protection of life and personal liberty",
            "part": "Part III - Fundamental Rights",
            "category": "Fundamental Right",
            "clauses": [
                {
                    "clause_id": "art_21_main",
                    "clause_number": "Main",
                    "text": "No person shall be deprived of his life or personal liberty except according to procedure established by law."
                }
            ],
            "text": "No person shall be deprived of his life or personal liberty except according to procedure established by law.",
            "explanation": "Guarantees right to dignified life and privacy post-Puttaswamy.",
            "historical_context": "Drafted by Constituent Assembly.",
            "provenance": {"source": "GoI Law Ministry", "retrieval_date": "2026-10-08", "version": "1.0"}
        }

        chunks = chunker.chunk_constitutional_article(sample_article)
        assert len(chunks) == 3  # 1 clause chunk + 1 analysis chunk + 1 history chunk

        clause_chunk = chunks[0]
        assert clause_chunk["clause_number"] == "Main"
        assert "Article 21" in clause_chunk["text"]
        assert "procedure established by law" in clause_chunk["text"]
        assert clause_chunk["parent_id"] == "parent_test_art_21"
        assert clause_chunk["doc_type"] == "constitution"
        assert clause_chunk["part"] == "Part III - Fundamental Rights"
        assert clause_chunk["category"] == "Fundamental Right"
        assert clause_chunk["char_count"] > 0
        assert clause_chunk["estimated_tokens"] > 0
        assert clause_chunk["source"] == "GoI Law Ministry"

        analysis_chunk = chunks[1]
        assert analysis_chunk["section"] == "Legal Analysis & Context"
        assert "Puttaswamy" in analysis_chunk["text"]

        history_chunk = chunks[2]
        assert history_chunk["section"] == "Historical Context & Framing"
        assert "Constituent Assembly" in history_chunk["text"]

    def test_multi_clause_article_chunking(self, chunker):
        """Verifies multi-clause articles produce distinct chunks for each clause."""
        sample_article = {
            "id": "test_art_20",
            "document_id": "const_art_020",
            "document_type": "constitution_article",
            "article_number": "Article 20",
            "title": "Protection in respect of conviction for offences",
            "part": "Part III",
            "clauses": [
                {"clause_id": "c1", "clause_number": "(1)", "text": "No person convicted except for violation of law."},
                {"clause_id": "c2", "clause_number": "(2)", "text": "No person prosecuted and punished twice for same offence."},
                {"clause_id": "c3", "clause_number": "(3)", "text": "No accused compelled to be witness against himself."}
            ],
            "explanation": "Protects against ex-post facto laws, double jeopardy, and self-incrimination."
        }

        chunks = chunker.chunk_constitutional_article(sample_article)
        # 3 clauses + 1 analysis chunk = 4 chunks
        assert len(chunks) == 4

        clause_numbers = [c["clause_number"] for c in chunks]
        assert "(1)" in clause_numbers
        assert "(2)" in clause_numbers
        assert "(3)" in clause_numbers
        assert "Analysis" in clause_numbers

    def test_long_clause_sub_clause_splitting(self, chunker):
        """Verifies unusually long clauses split cleanly at sub-clause markers or sentences."""
        long_text = "The State shall not discriminate (a) on grounds of religion; (b) on grounds of race; (c) on grounds of caste. " * 15
        sample_article = {
            "id": "test_art_long",
            "article_number": "Article 999",
            "title": "Long Test Article",
            "clauses": [
                {"clause_id": "c_long", "clause_number": "(1)", "text": long_text}
            ]
        }

        chunks = chunker.chunk_constitutional_article(sample_article)
        assert len(chunks) >= 2
        for c in chunks:
            assert c["char_count"] <= chunker.max_clause_chars + 100
            assert c["parent_id"] == "parent_test_art_long"


# =========================================================================
# 2. Supreme Court Judgment Chunking Tests
# =========================================================================

class TestJudgmentChunking:
    """Verifies structural section chunking of Supreme Court decisions."""

    def test_judgment_structural_sections_extracted(self, chunker):
        """Verifies judgment is structured into Facts, Issues, Ratio Decidendi, and Verdict."""
        sample_judg = {
            "id": "case_test_kesavananda",
            "document_id": "case_sc_kesavananda_1973",
            "document_type": "judgment",
            "case_name": "Kesavananda Bharati v. State of Kerala",
            "citation": "(1973) 4 SCC 225",
            "year": 1973,
            "bench": "13-Judge Bench",
            "articles_referred": ["Article 368", "Article 13"],
            "facts": "Challenge to Kerala land reforms restricting mutt properties.",
            "issues": ["Can Parliament alter the Basic Structure under Article 368?"],
            "ratio_decidendi": "Parliament cannot alter or destroy the Basic Structure of the Constitution.",
            "verdict": "Established the landmark Basic Structure Doctrine.",
            "key_takeaways": ["Preamble is part of the Constitution.", "Limited amending power is basic feature."],
            "provenance": {"source": "Supreme Court Reports", "retrieval_date": "2026-10-08", "version": "Final"}
        }

        chunks = chunker.chunk_judgment(sample_judg)
        assert len(chunks) == 5  # facts, issues, ratio_decidendi, verdict, takeaways_and_precedents

        sections = {c["section"]: c for c in chunks}
        assert "facts" in sections
        assert "issues" in sections
        assert "ratio_decidendi" in sections
        assert "verdict" in sections
        assert "takeaways_and_precedents" in sections

        # Test metadata inheritance
        for c in chunks:
            assert c["parent_id"] == "parent_case_test_kesavananda"
            assert c["doc_type"] == "judgment"
            assert c["case_name"] == "Kesavananda Bharati v. State of Kerala"
            assert c["year"] == 1973
            assert c["citation"] == "(1973) 4 SCC 225"
            assert "Article 368" in c["articles_referred"]
            assert c["source"] == "Supreme Court Reports"
            assert c["char_count"] > 0
            assert c["estimated_tokens"] > 0

        # Test content fidelity
        assert "Basic Structure" in sections["ratio_decidendi"]["text"]
        assert "Kerala land reforms" in sections["facts"]["text"]
        assert "Established the landmark Basic Structure Doctrine" in sections["verdict"]["text"]
        assert "Preamble is part of the Constitution" in sections["takeaways_and_precedents"]["text"]


# =========================================================================
# 3. Constitutional Amendment Chunking Tests
# =========================================================================

class TestAmendmentChunking:
    """Verifies chunking of Constitutional Amendments."""

    def test_amendment_chunks_produced(self, chunker):
        """Verifies amendment chunks contain summary and statement of objects."""
        sample_amend = {
            "id": "amend_044",
            "document_id": "amend_044",
            "document_type": "constitution_amendment",
            "amendment_number": "44th Constitutional Amendment Act",
            "year": 1978,
            "title": "The Constitution (Forty-fourth Amendment) Act, 1978",
            "provisions_modified": ["Article 300A", "Article 352", "Article 359"],
            "summary": "Restored civil liberties post-emergency; removed right to property to Art 300A.",
            "statement_of_objects_and_reasons": "To undo distortions introduced during Emergency.",
            "provenance": {"source": "Official Gazette", "retrieval_date": "2026-10-08", "version": "1.0"}
        }

        chunks = chunker.chunk_amendment(sample_amend)
        assert len(chunks) == 2  # summary + objects

        sections = [c["section"] for c in chunks]
        assert "Summary & Provisions" in sections
        assert "Statement of Objects and Reasons" in sections

        for c in chunks:
            assert c["parent_id"] == "parent_amend_044"
            assert c["doc_type"] == "amendment"
            assert c["year"] == 1978
            assert "Article 300A" in c["provisions_modified"]


# =========================================================================
# 4. Token Estimation and Edge Cases
# =========================================================================

class TestTokenEstimationAndEdgeCases:
    """Verifies token estimation formulas and edge case handling."""

    def test_estimate_tokens_accuracy(self):
        """Token count is roughly 1.3x word count for legal terminology."""
        text = "No person shall be deprived of his life or personal liberty except according to procedure established by law."
        # 18 words * 1.3 ~ 23 tokens
        tokens = estimate_tokens(text)
        assert 18 <= tokens <= 30

    def test_estimate_tokens_empty_string(self):
        """Empty text produces 0 tokens."""
        assert estimate_tokens("") == 0
        assert estimate_tokens(None) == 0

    def test_empty_article_chunking(self, chunker):
        """Empty input dict returns empty chunk list."""
        assert chunker.chunk_constitutional_article({}) == []
        assert chunker.chunk_constitutional_article(None) == []

    def test_empty_judgment_chunking(self, chunker):
        """Empty judgment dict returns empty chunk list."""
        assert chunker.chunk_judgment({}) == []
        assert chunker.chunk_judgment(None) == []

    def test_sliding_window_fallback(self, chunker):
        """Article without clauses falls back gracefully to sliding window."""
        flat_article = {
            "id": "flat_art",
            "article_number": "Article 1000",
            "title": "Flat Article",
            "text": "This is a plain unformatted constitutional article text that should be chunked cleanly."
        }
        chunks = chunker.chunk_constitutional_article(flat_article)
        assert len(chunks) >= 1
        assert "Article 1000" in chunks[0]["text"]


# =========================================================================
# 5. Expanded Corpus Dataset Integrity Tests
# =========================================================================

class TestExpandedCorpusIntegrity:
    """Verifies that the compiled corpus files exist and satisfy Stage 1 scale requirements."""

    def test_constitution_articles_count_and_schema(self):
        """Articles dataset contains >100 articles with full schema and provenance."""
        assert os.path.exists(CONSTITUTION_ARTICLES_PATH)
        with open(CONSTITUTION_ARTICLES_PATH, "r", encoding="utf-8") as f:
            articles = json.load(f)

        assert isinstance(articles, list)
        assert len(articles) > 100, f"Expected >100 articles, got {len(articles)}"

        for art in articles:
            assert "document_id" in art
            assert "article_number" in art
            assert "title" in art
            assert "text" in art
            assert "clauses" in art
            assert "provenance" in art
            assert art["provenance"]["verified"] is True

    def test_constitutional_amendments_count_and_schema(self):
        """Amendments dataset contains landmark amendments."""
        assert os.path.exists(CONSTITUTION_AMENDMENTS_PATH)
        with open(CONSTITUTION_AMENDMENTS_PATH, "r", encoding="utf-8") as f:
            amendments = json.load(f)

        assert isinstance(amendments, list)
        assert len(amendments) >= 15, f"Expected >=15 amendments, got {len(amendments)}"

        for amend in amendments:
            assert "document_id" in amend
            assert "amendment_number" in amend
            assert "year" in amend
            assert "summary" in amend
            assert "provenance" in amend

    def test_landmark_judgments_count_and_schema(self):
        """Judgments dataset contains >100 Supreme Court decisions with full schema."""
        assert os.path.exists(JUDGMENTS_LANDMARKS_PATH)
        with open(JUDGMENTS_LANDMARKS_PATH, "r", encoding="utf-8") as f:
            judgments = json.load(f)

        assert isinstance(judgments, list)
        assert len(judgments) >= 100, f"Expected >=100 judgments, got {len(judgments)}"

        for judg in judgments:
            assert "document_id" in judg
            assert "case_name" in judg
            assert "citation" in judg
            assert "year" in judg
            assert "court" in judg
            assert "facts" in judg
            assert "ratio_decidendi" in judg
            assert "verdict" in judg
            assert "provenance" in judg
            assert judg["provenance"]["verified"] is True
