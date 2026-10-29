# Corpus Sources & Legal Provenance

This document records the official provenance, retrieval methodology, licenses, and content specifications of all legal corpora ingested into the **Indian Constitution Legal AI Assistant**.

---

## 1. Consolidated Constitution of India

* **Authoritative Source:** Legislative Department, Ministry of Law and Justice, Government of India.
* **Official Portal:** [https://www.legislative.gov.in/constitution-of-india/](https://www.legislative.gov.in/constitution-of-india/)
* **Structured Mirror & Verification Dataset:** CivicTech India & Yash Handa Consolidated Constitution Datasets (`civictech-India/constitution-of-india`).
* **License:** Government Open Data License - India (GODL) / Public Domain.
* **Scope Ingested:**
  * **Preamble:** Solemn resolution of the Sovereign Socialist Secular Democratic Republic.
  * **Articles 1 to 395+:** Complete text spanning all 22 Parts (including inserted articles such as 21A, 31A, 31B, 31C, 39A, 43A, 43B, 48A, 51A, 243A–243ZG, 279A, 300A, 371A–371J, etc.). Total active provisions: 477.
  * **Clauses & Subclauses:** Structured JSON hierarchy preserving nested clauses, provisos, and explanations.
  * **Schedules 1 to 12:** Complete Schedules including First Schedule (States/UTs), Second to Fifth Schedules, Sixth Schedule (Tribal Areas), Seventh Schedule (Union, State, Concurrent Lists), Eighth Schedule (Recognized Languages), Ninth Schedule (Validation of certain Acts), Tenth Schedule (Anti-defection), Eleventh and Twelfth Schedules (Panchayats and Municipalities).
* **Local Storage:**
  * Raw: `data/raw/constitution/constitution_consolidated.json`
  * Processed: `data/processed/constitution/articles_consolidated.json`
* **Verification Checksum (SHA-256):** Verified deterministically on ingestion and validated via `scripts/validate_corpus.py`.

---

## 2. Constitution Amendment Acts (1st to 106th)

* **Authoritative Source:** Legislative Department, Ministry of Law and Justice, Government of India.
* **Official Portal:** [https://www.legislative.gov.in/amendment-acts/](https://www.legislative.gov.in/amendment-acts/)
* **Bulk Mirror & Structured Records:** CivicTech India Indian Constitution Amendments Dataset.
* **License:** Government Open Data License - India (GODL) / Public Domain.
* **Scope Ingested:**
  * All 106 official Constitution Amendment Acts (from the Constitution (First Amendment) Act, 1951 through the Constitution (One Hundred and Sixth Amendment) Act, 2023 - Nari Shakti Vandan Adhiniyam).
  * **Metadata Stored:**
    * Amendment number and official title.
    * Enactment date, presidential assent date, and effective enforcement date.
    * Constitutional provisions inserted, substituted, amended, or omitted.
    * Official Statement of Objects and Reasons (SOR).
    * Official source URL and SHA-256 content hash.
* **Local Storage:**
  * Raw: `data/raw/amendments/amendments_raw.json`
  * Processed: `data/processed/amendments/amendments_1_to_106.json`

---

## 3. Supreme Court Judgments & Precedents

* **Authoritative Sources:**
  * Supreme Court of India Digital SCR: [https://scr.sci.gov.in/](https://scr.sci.gov.in/)
  * Registry of Open Data on AWS — Indian Supreme Court Judgments (1950–present): [https://registry.opendata.aws/indian-supreme-court-judgments/](https://registry.opendata.aws/indian-supreme-court-judgments/)
* **License:** Public Domain / Open Data under Indian Public Records principles; non-copyrightable judicial determinations (Copyright Act, 1957 § 52(1)(q)(iv)).
* **Scope Ingested:**
  * 104 landmark constitutional decisions covering Fundamental Rights, Basic Structure Doctrine, Judicial Review, Federalism, Reservation, Emergency Provisions, and Secularism.
  * **Key Cases Included:**
    * *A.K. Gopalan v. State of Madras* (1950 INSC 14, [1950] SCR 88)
    * *Shankari Prasad v. Union of India* (1951 INSC 45, [1952] SCR 89)
    * *Golaknath v. State of Punjab* (1967 INSC 45, [1967] 2 SCR 762)
    * *Kesavananda Bharati v. State of Kerala* (1973 INSC 258, [1973] Supp SCR 1)
    * *Indira Nehru Gandhi v. Raj Narain* (1975 INSC 152, [1976] 2 SCR 347)
    * *Maneka Gandhi v. Union of India* (1978 INSC 16, [1978] 2 SCR 621)
    * *Minerva Mills Ltd. v. Union of India* (1980 INSC 141, [1981] 1 SCR 206)
    * *Waman Rao v. Union of India* (1980 INSC 211, [1981] 2 SCR 1)
    * *S.P. Gupta v. Union of India (First Judges Case)* (1981 INSC 220)
    * *Mohd. Ahmed Khan v. Shah Bano Begum* (1985 INSC 97)
    * *Indra Sawhney v. Union of India (Mandal Case)* (1992 INSC 260)
    * *S.R. Bommai v. Union of India* (1994 INSC 173, [1994] 2 SCR 644)
    * *Supreme Court Advocates-on-Record Assn v. UOI (Second Judges Case)* (1993 INSC 356)
    * *Special Reference No. 1 of 1998 (Third Judges Case)* (1998 INSC 516)
    * *I.R. Coelho v. State of Tamil Nadu* (2007 INSC 30, [2007] 1 SCR 706)
    * *National Legal Services Authority (NALSA) v. UOI* (2014 INSC 275)
    * *Supreme Court Advocates-on-Record Assn (NJAC Case)* (2015 INSC 758)
    * *Justice K.S. Puttaswamy v. Union of India (Privacy)* (2017 INSC 777)
    * *Navtej Singh Johar v. Union of India* (2018 INSC 790)
    * *Joseph Shine v. Union of India* (2018 INSC 898)
    * *Sabarimala Case (Indian Young Lawyers Assn)* (2018 INSC 904)
    * *Jarnail Singh v. Lachhmi Narain Gupta* (2018 INSC 899)
    * *Jarnail Singh II / Reservation Review* (2022 INSC 114)
    * *Supriyo @ Supriya Chakraborty v. Union of India (Marriage Equality)* (2023 INSC 920)
    * *In Re Article 370 of the Constitution* (2023 INSC 1058)
    * *Association for Democratic Reforms v. UOI (Electoral Bonds)* (2024 INSC 113)
  * **Structured Fields:**
    * Case Title, Official Neutral Citation (`YYYY INSC XXX`), SCR Citation, Date of Judgment.
    * Bench Strength and Judges.
    * Facts & Procedural History.
    * Ratio Decidendi and Constitutional Holdings.
    * Articles, Statutes, and Precedents Referenced.
* **Local Storage:**
  * Raw: `data/raw/judgments/`
  * Processed: `data/processed/judgments/supreme_court_landmarks.json`

---

## 4. Statutory Central Legislation

* **Authoritative Source:** India Code (Digital Repository of All Central and State Acts).
* **Official Portal:** [https://www.indiacode.nic.in/](https://www.indiacode.nic.in/)
* **License:** Government Open Data License - India (GODL) / Public Domain.
* **Scope Ingested:**
  Statutes directly implementing or interacting with constitutional guarantees:
  1. **Citizenship Act, 1955** (Act No. 57 of 1955) — Governs acquisition, termination, and registration of citizenship pursuant to Articles 5–11.
  2. **Representation of the People Act, 1951** (Act No. 43 of 1951) — Governs elections, conduct of polls, disqualification of legislators under Articles 102, 191, and Part XV.
  3. **Protection of Human Rights Act, 1993** (Act No. 10 of 1994) — Establishes NHRC and State HRCs to safeguard rights embodied in the Constitution and international covenants.
  4. **Right to Information Act, 2005** (Act No. 22 of 2005) — Codifies freedom of speech and right to know derived under Article 19(1)(a).
  5. **Armed Forces (Special Powers) Act, 1958** (Act No. 28 of 1958) — Relates to public order, armed forces deployments, and constitutional scrutiny under Articles 21, 33, 34, and 355.
* **Local Storage:**
  * Processed: `data/processed/legislation/central_acts.json`

---

## 5. Corpus Extensibility & Ingestion Integrity

* **Total Processed Documents:** 692 parent documents (477 constitutional articles/schedules, 106 amendments, 104 judgments, 5 statutory central acts).
* **Deterministic Content Hash:** Every record carries an invariant SHA-256 hash computed over its canonical normalized text and metadata.
* **Extensibility:** The ingestion scripts (`scripts/ingest_*.py`, `scripts/build_corpus.py`) accept dynamic parameters, support arbitrary counts, and stream large collections without in-memory limits.

