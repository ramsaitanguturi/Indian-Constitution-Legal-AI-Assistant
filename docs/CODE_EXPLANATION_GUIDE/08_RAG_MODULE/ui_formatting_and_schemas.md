# UI Formatting & Canonical Schemas: `rag/ui_formatter.py` & `rag/schema.py`

[Back to RAG Module Overview](README.md) • [Back to Main Index](../README.md)

---

## 1. Basic Introduction

### What are these files?
- **`rag/schema.py`** defines the **Canonical Data Contracts** and validation models using Pydantic (`LegalDocument`, `ProvenanceMetadata`, `ClauseRecord`). It ensures every ingested document possesses verifiable cryptographic hashes, strict typing, and structured fields.
- **`rag/ui_formatter.py`** defines the **Presentation Layer Transformation Engine**. It converts the complex, multi-stage `PipelineResult` dataclass into clean, presentation-ready UI data structures (`FormattedLegalAnswer`, `FormattedProvision`, `FormattedJudgment`) for the Streamlit front-end.

### Why are explicit schemas and UI formatters necessary?
1. **No Synthetic Metadata Fabrication**: In legal informatics, metadata must be mathematically verified. `rag/schema.py` mandates cryptographic SHA-256 hashes (`source_hash`) and leaves unavailable fields as `None` rather than fabricating synthetic judicial dates.
2. **Decoupling Logic from Display**: The Streamlit user interface (`app.py`) should not contain complex regex parsers or string manipulation logic. `rag/ui_formatter.py` acts as a clean Presentation ViewModel, isolating formatting nuances and guaranteeing that empty sections are never forced onto the user.

---

## 2. Canonical Data Schemas: `rag/schema.py`

```python
# rag/schema.py L11-L25
from pydantic import BaseModel, Field

class ProvenanceMetadata(BaseModel):
    """Source provenance and document verification metadata."""
    source_url: str = Field(description="Official authoritative or public dataset URL")
    source_name: str = Field(description="Name of the official issuing body or public repository")
    source_file: Optional[str] = Field(default=None, description="Original filename or path in raw archive")
    source_hash: str = Field(description="SHA-256 cryptographic checksum of original raw content")
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version_date: Optional[str] = None
    legal_status: str = "in_force"
    license: str = "Government Open Data License - India (GODL)"
    processing_status: str = "processed"
```

### The Master `LegalDocument` Schema (Lines 34-98)
Standardizes all four document types across the 886-document corpus:
- **`document_type`**: `"constitution_article"`, `"constitution_amendment"`, `"judgment"`, `"statute"`.
- **Judicial Metadata**: `court`, `case_name`, `citation`, `neutral_citation`, `document_date`, `bench`, `judges`.
- **Statutory Metadata**: `part`, `article_number`, `clause`, `section`, `schedule`, `amendment_number`, `year`.
- **Structural Text Units**: `text`, `clauses`, `sections`, `explanation`, `historical_context`.
- **Judgment Doctrinal Units**: `facts`, `questions_of_law`, `holdings`, `ratio_decidendi`, `verdict`, `key_takeaways`.
- **Methods**:
  - `compute_hash()`: Computes `hashlib.sha256(self.text.encode("utf-8")).hexdigest()`.
  - `to_parent_dict()`: Converts to the schema expected by `parent_store.json`.

---

## 3. UI Presentation Layer: `rag/ui_formatter.py`

### 3.1 Presentation Dataclasses

```python
# Lines 17-64
@dataclass
class FormattedProvision:
    title: str
    article_or_section: str
    document_id: str
    part: str = ""
    category: str = ""
    scope_and_guarantee: str = ""
    context: str = ""
    excerpt: str = ""
    full_text: str = ""

@dataclass
class FormattedJudgment:
    case_name: str
    citation: str
    year: str
    bench: str
    document_id: str
    ratio_decidendi: str = ""
    verdict: str = ""
    facts: str = ""
    key_principles: List[str] = field(default_factory=list)
    excerpt: str = ""
    full_text: str = ""

@dataclass
class FormattedLegalAnswer:
    is_abstained: bool
    abstention_reason: Optional[str]
    direct_answer: str
    provisions: List[FormattedProvision]
    judgments: List[FormattedJudgment]
    exceptions: List[str]
    citations: List[Dict[str, Any]]
    confidence_level: str
    confidence_score: float
    citations_valid: bool
    citations_checked_count: int
    strategy: str
    intent: str
    language: str
    extracted_entities: Dict[str, List[str]]
    unsupported_claims: List[str] = field(default_factory=list)
    invalid_citations: List[Dict[str, Any]] = field(default_factory=list)
```

---

### 3.2 Method: `format_legal_pipeline_result(res: Any) -> FormattedLegalAnswer`

Performs clean, robust data transformation:
1. **Abstention Interception (Lines 72-96)**: If `res.abstained` is `True`, returns a clean `FormattedLegalAnswer` with `provisions=[]`, `judgments=[]`, confidence set to `VERY_LOW`, and direct answer populated with the safe refusal notice.
2. **Context Categorization (Lines 108-110)**: Separates recovered parents into constitutional articles (`const_parents`), court judgments (`judgment_parents`), and statutory acts (`statute_parents`).
3. **Executive Summary Extraction**: Parses direct answers, procedural tests, exceptions, and limitations.
4. **Provision Card Construction**: Creates `FormattedProvision` instances with verbatim full text, scope, and part information.
5. **Judgment Card Construction**: Creates `FormattedJudgment` instances with case citations, bench composition, ratio decidendi, and key legal takeaways.

---

## 4. Actual Code Walkthrough

### Code Excerpt: Abstention Formatting in `ui_formatter.py` (Lines 71-96)
```python
    # 1. Abstention handling
    if getattr(res, "abstained", False):
        reason = getattr(res, "abstention_reason", "Out of Scope / Low Relevance")
        answer_text = getattr(res, "generated_answer", "")
        clean_ans = answer_text or (
            "The assistant could not identify verified constitutional or statutory evidence "
            "directly addressing this query. To prevent ungrounded legal assertions, "
            "generation has been safely withheld."
        )
        return FormattedLegalAnswer(
            is_abstained=True,
            abstention_reason=reason,
            direct_answer=clean_ans,
            provisions=[],
            judgments=[],
            exceptions=[],
            citations=[],
            confidence_level="VERY_LOW",
            confidence_score=0.0,
            citations_valid=True,
            citations_checked_count=0,
            strategy=res.routing_decision.get("strategy", "N/A") if hasattr(res, "routing_decision") else "N/A",
            intent=res.intent.get("intent", "N/A") if hasattr(res, "intent") else "N/A",
            language=res.language.get("language", "en").upper() if hasattr(res, "language") else "EN",
            extracted_entities=getattr(res, "entities", {}),
        )
```
- **Why this structure prevents UI crashes**: In Streamlit, if an answer is abstained, attempting to iterate over `res.parent_context["parents"]` would cause `KeyError` or render blank ugly boxes. By constructing an explicit `FormattedLegalAnswer` with empty lists, `app.py` simply displays the safe message and hides the evidence cards automatically.

---

## 5. Viva Presentation & Defense Q&A

### Q1: Why use Pydantic for data validation in `schema.py`?
> **Student Answer**:
> *"Pydantic enforces strict type validation and data integrity at runtime. In legal applications, missing fields or incorrect types (e.g. integer year stored as string or missing SHA-256 hash) can corrupt downstream indexers. Pydantic ensures that every document ingested into our database strictly adheres to our schema, providing cryptographic provenance tracking with zero synthetic metadata fabrication."*

### Q2: What is the role of `ui_formatter.py` in the system architecture?
> **Student Answer**:
> *"It serves as the ViewModel in our 4-tier architecture. It isolates the presentation logic from the underlying pipeline execution. `LegalRAGPipeline` outputs a complex `PipelineResult` with 17 intermediate diagnostic fields. `ui_formatter.py` transforms this into clean, strongly typed display cards (`FormattedProvision`, `FormattedJudgment`) for Streamlit. If we ever swap Streamlit for React or FastAPI, the backend pipeline remains 100% untouched."*

