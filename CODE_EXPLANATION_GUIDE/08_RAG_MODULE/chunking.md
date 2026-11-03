# Structure-Aware Legal Chunking: `rag/chunking.py`

[Back to RAG Module Overview](README.md) • [Back to Main Index](../README.md)

---

## 1. Basic Introduction

### What is this file?
`rag/chunking.py` is the **Structure-Aware Document Chunking Engine**. It converts raw legal documents (Constitutional Articles, Amendments, Supreme Court Judgments, and Central Acts) into semantic child passages suitable for dense and sparse indexing while retaining complete provenance linkages to their parent records.

### Why does naive chunking fail in the legal domain?
Generic RAG systems use fixed-size sliding-window character chunking (e.g., cut every 500 characters with 50-character overlap). In legal documents, this creates critical failures:
1. **Clause Severance**: Splitting an article in the middle of a clause severs crucial conditional qualifications (e.g. cutting *"No person shall be deprived of life or personal liberty"* away from *"except according to procedure established by law"*).
2. **Loss of Judicial Context**: In a 50-page judgment, sliding windows mix opposing attorney arguments with judicial holdings, causing the retriever to retrieve appellant claims as if they were established law!
3. **Statutory Anchor Loss**: Sub-clauses like `(b)` lose their parent Article number, rendering them unsearchable.

`rag/chunking.py` solves this by chunking strictly along natural legal boundaries:
- **Constitutional Articles**: Split by clause (`Clause (1)`, `Clause (2)`) and legal analysis.
- **Constitutional Amendments**: Split into Summary and Statement of Objects and Reasons.
- **Supreme Court Judgments**: Split into structural legal sections: **Facts**, **Legal Issues**, **Ratio Decidendi**, **Verdict**, and **Key Takeaways**.
- **Central Acts / Statutes**: Split by statutory Sections.

---

## 2. Imports and Dependencies

```python
# rag/chunking.py L12-L20
import re
from typing import List, Dict, Any, Optional

from config import (
    CHILD_CHUNK_SIZE,
    CHILD_CHUNK_OVERLAP,
    MAX_CLAUSE_CHUNK_CHARS,
    MIN_CHUNK_CHARS
)
```

| Import / Constant | Purpose |
| :--- | :--- |
| `CHILD_CHUNK_SIZE` | Configured in `config.py` as `300`. Baseline character size for sliding-window chunks. |
| `CHILD_CHUNK_OVERLAP` | Configured in `config.py` as `50`. Overlap characters between consecutive windows. |
| `MAX_CLAUSE_CHUNK_CHARS` | Configured in `config.py` as `600`. Maximum character limit before an unusually long clause is subdivided. |
| `MIN_CHUNK_CHARS` | Configured in `config.py` as `40`. Minimum characters required to accept a chunk (filters noise). |

---

## 3. Helper Function: `estimate_tokens(text: str) -> int`

```python
# Lines 23-33
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
```
- **Why scale by 1.3?** Transformer tokenizers (BPE / WordPiece) split complex multi-syllable legal terms (e.g., *"unconstitutional"*, *"jurisprudence"*, *"retrospective"*) into multiple subword tokens. Scaling word count by $1.3$ provides an accurate token estimate without requiring heavy tokenizer imports during ingestion.

---

## 4. Class: `LegalStructureChunker`

```python
class LegalStructureChunker:
    """
    Structure-Aware Legal Chunker.
    Preserves legal clause boundaries and judgment section semantic coherence.
    """
```

### 4.1 `chunk_constitutional_article(article: Dict[str, Any]) -> List[Dict[str, Any]]`

Transforms a constitutional article JSON record into structured child chunks:
1. **Iterates over `article["clauses"]`**:
   Creates a chunk formatted with complete context:
   `"{art_num} - {title} [Clause {cl_num}]: {cl_text}"`
2. **Subdivision of Long Clauses**:
   If the clause exceeds `max_clause_chars` (600 chars), invokes `_split_long_clause()` to break on sub-clause markers `(a)`, `(b)` or sentence boundaries.
3. **Legal Analysis & Scope Chunk**:
   If `article["explanation"]` is present, creates an explicit analysis child chunk:
   `"{art_num} - {title}. Legal Analysis & Scope: {explanation}"`
4. **Historical Context Chunk**:
   If `article["historical_context"]` exists, chunks it under `Historical Context & Framing`.
5. **Fallback**:
   If no clauses are defined, falls back to `chunk_legacy_sliding_window()`.

Every child dictionary contains:
```python
{
    "child_id": "child_const_art_021_cl_0",
    "parent_id": "parent_const_art_021",
    "doc_type": "constitution",
    "document_type": "constitution_article",
    "article_number": "Article 21",
    "title": "Protection of life and personal liberty",
    "part": "Part III",
    "category": "Fundamental Rights",
    "section": "Clause (1)",
    "clause_number": "(1)",
    "text": "Article 21 - Protection of life and personal liberty [Clause (1)]: No person shall be deprived...",
    "char_count": 184,
    "estimated_tokens": 42,
    "source": "Constitution of India"
}
```

---

### 4.2 `chunk_amendment(amendment: Dict[str, Any]) -> List[Dict[str, Any]]`

Divides constitutional amendment records into two focused semantic chunks:
1. **Summary & Modified Provisions**:
   `"{title} ({year}). Provisions Modified: {prov_str}. Summary: {summary}"`
2. **Statement of Objects and Reasons**:
   `"{title} ({year}). Statement of Objects and Reasons: {objects_reasons}"`

---

### 4.3 `chunk_judgment(judgment: Dict[str, Any]) -> List[Dict[str, Any]]`

Splits Supreme Court judgments into distinct doctrinal sections:
1. **Facts**: `"{case_name} ({year}, {citation}). BENCH: {bench}. ARTICLES: {arts_str}. FACTS: {facts}"`
2. **Legal Issues**: `"{case_name} ({year}). LEGAL ISSUES: {issues_str}"`
3. **Ratio Decidendi**: `"{case_name} ({year}, {citation}). RATIO DECIDENDI: {ratio}"`
4. **Verdict & Holding**: `"{case_name} ({year}). FINAL VERDICT: {verdict}"`
5. **Key Takeaways & Precedents**: Key principles and list of overruled precedents.
6. **Full-Text Passages**: If full judgment text is present, slices official ruling text into 1,200-character segments.

---

### 4.4 `chunk_statute(statute: Dict[str, Any]) -> List[Dict[str, Any]]`

Chunks statutory Central Acts (e.g., CrPC, IPC, Indian Evidence Act) by statutory sections:
`"{short_title} ({year}). {sec_num}: {sec_title}. {sec_text}"`
Preserves constitutional cross-references (`constitutional_basis`).

---

### 4.5 `_split_long_clause(...)` and `chunk_legacy_sliding_window(...)`

- **`_split_long_clause`**: Uses regex `(?=\s*\([a-z]\)\s*)` to look ahead and split on sub-clause markers like `(a)`, `(b)`, `(c)` without removing the markers. If no sub-markers exist, splits on sentence terminals `(?<=[.!?])\s+`.
- **`chunk_legacy_sliding_window`**: Retained for baseline empirical comparisons. Employs backward search (`rfind(' ')`) to ensure windows end on whitespace boundaries rather than mid-word.

---

## 5. Actual Code Walkthrough

### Code Excerpt: Constitutional Clause Chunking (Lines 78-107)
```python
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
```
- **Why prepending `{art_num} - {title}` is essential**: In dense vector space, isolated clause text like *"Every citizen shall have the right..."* is generic. Prepending *"Article 19 - Protection of certain rights regarding freedom of speech..."* embeds the statutory identity directly into the vector representation, drastically improving retrieval accuracy.

---

## 6. Practical Working Example

### Input Record (Article 21):
```json
{
  "id": "const_art_021",
  "article_number": "Article 21",
  "title": "Protection of life and personal liberty",
  "part": "Part III",
  "clauses": [
    {
      "clause_number": "(1)",
      "text": "No person shall be deprived of his life or personal liberty except according to procedure established by law."
    }
  ],
  "explanation": "Article 21 is the heart of the Fundamental Rights...",
  "historical_context": "Framed after extensive constituent assembly debates on 'due process' vs 'procedure established by law'."
}
```

### Resulting Output Chunks:
1. **`child_const_art_021_cl_0`**: Clause 1 text with article header.
2. **`child_const_art_021_analysis`**: Doctrinal scope and legal explanation.
3. **`child_const_art_021_history`**: Drafting history regarding "due process" vs "procedure established by law".

All 3 child chunks point to `parent_id = "parent_const_art_021"`.

---

## 7. Viva Presentation & Defense Q&A

### Q1: Why not just use LangChain's `RecursiveCharacterTextSplitter`?
> **Student Answer**:
> *"RecursiveCharacterTextSplitter is domain-agnostic. It splits on paragraph breaks, newlines, and spaces based on character count thresholds. In constitutional law, that cuts across critical conditional clauses and separates legal tests from their exceptions. Our `LegalStructureChunker` is built specifically for Indian legal materials: it respects constitutional clause boundaries, isolates judgment ratio decidendi from background facts, and prefixes statutory headers so that child chunks never lose their legal identity."*

### Q2: How does chunk size affect retrieval and generation in this system?
> **Student Answer**:
> *"We adopt an asymmetric parent-child strategy. For retrieval, small child chunks (~300 characters) maximize embedding precision because vector representations are dense and focused on specific legal questions. For generation, however, small chunks lack broad context. Therefore, after the winning child chunks are retrieved, our system automatically hydrates the complete parent document (~1,200 to 4,000 characters) into the prompt context. This gives us the best of both worlds: pinpoint retrieval precision without sacrificing complete generative context."*

