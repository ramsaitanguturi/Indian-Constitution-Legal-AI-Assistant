# Adversarial Benchmark Quality, Independence, and Grounding Audit Report

**Project**: Indian Constitution Legal AI Assistant  
**Role**: Senior NLP Researcher & Adversarial Evaluator  
**Audit Date**: October 2026  
**Status**: **PARTIAL** (Distinct query strings, but high template repetition, heavy document concentration, and uncataloged ground truth targets)  

---

## 1. Executive Summary

An adversarial audit was performed across all benchmark assets in `data/benchmark/` and `data/annotations/`. The previous audit claimed "zero duplicates, zero leakage, and 100% benchmark integrity." While exact duplicate strings are indeed 0, a rigorous forensic analysis reveals three significant methodological caveats:

1. **High Syntactical Template Repetition**: Over **30.5% of retrieval queries** (61/200) begin with the identical two-word prefix *"Explain the"*, and **53.0%** begin with either *"What"* or *"Explain"*.
2. **Heavy Document Target Concentration**: Just **5 constitutional provisions** (Articles 21, 124, 19, 368, and 14) account for **over 40% of all benchmark targets**.
3. **Uncataloged Corpus Targets**: **20 queries out of 200 (10.0%)** reference constitutional articles or amendments (Articles 148, 174, 191, 249, 280, 311, 343, 7th Amendment, etc.) that **do not exist in the repository's corpus**. Consequently, no retriever can ever retrieve them, imposing an empirical cap on recall.
4. **Relevance Label Alias Discrepancy**: 171 references in `data/annotations/relevance_labels.json` were unpadded or shorthand aliases (e.g., `parent_const_art_14` alongside `parent_const_art_014`), which treated a single constitutional article as two separate documents and artificially depressed evaluated recall.

---

## 2. Syntactical Template Repetition Analysis

An n-gram prefix frequency scan of the 200 retrieval queries in `data/benchmark/retrieval_queries.json` reveals substantial template homogeneity:

### 2.1 2-Gram Prefix Distribution (Top 8)
- `'explain the'`: **61 occurrences (30.5%)**
- `'how did'`: **15 occurrences (7.5%)**
- `'what does'`: **12 occurrences (6.0%)**
- `'what did'`: **11 occurrences (5.5%)**
- `'what is'`: **11 occurrences (5.5%)**
- `'what are'`: **8 occurrences (4.0%)**
- `'what was'`: **7 occurrences (3.5%)**
- `'how does'`: **7 occurrences (3.5%)**
- *Combined 'What...' or 'Explain...'* = **106 / 200 queries (53.0%)**

### 2.2 Academic Implication:
Zero exact string duplicates does **not** prove that the queries are natural, spontaneous citizen inputs. The benchmark was synthetically constructed using formal question templates, which gives an advantage to retrieval models that match legal interrogative patterns.

---

## 3. Document Target Concentration Analysis

Analyzing the ground truth document targets in `relevant_documents` across the 200 retrieval queries reveals severe topic concentration:

| Target Document | Provision / Case | Query Count | % of Benchmark |
|---|---|:---:|:---:|
| `parent_const_art_021` | Article 21 (Protection of life & personal liberty) | 26 | 13.0% |
| `parent_const_art_124` | Article 124 (Establishment of Supreme Court) | 16 | 8.0% |
| `parent_const_art_019` | Article 19 (Protection of certain rights / speech) | 15 | 7.5% |
| `parent_const_art_368` | Article 368 (Power of Parliament to amend) | 14 | 7.0% |
| `parent_const_art_014` | Article 14 (Equality before law) | 10 | 5.0% |
| `parent_case_sc_kesavananda_1973` | Kesavananda Bharati (Basic Structure) | 6 | 3.0% |
| `parent_case_sc_puttaswamy_privacy_2017` | Puttaswamy (Right to Privacy) | 6 | 3.0% |
| `parent_const_art_016` | Article 16 (Equal opportunity in public employment) | 6 | 3.0% |
| `parent_const_art_142` | Article 142 (Complete justice powers) | 6 | 3.0% |

**Audit Finding**: The top 5 articles alone represent **40.5% of the benchmark**. Rare constitutional parts (such as Part XII Finance, Part XIII Trade, or Part XIV Services) are under-represented or absent from the corpus.

---

## 4. The Uncataloged Corpus Targets (20 Zero-Overlap Queries)

A strict intersection check between ground-truth document IDs in `data/annotations/relevance_labels.json` and the active corpus in `parent_store.json` (270 hydrated parent documents) reveals that **20 queries target provisions that were never ingested**:

| Query ID | Target Article / Act | Query Text | Document Exists in Corpus? |
|---|---|---|:---:|
| `RET_049` | Article 43B | Promotion of cooperative societies | **NO** (Only 43 & 43A ingested) |
| `RET_085` | Article 311 | Protections for civil servants against arbitrary dismissal | **NO** |
| `RET_086` | Article 323A | Administrative tribunals | **NO** |
| `RET_090` | Article 353 | Proclamation of emergency effects on Union/State | **NO** |
| `RET_097` | 7th Amendment | Reorganization of States (1956) | **NO** (Only 18 landmark amendments) |
| `RET_182` | Article 302–304 | Freedom of trade and commerce restrictions | **NO** |
| `RET_183` | Article 280 | Finance Commission functioning | **NO** |
| `RET_184` | Article 148 | Comptroller and Auditor-General of India (CAG) | **NO** |
| `RET_185` | Article 266–267 | Consolidated Fund and Contingency Fund | **NO** |
| `RET_187` | Article 194 | State Legislative Assembly immunities | **NO** |
| `RET_190` | Article 312 | All-India Services creation by Rajya Sabha | **NO** |
| `RET_191` | Article 320 | Union Public Service Commission functions | **NO** |
| `RET_192` | Article 350B | Special Officer for Linguistic Minorities | **NO** |
| `RET_193` | Article 343 | Official language of the Union | **NO** |
| `RET_194` | Article 348 | Language in Supreme Court and High Courts | **NO** |
| `RET_195` | Article 351 | Duty to promote Hindi language | **NO** |
| `RET_197` | Article 249 | Legislation on State List in national interest | **NO** |
| `RET_198` | Article 252 | Legislation for States by consent | **NO** |
| `RET_199` | Article 253 | Legislation implementing international treaties | **NO** |
| `RET_200` | Article 300 | Suits against the Government | **NO** |

### Mathematical Ceiling on Recall:
Because these 20 queries have $0$ retrievable targets in the corpus, their evaluated Recall@10 is mathematically $0.0$. Across the 200-query benchmark, this introduces an automatic $-10.0\%$ penalty on overall mean recall.

---

## 5. Versioned Relevance Label Canonicalization & Empirical Verification

To resolve the 171 unpadded/shorthand alias references (`parent_const_art_14` alongside `parent_const_art_014`) without overwriting the original annotations, an auditable, versioned canonicalization was created:
- **Canonical Label Artifact**: [`data/annotations/relevance_labels_v2_canonicalized.json`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/data/annotations/relevance_labels_v2_canonicalized.json)
- **Normalization Principle**: 1-to-1 mapping of unpadded article IDs (`parent_const_art_X` $\to$ `parent_const_art_00X`) and case aliases (`parent_case_adm` $\to$ `parent_case_sc_adm_jabalpur_1976`) to the single canonical parent ID.

### 5.1 Empirical Metric Comparison Across All 6 Configurations (All 200 Queries)

| Configuration | Original Hit@1 | Canonical Hit@1 | Original Recall@10 | Canonical Recall@10 | Original MRR | Canonical MRR | Original NDCG@10 | Canonical NDCG@10 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Exp 1: BM25 Only** | 0.7500 | **0.7900** | 0.5064 | **0.7003** (+19.39%) | 0.7962 | **0.8271** | 0.6157 | **0.7197** (+10.40%) |
| **Exp 2: Dense Only** | 0.7750 | **0.8100** | 0.5250 | **0.7131** (+18.81%) | 0.8072 | **0.8385** | 0.6429 | **0.7432** (+10.03%) |
| **Exp 3: Linear Hybrid** | 0.7700 | **0.8100** | 0.5150 | **0.7076** (+19.26%) | 0.8099 | **0.8411** | 0.6298 | **0.7333** (+10.35%) |
| **Exp 4: RRF (k=60)** | 0.7700 | **0.8100** | 0.5106 | **0.7005** (+19.00%) | 0.8071 | **0.8396** | 0.6244 | **0.7262** (+10.18%) |
| **Exp 5: Entity Boost** | 0.7800 | **0.8200** | 0.5352 | **0.7229** (+18.77%) | 0.8096 | **0.8421** | 0.6482 | **0.7493** (+10.11%) |
| **Exp 6: Cross-Encoder** | **0.8000** | **0.8400** | **0.5526** | **0.7478** (+19.51%) | **0.8263** | **0.8583** | **0.6730** | **0.7787** (+10.57%) |

### 5.2 Refutation of the $\ge 0.85$ Recall Conjecture
The previous audit conjectured that canonicalization would lift Recall@10 to $\ge 0.85$. **The empirical experiment refutes this claim**:
- Canonical Recall@10 across all 200 queries reaches **0.7003** for BM25 and **0.7478** for Cross-Encoder.
- Even when restricting evaluation exclusively to the 180 in-corpus queries, BM25 Recall@10 is **0.7781** and Cross-Encoder is **~0.8310**.
- The shortfall from 0.85 is due to the 20 uncataloged corpus documents and real-world retrieval rank cutoffs at $K=10$.

---

## 6. Audit Verdict on Benchmark Integrity

| Dimension | Status | Notes |
|---|:---:|---|
| **String Duplication** | **PASS** | 0 exact string duplicates detected across all 5 benchmark files. |
| **Leakage Isolation** | **PASS** | Intent classification 5-fold CV fits vectorizers strictly within training folds. |
| **Template Diversity** | **PARTIAL** | 53% of queries share "what" or "explain" prefixes; synthetically patterned. |
| **Topic Distribution** | **PARTIAL** | > 40% of queries target only 5 constitutional articles (21, 124, 19, 368, 14). |
| **Corpus Completeness** | **FAIL** | 20 queries target uningested constitutional provisions, scoring 0 by definition. |
