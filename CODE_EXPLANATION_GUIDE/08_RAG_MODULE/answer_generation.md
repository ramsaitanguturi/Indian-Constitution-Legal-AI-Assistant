# Grounded Legal Answer Generation: `rag/generator.py`

[Back to RAG Module Overview](README.md) • [Back to Main Index](../README.md)

---

## 1. Basic Introduction

### What is this file?
`rag/generator.py` is the **Grounded Legal Answer Generation Engine**. It takes the deduplicated parent documents and exact supporting child passages recovered by `ParentChildRecovery` and synthesizes an authoritative, structured legal answer.

### Why does this file exist?
Unconstrained LLMs are prone to **legal hallucination**:
- Fabricating non-existent constitutional articles (e.g., claiming *"Article 21B guarantees housing"*).
- Inverting judicial holdings (e.g., stating a judgment was unanimous when it was a 5:4 split).
- Citing non-existent case reporters (e.g., fabricating AIR or SCC citations).

`rag/generator.py` enforces absolute factual grounding through a dual-mode architecture:
1. **Online Mode (Google Gemini)**: Governed by `GROUNDED_RAG_PROMPT` at `temperature = 0.0` with explicit bracketed citation requirements `[Doc: <doc_id>]` and zero-external-knowledge constraints.
2. **Offline Fallback Mode (Deterministic Legal Synthesizer)**: When internet is unavailable or no API key is supplied, a built-in deterministic synthesizer constructs structured, publication-grade answers directly from verified `parent_store.json` records without calling any external API.

---

## 2. Imports and Dependencies

```python
# rag/generator.py L8-L13
import os
import re
from typing import Dict, List, Any, Optional

from config import GEMINI_API_KEY, DEFAULT_LLM_MODEL
```

| Import / Constant | Purpose |
| :--- | :--- |
| `GEMINI_API_KEY` | Imported from `config.py`. Read from environment variables `GEMINI_API_KEY` or `GOOGLE_API_KEY`. |
| `DEFAULT_LLM_MODEL` | Defaults to `"gemini-1.5-flash"` in `config.py`. Fast, accurate, and cost-effective for grounded question answering. |
| `langchain_google_genai.ChatGoogleGenerativeAI` | Dynamically imported inside `_init_llm()` to connect to the Google Gemini API. |

---

## 3. Grounding Prompt: `GROUNDED_RAG_PROMPT`

```text
You are a senior Constitutional Law Scholar and Legal Grounding Engine specializing in the Constitution of India.
Your mission is to formulate an authoritative, precise legal answer derived STRICTLY and EXCLUSIVELY from the verified SOURCE DOCUMENTS provided below.

GROUNDING & INTEGRITY CONSTRAINTS:
1. Answer ONLY using the facts, provisions, definitions, and legal ratios contained in the provided evidence.
2. ZERO EXTERNAL HALLUCINATION: Under NO circumstances should you cite Articles, Amendments, or Judgments that are NOT present in the provided source documents.
3. Every legal claim MUST include an explicit bracketed citation key matching the source document ID, e.g. [Doc: <doc_id>].
4. Clearly distinguish direct statutory/judicial evidence from explanatory legal analysis.
5. If the provided documents are insufficient to answer the query, state explicitly: "INSUFFICIENT EVIDENCE: The provided constitutional sources do not contain sufficient evidence to answer this query."

STRUCTURE YOUR RESPONSE INTO THREE DISTINCT SECTIONS:
### 📜 Direct Legal Evidence
(Quote or present verbatim the exact constitutional clauses or judicial ratio decidendi from the sources, with citation keys)

### ⚖️ Grounded Legal Analysis
(Provide structured, objective synthesis explaining the legal implications, scope, and principles strictly based on the evidence)

### 📚 Verified Citations
(List the exact documents cited using [Doc: <doc_id>] and their formal titles)
```

### Why are these constraints effective?
1. **Strict Three-Part Separation**: Separating verbatim quotations (`### 📜 Direct Legal Evidence`) from synthesis (`### ⚖️ Grounded Legal Analysis`) ensures that users can immediately verify primary statutory text versus legal interpretation.
2. **Explicit Bracketed Citations**: Requiring `[Doc: <doc_id>]` on every factual claim enables downstream automated parsing by `CitationValidator`.
3. **Negative Constraint Trigger**: Instructing the model to output `"INSUFFICIENT EVIDENCE"` overrides the LLM's natural propensity to please the user with speculative general knowledge.

---

## 4. Class: `GroundedGenerator`

```python
class GroundedGenerator:
    """
    Grounded Generator with dual-mode execution:
    1. Online Google Gemini Chat with strict grounding constraints when API key is provided.
    2. Deterministic Grounded Legal Synthesis Engine when offline or API key is absent.
    """
```

### 4.1 Constructor and Dynamic Key Update
```python
# Lines 51-65
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        enable_online: bool = False,
    ):
        self.api_key = api_key or GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
        self.model_name = model_name or DEFAULT_LLM_MODEL
        self.enable_online = enable_online or bool(api_key and len(api_key) > 5)
        self.llm_available = bool(self.enable_online and self.api_key and len(self.api_key) > 5)
        self.llm = None

        if self.llm_available:
            self._init_llm()
```
- **Zero Temperature**: Notice line 76: `temperature=0.0`. In creative writing, high temperature encourages novelty. In legal RAG, `temperature=0.0` ensures greedy decoding for maximum determinism and factual fidelity.
- **Short Timeout**: Line 77 sets `timeout=5.0` seconds so that any temporary network glitch falls back smoothly to offline mode rather than freezing the application.

---

### 4.2 Primary Method: `generate(...)`

```python
def generate(
    self,
    query: str,
    recovered_context: Dict[str, Any],
    routing_decision: Optional[Any] = None,
    dynamic_api_key: Optional[str] = None,
) -> Dict[str, Any]
```

#### Execution Steps:
1. **Input Verification**: If `recovered_context["parents"]` is empty, immediately returns an authoritative notice of insufficient evidence without invoking the LLM.
2. **Structured Citation Catalog Creation**: Calls `_build_structured_citations(parents)` to generate structured metadata objects for every recovered document.
3. **Execution Branch**:
   - **Branch A (Online)**: If `llm_available` is `True`, passes context and query through the LangChain prompt chain. Parses output into three sections via `_parse_distinguished_sections()`.
   - **Branch B (Offline Fallback)**: If offline or if LLM call fails, invokes `_synthesize_grounded_offline()`.

---

### 4.3 Deterministic Offline Legal Synthesis (`_synthesize_grounded_offline`)

When running locally without an internet connection or API key, the offline engine constructs an answer directly from the verified database records:
- For Constitutional Articles: Formats the official title, part, category, verbatim clause text, legal explanation, and historical framing.
- For Landmark Judgments: Formats the case name, citation, bench, year, facts, ratio decidendi, and verdict.
- Formats structured citations with `[Doc: <doc_id>]` keys.

This guarantees that the application **never fails to demonstrate complete functionality** even during offline classroom viva presentations!

---

## 5. Actual Code Walkthrough

### Code Excerpt: Parsing Structured Sections (Lines 208-234)
```python
    def _parse_distinguished_sections(self, text: str) -> Dict[str, str]:
        """Separates response text into Evidence, Analysis, and Citations sections."""
        evidence = ""
        analysis = ""
        citations = ""

        ev_match = re.search(r"###\s*📜\s*Direct Legal Evidence(.*?)(?=###\s*⚖️|###\s*📚|$)", text, re.DOTALL)
        an_match = re.search(r"###\s*⚖️\s*Grounded Legal Analysis(.*?)(?=###\s*📚|$)", text, re.DOTALL)
        cit_match = re.search(r"###\s*📚\s*Verified Citations(.*?)$", text, re.DOTALL)

        if ev_match:
            evidence = ev_match.group(1).strip()
        if an_match:
            analysis = an_match.group(1).strip()
        if cit_match:
            citations = cit_match.group(1).strip()

        if not evidence and not analysis:
            analysis = text

        return {
            "evidence": evidence,
            "analysis": analysis,
            "citations": citations,
        }
```
- **Why this regex parsing matters**: It unpacks the raw model text into clean distinct UI components. In the Streamlit app, `ui_formatter.py` places `evidence` into an expandable statutory quote box, `analysis` into the primary answer pane, and `citations` into structured citation cards.

---

## 6. Viva Presentation & Defense Q&A

### Q1: Why is `temperature = 0.0` strictly required in legal RAG?
> **Student Answer**:
> *"Temperature in an LLM controls the entropy of the next-token probability distribution. A temperature above 0.0 introduces stochastic sampling, which increases the likelihood of sampling tokens outside the retrieved evidence context—leading to hallucinations or altered statutory wording. In legal question answering, consistency, predictability, and verbatim statutory accuracy are paramount. Setting `temperature = 0.0` forces deterministic greedy token selection, ensuring the model adheres strictly to the retrieved context."*

### Q2: What happens if there is no internet connection during the viva demonstration?
> **Student Answer**:
> *"The system is built with complete offline resilience. If an API key is not provided or the internet is disconnected, `GroundedGenerator` automatically falls back to our deterministic offline synthesis engine (`_synthesize_grounded_offline`). It pulls the full verified text, ratio decidendi, and legal analysis directly from `parent_store.json`, constructing a complete, properly cited legal response. The entire pipeline remains 100% operational offline."*

