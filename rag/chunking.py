"""
Structure-Aware Legal Chunking Engine.

Replaces naive sliding-window character slicing with legal structure-aware chunking:
1. Constitutional Articles: Split on Article -> Clause -> Sub-clause without mid-clause breaking.
2. Constitutional Amendments: Chunks by Provisions, Summary, and Statement of Objects.
3. Supreme Court Judgments: Chunks by structural legal sections: Facts, Issues, Ratio Decidendi, Verdict.
4. Metadata Inheritance: Every child chunk inherits complete provenance and parent metadata.
5. Character vs Token Metrics: Accurately reports character length and estimated token count.
"""

import re
from typing import List, Dict, Any, Optional

from config import (
    CHILD_CHUNK_SIZE,
    CHILD_CHUNK_OVERLAP,
    MAX_CLAUSE_CHUNK_CHARS,
    MIN_CHUNK_CHARS
)


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for a text snippet.
    In English/legal domain, 1 token ~ 0.75 words or ~4 characters.
    We compute token count using whitespace and punctuation word units scaled by 1.3.
    """
    if not text:
        return 0
    words = re.findall(r'\b\w+\b', text)
    # Average subword expansion factor for legal terminology in SentenceTransformers/BERT
    return max(1, int(len(words) * 1.3))


class LegalStructureChunker:
    """
    Structure-Aware Legal Chunker.
    Preserves legal clause boundaries and judgment section semantic coherence.
    """

    def __init__(
        self,
        max_clause_chars: int = MAX_CLAUSE_CHUNK_CHARS,
        min_chunk_chars: int = MIN_CHUNK_CHARS,
        legacy_chunk_size: int = CHILD_CHUNK_SIZE,
        legacy_overlap: int = CHILD_CHUNK_OVERLAP
    ):
        self.max_clause_chars = max_clause_chars
        self.min_chunk_chars = min_chunk_chars
        self.legacy_chunk_size = legacy_chunk_size
        self.legacy_overlap = legacy_overlap

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Expose static token estimator."""
        return estimate_tokens(text)

    def chunk_constitutional_article(self, article: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split a constitutional article into structure-aware child chunks based on its clauses.
        Ensures clauses are not split mid-sentence or mid-phrase.
        """
        if not article:
            return []

        parent_id = f"parent_{article.get('id', article.get('document_id', 'unknown'))}"
        art_num = article.get("article_number", "")
        title = article.get("title", "")
        part = article.get("part", "")
        category = article.get("category", "")
        provenance = article.get("provenance", {})
        source = provenance.get("source", "Constitution of India")

        chunks: List[Dict[str, Any]] = []
        clauses = article.get("clauses", [])

        if clauses and isinstance(clauses, list):
            for idx, cl in enumerate(clauses):
                cl_num = cl.get("clause_number", f"({idx+1})")
                cl_text = cl.get("text", "").strip()
                if not cl_text:
                    continue

                chunk_text = f"{art_num} - {title} [Clause {cl_num}]: {cl_text}"

                # If clause is unusually long, split on sub-clause markers like (a), (b), or sentences
                if len(chunk_text) > self.max_clause_chars:
                    sub_parts = self._split_long_clause(chunk_text, art_num, title, cl_num)
                    for sub_idx, sub_text in enumerate(sub_parts):
                        sub_id = f"child_const_{article.get('id', 'art')}_{idx}_sub_{sub_idx}"
                        chunks.append({
                            "child_id": sub_id,
                            "parent_id": parent_id,
                            "doc_type": "constitution",
                            "document_type": "constitution_article",
                            "article_number": art_num,
                            "title": title,
                            "part": part,
                            "category": category,
                            "section": f"Clause {cl_num} (Part {sub_idx+1})",
                            "clause_number": cl_num,
                            "text": sub_text,
                            "char_count": len(sub_text),
                            "estimated_tokens": estimate_tokens(sub_text),
                            "source": source
                        })
                else:
                    child_id = f"child_const_{article.get('id', 'art')}_cl_{idx}"
                    chunks.append({
                        "child_id": child_id,
                        "parent_id": parent_id,
                        "doc_type": "constitution",
                        "document_type": "constitution_article",
                        "article_number": art_num,
                        "title": title,
                        "part": part,
                        "category": category,
                        "section": f"Clause {cl_num}",
                        "clause_number": cl_num,
                        "text": chunk_text,
                        "char_count": len(chunk_text),
                        "estimated_tokens": estimate_tokens(chunk_text),
                        "source": source
                    })

        # Also add explanation / legal analysis chunk if present
        explanation = article.get("explanation", "").strip()
        hist_context = article.get("historical_context", "").strip()
        if explanation:
            expl_text = f"{art_num} - {title}. Legal Analysis & Scope: {explanation}"
            chunks.append({
                "child_id": f"child_const_{article.get('id', 'art')}_analysis",
                "parent_id": parent_id,
                "doc_type": "constitution",
                "document_type": "constitution_article",
                "article_number": art_num,
                "title": title,
                "part": part,
                "category": category,
                "section": "Legal Analysis & Context",
                "clause_number": "Analysis",
                "text": expl_text,
                "char_count": len(expl_text),
                "estimated_tokens": estimate_tokens(expl_text),
                "source": source
            })

        if hist_context:
            hist_text = f"{art_num} - {title}. Historical Context & Framing: {hist_context}"
            chunks.append({
                "child_id": f"child_const_{article.get('id', 'art')}_history",
                "parent_id": parent_id,
                "doc_type": "constitution",
                "document_type": "constitution_article",
                "article_number": art_num,
                "title": title,
                "part": part,
                "category": category,
                "section": "Historical Context & Framing",
                "clause_number": "History",
                "text": hist_text,
                "char_count": len(hist_text),
                "estimated_tokens": estimate_tokens(hist_text),
                "source": source
            })

        # Fallback if no clauses were defined
        if not chunks:
            raw_text = article.get("text", "").strip()
            if raw_text:
                fallback_chunks = self.chunk_legacy_sliding_window(
                    f"{art_num} - {title}. {raw_text}",
                    chunk_size=self.legacy_chunk_size,
                    overlap=self.legacy_overlap
                )
                for f_idx, f_text in enumerate(fallback_chunks):
                    chunks.append({
                        "child_id": f"child_const_{article.get('id', 'art')}_{f_idx}",
                        "parent_id": parent_id,
                        "doc_type": "constitution",
                        "document_type": "constitution_article",
                        "article_number": art_num,
                        "title": title,
                        "part": part,
                        "category": category,
                        "section": f"Passage {f_idx+1}",
                        "clause_number": "General",
                        "text": f_text,
                        "char_count": len(f_text),
                        "estimated_tokens": estimate_tokens(f_text),
                        "source": source
                    })

        return chunks

    def chunk_amendment(self, amendment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split a constitutional amendment into structure-aware child chunks:
        1. Summary and modified provisions
        2. Statement of Objects and Reasons
        """
        if not amendment:
            return []

        parent_id = f"parent_{amendment.get('id', amendment.get('document_id', 'amend'))}"
        amend_num = amendment.get("amendment_number", "")
        title = amendment.get("title", "")
        year = amendment.get("year", 0)
        source = amendment.get("provenance", {}).get("source", "Official Gazette of India")

        chunks: List[Dict[str, Any]] = []

        # 1. Summary Chunk
        summary = amendment.get("summary", "").strip()
        provs = amendment.get("provisions_modified", [])
        prov_str = ", ".join(provs) if isinstance(provs, list) else str(provs)
        if summary:
            sum_text = f"{title} ({year}). Provisions Modified: {prov_str}. Summary: {summary}"
            chunks.append({
                "child_id": f"child_{amendment.get('id', 'amend')}_summary",
                "parent_id": parent_id,
                "doc_type": "amendment",
                "document_type": "constitution_amendment",
                "amendment_number": amend_num,
                "title": title,
                "year": year,
                "section": "Summary & Provisions",
                "provisions_modified": prov_str,
                "text": sum_text,
                "char_count": len(sum_text),
                "estimated_tokens": estimate_tokens(sum_text),
                "source": source
            })

        # 2. Objects and Reasons Chunk
        objects_reasons = amendment.get("statement_of_objects_and_reasons", "").strip()
        if objects_reasons:
            obj_text = f"{title} ({year}). Statement of Objects and Reasons: {objects_reasons}"
            chunks.append({
                "child_id": f"child_{amendment.get('id', 'amend')}_objects",
                "parent_id": parent_id,
                "doc_type": "amendment",
                "document_type": "constitution_amendment",
                "amendment_number": amend_num,
                "title": title,
                "year": year,
                "section": "Statement of Objects and Reasons",
                "provisions_modified": prov_str,
                "text": obj_text,
                "char_count": len(obj_text),
                "estimated_tokens": estimate_tokens(obj_text),
                "source": source
            })

        return chunks

    def chunk_judgment(self, judgment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split a Supreme Court judgment into structure-aware sections:
        1. Facts
        2. Legal Issues
        3. Ratio Decidendi
        4. Verdict & Holding
        """
        if not judgment:
            return []

        parent_id = f"parent_{judgment.get('id', judgment.get('document_id', 'judg'))}"
        case_name = judgment.get("case_name", "")
        citation = judgment.get("citation", "")
        year = judgment.get("year", 0)
        bench = judgment.get("bench", "")
        arts_ref = judgment.get("articles_referred", [])
        arts_str = ", ".join(arts_ref) if isinstance(arts_ref, list) else str(arts_ref)
        source = judgment.get("provenance", {}).get("source", "Supreme Court Reports")

        chunks: List[Dict[str, Any]] = []

        # Section 1: Facts
        facts = judgment.get("facts", "").strip()
        if facts:
            facts_text = f"{case_name} ({year}, {citation}). BENCH: {bench}. ARTICLES: {arts_str}. FACTS: {facts}"
            chunks.append({
                "child_id": f"child_{judgment.get('id', 'judg')}_facts",
                "parent_id": parent_id,
                "doc_type": "judgment",
                "document_type": "judgment",
                "case_name": case_name,
                "citation": citation,
                "year": year,
                "bench": bench,
                "articles_referred": arts_str,
                "section": "facts",
                "text": facts_text,
                "char_count": len(facts_text),
                "estimated_tokens": estimate_tokens(facts_text),
                "source": source
            })

        # Section 2: Legal Issues
        issues = judgment.get("issues", [])
        if issues:
            issues_str = " ".join(issues) if isinstance(issues, list) else str(issues)
            issues_text = f"{case_name} ({year}). LEGAL ISSUES: {issues_str}"
            chunks.append({
                "child_id": f"child_{judgment.get('id', 'judg')}_issues",
                "parent_id": parent_id,
                "doc_type": "judgment",
                "document_type": "judgment",
                "case_name": case_name,
                "citation": citation,
                "year": year,
                "bench": bench,
                "articles_referred": arts_str,
                "section": "issues",
                "text": issues_text,
                "char_count": len(issues_text),
                "estimated_tokens": estimate_tokens(issues_text),
                "source": source
            })

        # Section 3: Ratio Decidendi
        ratio = judgment.get("ratio_decidendi", "").strip()
        if ratio:
            ratio_text = f"{case_name} ({year}, {citation}). RATIO DECIDENDI: {ratio}"
            chunks.append({
                "child_id": f"child_{judgment.get('id', 'judg')}_ratio",
                "parent_id": parent_id,
                "doc_type": "judgment",
                "document_type": "judgment",
                "case_name": case_name,
                "citation": citation,
                "year": year,
                "bench": bench,
                "articles_referred": arts_str,
                "section": "ratio_decidendi",
                "text": ratio_text,
                "char_count": len(ratio_text),
                "estimated_tokens": estimate_tokens(ratio_text),
                "source": source
            })

        # Section 4: Verdict
        verdict = judgment.get("verdict", "").strip()
        if verdict:
            verdict_text = f"{case_name} ({year}). FINAL VERDICT: {verdict}"
            chunks.append({
                "child_id": f"child_{judgment.get('id', 'judg')}_verdict",
                "parent_id": parent_id,
                "doc_type": "judgment",
                "document_type": "judgment",
                "case_name": case_name,
                "citation": citation,
                "year": year,
                "bench": bench,
                "articles_referred": arts_str,
                "section": "verdict",
                "text": verdict_text,
                "char_count": len(verdict_text),
                "estimated_tokens": estimate_tokens(verdict_text),
                "source": source
            })

        # Section 5: Key Takeaways & Precedents
        takeaways = judgment.get("key_takeaways", [])
        precedents = judgment.get("precedents_overruled", [])
        takeaways_str = " ".join(takeaways) if isinstance(takeaways, list) else str(takeaways)
        precedents_str = ", ".join(precedents) if isinstance(precedents, list) else str(precedents)
        if takeaways_str or precedents_str:
            take_text = f"{case_name} ({year}). KEY TAKEAWAYS: {takeaways_str}" if takeaways_str else f"{case_name} ({year})."
            if precedents_str:
                take_text += f" PRECEDENTS OVERRULED/DISCUSSED: {precedents_str}"

            chunks.append({
                "child_id": f"child_{judgment.get('id', 'judg')}_takeaways",
                "parent_id": parent_id,
                "doc_type": "judgment",
                "document_type": "judgment",
                "case_name": case_name,
                "citation": citation,
                "year": year,
                "bench": bench,
                "articles_referred": arts_str,
                "section": "takeaways_and_precedents",
                "text": take_text,
                "char_count": len(take_text),
                "estimated_tokens": estimate_tokens(take_text),
                "source": source
            })

        # Fallback if document has non-standard format
        if not chunks:
            combined = f"{case_name} ({year}). {facts} {ratio} {verdict}"
            fallback_chunks = self.chunk_legacy_sliding_window(
                combined,
                chunk_size=self.legacy_chunk_size,
                overlap=self.legacy_overlap
            )
            for f_idx, f_text in enumerate(fallback_chunks):
                chunks.append({
                    "child_id": f"child_{judgment.get('id', 'judg')}_{f_idx}",
                    "parent_id": parent_id,
                    "doc_type": "judgment",
                    "document_type": "judgment",
                    "case_name": case_name,
                    "citation": citation,
                    "year": year,
                    "bench": bench,
                    "articles_referred": arts_str,
                    "section": f"Passage {f_idx+1}",
                    "text": f_text,
                    "char_count": len(f_text),
                    "estimated_tokens": estimate_tokens(f_text),
                    "source": source
                })

        return chunks

    def chunk_legacy_sliding_window(
        self,
        text: str,
        chunk_size: int = CHILD_CHUNK_SIZE,
        overlap: int = CHILD_CHUNK_OVERLAP
    ) -> List[str]:
        """
        Original character-based sliding window chunking algorithm.
        Retained for baseline reproducibility and backward compatibility.
        """
        if not text:
            return []

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + chunk_size, text_len)
            # Find word boundary if possible
            if end < text_len:
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space

            chunk = text[start:end].strip()
            if chunk and len(chunk) >= self.min_chunk_chars:
                chunks.append(chunk)
            elif chunk and not chunks:
                chunks.append(chunk)

            start = end - overlap if (end - overlap) > start else end

        return chunks

    def _split_long_clause(self, text: str, art_num: str, title: str, cl_num: str) -> List[str]:
        """Split an excessively long clause at sub-clause markers like (a), (b) or full stops."""
        # Try sub-clause split on pattern ' (a) ', ' (b) '
        sub_markers = re.split(r'(?=\s*\([a-z]\)\s*)', text)
        if len(sub_markers) > 1 and all(len(s.strip()) > 30 for s in sub_markers):
            return [s.strip() for s in sub_markers if s.strip()]

        # Otherwise split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        result_chunks = []
        current = ""

        for s in sentences:
            if len(current) + len(s) + 1 <= self.max_clause_chars:
                current = f"{current} {s}".strip() if current else s
            else:
                if current:
                    result_chunks.append(current)
                current = s

        if current:
            result_chunks.append(current)

        return result_chunks or [text]
