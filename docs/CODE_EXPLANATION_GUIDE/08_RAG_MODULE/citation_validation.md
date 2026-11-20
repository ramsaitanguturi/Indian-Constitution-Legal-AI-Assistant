# Citation Validation & Structural Grounding: `rag/citation_validator.py`

[Back to RAG Module Overview](README.md) • [Back to Main Index](../README.md)

---

## 1. Basic Introduction

### What is this file?
`rag/citation_validator.py` is the **Post-Generation Citation and Factual Integrity Guard**. It performs deterministic structural verification on every citation declared by the generator and scans the generated text for ungrounded statutory or case-law claims.

### Why does this file exist?
Generative LLMs frequently suffer from **citation hallucination**:
1. **Fabricated Document IDs**: Generating synthetically plausible but non-existent IDs (e.g. `[Doc: const_art_999]`).
2. **Unretrieved Evidence Citation**: Citing a real legal document that exists in the database but **was never actually retrieved or provided in the prompt context** for this specific query. (The LLM retrieved it from its pre-trained parametric memory instead of grounding it in retrieved evidence!).
3. **Unsupported Article / Precedent Mentions**: Generating text that casually asserts *"In Kesavananda Bharati..."* or *"Under Article 356..."* when neither Kesavananda nor Article 356 was part of the retrieved evidence.
4. **Substantive Claim Inversion**: Asserting statutory claims directly contradicted by the retrieved text.

`rag/citation_validator.py` catches all four error types before the answer reaches the user interface.

---

## 2. Imports and Dependencies

```python
# rag/citation_validator.py L9-L16
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple

from config import PARENT_STORE_PATH
from rag.nli_verifier import get_nli_verifier, NLIVerifier, LEGAL_GENERIC_STOPWORDS
```

| Import / Dependency | Purpose |
| :--- | :--- |
| `PARENT_STORE_PATH` | Path to `data/parent_store.json` used to verify that cited document IDs actually exist in the database. |
| `rag.nli_verifier` | Provides the proposition-level Natural Language Inference engine for detecting semantic contradictions. |
| `LEGAL_GENERIC_STOPWORDS` | Set of legal stop-words (e.g. `"court"`, `"action"`, `"sections"`) excluded during substantive overlap calculations. |

---

## 3. Structural Integrity Checks in `CitationValidator`

```python
class CitationValidator:
    """
    Validates structural integrity and evidence provenance of citations in RAG answers.
    Detects unretrieved documents, fabricated IDs, missing metadata, and unsupported references,
    with atomic proposition-level Natural Language Inference (NLI) claim verification.
    """
```

### 3.1 Five-Stage Citation Validation Rules

For every citation dictionary in `citations`:

| Check | Failure Reason Code | Condition | Explanation |
| :--- | :--- | :--- | :--- |
| **Check 1** | `MISSING_REQUIRED_METADATA` | `not doc_id` or `not source_title` or `not doc_type` | Citation dictionary lacks essential provenance fields. |
| **Check 2** | `DOCUMENT_DOES_NOT_EXIST` | `doc_id` not found in `parent_store.json` | The model fabricated a non-existent document ID. |
| **Check 3** | `UNRETRIEVED_EVIDENCE_CITED` | `doc_id` not in `retrieved_parent_ids` | The document exists in the legal corpus, but was **NOT** retrieved for this question. Citing it is an ungrounded hallucination from parametric memory! |
| **Check 4** | `INVALID_CHILD_CHUNK_REFERENCE` | `cid` not in `retrieved_child_ids` | Cited child chunk was not part of the retrieved candidate pool. |
| **Check 5** | `INSUFFICIENT_SUBSTANTIVE_SUPPORT` | Claimed section numbers not in evidence | The answer claims specific statutory sections (e.g., Section 41A) that do not appear in the retrieved passage text. |

---

### 3.2 Text-Level Reference & Ungrounded Mention Detection

Even if the model does not include an explicit citation in the citations list, it might mention legal entities in prose:

1. **Inline `[Doc: <id>]` Keys (Lines 244-251)**:
   Extracts all bracketed keys `\[Doc:\s*([^\]]+)\]`. If any inline key does not match retrieved documents, it is flagged as unsupported.
2. **Ungrounded Article Claims (Lines 254-264)**:
   Extracts all mentions of `Article \d+[A-Z]?`. If the text mentions `Article 370` when only `Article 21` was retrieved, it is added to `unsupported_claims`.
3. **Ungrounded Landmark Cases (Lines 266-276)**:
   Checks 17 canonical landmark precedents (`"Kesavananda"`, `"Maneka Gandhi"`, `"Puttaswamy"`, `"Bommai"`, `"Indra Sawhney"`, etc.). If a case is named in the text but absent from retrieved parents, it is flagged.

---

### 3.3 Integration with Natural Language Inference (NLI)

At line 303, the validator calls `self.nli_verifier.verify_answer()`:
```python
        # Natural Language Inference (NLI) Claim-Level Verification
        nli_report = self.nli_verifier.verify_answer(generated_answer, recovered_context)
        if nli_report.get("has_contradictions"):
            for clm in nli_report.get("claims_breakdown", []):
                if clm.get("verdict") == "CONTRADICTION":
                    unsupported_claims.append(
                        f"Fact contradicted by retrieved evidence: '{clm['claim']}'"
                    )
            is_valid = False
            validation_score = max(0.0, round(validation_score - 0.30, 4))
```
If an atomic proposition directly contradicts the statutory text, validation immediately fails and the score is penalized by $-0.30$.

---

## 4. Actual Code Walkthrough

### Code Excerpt: Unretrieved Evidence Detection (Lines 171-178)
```python
            # Check 3: Document was actually retrieved in supplied evidence
            if not any(v in retrieved_variants for v in doc_vars):
                invalid_citations.append({
                    "citation": cit,
                    "reason": "UNRETRIEVED_EVIDENCE_CITED",
                    "details": f"Document '{doc_id}' exists in database but was NOT part of the retrieved evidence for this query.",
                })
                continue
```
- **Why this check is groundbreaking for academic defense**: Most RAG systems only check whether a cited document exists in the database. But if the model cites Article 14 when only Article 21 was in the retrieved prompt, the model is hallucinating based on pre-trained parametric memory! Our system enforces **strict evidentiary provenance**: a document must not only exist—it must be in the active retrieved set.

---

## 5. Practical Working Example

### Query:
> *"What are the restrictions on personal liberty under Article 21?"*

### Retrieved Evidence:
- `parent_const_art_021` (Article 21: Protection of life and personal liberty)

### Generated Model Answer (Hypothetical Hallucinated Output):
> *"Personal liberty is guaranteed under Article 21 [Doc: parent_const_art_021]. Furthermore, freedom of speech is protected under Article 19 [Doc: parent_const_art_019], as held in the landmark case of Kesavananda Bharati."*

### Validation Report Produced by `CitationValidator`:
```python
{
    "valid": False,
    "citations_checked": 2,
    "valid_citations": [{"document_id": "parent_const_art_021", ...}],
    "invalid_citations": [
        {
            "citation": {"document_id": "parent_const_art_019", ...},
            "reason": "UNRETRIEVED_EVIDENCE_CITED",
            "details": "Document 'parent_const_art_019' exists in database but was NOT part of the retrieved evidence for this query."
        }
    ],
    "unsupported_claims": [
        "Generated text refers to 'Article 19' which was not present in the retrieved evidence.",
        "Generated text cites precedent 'Kesavananda Bharati' which was not in the retrieved evidence."
    ],
    "validation_score": 0.0,
    "summary": "Validation failed (1 invalid citations, 2 unsupported/contradicted references detected)."
}
```

---

## 6. Viva Presentation & Defense Q&A

### Q1: What is the difference between a fabricated citation and an unretrieved citation?
> **Student Answer**:
> *"A fabricated citation is a completely invented identifier (e.g. `[Doc: art_999]`) that does not exist in any statute or database. An unretrieved citation is much subtler: the document is completely genuine and exists in our 886-document database (e.g. `parent_const_art_019`), but it was never retrieved by the search engine for this user's question. Citing it means the LLM used unverified internal pre-training memory rather than grounding its claim in the evidence retrieved for that query. Our `CitationValidator` catches both errors."*

### Q2: How does the validation score impact the rest of the application?
> **Student Answer**:
> *"The validation score directly feeds into Signal 5 of our `ConfidenceEstimator` (weighted at 15%). Furthermore, if strict validation is enabled or if all citations are invalid, the `AbstentionManager` intercepts the response at Stage 17, withholding the answer and presenting a transparent notice that the generated text could not be verified against retrieved evidence."*

