# Ingestion of Central Legislation: `scripts/ingest_legislation.py`

[Back to Ingestion Overview](README.md) • [Back to Main Index](../README.md)

---

## 1. Basic Introduction

### What is this file?
`scripts/ingest_legislation.py` is the **Statutory Central Legislation Ingestion Module**. It parses, structures, and cross-references **17 core Central Acts comprising 1,975 statutory sections** from the official *India Code* repository (Ministry of Law and Justice, Government of India).

### Why must a Constitutional Legal Assistant ingest statutory acts?
Constitutional law does not exist in a vacuum. Most constitutional disputes emerge directly from the enforcement of statutory enactments:
- **Procedural Safeguards**: Article 21 and Article 22(1)–(2) operate directly through Sections 41, 50, 56, and 57 of the Code of Criminal Procedure (CrPC).
- **Fundamental Freedoms vs Penal Laws**: Freedom of speech (Article 19(1)(a)) is frequently tested against Sections 124A (Sedition), 153A, 295A, and 499 (Defamation) of the Indian Penal Code (IPC).
- **Statutory Rights Grounded in Constitution**: The Right to Information Act (RTI 2005) derives directly from Article 19(1)(a); the Citizenship Act, 1955 derives from Articles 5–11; the Representation of the People Act, 1951 derives from Article 326.

Without statutory acts, an AI assistant cannot answer practical legal questions like *"Can police search my house without a warrant under CrPC and Article 21?"*

---

## 2. Ingested Acts & Constitutional Cross-References

The 17 Central Acts are grouped into two categories:

### Category 1: Constitutional Framework Acts (10 Acts)

| Act Name | Enactment | Key Sections | Constitutional Relationship |
| :--- | :--- | :--- | :--- |
| **Citizenship Act, 1955** | Act 57 of 1955 | Sec 3, 4, 5, 6, 6A, 8, 9, 10, 14A | Operationalizes **Articles 5–11** (Citizenship by birth, descent, naturalization, Assam Accord Sec 6A). |
| **Representation of the People Act, 1951** | Act 43 of 1951 | Sec 8, 9, 11, 29A, 29B, 29C, 123 | Operationalizes **Part XV (Elections)**: Disqualification of convicted MPs/MLAs, electoral corrupt practices. |
| **Protection of Human Rights Act, 1993** | Act 10 of 1994 | Sec 2(1)(d), 3, 12, 18, 21, 30 | Establishes NHRC & SHRC enforcing **Part III Fundamental Rights** and international covenants. |
| **Right to Information Act, 2005** | Act 22 of 2005 | Sec 3, 4, 6, 7, 8, 19, 20 | Operationalizes implied right to information under **Article 19(1)(a)**. |
| **Armed Forces (Special Powers) Act, 1958** | Act 28 of 1958 | Sec 3, 4, 6 | Disturbed areas, immunity for armed forces under **Article 34**. |
| **Official Languages Act, 1963** | Act 19 of 1963 | Sec 3, 4, 7 | Implements **Part XVII (Articles 343–351)** on Hindi and English usage in Union & Supreme Court. |
| **Delimitation Act, 2002** | Act 33 of 2002 | Sec 3, 8, 9 | Boundary readjustment of electoral constituencies under **Article 82**. |
| **CAG's (Duties and Powers) Act, 1971** | Act 56 of 1971 | Sec 10, 13, 16 | Operationalizes auditing duties of the CAG under **Articles 148–151**. |
| **Supreme Court (Number of Judges) Act, 1956** | Act 55 of 1956 | Sec 2 | Enacted under **Article 124(1)** to fix judge strength (increased to 34 judges). |
| **National Commission for Minorities Act, 1992** | Act 19 of 1992 | Sec 3, 9 | Safeguards religious and linguistic minority rights under **Articles 29 & 30**. |

---

### Category 2: Downloaded Central Legal Codes (7 Major Codes / 1,900+ Sections)

| Central Code | Enactment | Sections Ingested | Key Intersections with Constitutional Law |
| :--- | :--- | :--- | :--- |
| **Indian Penal Code (IPC), 1860** | Act 45 of 1860 | **575 sections** | Tested against Article 14, 19, 21 (e.g., Sec 377, Sec 497 adultery, Sec 124A sedition). |
| **Code of Criminal Procedure (CrPC), 1973** | Act 2 of 1974 | **525 sections** | Tested against Article 21 & 22: Arrest (Sec 41), Bail (Sec 436–439), Search warrants (Sec 93, 165), Remand (Sec 167). |
| **Indian Evidence Act (IEA), 1872** | Act 1 of 1872 | **184 sections** | Self-incrimination Article 20(3) vs Sec 25–27 (confessions to police). |
| **Code of Civil Procedure (CPC), 1908** | Act 5 of 1908 | **171 sections** | Res judicata (Sec 11), writ jurisdiction, execution of decrees. |
| **Industrial Disputes Act, 1947** | Act 14 of 1947 | **64 sections** | Right to livelihood (Article 21), retrenchment, labor rights. |
| **Negotiable Instruments Act, 1881** | Act 26 of 1881 | **156 sections** | Cheque bounce (Sec 138), procedural due process. |
| **Motor Vehicles Act, 1988** | Act 59 of 1988 | **256 sections** | Third-party insurance compensation under Article 21 right to life. |

---

## 3. Section-Level Data Structure

Every central act is parsed into structured individual sections:
```python
{
    "id": "act_citizenship_1955",
    "document_id": "act_citizenship_1955",
    "document_type": "statute",
    "title": "Citizenship Act, 1955 (Act No. 57 of 1955)",
    "short_title": "Citizenship Act, 1955",
    "year": 1955,
    "constitutional_basis": ["Article 5", "Article 6", "Article 7", "Article 8", "Article 9", "Article 10", "Article 11"],
    "sections": [
        {
            "section_id": "act_citizenship_1955_sec_03",
            "section_number": "Section 3",
            "title": "Citizenship by birth",
            "text": "Every person born in India— (a) on or after the 26th day of January, 1950..."
        },
        ...
    ],
    "source_url": "https://www.indiacode.nic.in",
    "source_name": "India Code: Digital Repository of All Central and State Acts, Government of India"
}
```

---

## 4. Viva Presentation & Defense Q&A

### Q1: Why did you include statutory acts like CrPC and IPC in a Constitutional Legal AI?
> **Student Answer**:
> *"Constitutional principles are operationalized through statutory legislation. For example, when a citizen asks about illegal detention or warrantless home searches, Article 21 provides the overarching constitutional guarantee ('procedure established by law'), but Section 165 of the CrPC specifies the exact procedural preconditions police must follow. By ingesting both Constitutional Articles and Central Acts, our hybrid retriever can perform cross-corpus synthesis, providing answers that are both constitutionally grounded and practically actionable."*

### Q2: What is the source of the statutory text and how was it verified?
> **Student Answer**:
> *"All statutory acts were obtained directly from the official **India Code** digital repository (`indiacode.nic.in`), administered by the Legislative Department of the Ministry of Law and Justice. Every record retains its official Act Number (e.g. Act No. 2 of 1974 for CrPC), enactment date, commencement date, and an immutable SHA-256 cryptographic checksum."*

