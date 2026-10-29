# Legal Data Schema Specification

This document details the unified data schema utilized across the **Indian Constitution Legal AI Assistant** ingestion, validation, vectorization, and retrieval pipelines.

---

## 1. Unified Canonical Schema: `LegalDocument`

All source documents ingested from the Constitution of India, Constitution Amendment Acts, Supreme Court judgments, and Central Statutes are mapped to the canonical `LegalDocument` schema implemented in `rag/schema.py` using Pydantic V2.

```python
class LegalDocument(BaseModel):
    document_id: str                      # Deterministic ID: {doc_type}_{identifier}
    document_type: str                    # constitution | amendment | judgment | legislation
    title: str                            # Full formal title
    short_title: Optional[str]            # Abbreviated title or common name
    court: Optional[str]                  # E.g. "Supreme Court of India"
    case_name: Optional[str]              # E.g. "Kesavananda Bharati v. State of Kerala"
    citation: Optional[str]               # Reported citation (e.g. [1973] Supp SCR 1)
    neutral_citation: Optional[str]       # Neutral citation (e.g. 1973 INSC 258)
    petition_number: Optional[str]        # E.g. Writ Petition (Civil) No. 135 of 1970
    document_date: Optional[str]          # ISO date YYYY-MM-DD
    enactment_date: Optional[str]         # Date of legislative passage
    effective_date: Optional[str]         # Date of formal commencement
    jurisdiction: str = "India"           # Legal jurisdiction
    part: Optional[str]                   # E.g. "Part III"
    article: Optional[str]                # E.g. "21"
    clause: Optional[str]                 # E.g. "(1)"
    section: Optional[str]                # E.g. "Section 3"
    schedule: Optional[str]               # E.g. "Seventh Schedule"
    amendment_number: Optional[int]       # E.g. 42
    provisions_modified: List[str]        # Articles/Schedules affected
    statement_of_objects: Optional[str]   # Legislative statement of purpose
    full_text: str                        # Unaltered primary legal text
    source_url: str                       # Authoritative official URL
    source_name: str                      # Official source organization
    source_file: Optional[str]            # Original downloaded filename
    source_hash: str                      # SHA-256 of text and core fields
    retrieved_at: str                     # ISO timestamp of retrieval
    version_date: Optional[str]           # Date of legal consolidation
    legal_status: str = "in_force"        # in_force | amended | repealed
    language: str = "en"                  # Language code
    parent_document_id: Optional[str]     # Parent ID if a subordinate provision
    license: str                          # License (e.g. GODL-India)
    processing_status: str = "processed"  # processed | raw | failed
```

---

## 2. Document Identifiers

To guarantee idempotency and avoid duplicate chunking/indexing:

| Document Type | Document ID Pattern | Example |
| :--- | :--- | :--- |
| **Constitutional Article** | `const_art_{article_clean}` | `const_art_21` |
| **Constitutional Schedule** | `const_sched_{schedule_num}` | `const_sched_7` |
| **Preamble** | `const_preamble` | `const_preamble` |
| **Constitution Amendment** | `amend_act_{number}` | `amend_act_42` |
| **Supreme Court Judgment** | `judg_sc_{neutral_citation_clean}` | `judg_sc_1973_insc_258` |
| **Central Statute** | `leg_central_{slug}` | `leg_central_citizenship_act_1955` |

---

## 3. Child Chunk Schema & Relationship

To enable high-precision retrieval without losing broader statutory context, the chunker (`rag/chunking.py`) splits large legal texts into passages while preserving parent context metadata:

```python
class LegalChunk:
    chunk_id: str             # {document_id}#chunk_{chunk_index}
    parent_id: str            # Maps directly to parent_store.json document_id
    text: str                 # Chunk text (clause/subclause/ratio level)
    chunk_index: int          # Position in document
    char_start: int           # Character offset start
    char_end: int             # Character offset end
    document_type: str        # constitution | amendment | judgment | legislation
    title: str                # Document title
    source_url: str           # Source URL for direct citation
    legal_identifiers: List   # Embedded tokens (e.g. ["article_21", "1973_insc_258"])
```

### Parent-Store Hydration
During retrieval, child chunks retrieved by Dense and BM25 search are mapped to their canonical parent record in `data/processed/parent_store.json`. This provides the LLM generator with complete statutory context, provisos, and ratio decidendi.

