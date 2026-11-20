# JSON Data Schemas & Records: `15_DATA_AND_DATABASE/json_schemas.md`

[Back to Data Overview](data_directory_explained.md) • [Back to Main Index](../README.md)

---

## 1. Overview

This document specifies the exact JSON structures, data types, required fields, and sample records for all primary datasets in the repository, matching the `LegalDocument` Pydantic model defined in `rag/schema.py`.

---

## 2. Document Schemas

### 2.1 Constitutional Article Record Schema
Stored in: `data/processed/constitution/articles_consolidated.json`

```json
{
  "document_id": "const_art_021",
  "document_type": "constitution_article",
  "title": "Protection of life and personal liberty",
  "article_number": "Article 21",
  "part": "Part III - Fundamental Rights",
  "category": "Fundamental Rights & Constitutional Remedies",
  "legal_status": "in_force",
  "text": "No person shall be deprived of his life or personal liberty except according to procedure established by law.",
  "clauses": [
    {
      "clause_id": "const_art_021_cl_0",
      "clause_number": "(1)",
      "text": "No person shall be deprived of his life or personal liberty except according to procedure established by law."
    }
  ],
  "explanation": "Article 21 guarantees substantive and procedural protection against arbitrary executive deprivation of life and personal liberty...",
  "historical_context": "Drafted following extensive constituent assembly debates on 'due process' vs 'procedure established by law'...",
  "source_url": "https://www.legislative.gov.in/constitution-of-india/",
  "source_name": "Legislative Department, Ministry of Law and Justice, Government of India",
  "source_hash": "a4f89d3c52e89b4f...",
  "retrieved_at": "2024-01-01T00:00:00Z",
  "license": "Government Open Data License - India (GODL)"
}
```

---

### 2.2 Constitutional Amendment Record Schema
Stored in: `data/processed/amendments/amendments_1_to_106.json`

```json
{
  "document_id": "const_amend_106",
  "document_type": "constitution_amendment",
  "title": "Constitution (One Hundred and Sixth Amendment) Act, 2023",
  "short_title": "106th Amendment Act (Nari Shakti Vandan Adhiniyam)",
  "amendment_number": "106th Amendment",
  "year": 2023,
  "enactment_date": "2023-09-28",
  "provisions_modified": [
    "Article 239AA",
    "Article 330A",
    "Article 332A",
    "Article 334A"
  ],
  "summary": "Provides for 33% reservation for women in Lok Sabha, State Legislative Assemblies, and NCT of Delhi for 15 years.",
  "statement_of_objects_and_reasons": "To enable greater participation of women as public representatives in policy making at national and state levels...",
  "text": "The Constitution (One Hundred and Sixth Amendment) Act, 2023. An Act further to amend the Constitution of India...",
  "source_url": "https://egazette.gov.in/",
  "source_name": "The Gazette of India, Ministry of Law and Justice",
  "source_hash": "e7b1a2c3d4f5...",
  "license": "Government Open Data License - India (GODL)"
}
```

---

### 2.3 Supreme Court Judgment Record Schema
Stored in: `data/processed/judgments/supreme_court_landmarks.json`

```json
{
  "document_id": "sc_puttaswamy_2017",
  "document_type": "judgment",
  "title": "Justice K.S. Puttaswamy (Retd.) v. Union of India",
  "case_name": "Justice K.S. Puttaswamy (Retd.) and Another v. Union of India and Others",
  "citation": "(2017) 10 SCC 1",
  "neutral_citation": "2017 INSC 790",
  "year": 2017,
  "court": "Supreme Court of India",
  "bench": "9-Judge Constitution Bench (J.S. Khehar C.J., J. Chelameswar, S.A. Bobde, R.K. Agrawal, R.F. Nariman, A.M. Sapre, D.Y. Chandrachud, S.K. Kaul, S. Abdul Nazeer JJ.)",
  "articles_referred": ["Article 14", "Article 19", "Article 21"],
  "content_type": "summary_only",
  "facts": "A retired High Court judge challenged the mandatory biometric Aadhaar scheme, arguing that compulsory collection of biometrics violates the fundamental right to privacy...",
  "issues": [
    "Whether the right to privacy is a fundamental right under Part III of the Constitution of India.",
    "Whether the earlier decisions in M.P. Sharma (8-Judge) and Kharak Singh (6-Judge) correctly decided that privacy is not a fundamental right."
  ],
  "ratio_decidendi": "The right to privacy is an intrinsic part of the right to life and personal liberty under Article 21 and as a part of the freedoms guaranteed by Part III of the Constitution. Privacy has both positive and negative content: it creates an obligation on the state not only to refrain from encroaching on personal privacy but to take legislative measures to safeguard it.",
  "verdict": "Unanimously held that privacy is a fundamental right. M.P. Sharma and Kharak Singh were expressly overruled to the extent they held otherwise.",
  "key_takeaways": [
    "Privacy is a natural, inalienable fundamental right intrinsic to Article 21.",
    "Proportionality Test established: Legitimate state goal, rational nexus, necessity (least intrusive measure), and proportionality stricto sensu."
  ],
  "precedents_overruled": [
    "M.P. Sharma v. Satish Chandra (1954) 8-Judge Bench",
    "Kharak Singh v. State of U.P. (1962) 6-Judge Bench"
  ],
  "text": "Justice K.S. Puttaswamy (Retd.) v. Union of India (2017) 10 SCC 1. The right to privacy is protected as an intrinsic part of the right to life and personal liberty under Article 21...",
  "source_url": "https://main.sci.gov.in/judgments",
  "source_name": "Supreme Court of India / Open Data AWS Registry",
  "source_hash": "b8d2f1e4a6c9..."
}
```

---

### 2.4 Central Legislation / Statute Record Schema
Stored in: `data/processed/legislation/central_acts.json`

```json
{
  "document_id": "act_crpc_1973",
  "document_type": "statute",
  "title": "Code of Criminal Procedure, 1973 (Act No. 2 of 1974)",
  "short_title": "Code of Criminal Procedure, 1973",
  "act_number": "2 of 1974",
  "year": 1974,
  "enactment_date": "1974-01-25",
  "commencement_date": "1974-04-01",
  "constitutional_basis": ["Article 21", "Article 22"],
  "legal_status": "in_force",
  "sections": [
    {
      "section_id": "act_crpc_1973_sec_165",
      "section_number": "Section 165",
      "title": "Search by police officer",
      "text": "(1) Whenever an officer in charge of a police station or a police officer making an investigation has reasonable grounds for believing that anything necessary for the purposes of an investigation into any offence which he is authorised to investigate may be found in any place... and that such thing cannot in his opinion be otherwise obtained without undue delay, such officer may, after recording in writing the grounds of his belief and specifying in such writing the thing for which search is to be made, search, or cause search to be made, for such thing in any place within the limits of such station."
    }
  ],
  "text": "Code of Criminal Procedure, 1973 (Act No. 2 of 1974). An Act to consolidate and amend the law relating to Criminal Procedure...",
  "source_url": "https://www.indiacode.nic.in",
  "source_name": "India Code, Ministry of Law and Justice, Government of India",
  "source_hash": "c3f5a7e9b1d2..."
}
```

---

## 3. Benchmark Query Schemas

### 3.1 Gold Retrieval Query: `legal_queries_gold.json`
```json
{
  "query_id": "LQ_045",
  "query": "Can police search premises without warrant under CrPC and how does Article 21 apply?",
  "category": "Procedural Due Process",
  "difficulty": "multi_hop",
  "intent": "CONSTITUTIONAL_PROCEDURE",
  "relevant_documents": [
    "act_crpc_1973",
    "parent_const_art_021"
  ],
  "expected_articles": ["Article 21"],
  "expected_statutes": ["Code of Criminal Procedure, 1973"],
  "graded_relevance": {
    "act_crpc_1973": 3,
    "parent_const_art_021": 3,
    "parent_const_art_022": 1
  }
}
```

---

## 4. Viva Presentation & Defense Q&A

### Q1: What guarantees that your JSON records follow this schema?
> **Student Answer**:
> *"All JSON datasets are validated by Pydantic's `LegalDocument` schema (`rag/schema.py`). Before any data is committed to disk in `scripts/build_corpus.py`, the `validate_document_records()` function runs automated assertions checking `document_id`, `document_type`, non-empty `text`, `source_url`, and `source_hash`. If any field is missing or malformed, the pipeline fails immediately."*

