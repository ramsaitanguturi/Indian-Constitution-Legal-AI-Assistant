# Grounded RAG, Citation Integrity, and Confidence Calibration Audit

**Project**: Indian Constitution Legal AI Assistant  
**Role**: Senior NLP Researcher & Independent Evaluator  
**Component**: `rag/` (`citation_validator.py`, `confidence_scorer.py`, `answer_generator.py`) & `evaluation/rag_eval.py`  
**Date**: October 2026  

---

## 1. Architectural Overview of Grounded Legal Generation

In legal and constitutional QA, unsupported assertions and hallucinated citations carry severe real-world consequences. To mitigate hallucination, the repository implements a multi-stage **Grounded RAG Pipeline**:

```
User Query
    │
    ▼
[Legal Query Router & Expander]
    │
    ▼
[Hybrid RRF Retriever + Cross-Encoder]
    │
    ▼
[Parent-Child Hydration (Evidence Retrieval)]
    │
    ▼
[Grounded Answer Generator (LLM with Evidence-Constrained Prompt)]
    │
    ▼
[Deterministic Citation Validator] ──► [Hallucination Detection]
    │
    ▼
[Multi-Signal Confidence Scorer] ──► [Abstention Gate (< 0.40)]
    │
    ▼
Final Grounded Answer with Auditable Citation Badges
```

---

## 2. Forensic Audit of `CitationValidator`

`rag/citation_validator.py` executes deterministic validation of generated citations and references against the retrieved evidence pool.

### 2.1 The Four Structural Integrity Gates

For every declared citation dictionary `[cit]` in the response:
1. **Metadata Completeness Check**: Verifies non-empty presence of `document_id`, `source_title`, and `doc_type`. Flags `MISSING_REQUIRED_METADATA` if any field is absent.
2. **Database Existence Check**: Verifies that the cited ID exists in `parent_store.json` (or expanded corpus), handling ID normalization variants (e.g., stripping `parent_` or padding numbers). Flags `DOCUMENT_DOES_NOT_EXIST` if uncataloged.
3. **Retrieval Set Membership Check**: Verifies that the cited document was actually among the top-k retrieved parent records for the specific query. Flags `UNRETRIEVED_EVIDENCE_CITED` if the generator cited a document outside the retrieved evidence.
4. **Child Chunk Provenance Check**: Verifies that all supporting chunk IDs belong to the retrieved child passages. Flags `INVALID_CHILD_CHUNK_REFERENCE` if child references are ungrounded.

### 2.2 Text-Level Unsupported Mention Detection

Beyond declared citation arrays, `CitationValidator` scans the generated response text:
- **Inline Tag Detection**: Regex `\[Doc:\s*([^\]]+)\]` extracts inline citations and ensures they match retrieved document IDs.
- **Constitutional Article Scanning**: Regex `\bArticle\s*(\d+[A-Z]?|Preamble)\b` detects constitutional provisions mentioned in the text and verifies whether that article was part of the retrieved parent documents.
- **Landmark Case Scanning**: Scans for 17 canonical precedent names (e.g., *Kesavananda Bharati*, *Maneka Gandhi*, *Puttaswamy*). If a landmark is invoked in the text but absent from retrieved parents, it is flagged as an `UNSUPPORTED_CLAIM`.

---

## 3. Structural Citation Validity vs. Claim-Level Semantic Entailment

A central contribution of this independent audit is clarifying the exact boundary between **Structural Citation Validity** and **Semantic Entailment**:

| Level | Definition | Enforcement in Repository | Evaluation Status |
|---|---|---|:---:|
| **Level 1: Syntactic Existence** | Are cited document IDs valid strings in the legal corpus? | Regex + Store ID lookup | **Automated & Verified** |
| **Level 2: Retrieval Provenance** | Was the cited document actually present in the evidence fed to the LLM? | Set intersection with retrieved IDs | **Automated & Verified** |
| **Level 3: Entity Grounding** | Does the answer mention articles/cases that were never retrieved? | Entity extraction over text vs. retrieved metadata | **Automated & Verified** |
| **Level 4: Claim-Level Semantic Entailment** | Does sentence $S_i$ in the answer logically follow (entailment vs. neutral/contradiction) from passage $P_j$? | Requires Natural Language Inference (NLI) Cross-Encoder (e.g., `deberta-v3-large-mnli`) | **Documented Extension** |

### Academic Clarification:
The repository's citation validation operates at **Levels 1, 2, and 3**. It deterministically prevents hallucinations of non-existent articles, fabricated citations, unretrieved precedents, and unretrieved IDs. It does **not** decompose generated answers into atomic facts to compute natural language inference (NLI) scores. For a B.Tech NLP capstone, this is an architecturally sound and robust defense against citation hallucination, and the scope should be clearly articulated during academic presentations.

---

## 4. Confidence Scoring & Abstention Logic

### 4.1 Confidence Formulation

`rag/confidence_scorer.py` calculates a continuous confidence score $C \in [0.0, 1.0]$ based on three weighted components:

$$C = w_{\text{ret}} \cdot S_{\text{retrieval}} + w_{\text{cit}} \cdot S_{\text{citation}} + w_{\text{align}} \cdot S_{\text{alignment}}$$

Default parameters:
- $w_{\text{ret}} = 0.40$ (Normalized retrieval score of top-ranked evidence)
- $w_{\text{cit}} = 0.40$ (Citation validation score from `CitationValidator`)
- $w_{\text{align}} = 0.20$ (Lexical/entity query-context alignment)

### 4.2 Abstention Gate

The pipeline defines an explicit abstention threshold:
- `CONFIDENCE_THRESHOLD_ABSTAIN = 0.40`
- If $C < 0.40$ or if the retriever returns no supporting evidence, the system abstains from generating legal advice, returning a standardized disclaimer:
  > *"I am unable to provide a grounded legal explanation based on the verified constitutional documents available. The retrieved evidence does not meet the confidence threshold (Confidence: X.XX < 0.40)."*

This prevents deceptive or ungrounded responses when queried on out-of-scope statutory or criminal law queries outside the constitutional knowledge base.

---

## 5. Offline Synthetic Evaluation Behavior in `evaluation/rag_eval.py`

In `evaluation/rag_eval.py`, the evaluation method `evaluate_citation_validation()` supports both live API generation and deterministic offline testing:

- **Offline Mode**: If no LLM API key (`OPENAI_API_KEY` or `ANTHROPIC_API_KEY`) is configured, the evaluator generates synthetic responses structured around each benchmark query's `expected_citations` to validate the citation parsing regexes, ID normalization variants, error handling, and score computation pipelines.
- **Online Mode**: When an API key is present, the live LLM generator synthesizes responses from retrieved chunks, and the resulting citations are evaluated for real-world hallucination rates.

---

## 6. Audit Summary

1. **Citation Validation Integrity**: The 4-gate verification process in `CitationValidator` effectively eliminates fabricated citations and out-of-evidence precedent hallucination.
2. **Abstention Reliability**: The confidence scorer's multi-signal formulation reliably routes ambiguous or ungrounded queries to abstention.
3. **Research Integrity**: The distinction between structural provenance validation (implemented) and semantic claim entailment (future work) is now formalized.
