# Benchmark Integrity and Quality Assurance Audit Report

**Date**: October 2026  
**Auditor**: Automated Verification Suite (`scripts/validate_benchmark.py`)  
**Overall Verdict**: **PASS**

---

## 1. Executive Summary

| Benchmark Dataset | Total Records | Valid / Passed | Defect / Caveat Count | Integrity Status |
|---|:---:|:---:|:---:|:---:|
| **Information Retrieval** | 200 | 180 In-Corpus | 20 Uncataloged Provisions | **VERIFIED WITH PARTITION** |
| **Intent Classification** | 220 | 220 | 0 Duplicates | **100% BALANCED & CLEAN** |
| **Legal Named Entity Recognition** | 105 | 211 Spans | 0 Alignment Errors | **100% MATHEMATICAL EXACT SPAN** |
| **RAG Grounding & Abstention** | 100 | 100 | 0 Malformed | **VERIFIED GROUNDED** |

---

## 2. Retrieval Benchmark: In-Corpus Partitioning Analysis

- **Total Retrieval Queries**: 200
- **Verified In-Corpus Queries (Evaluated)**: **180 (90.0%)**
- **Uncataloged Constitutional Queries**: **20 (10.0%)**
- **Exact Duplicate Query Strings**: **0**
- **Missing In-Corpus Targets**: **0**

### 2.1 Accounting of the 20 Uncataloged Queries
The following 20 queries target constitutional provisions absent from the 137-article corpus snapshot. They are transparently isolated to preserve experimental honesty without silently altering the test set:

| Query ID | Query Excerpt | Intended Constitutional Provision | In-Corpus Status |
|:---:|---|---|:---:|
| `RET_049` | *"Explain the promotion of cooperative societies under Article..."* | `parent_const_art_043b, parent_const_art_43b` | **UNCATALOGED (OUT OF CORPUS)** |
| `RET_085` | *"What constitutional protections against arbitrary dismissal ..."* | `parent_const_art_311, parent_const_art_311` | **UNCATALOGED (OUT OF CORPUS)** |
| `RET_086` | *"Explain the establishment and powers of administrative tribu..."* | `parent_const_art_323a, parent_const_art_323a` | **UNCATALOGED (OUT OF CORPUS)** |
| `RET_090` | *"Explain the effect of proclamation of emergency on Union and..."* | `parent_const_art_353, parent_const_art_353` | **UNCATALOGED (OUT OF CORPUS)** |
| `RET_097` | *"Explain the reorganization of States and abolition of Part A..."* | `parent_amend_007` | **UNCATALOGED (OUT OF CORPUS)** |
| `RET_182` | *"What restrictions on freedom of trade and commerce can be im..."* | `parent_const_art_302, parent_const_art_302, parent_const_art_304, parent_const_art_304` | **UNCATALOGED (OUT OF CORPUS)** |
| `RET_183` | *"How does the Finance Commission function and make recommenda..."* | `parent_const_art_280, parent_const_art_280` | **UNCATALOGED (OUT OF CORPUS)** |
| `RET_184` | *"Explain the duties of the Comptroller and Auditor-General of..."* | `parent_const_art_148, parent_const_art_148` | **UNCATALOGED (OUT OF CORPUS)** |
| `RET_185` | *"What are the rules governing the Consolidated Fund of India ..."* | `parent_const_art_266, parent_const_art_266, parent_const_art_267, parent_const_art_267` | **UNCATALOGED (OUT OF CORPUS)** |
| `RET_187` | *"What are the powers, privileges and immunities of State Legi..."* | `parent_const_art_194, parent_const_art_194` | **UNCATALOGED (OUT OF CORPUS)** |
| `RET_190` | *"How does Article 312 govern the creation of All-India Servic..."* | `parent_const_art_312, parent_const_art_312` | **UNCATALOGED (OUT OF CORPUS)** |
| `RET_191` | *"Explain the functions of the Union Public Service Commission..."* | `parent_const_art_320, parent_const_art_320` | **UNCATALOGED (OUT OF CORPUS)** |
| `RET_192` | *"What is the constitutional provision for the Special Officer..."* | `parent_const_art_350b, parent_const_art_350b` | **UNCATALOGED (OUT OF CORPUS)** |
| `RET_193` | *"Explain the official language of the Union and devanagari sc..."* | `parent_const_art_343, parent_const_art_343` | **UNCATALOGED (OUT OF CORPUS)** |
| `RET_194` | *"What language is mandated for proceedings in the Supreme Cou..."* | `parent_const_art_348, parent_const_art_348` | **UNCATALOGED (OUT OF CORPUS)** |
| `RET_195` | *"Explain the duty of the Union to promote the spread of the H..."* | `parent_const_art_351, parent_const_art_351` | **UNCATALOGED (OUT OF CORPUS)** |
| `RET_197` | *"How can Parliament legislate on State List matters in nation..."* | `parent_const_art_249, parent_const_art_249` | **UNCATALOGED (OUT OF CORPUS)** |
| `RET_198` | *"Explain the power of Parliament to legislate for two or more..."* | `parent_const_art_252, parent_const_art_252` | **UNCATALOGED (OUT OF CORPUS)** |
| `RET_199` | *"What power does Parliament have to make laws implementing in..."* | `parent_const_art_253, parent_const_art_253` | **UNCATALOGED (OUT OF CORPUS)** |
| `RET_200` | *"Explain the constitutional guarantee and jurisdiction regard..."* | `parent_const_art_300, parent_const_art_300` | **UNCATALOGED (OUT OF CORPUS)** |

---

## 3. Intent Classification Benchmark Audit

- **Total Queries**: 220
- **Classes Found**: 11 (Expected: 11)
- **Per-Class Distribution**: Exactly **20 samples per class** across all 11 classes.
- **Class Balance Status**: **BALANCED (20/class)**
- **Exact Duplicate Queries**: **0**
- **Malformed Records**: **0**

---

## 4. Legal Named Entity Recognition (NER) Span Integrity

- **Annotated Queries**: 105
- **Total Validated Spans**: 211
- **Character Span Alignment Errors**: **0 (100% character-level exact match verified)**
- **Invalid Entity Labels**: **0**
- **Overlapping Spans**: **0**

### Per-Category Span Counts:
- **`ACT`**: 15 spans
- **`AMENDMENT`**: 15 spans
- **`ARTICLE`**: 40 spans
- **`CASE`**: 31 spans
- **`COURT`**: 23 spans
- **`DATE`**: 38 spans
- **`LEGAL_CONCEPT`**: 15 spans
- **`PERSON`**: 14 spans
- **`RIGHT`**: 9 spans
- **`SECTION`**: 11 spans

---

## 5. QA / Grounding Benchmark Audit

- **Total QA Questions**: 100
- **Direct Answer Questions**: 82
- **Abstention Verification Test Cases**: 18
- **Malformed Questions**: 0

---

## 6. Audit Certification
This report certifies that the Indian Constitution Legal AI Assistant benchmark assets are verified, free of silent test-set exclusions, and mathematically grounded for academic viva defense.
