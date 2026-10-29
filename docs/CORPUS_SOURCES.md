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
  * 211 total Supreme Court judgment records, explicitly categorized by content granularity:
    * **13 Official Full-Text Judgments (`content_type: "full_text"`):** Extracted page-by-page from official Supreme Court of India PDF documents using `pypdf` (>1.2M characters total). Key full-text decisions include:
      * *A.K. Gopalan v. State of Madras* (1950 INSC 13, 247-page landmark constitutional bench decision on preventive detention and Article 21)
      * *Romesh Thappar v. State of Madras* (1950 INSC 16, freedom of speech and public order)
      * *Brij Bhushan v. State of Delhi* (1950 INSC 17, pre-censorship of the press)
      * *Rashid Ahmed v. Municipal Board, Kairana* (1950 INSC 11, writ jurisdiction under Article 32)
      * *Chintaman Rao v. State of M.P.* (1950 INSC 28, test of reasonable restrictions under Article 19)
      * *Chiranjit Lal Chowdhuri v. Union of India* (1950 INSC 30, corporate rights under Article 14 & 31)
      * *Dr. N.B. Khare v. State of Delhi* (1950 INSC 15, externment and Article 19)
      * *State of Madras v. Champakam Dorairajan* (1951 INSC 25, caste-based reservations and Article 15)
      * *Keshavan Madhava Menon v. State of Bombay* (1951 INSC 3, doctrine of eclipse and pre-constitutional laws)
      * *State of Bombay v. F.N. Balsara* (1951 INSC 32, pith and substance doctrine and prohibition laws)
      * *Shankari Prasad Singh Deo v. Union of India* (1951 INSC 45, First Constitutional Amendment challenge)
      * *State of Bombay v. Atma Ram Sridhar Vaidya* (1951 INSC 4, preventive detention grounds under Article 22)
      * *Shamdasani v. Central Bank of India* (1951 INSC 66, fundamental rights enforceable only against State, not private individuals)
    * **104 Landmark Precedent Briefs (`content_type: "summary_only"`):** Digest-level legal briefs preserving case title, neutral citation (`YYYY INSC XXX`), SCR citation, coram/bench strength, procedural history, issues, ratio decidendi, and constitutional holdings (e.g. *Kesavananda Bharati*, *Maneka Gandhi*, *Minerva Mills*, *Indra Sawhney*, *S.R. Bommai*, *Puttaswamy*, *Navtej Johar*, *Sabarimala*, *Electoral Bonds*). Explicitly labeled to prevent presenting digests as official judgment text.
    * **94 Open Data Registry Records (`content_type: "metadata_only"`):** Discovered and ingested from official AWS Open Data Registry Parquet tables (`s3://indian-supreme-court-judgments/`) for 1950 and 1951. Preserves case metadata, neutral citations, and judges.
  * **Structured Fields:**
    * Case Title, Official Neutral Citation (`YYYY INSC XXX`), SCR Citation, Date of Judgment.
    * Bench Strength and Coram / Judges.
    * Facts & Procedural History.
    * Ratio Decidendi and Constitutional Holdings.
    * Articles, Statutes, and Precedents Referenced.
    * Full Text (where available) with SHA-256 and source PDF provenance.
* **Local Storage:**
  * Raw: `data/raw/judgments/`
  * Processed: `data/processed/judgments/supreme_court_landmarks.json`

---

## 4. Statutory Central Legislation

* **Authoritative Source:** India Code (Digital Repository of All Central and State Acts).
* **Official Portal:** [https://www.indiacode.nic.in/](https://www.indiacode.nic.in/)
* **License:** Government Open Data License - India (GODL) / Public Domain.
* **Scope Ingested:**
  12 Central Acts with complete section-level structure (1,947 sections total) directly implementing or interacting with constitutional guarantees:
  1. **Indian Penal Code, 1860** (Act No. 45 of 1860) — 511 sections; substantive criminal law, sedition (§ 124A), defamation (§ 499), offences against state and public tranquility.
  2. **Code of Criminal Procedure, 1973** (Act No. 2 of 1974) — 484 sections; procedural safeguards, arrest (§ 41), preventive detention (§ 151), search and seizure, bail.
  3. **Indian Evidence Act, 1872** (Act No. 1 of 1872) — 167 sections; admissibility, burden of proof, confessions, statutory presumptions.
  4. **Code of Civil Procedure, 1908** (Act No. 5 of 1908) — 158 sections; civil adjudication, res judicata (§ 11), inherent powers (§ 151).
  5. **Industrial Disputes Act, 1947** (Act No. 14 of 1947) — 40 sections; labor rights, dispute resolution, strikes and lockouts pursuant to Article 43.
  6. **Negotiable Instruments Act, 1881** (Act No. 26 of 1881) — 147 sections; commercial instruments, dishonor proceedings (§ 138).
  7. **Motor Vehicles Act, 1988** (Act No. 59 of 1988) — 217 sections; transport regulation, third-party liability, compensation tribunals.
  8. **Citizenship Act, 1955** (Act No. 57 of 1955) — 19 sections; governs acquisition, termination, and registration of citizenship pursuant to Articles 5–11.
  9. **Representation of the People Act, 1951** (Act No. 43 of 1951) — 171 sections; governs elections, conduct of polls, disqualification of legislators under Articles 102, 191, and Part XV.
  10. **Protection of Human Rights Act, 1993** (Act No. 10 of 1994) — 43 sections; establishment of NHRC, SHRCs, and Human Rights Courts.
  11. **Right to Information Act, 2005** (Act No. 22 of 2005) — 31 sections; operationalizes freedom of expression and citizen oversight under Article 19(1)(a).
  12. **Armed Forces (Special Powers) Act, 1958** (Act No. 28 of 1958) — 6 sections; special powers in disturbed areas, interacting with Articles 21, 33, and 34.
* **Local Storage:**
  * Raw: `data/raw/legislation/`
  * Processed: `data/processed/legislation/central_acts.json`

---

## 5. Corpus Extensibility & Ingestion Integrity

* **Total Processed Documents:** 806 parent documents (477 constitutional articles/schedules, 106 amendments, 211 judgments [13 full-text, 104 briefs, 94 metadata], 12 statutory central acts).
* **Deterministic Content Hash:** Every record carries an invariant SHA-256 hash computed over its canonical normalized text and metadata.
* **Extensibility:** The ingestion scripts (`scripts/ingest_*.py`, `scripts/build_corpus.py`) accept dynamic parameters, support arbitrary counts, and stream large collections without in-memory limits.


