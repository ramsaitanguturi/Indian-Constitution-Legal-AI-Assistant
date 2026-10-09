# Indian Constitution Legal AI Assistant — Dataset & Corpus Documentation

## 1. Executive Summary & Provenance

This document specifies the exact dataset provenance, corpus statistics, JSON schemas, chunking mechanics, and benchmark configurations of the **Indian Constitution Legal AI Assistant** (`Entity-Aware Hybrid Retrieval and Reranking Framework for Indian Constitutional Question Answering`).

To maintain academic and research integrity, all counts, filepaths, and schemas documented below reflect the active repository state.

---

## 2. Corpus Provenance & Legal Authority Sources

| Corpus Asset | Relative Path | Official Legal Provenance | Description / Coverage |
|---|---|---|---|
| **Constitutional Articles** | `data/constitution/articles.json` | Legislative Department, Ministry of Law and Justice, Government of India | 137 curated constitutional provisions covering the Preamble, Fundamental Rights (Part III), Directive Principles (Part IV), Fundamental Duties (Part IVA), Union Judiciary (Part V), High Courts (Part VI), Legislative Relations (Part XI), Emergency Provisions (Part XVIII), and Constitutional Amendments (Part XX). |
| **Constitutional Amendments** | `data/constitution/amendments.json` | Gazette of India / Legislative Department, Ministry of Law and Justice | 18 landmark constitutional amendments (1st, 7th, 24th, 25th, 42nd, 44th, 52nd, 61st, 73rd, 74th, 77th, 81st, 85th, 86th, 91st, 99th, 101st, 103rd Amendments). |
| **Landmark Judgments** | `data/judgments/supreme_court_landmarks.json` | Supreme Court Reports (SCR) & Indian Kanoon public legal archives | 104 curated Supreme Court constitutional decisions spanning 1950 to 2023 across 7 major constitutional doctrines. |
| **Legacy Sample Constitution** | `data/sample_constitution.json` | Legislative Department, GoI | 9 foundational provisions used for baseline backwards-compatibility testing. |
| **Legacy Sample Judgments** | `data/sample_judgments.json` | Supreme Court of India public records | 5 landmark judgments used for baseline regression tests. |
| **Parent Document Store** | `parent_store.json` | Consolidated Ingestion Pipeline | 270 hydrated parent records (143 constitutional articles/provisions, 109 judgments, 18 amendments). |
| **ChromaDB Vector Store** | `chroma_db/` | SentenceTransformers MiniLM-L6-v2 Embeddings | 1,001 child chunk vectors in the `indian_legal_rag` collection. |

---

## 3. Corpus Scale & Distribution

### 3.1 Numerical Corpus Inventory

```text
Constitutional Articles : 137 documents (210.8 KB)
Constitutional Amendments: 18 documents (20.1 KB)
Landmark SC Judgments   : 104 documents (176.7 KB)
--------------------------------------------------
Total Parent Documents  : 270 documents (527.4 KB in parent_store.json)
Total Indexed Passages  : 1,001 child chunks (ChromaDB vectors)
```

### 3.2 Constitutional Coverage by Part

The active constitutional corpus focuses on heavily litigated and doctrinally critical sections of the Indian Constitution:

1. **Preamble**: Sovereign, Socialist, Secular, Democratic, Republic.
2. **Part I (Articles 1–4)**: Union and its Territory.
3. **Part II (Articles 5–11)**: Citizenship at the commencement of the Constitution.
4. **Part III (Articles 12–35)**: **100% complete Fundamental Rights**, including:
   - General definitions (Arts. 12, 13)
   - Right to Equality (Arts. 14–18)
   - Right to Freedom (Arts. 19–22)
   - Right against Exploitation (Arts. 23–24)
   - Right to Freedom of Religion (Arts. 25–28)
   - Cultural and Educational Rights (Arts. 29–30)
   - Right to Constitutional Remedies & Writs (Arts. 32–35)
5. **Part IV (Articles 36–51)**: Directive Principles of State Policy (DPSPs), including Uniform Civil Code (Art. 44) and Separation of Powers (Art. 50).
6. **Part IVA (Article 51A)**: Fundamental Duties (clauses (a) through (k)).
7. **Part V (Selected Institutional Articles)**:
   - President's clemency powers (Art. 72)
   - Supreme Court establishment, jurisdiction, advisory opinions, and complete justice powers (Arts. 124, 129, 131, 136, 137, 141, 142, 143, 144)
8. **Part VI (Selected Judicial Articles)**: High Courts and writ jurisdiction (Arts. 214, 215, 226, 227).
9. **Part XI (Legislative Relations)**: Center-State relations, territorial nexus, and repugnancy (Arts. 245, 246, 248, 254).
10. **Part XVIII (Emergency Provisions)**: National Emergency, President's Rule, Financial Emergency (Arts. 352, 356, 359, 360).
11. **Part XX (Article 368)**: Constituent amending power and constitutional amendment procedures.

### 3.3 Judicial Doctrines Covered in Case Law Corpus (104 Decisions)

The 104 landmark judgments are distributed across seven primary constitutional domains:

1. **Basic Structure Doctrine & Constituent Power** (12 cases): *Kesavananda Bharati*, *Indira Nehru Gandhi*, *Minerva Mills*, *Waman Rao*, *I.R. Coelho*, *Golaknath*, *Shankari Prasad*, *Sajjan Singh*.
2. **Right to Life, Personal Liberty & Due Process (Art. 21)** (24 cases): *A.K. Gopalan*, *Kharak Singh*, *Maneka Gandhi*, *Sunil Batra*, *Olga Tellis*, *Francis Coralie Mullin*, *K.S. Puttaswamy (Privacy)*, *Navtej Singh Johar*, *Joseph Shine*, *Common Cause (Passive Euthanasia)*.
3. **Equality, Affirmative Action & Reservations (Arts. 14–16)** (18 cases): *Champakam Dorairajan*, *E.P. Royappa*, *Indra Sawhney (Mandal)*, *M. Nagaraj*, *Jarnail Singh*, *Janhit Abhiyan (EWS)*, *Shayara Bano (Triple Talaq)*.
4. **Freedom of Speech, Expression & Media (Art. 19)** (16 cases): *Romesh Thappar*, *Brij Bhushan*, *Bennett Coleman*, *Indian Express*, *Tata Press*, *Shreya Singhal (Section 66A IT Act)*, *Anuradha Bhasin (Internet Shutdown)*.
5. **Freedom of Religion & Secularism (Arts. 25–28)** (14 cases): *Commissioner, Hindu Religious Endowments (Shirur Mutt)*, *Sardar Syedna Taher Saifuddin*, *S.R. Bommai*, *M. Ismail Faruqui*, *Indian Young Lawyers Association (Sabarimala)*.
6. **Judicial Independence, Appointments & Remedies (Arts. 32, 124, 226)** (12 cases): *S.P. Gupta (First Judges)*, *Supreme Court Advocates-on-Record (Second Judges)*, *Special Reference 1 of 1998 (Third Judges)*, *NJAC Case (Fourth Judges)*, *ADM Jabalpur (Habeas Corpus)*, *Bandhua Mukti Morcha (PIL)*.
7. **Federalism, Center-State Relations & President's Rule (Art. 356)** (8 cases): *State of Rajasthan v. Union of India*, *S.R. Bommai*, *Government of NCT of Delhi v. Union of India (2018 & 2023)*.

---

## 4. Document Data Schemas

### 4.1 Constitutional Article Schema (`data/constitution/articles.json`)

```json
{
  "document_id": "const_art_021",
  "document_type": "constitution_article",
  "article_number": "Article 21",
  "part": "Part III - Fundamental Rights",
  "title": "Protection of life and personal liberty",
  "clauses": [
    {
      "clause_id": "const_art_021_main",
      "clause_number": "Main",
      "text": "No person shall be deprived of his life or personal liberty except according to procedure established by law."
    }
  ],
  "explanation": "Expansive judicial interpretation including right to privacy, clean environment, speedy trial, and human dignity.",
  "historical_context": "Drafted by the Constituent Assembly; deeply transformed by Maneka Gandhi (1978) which incorporated substantive due process.",
  "provenance": {
    "source": "Legislative Department, Ministry of Law and Justice, GoI",
    "retrieval_date": "2026-10-08",
    "version": "Constitution of India (as amended up to 105th Amendment)",
    "verified": true
  }
}
```

### 4.2 Supreme Court Judgment Schema (`data/judgments/supreme_court_landmarks.json`)

```json
{
  "document_id": "case_sc_puttaswamy_privacy_2017",
  "document_type": "judgment",
  "case_name": "Justice K.S. Puttaswamy (Retd.) v. Union of India",
  "citation": "(2017) 10 SCC 1",
  "court": "Supreme Court of India",
  "year": 2017,
  "bench": "9-Judge Constitution Bench (Unanimous 9:0)",
  "articles_referred": ["Article 21", "Article 14", "Article 19"],
  "acts_referred": ["Aadhaar Act, 2016", "Information Technology Act, 2000"],
  "facts": "Petitioners challenged the constitutional validity of the Aadhaar biometric identification project, asserting that mandatory collection of biometrics infringed upon fundamental privacy.",
  "issues": [
    "Whether the right to privacy is guaranteed as an independent fundamental right under Part III of the Constitution."
  ],
  "ratio_decidendi": "Privacy is an intrinsic and essential component of life and personal liberty under Article 21 and emanates from the freedoms guaranteed by Part III. State encroachments on privacy must satisfy legality, legitimate state aim, and proportionality.",
  "verdict": "Unanimously affirmed privacy as a fundamental right under Article 21; overruled M.P. Sharma (1954) and Kharak Singh (1962) to the extent they held otherwise.",
  "precedents_overruled": ["M.P. Sharma v. Satish Chandra (1954)", "Kharak Singh v. State of U.P. (1962)"],
  "keywords": ["privacy", "informational privacy", "biometric surveillance", "proportionality test"],
  "provenance": {
    "source": "Supreme Court Reports / Indian Kanoon public legal records",
    "retrieval_date": "2026-10-08",
    "version": "Final Judgment",
    "verified": true
  }
}
```

### 4.3 Constitutional Amendment Schema (`data/constitution/amendments.json`)

```json
{
  "document_id": "const_amend_042",
  "document_type": "amendment",
  "amendment_number": "42nd Amendment",
  "year": 1976,
  "title": "Constitution (Forty-second Amendment) Act, 1976",
  "description": "Comprehensive constitutional overhaul during Emergency; added 'Secular', 'Socialist', and 'Integrity' to Preamble; introduced Part IVA (Fundamental Duties); sought to curtail judicial review of constitutional amendments.",
  "articles_affected": ["Preamble", "Article 31C", "Article 39A", "Article 48A", "Article 51A", "Article 368"],
  "historical_context": "Enacted during the National Emergency (1975-1977); later partly invalidated in Minerva Mills (1980) and moderated by the 44th Amendment Act, 1978.",
  "provenance": {
    "source": "Legislative Department, Ministry of Law and Justice, GoI",
    "retrieval_date": "2026-10-08",
    "version": "Official Gazette Notification",
    "verified": true
  }
}
```

---

## 5. Chunking Strategy & Ingestion Pipeline

### 5.1 Hierarchical Parent-Child Architecture

Standard NLP chunking uses a single sliding window, introducing an inherent trade-off:
- **Small chunks (e.g. 100–300 chars)**: Maximize dense embedding similarity and lexical BM25 matching precision, but starve the generator of legal context (losing clauses, procedural steps, and facts).
- **Large chunks (e.g. 1,000–2,000 chars)**: Retain context, but dilute vector embeddings with multi-topic text, causing poor retrieval scores.

This repository resolves the dilemma using **Hierarchical Parent-Child RAG**:
1. **Child Chunks (~300 characters, overlap 50)**: Derived from statutory clauses and judicial ratio sections. Indexed in **ChromaDB** and **BM25Okapi** for retrieval.
2. **Parent Documents (~1,200 characters)**: Full Articles, Clauses, Explanations, Facts, and Ratios saved in `parent_store.json`.
3. **Runtime Hydration**: When child chunks rank in the top-$K$, the `ParentChildRecovery` module fetches their corresponding parent IDs and supplies complete, coherent legal text to the generator.

```
                    ┌─────────────────────────────────┐
                    │     Full Parent Document        │
                    │   (Article 21 + Full Context)   │
                    │      in parent_store.json       │
                    └────────────────┬────────────────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           ▼                         ▼                         ▼
   ┌───────────────┐         ┌───────────────┐         ┌───────────────┐
   │ Child Chunk 1 │         │ Child Chunk 2 │         │ Child Chunk 3 │
   │ (Main Clause) │         │ (Due Process) │         │ (Privacy Exp) │
   │  ~300 chars   │         │  ~300 chars   │         │  ~300 chars   │
   └───────┬───────┘         └───────┬───────┘         └───────┬───────┘
           │                         │                         │
           ▼                         ▼                         ▼
     [BM25 Index]              [BM25 Index]              [BM25 Index]
    [ChromaDB Vec]            [ChromaDB Vec]            [ChromaDB Vec]
```

### 5.2 Structure-Aware Legal Chunking (`rag/chunking.py`)

Rather than blind character splitting, `LegalStructureChunker` implements domain-specific boundaries:
- **Clause Protection**: Constitutional clauses (e.g., `Article 19(1)(a)`, `Article 19(2)`) are kept intact where possible (`MAX_CLAUSE_CHUNK_CHARS = 800`).
- **Section Separation**: In judgments, Facts, Issues, Ratio Decidendi, and Verdict are split into separate chunking units so that factual summaries do not contaminate ratio vectors.
- **Minimum Meaningful Threshold**: Chunks smaller than `MIN_CHUNK_CHARS = 40` characters are discarded to prevent indexing useless artifacts.

---

## 6. Evaluation Benchmarks

The benchmark suite in `data/benchmark/` and `data/annotations/` was constructed for quantitative evaluation across all pipeline stages:

| Benchmark File | Modality | Sample Count | Structure & Annotations |
|---|---|:---:|---|
| `data/benchmark/retrieval_queries.json` | Information Retrieval | 200 queries | Query text, query type (`ARTICLE_LOOKUP`, `PRECEDENT`, `CONCEPT_TO_ARTICLE`, `COMPARISON`), and gold relevant document IDs. |
| `data/annotations/relevance_labels.json` | IR Gold Relevance | 200 queries | Ground truth list of relevant parent IDs for each retrieval query. |
| `data/annotations/relevance_labels_v2_canonicalized.json` | IR Canonical Gold | 200 queries | Versioned canonical labels with 171 unpadded/shorthand aliases resolved to exact zero-padded parent IDs. |
| `data/benchmark/classification_queries.json` | Intent Classification | 220 queries | Query string, intent class (11 classes: `ARTICLE_LOOKUP`, `CASE_LAW_QUERY`, `CASE_COMPARISON`, `LEGAL_EXPLANATION`, `RIGHTS_QUERY`, `AMENDMENT_QUERY`, `PRECEDENT_QUERY`, `DEFINITION_QUERY`, `CONSTITUTIONAL_PROCEDURE`, `MULTI_DOCUMENT_QUERY`, `OUT_OF_SCOPE`). Partitioned into 80% train (187 queries) and 20% test (33 queries). |
| `data/annotations/ner_annotations.json` | Legal Named Entity Recognition | 105 queries | Character span offsets (`start`, `end`, `label`, `text`) covering 211 entity spans across 10 classes (`ACT`, `AMENDMENT`, `ARTICLE`, `CASE`, `COURT`, `DATE`, `LEGAL_CONCEPT`, `PERSON`, `RIGHT`, `SECTION`). |
| `data/benchmark/entity_linking_queries.json` | Canonical Entity Linking | 33 queries | 30 in-KB surface variants mapping to canonical corpus IDs + 3 adversarial out-of-KB entities testing rejection. |
| `data/benchmark/query_expansion_benchmark.json` | Controlled Query Expansion | 20 queries | Informal citizen phrases mapped to expected constitutional terms to evaluate semantic drift. |
| `data/benchmark/rag_questions.json` | Grounded Generation | 100 questions | Legal questions paired with verified citation targets and core holdings for groundedness testing. |

---

## 7. Known Dataset Limitations & Academic Disclosures

1. **Constitutional Coverage Ceiling**: The active corpus includes **137 articles out of 395 numbered constitutional articles** (~34.7% of numbered articles) and 18 amendments out of 105. Parts covering Finance, Property, Contracts (Part XII), Trade and Commerce (Part XIII), Services under the Union and States (Part XIV), and Tribunals (Part XIVA) are not present.
2. **Uncataloged Benchmark Targets (10.0%)**: In `data/benchmark/retrieval_queries.json`, **20 queries out of 200** reference constitutional articles or amendments (e.g., Articles 148, 174, 191, 249, 280, 311, 343, 7th Amendment) that were not ingested into the database. Consequently, no retriever can achieve 1.00 Recall@10 across all 200 queries; the theoretical recall ceiling is bounded at ~0.90 on raw queries.
3. **Synthetic Template Concentration**: 53% of retrieval benchmark queries begin with either *"What"* or *"Explain"*, and 40.5% of targets concentrate on just 5 provisions (Articles 21, 124, 19, 368, and 14).
4. **Static Gazetteer Memorization**: The NER gazetteer was augmented with specific Supreme Court judge names and concepts present in the benchmark. It achieves high precision on those terms, but open-domain bare personal names fail without judicial titles or gazetteer entries.

---

## 8. Ingestion & Index Rebuilding Commands

To rebuild the parent store, ChromaDB vector collection, and BM25 index safely from scratch:

```powershell
# Rebuild full corpus index (137 articles, 18 amendments, 104 judgments)
python scripts/ingest_data.py --corpus full --batch-size 64

# Rebuild minimal 14-document sample (for quick regression checks)
python scripts/ingest_data.py --corpus sample
```
