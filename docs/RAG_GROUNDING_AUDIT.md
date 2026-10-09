# Adversarial RAG Grounding, Citation Integrity, and Semantic Entailment Audit

**Project**: Indian Constitution Legal AI Assistant  
**Role**: Senior NLP Researcher & Adversarial Evaluator  
**Component**: `rag/` (`citation_validator.py`, `confidence_scorer.py`, `generator.py`) & `evaluation/rag_eval.py`  
**Audit Date**: October 2026  
**Status**: **NOT VERIFIED for Semantic Entailment** | **PASS for Structural Validation & Abstention**  

---

## 1. Executive Summary & Grounding Taxonomy

A critical adversarial question in legal question answering is: **"Does a valid citation prove that the generated answer is legally correct?"**

The answer is an unequivocal **NO**. The codebase must be audited across five distinct, non-fungible grounding dimensions:

| Grounding Dimension | What is Evaluated | Mechanism | Adversarial Status |
|---|---|---|:---:|
| **1. Citation Format & Structural Validity** | Are citations formatted correctly (e.g. `[Doc: <id>]`) with non-empty metadata? | Regex parsing in `CitationValidator` | **PASS** |
| **2. Corpus Existence** | Do cited IDs exist in `parent_store.json`? | Parent document hash lookup | **PASS** |
| **3. Retrieval Provenance** | Were cited documents present in the top-k retrieved evidence for *this specific query*? | Set intersection with candidate pool | **PASS** |
| **4. Factual Claim-Level Semantic Entailment** | Does every atomic assertion in the answer logically follow from the cited passage? | Natural Language Inference (NLI) Cross-Encoder | **NOT VERIFIED** (Not Implemented) |
| **5. Out-of-Scope Automated Abstention** | Does the system refuse to answer non-constitutional, criminal, or out-of-scope legal queries? | Multi-signal confidence threshold ($C < 0.40$) | **PASS** |

---

## 2. Forensic Proof: The Danger of Structural Validation Without Semantic Entailment

To demonstrate empirically why structural citation validity cannot substitute for semantic entailment, an adversarial query was executed through the pipeline:

### 2.1 Adversarial Case Study: Section 138 Negotiable Instruments Act
- **User Query**: *"What is the penalty for dishonour of cheques under Section 138 of Negotiable Instruments Act?"*
- **Domain**: Statutory Commercial / Banking Law (Out of scope of Constitutional database).
- **Retriever Output**: Because words like *"penalty"*, *"offence"*, and *"punishment"* appeared, the hybrid retriever returned:
  `parent_const_art_020` (Article 20: Protection in respect of conviction for offences), `parent_const_art_035`, and `parent_case_sc_shreya_singhal_2015`.
- **Generator Output**: Synthesized text referencing Article 20 with inline citation tag `[Doc: parent_const_art_020]`.
- **Structural Citation Validator Result**:
  - `citations_valid`: **5 / 5**
  - `validation_score`: **1.0000**
  - `unsupported_claims`: **0**
  - *Why?* Because `parent_const_art_020` was part of the retrieved candidate pool, the structural validator passed it with a perfect score!

### 2.2 The Safety Layer: Confidence Scoring and Automated Abstention
Fortunately, the repository's secondary defense—the multi-signal **Confidence Estimator & Abstention Gate** (`rag/abstention.py` and `rag/confidence.py`)—successfully prevented hallucination:
- Normalized retrieval confidence fell below the safety threshold ($C = 0.28 < 0.40$).
- **System Outcome**: **`Abstained: True`**.
- The system refused to answer, returning the standardized abstention notice:
  > *"I am unable to provide a grounded legal explanation based on the verified constitutional documents available. The retrieved evidence does not meet the confidence threshold."*

**Academic Verdict**: This case study proves both the **limitation of structural citation checks** and the **vital necessity of the multi-signal abstention gate**.

---

## 3. Empirical Grounding & Abstention Audit Matrix

Evaluated across a documented sample of 6 adversarial test cases (stored in [`evaluation/results/rag_grounding_adversarial_audit.json`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/evaluation/results/rag_grounding_adversarial_audit.json)):

| Case ID | Category | Query Text | Retrieved Evidence | Structural Score | Abstained? | Correct Behavior? |
|:---:|:---:|---|---|:---:|:---:|:---:|
| `RAG_01` | In-Domain | Supreme Court ruling in Puttaswamy on Article 21 Privacy | Art 21, Puttaswamy (2017), Rajagopal | **1.00** | **False** | **YES** (Grounded answer provided) |
| `RAG_02` | In-Domain | Basic structure limits on amending power in Kesavananda | Art 368, Kesavananda (1973), Art 13 | **1.00** | **False** | **YES** (Grounded answer provided) |
| `RAG_03` | In-Domain | Restrictions on freedom of speech under Article 19(2) | Art 19, Romesh Thappar, Shreya Singhal | **1.00** | **False** | **YES** (Grounded answer provided) |
| `RAG_04` | Out-of-Scope | Penalty for dishonour of cheques under Section 138 NI Act | Art 20, Art 35, Shreya Singhal | 1.00 | **True** | **YES** (Refused to answer) |
| `RAG_05` | Out-of-Scope | Bail under Section 437 and 439 CrPC for non-bailable offences | Art 20, Art 22 | 1.00 | **True** | **YES** (Refused to answer) |
| `RAG_06` | Out-of-Scope | Punishment for cheating under Section 420 IPC | Joseph Shine, Navtej Johar | 1.00 | **True** | **YES** (Refused to answer) |

---

## 4. What Is and Is Not Implemented

### 4.1 Implemented & Verified:
1. **Deterministic Structural Provenance**: Checks metadata presence, corpus ID existence, and candidate pool set inclusion.
2. **Text-Level Entity Scanning**: Scans for ungrounded mentions of unretrieved Articles or landmark cases.
3. **Multi-Signal Abstention**: Prevents out-of-scope advice by gating on continuous confidence ($C < 0.40$).

### 4.2 NOT Implemented & Marked NOT VERIFIED:
1. **Sentence-Level Natural Language Inference (NLI)**: No model (e.g. `deberta-v3-large-mnli`) decomposes generated responses into atomic propositions to check whether each proposition is entailed by the retrieved text.
2. **Legal Substantive Correctness**: Token overlap metrics (ROUGE / BLEU) against reference answers measure lexical similarity, not statutory truth.

---

## 5. Defense Guidance

For the B.Tech viva defense, explicitly articulate:
> *"Our citation validation is an architectural provenance and hallucination gate that verifies that all cited statutes and precedents were physically retrieved and exist in the legal corpus. We do not claim claim-level NLI semantic entailment, which remains a valuable direction for future research."*
