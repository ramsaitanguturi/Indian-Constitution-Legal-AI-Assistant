# Code Explanation: `agents.py` 🤖

> **Source File**: [`agents.py`](../../agents.py)  
> **Lines of Code**: 331 lines  
> **Primary Responsibility**: Multi-agent prompt engineering, specialized legal personas (Article Agent, Case-Law Agent, Explanation Agent), and heuristic offline synthesis.

---

## 1. Basic Introduction

### What is this file?
[`agents.py`](../../agents.py) defines the **Multi-Agent Router and LLM Engine** for the legal assistant. It equips the system with specialized prompt templates tailored for distinct legal research tasks and integrates with Google Gemini (`ChatGoogleGenerativeAI`).

### Why does this file exist?
Legal inquiries have distinct requirements depending on their nature:
1. A question about an Article requires exact constitutional text, clause numbering, and amendment history.
2. A question about a judgment requires bench compositions, case facts, the Ratio Decidendi (principle of law), and final verdicts.
3. A question from an ordinary citizen requires simplifying dense legal jargon into plain language with everyday examples (and brief Hindi translations).

Rather than using one generic, one-size-fits-all prompt, [`agents.py`](../../agents.py) defines three specialized personas and provides an **offline heuristic legal synthesizer** that generates structured answers even when no internet or API keys are present.

### Where does it fit in the project?
It serves as the LLM orchestration layer for legacy callers and provides specialized persona prompts. In the modern 16-stage pipeline, its concepts are bridged with [`rag/generator.py`](../../rag/generator.py) to guarantee zero hallucination.

---

## 2. Imports and Dependencies

```python
import os
import sys

# Ensure UTF-8 output encoding for Windows command line environment (Lines 14-15)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from typing import Dict, List, Any, Optional
from langchain_core.prompts import ChatPromptTemplate       # Prompt engineering
from langchain_core.output_parsers import StrOutputParser   # Parses LLM output to clean string

from config import GEMINI_API_KEY, DEFAULT_LLM_MODEL        # API keys and model names
```

### Why are these libraries imported?
- **`sys.stdout.reconfigure(encoding="utf-8")`**: On Windows PowerShell, printing Unicode characters (such as Hindi text or emoji symbols `⚖️`, `📜`) can crash with `UnicodeEncodeError`. This line forces Python to output standard UTF-8.
- **`langchain_core.prompts.ChatPromptTemplate`**: Allows structuring zero-shot system prompts with strict grounding constraints.
- **`langchain_core.output_parsers.StrOutputParser`**: Extracts raw string text from Gemini's message objects.

---

## 3. Specialized Prompt Templates

[`agents.py`](../../agents.py) defines three distinct system prompt templates (Lines 25–76):

### 1. `ARTICLE_AGENT_PROMPT` (Lines 25–40)
- **Role**: Expert Constitutional Law Specialist.
- **Constraints**:
  - Base answer **exclusively** on the provided constitutional context.
  - Zero hallucination: Never invent or extrapolate outside the context.
  - Always cite exact Article numbers, Parts, and Titles.
  - Explain legal scope and historical context.

### 2. `CASE_LAW_AGENT_PROMPT` (Lines 43–59)
- **Role**: Supreme Court Legal Precedents Specialist.
- **Constraints**:
  - Base response exclusively on the judgments context provided.
  - Clearly highlight: Case Name, Citation, Bench details, Facts, Ratio Decidendi, and Final Verdict.
  - If comparing cases, structure comparisons clearly under distinct headings.

### 3. `EXPLANATION_AGENT_PROMPT` (Lines 61–76)
- **Role**: Plain-Language Legal Educator for citizens and law students.
- **Constraints**:
  - Demystify complex legal jargon into simple, clear, engaging plain English.
  - Structure into `"What it means"`, `"Why it matters"`, and `"Key Takeaway"`.
  - Include a brief Hindi translation summary (*संक्षिप्त सारांश*).

---

## 4. Classes in `agents.py`

### Class 1: `HeuristicLegalSynthesizer`
- **Lines in Source**: [Lines 79–182](../../agents.py#L79-L182)
- **Purpose**: A deterministic fallback legal synthesis engine. When the Google Gemini API key is missing or offline, this class formats a complete, structured legal answer directly from the retrieved parent/child context without invoking any neural network.
- **Real-World Analogy**: Think of it as an emergency rulebook. If the expert professor is unavailable, you read the official statute book directly and compile the answer following a rigid template.

#### Methods:
- **`synthesize(agent_type, query, context_docs, entities)`** (Static Method):
  - **Inputs**: `agent_type` (str), `query` (str), `context_docs` (list of retrieved dictionaries), `entities` (extracted legal entities).
  - **Processing**:
    - If `agent_type == "article_agent"`: Formats Article number, Title, Part, Category, Exact Provision quote, Legal Scope, and Amendments.
    - If `agent_type == "case_law_agent"`: Formats Case Name, Year, Citation, Judicial Bench, Facts, Ratio Decidendi, Verdict, and Key Takeaways.
    - If `agent_type == "explanation_agent"`: Formats `"What You Need to Know"`, `"Key Takeaways"`, and Hindi summary.
  - **Return**: Formatted markdown string.

---

### Class 2: `MultiAgentRouter`
- **Lines in Source**: [Lines 185–307](../../agents.py#L185-L307)
- **Purpose**: Classifies queries into the appropriate agent persona and executes either the LangChain Gemini chain or the `HeuristicLegalSynthesizer` fallback.

#### Constructor: `__init__(api_key=None, model=None)` (Lines 195–203)
- Sets `self.api_key` from argument, `.env`, or `config.py`.
- Sets `self.model` (defaults to `gemini-3.8-flash`).
- Calls `self._init_llm()` if an API key is available.

#### Important Methods:

##### `_init_llm(api_key=None)` (Lines 204–222)
- Lazily instantiates `ChatGoogleGenerativeAI` with `temperature=0.1`, `timeout=5.0`, and `max_retries=1`.
- If initialization fails (e.g. invalid key or no internet), prints a warning and sets `self.llm_available = False`.

##### `update_api_key(new_key)` (Lines 223–227)
- Updates the API key at runtime if the user enters a key in the Streamlit sidebar.

##### `classify_query(query, entities, override_mode="Auto-route")` (Lines 228–251)
- **Inputs**: `query` (str), `entities` (dict), `override_mode` (str).
- **Logic**:
  - If `override_mode != "Auto-route"`, uses manual selection.
  - If `entities` contains case names or query contains keywords like `"v."`, `"versus"`, `"judgment"`, `"ratio"`, returns `"case_law_agent"`.
  - If query contains keywords like `"explain"`, `"simple"`, `"meaning"`, `"citizen"`, returns `"explanation_agent"`.
  - If `entities` contains article numbers or keywords like `"article"`, `"amendment"`, returns `"article_agent"`.
  - Default fallback: `"explanation_agent"`.
- **Return**: String identifier of the chosen agent.

##### `execute_agent(agent_type, query, context_docs, entities, dynamic_api_key=None)` (Lines 253–307)
- **Inputs**: Agent persona, user query, retrieved context documents, entities, and optional runtime API key.
- **Logic**:
  - Updates API key dynamically if a new key was passed from UI.
  - Concatenates retrieved parent document texts into a single `combined_context` string.
  - If `self.llm_available` is True, invokes the prompt template with Gemini via LangChain:
    ```python
    chain = prompt | self.llm | StrOutputParser()
    response_text = chain.invoke({"context": combined_context, "query": query})
    ```
  - If Gemini raises an exception or is unavailable, falls back to `HeuristicLegalSynthesizer.synthesize()`.
- **Return**: Dictionary containing `agent_type`, `agent_name`, `response`, `query`, `entities`, `source_docs`, `used_llm`, and `model_name`.

---

## 5. Actual Code Walkthrough

### Code Excerpt 1: MultiAgentRouter Query Classification
```python
# Lines 238-251 in agents.py
query_lower = query.lower()

# Heuristic rules based on entities and keywords
if entities.get("cases") or any(k in query_lower for k in ["v.", "versus", "case", "judgment", "verdict", "ratio", "bench", "precedent", "court"]):
    return "case_law_agent"

if any(k in query_lower for k in ["explain", "simple", "meaning", "plain english", "citizen", "what does", "in easy words", "hindi"]):
    return "explanation_agent"

if entities.get("articles") or any(k in query_lower for k in ["article", "clause", "part", "preamble", "amendment", "schedule", "constitution"]):
    return "article_agent"

# Default fallback
return "explanation_agent"
```
- **Explanation**: Inspects extracted named entities and keywords in the query to select the specialized agent persona.
- **Why is this needed?**: Ensures that questions about Supreme Court cases receive judicial bench analysis, while general conceptual questions receive citizen-friendly summaries.

---

### Code Excerpt 2: Heuristic Fallback Synthesis
```python
# Lines 126-136 in agents.py
for idx, doc in enumerate(context_docs, start=1):
    pdata = doc.get("parent_data", {})
    if pdata.get("doc_type") == "judgment":
        output_lines.append(f"#### {idx}. {pdata.get('case_name', 'Landmark Case')} ({pdata.get('year', '')})")
        output_lines.append(f"- **Citation**: `{pdata.get('citation', 'N/A')}`")
        output_lines.append(f"- **Judicial Bench**: {pdata.get('bench', 'N/A')}")
        output_lines.append(f"- **Articles Referred**: {', '.join(pdata.get('articles_referred', []))}")
        output_lines.append(f"\n**Facts of the Case**:\n{pdata.get('facts', '')}\n")
        output_lines.append(f"**Ratio Decidendi (Principle of Law)**:\n{pdata.get('ratio_decidendi', '')}\n")
        output_lines.append(f"**Final Verdict**:\n{pdata.get('verdict', '')}\n")
```
- **Explanation**: Extracts structured metadata from the parent judgment object and formats it into clean, verifiable markdown sections.
- **Why is this needed?**: Guarantees that even if offline without an LLM, the user receives an authoritative legal breakdown directly from the database.

---

## 6. Practical Example

### Query:
`"Explain Puttaswamy case on privacy"`

### Processing:
1. `classify_query()` matches `"Puttaswamy"` in `entities["cases"]` $\to$ selects `"case_law_agent"`.
2. Formats `CASE_LAW_AGENT_PROMPT` with the retrieved 9-judge bench holding.
3. Executes Gemini LLM (or `HeuristicLegalSynthesizer`).

### Output Response:
```markdown
### ⚖️ Supreme Court Case-Law & Precedents Analysis

**Landmark Precedents Identified**: Justice K.S. Puttaswamy v. Union of India

#### 1. Justice K.S. Puttaswamy (Retd.) v. Union of India (2017)
- **Citation**: `(2017) 10 SCC 1`
- **Judicial Bench**: 9-Judge Constitutional Bench
- **Articles Referred**: Article 21, Article 14, Article 19

**Facts of the Case**:
A constitutional challenge brought by retired Justice Puttaswamy challenging the government's Aadhaar biometric scheme...

**Ratio Decidendi (Principle of Law)**:
The right to privacy is a fundamental right and an intrinsic part of the right to life and personal liberty under Article 21...

**Final Verdict**:
Unanimously affirmed privacy as a fundamental constitutional right.
```

---

## 7. Connection to Other Files

- **Imported by**: [`app.py`](../../app.py) (instantiated in `load_rag_pipeline()`).
- **Imports from**: [`config.py`](../../config.py) for `GEMINI_API_KEY` and `DEFAULT_LLM_MODEL`.
- **Related to**: [`rag/generator.py`](../../rag/generator.py), which implements modern 16-stage grounded generation.
- **Proceed to**: [**`config_py.md`**](config_py.md) to inspect the project's centralized paths, constants, and dimension validation.

