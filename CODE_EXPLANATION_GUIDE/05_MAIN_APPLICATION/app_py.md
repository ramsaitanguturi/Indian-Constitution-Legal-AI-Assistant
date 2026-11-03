# Code Explanation: `app.py` 🖥️

> **Source File**: [`app.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/app.py)  
> **Lines of Code**: 672 lines  
> **Primary Responsibility**: Web application user interface, session state management, user input handling, and presentation of grounded legal responses.

---

## 1. Basic Introduction

### What is this file?
[`app.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/app.py) is the primary user-facing entry point for the **Indian Constitution Legal AI Assistant**. It is an interactive, browser-based single-page application built using the Streamlit web framework.

### Why does this file exist?
Without an accessible graphical interface, users, legal researchers, and examination committee members would have to run complex Python terminal commands or inspect raw JSON files. [`app.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/app.py) wraps the complex 16-stage NLP and retrieval pipeline into a professional, dark-themed legal research portal where anyone can ask a question in natural language and receive an authoritative, structured, and citation-verified legal answer.

### What responsibility does it have?
1. **Linux / Cloud Compatibility**: Patches older SQLite versions at runtime so ChromaDB does not crash on Linux or Streamlit Cloud.
2. **Resource Caching**: Caches the heavy RAG pipeline, ingestor, retriever, and vector store so they are loaded into RAM once, avoiding slow reloads on every user click.
3. **Session State Management**: Tracks `st.session_state` variables (`current_result`, `current_formatted`, `current_query`) to ensure that clicking tabs or expanders does not erase previous search results.
4. **Sidebar Controls**: Allows users to configure retrieval depth (Top-K slider from 2 to 6) and dynamically inject a Google Gemini API key if online generative expansion is desired.
5. **Grounded Presentation**: Displays results in clearly distinguished, non-overlapping cards: Direct Answer, Relevant Provisions, Relevant Judgments, Important Exceptions, and Verified Source Cards.
6. **Technical Diagnostic Audit**: Renders a dedicated expander revealing internal research metrics (intent, routing strategy, 6-signal confidence score, NLI checks, and extracted legal entities).

---

## 2. Imports and Dependencies

```python
# Linux / Streamlit Cloud SQLite3 compatibility patch for ChromaDB (Lines 7-12)
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st           # Web framework for rendering UI
import pandas as pd              # Data manipulation (if needed for tables)
import chromadb                  # Vector database client

from config import (             # Central configuration constants
    DEFAULT_TOP_K,
    GEMINI_API_KEY,
    DEFAULT_LLM_MODEL,
    DEFAULT_EMBEDDING_MODEL,
    CHROMA_PERSIST_DIR,
    get_chroma_collection_name,
)
from ingestion import ParentChildIngestor                      # Document ingestion facade
from retriever import HybridRRFRetriever                      # Hybrid retrieval facade
from agents import MultiAgentRouter                           # Multi-agent LLM router
from rag.pipeline import get_legal_rag_pipeline, PipelineResult # 16-stage Legal RAG pipeline
from rag.ui_formatter import format_legal_pipeline_result, FormattedLegalAnswer # Result formatter
from rag.pipeline_inspector import render_pipeline_inspector   # Diagnostic inspector
```

### Why are these libraries imported?
- **`pysqlite3`**: Streamlit Cloud and Ubuntu Linux ship with SQLite version 3.31, but ChromaDB requires SQLite $\ge 3.35.0$. The try-except block replaces Python's built-in `sqlite3` with `pysqlite3-binary` at runtime.
- **`streamlit`**: Provides reactive UI primitives (`st.set_page_config`, `st.sidebar`, `st.text_area`, `st.button`, `st.markdown`, `st.expander`).
- **`config` constants**: Provides persistent directories, default embedding model (`BAAI/bge-m3`), and default retrieval depth ($k=4$).
- **`rag.pipeline`**: Provides the master singleton `get_legal_rag_pipeline()` that coordinates all 16 stages of query understanding, hybrid retrieval, and grounded generation.
- **`rag.ui_formatter`**: Transforms raw dictionary results into strongly typed `FormattedLegalAnswer` objects.

---

## 3. Important Functions in `app.py`

### `load_rag_pipeline()`
- **Signature**: `@st.cache_resource(show_spinner=False) def load_rag_pipeline()`
- **Lines in Source**: [Lines 341–372](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/app.py#L341-L372)
- **What it does**: Initializes the vector database connection, checks whether ChromaDB is already populated, loads the parent store, builds the BM25 index, and initializes the `LegalRAGPipeline`.
- **Why it is needed**: Embedding models and vector stores take several seconds to load into memory. Using Streamlit's `@st.cache_resource` decorator guarantees that this initialization runs **only once** when the server starts, not every time a user types a character.
- **Return Value**: Tuple containing `(ingestor, retriever, router, stage4_pipeline)`.
- **Step-by-Step Execution**:
  1. Connects to `CHROMA_PERSIST_DIR` using `chromadb.PersistentClient`.
  2. Queries the target collection name (`indian_legal_rag_bgem3`).
  3. Checks `col.count() > 0`. If populated, loads `parent_store.json` and builds the fast BM25 index. If empty, runs `ingestor.run_pipeline()`.
  4. Instantiates `HybridRRFRetriever`, `MultiAgentRouter`, and `get_legal_rag_pipeline()`.
  5. Returns all initialized instances.

---

## 4. Actual Code Walkthrough

### Code Excerpt 1: Linux SQLite Compatibility Patch
```python
# Lines 7-12 in app.py
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass
```
- **Explanation**: Checks if `pysqlite3` is installed. If so, it removes standard `sqlite3` from Python's module registry and replaces it with `pysqlite3`. On Windows, this block safely catches `ImportError` and continues normally.
- **Why is this needed?**: Prevents runtime crash `RuntimeError: Your system has an unsupported version of sqlite3` when deployed to Linux environments or Streamlit Cloud.
- **What happens next**: Code proceeds to import `streamlit` and `chromadb`.

---

### Code Excerpt 2: Pipeline Execution Trigger
```python
# Lines 451-465 in app.py
if ask_clicked:
    query_str = user_input.strip()
    if query_str:
        with st.spinner("Analyzing constitutional provisions and case precedents..."):
            pipeline_result = stage4_pipeline.run(
                query_str,
                dynamic_api_key=user_api_key,
                override_top_k=top_k,
            )
            formatted_answer = format_legal_pipeline_result(pipeline_result)

            st.session_state.current_result = pipeline_result
            st.session_state.current_formatted = formatted_answer
            st.session_state.current_query = query_str
    else:
        st.warning("Please enter a legal question or constitutional query.")
```
- **Explanation**: When the user clicks `"Ask Assistant"`, the query string is trimmed. A loading spinner appears while `stage4_pipeline.run()` executes the full 16-stage pipeline. The resulting `PipelineResult` is passed to `format_legal_pipeline_result()` to prepare UI cards, and both are stored in `st.session_state`.
- **Why is this needed?**: Storing results in `st.session_state` prevents Streamlit's default behavior of resetting all variables upon subsequent page interactions (such as opening full text expanders).
- **What happens next**: The UI rendering block checks `if st.session_state.current_formatted:` and displays the response cards.

---

### Code Excerpt 3: Rendering the Verified Source Cards
```python
# Lines 553-605 in app.py
parents_recovered = raw_res.parent_context.get("parents", [])
if parents_recovered:
    for idx, p in enumerate(parents_recovered, start=1):
        doc_type = p.get("doc_type", "constitution")
        doc_id = p.get("document_id") or p.get("parent_id", f"source_{idx}")
        
        # Title and metadata formatting
        if doc_type == "constitution":
            art_num = p.get("article_number", "Article")
            title = p.get("title", "")
            card_title = f"📜 {art_num} — {title}"
            meta_desc = f"{p.get('part', '')} • {p.get('category', '')}"
        elif doc_type == "judgment":
            c_name = p.get("case_name", "Judgment")
            yr = p.get("year", "")
            cit = p.get("citation", "")
            card_title = f"⚖️ {c_name} ({yr})"
            meta_desc = f"Citation: {cit} • Bench: {p.get('bench', '')}"
        else:
            card_title = f"📑 {p.get('title', doc_id)}"
            meta_desc = "Statute / Code"
        
        # Render compact source card with verified citation badge
        st.markdown(
            f"""
            <div class="source-card">
                <div class="source-card-header">
                    <div>
                        <span class="source-title">{card_title}</span>
                        <span class="source-id-tag">{doc_id}</span>
                    </div>
                    <span class="badge-verified">✓ Verified Citation</span>
                </div>
                <div style="font-size: 0.8rem; color: #8b949e; margin-bottom: 0.3rem;">{meta_desc}</div>
                <div class="source-excerpt">"{excerpt}"</div>
            </div>
            """,
            unsafe_allow_html=True
        )
```
- **Explanation**: Iterates through each recovered parent document. Renders a card showing the formal legal title, statutory citation, document ID, a green `✓ Verified Citation` pill badge, and an excerpt from the winning child chunk.
- **Why is this needed?**: Proves to the user and examiner that the answer is completely traceable to official legal provisions.
- **What happens next**: Below each card, a Streamlit `st.expander` lets the user expand and read the complete primary constitutional article or Supreme Court judgment.

---

## 5. Practical Example

### User Input:
```text
"What is the procedure for presidential impeachment under Article 61?"
```

### Internal Processing in `app.py`:
1. `app.py` passes the string to `stage4_pipeline.run()`.
2. Pipeline identifies `CONSTITUTIONAL_PROCEDURE` intent and retrieves `parent_const_art_061`.
3. `format_legal_pipeline_result()` extracts the Direct Answer and provisions.

### Rendered Output on Screen:
- **Direct Answer Card**: Explains the 14-day notice, two-thirds majority requirement of the originating House, and the investigating House's proceedings.
- **Relevant Legal Provisions**: Card for `Article 61: Procedure for impeachment of the President`.
- **Verified Sources**: Card with `[Doc: parent_const_art_061]`, `✓ Verified Citation`, and expandable full text of Article 61.
- **Technical Details Expander**: Displays Strategy: `PROCEDURE_SEARCH`, Intent: `CONSTITUTIONAL_PROCEDURE`, Confidence: `0.92 HIGH`, Citations: `1 Validated`.

---

## 6. Connection to Other Files

```mermaid
flowchart TD
    APP["app.py"]
    CONFIG["config.py"]
    PIPE["rag/pipeline.py"]
    UIF["rag/ui_formatter.py"]
    PSTORE["parent_store.json"]
    CDB["chroma_db/"]

    APP -->|Reads paths & defaults| CONFIG
    APP -->|Executes query via run()| PIPE
    APP -->|Formats result into cards| UIF
    APP -->|Checks collection count| CDB
    APP -->|Reads documents| PSTORE
```

- **Imports from**:
  - [`config.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/config.py): Hyperparameters and collection paths.
  - [`rag/pipeline.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/rag/pipeline.py): `get_legal_rag_pipeline()` singleton.
  - [`rag/ui_formatter.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/rag/ui_formatter.py): `format_legal_pipeline_result()`.
- **Invoked by**: The user running `streamlit run app.py` from PowerShell or terminal.
- **Proceed to**: [**`agents_py.md`**](agents_py.md) to learn how specialized LLM agents and heuristic prompt templates work.

