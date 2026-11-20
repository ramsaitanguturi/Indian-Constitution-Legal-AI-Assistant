# Ingestion of Constitution & Amendments: `scripts/ingest_constitution.py` & `ingest_amendments.py`

[Back to Ingestion Overview](README.md) • [Back to Main Index](../README.md)

---

## 1. Basic Introduction

### What are these files?
- **`scripts/ingest_constitution.py`**: Parses the consolidated text of the Constitution of India into 477 structured records comprising the Preamble, Articles 1 through 395+ (including alphabetical insertions like 21A, 51A, 243A–ZG, 300A), and Schedules 1 through 12.
- **`scripts/ingest_amendments.py`**: Ingests all 106 Constitutional Amendment Acts enacted from 1951 (1st Amendment) to 2023 (106th Amendment Act — *Nari Shakti Vandan Adhiniyam*).

### Why do these files exist?
The Indian Constitution is the longest written national constitution in the world. It has evolved substantially since its adoption on 26 January 1950:
- Numerous articles were inserted (e.g., Article 21A on the Right to Education via the 86th Amendment).
- Articles were repealed (e.g., Article 31 on the Right to Property via the 44th Amendment).
- Special provisions became inoperative (e.g., Article 370 via Constitutional Orders in 2019).

These scripts ensure that the AI assistant operates on **current, consolidated law** with explicit annotations for repealed, omitted, or amended provisions, preventing outdated advice.

---

## 2. Ingestion of the Constitution: `scripts/ingest_constitution.py`

### 2.1 Mapping Articles to Parts and Categories
`determine_part_and_category(article_num_str)` maps numeric and alphanumeric article identifiers to their constitutional Parts (I through XXII) and substantive categories:

| Article Range | Constitutional Part | Category |
| :--- | :--- | :--- |
| **Preamble / 0** | Preamble | Foundational Philosophy |
| **1 – 4** | Part I - The Union and its Territory | Territorial Sovereignty |
| **5 – 11** | Part II - Citizenship | Citizenship & Nationality |
| **12 – 35** | Part III - Fundamental Rights | Fundamental Rights & Constitutional Remedies |
| **36 – 51** | Part IV - Directive Principles of State Policy | Directive Principles of State Policy |
| **51A** | Part IVA - Fundamental Duties | Fundamental Duties |
| **52 – 151** | Part V - The Union | Union Executive, Parliament & Supreme Court |
| **152 – 237** | Part VI - The States | State Executive, Legislature & High Courts |
| **243 – 243O** | Part IX - The Panchayats | Local Self-Government (Rural) |
| **243P – 243ZG** | Part IXA - The Municipalities | Local Self-Government (Urban) |
| **245 – 263** | Part XI - Relations between Union and States | Federal Legislative & Administrative Relations |
| **300A** | Part XII - Finance, Property, Contracts | Constitutional Right to Property |
| **352 – 360** | Part XVIII - Emergency Provisions | National, State & Financial Emergency |
| **368** | Part XX - Amendment of the Constitution | Constitutional Amendment Power & Procedure |
| **370 – 392** | Part XXI - Temporary, Transitional Provisions | Special Asymmetric Federalism (J&K, Nagaland, etc.) |

---

### 2.2 Clause Extraction & Provenance Tracking
`parse_clauses_from_text(raw_text, doc_id)` uses regex `(?:\n|^)\s*(\(\d+[a-zA-Z]?\))\s*(.*?)(?=(?:\n\s*\(\d+[a-zA-Z]?\)|\Z))` to segment clauses without phrase breaking.

Each article dictionary records:
```python
{
    "document_id": "const_art_021",
    "document_type": "constitution_article",
    "title": "Protection of life and personal liberty",
    "article_number": "Article 21",
    "part": "Part III - Fundamental Rights",
    "category": "Fundamental Rights & Constitutional Remedies",
    "legal_status": "in_force",
    "text": "No person shall be deprived of his life or personal liberty except according to procedure established by law.",
    "clauses": [...],
    "explanation": "Article 21 guarantees the substantive and procedural right to life...",
    "historical_context": "Drafted following constituent assembly debates replacing 'due process of law'...",
    "source_url": "https://www.legislative.gov.in/constitution-of-india/",
    "source_name": "Legislative Department, Ministry of Law and Justice, Government of India",
    "source_hash": "a4f89d3...",
    "license": "Government Open Data License - India (GODL)"
}
```

---

## 3. Ingestion of Amendments: `scripts/ingest_amendments.py`

### 3.1 Historical Scope (1st to 106th Amendments)
The script compiles all 106 enacted constitutional amendment acts:
- **1st Amendment Act, 1951**: Inserted Articles 31A, 31B, and the Ninth Schedule.
- **24th & 25th Amendment Acts, 1971**: Curtailed fundamental rights to implement directive principles (challenged in *Kesavananda Bharati*).
- **42nd Amendment Act, 1976**: Inserted *"Secular"*, *"Socialist"*, Part IVA (Fundamental Duties), and curtailed judicial review.
- **44th Amendment Act, 1978**: Removed Article 31 (Right to Property) from Fundamental Rights, making it a constitutional right under Article 300A; restored judicial independence.
- **73rd & 74th Amendment Acts, 1992**: Panchayati Raj and Municipalities (Parts IX and IXA).
- **86th Amendment Act, 2002**: Inserted Article 21A (Right to Education).
- **101st Amendment Act, 2016**: Goods and Services Tax (GST) regime.
- **103rd Amendment Act, 2019**: 10% Economically Weaker Sections (EWS) reservation (Articles 15(6) and 16(6)).
- **106th Amendment Act, 2023**: *Nari Shakti Vandan Adhiniyam* (33% reservation for women in Lok Sabha and State Legislative Assemblies).

### 3.2 Amendment Schema Attributes
Each amendment record captures:
- `amendment_number`: e.g., `"106th Amendment"`
- `year`: Enactment year (e.g., `2023`)
- `provisions_modified`: List of affected articles (e.g., `["Article 239AA", "Article 330A", "Article 332A", "Article 334A"]`)
- `statement_of_objects_and_reasons`: Official legislative purpose.
- `summary`: High-level explanation of legal changes.

---

## 4. Viva Presentation & Defense Q&A

### Q1: How does the system handle repealed articles like Article 31?
> **Student Answer**:
> *"When `ingest_constitution.py` parses the Constitution, it explicitly tags repealed or omitted articles with `legal_status = 'repealed'`. In Article 31 (Right to Property), the explanation explicitly clarifies that the 44th Amendment Act of 1978 removed it from Part III Fundamental Rights and re-enacted it as a constitutional right under Article 300A. If a user asks about property rights, our retriever and generator inform the user that property is no longer a fundamental right under Article 31 but a constitutional right under Article 300A."*

### Q2: Why are all 106 amendments ingested into a separate dataset?
> **Student Answer**:
> *"Constitutional amendments represent the legislative evolution of the Constitution. Many landmark Supreme Court decisions (such as *Sankari Prasad*, *Sajjan Singh*, *Golak Nath*, and *Kesavananda Bharati*) revolve entirely around whether Parliament has the power to amend fundamental rights under Article 368. Having dedicated amendment records allows our router to activate `AMENDMENT_QUERY` routing and retrieve both the amending act and the constitutional challenge."*

