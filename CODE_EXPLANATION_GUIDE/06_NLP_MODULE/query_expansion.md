# Code Explanation: `nlp/query_expansion.py` 📈

> **Source File**: [`nlp/query_expansion.py`](../../nlp/query_expansion.py)  
> **Lines of Code**: 130 lines  
> **Primary Responsibility**: Controlled legal query expansion mapping conversational citizen phrasing to formal constitutional terms using a verified synonym graph.

---

## 1. Basic Introduction

### What is this file?
[`nlp/query_expansion.py`](../../nlp/query_expansion.py) bridges the colloquial language of non-lawyers with the formal statutory phrasing of the Indian Constitution and Central Acts.

### Why does this file exist?
Unconstrained query expansion (such as generating 10 synonyms using an unconstrained LLM or WordNet) frequently causes **Query Drift**. For example, expanding *"arrest"* to *"detention"*, *"custody"*, *"hostage"*, *"imprisonment"*, *"jail"* introduces irrelevant terms that pull the search engine toward unrelated statutes.

[`nlp/query_expansion.py`](../../nlp/query_expansion.py) implements **controlled, deterministic query expansion**:
- Uses an authoritative, domain-curated legal synonym graph (`nlp/legal_synonyms.json`).
- Enforces a strict ceiling of **`max_terms = 3`**.
- Matches whole-word boundaries only.
- Never appends a term if the query already contains it.

---

## 2. Structure of `legal_synonyms.json`

The expander loads `nlp/legal_synonyms.json`, which maps conversational triggers to statutory concepts:
```json
{
  "search without warrant": [
    "Section 165 CrPC",
    "procedure established by law",
    "inviolability of home"
  ],
  "phone tapping": [
    "Right to Privacy",
    "Article 21",
    "Section 5(2) Telegraph Act"
  ],
  "free speech": [
    "Article 19(1)(a)",
    "reasonable restrictions",
    "Article 19(2)"
  ],
  "death penalty": [
    "Article 21",
    "rarest of rare cases",
    "Bachan Singh v. State of Punjab"
  ],
  "reservation": [
    "Article 15(4)",
    "Article 16(4)",
    "Indra Sawhney"
  ]
}
```

---

## 3. Important Methods in `QueryExpander`

### 1. `_load_synonym_graph()` (Lines 27–35)
- Reads `SYNONYM_GRAPH_PATH` (`nlp/legal_synonyms.json`).
- Populates `self.synonym_graph` dictionary.

### 2. `expand(query: str, max_terms: int = 3, enabled: bool = True) -> Dict[str, Any]` (Lines 36–119)
- **Execution Algorithm**:
  1. Normalizes the query via `normalize_legal_text()`.
  2. Sorts trigger phrases by character length descending so multi-word concepts (e.g. `"search without warrant"`) are evaluated before single words (`"search"`).
  3. Checks regex boundary `\b<trigger>\b` against the lowercased query.
  4. If matched, inspects candidate expansion terms:
     - Rejects any term already present in the user query.
     - Rejects duplicate expansion terms.
     - Appends valid terms until `max_terms` (default 3) is reached.
  5. If terms were added, constructs composite expanded query:  
     `"<Normalized Query> <Term 1> <Term 2> <Term 3>"`
- **Return Value**:
  ```python
  {
      "original_query": str,
      "expanded_query": str,
      "expanded_terms": List[str],
      "expansion_sources": Dict[str, str],
      "was_expanded": bool
  }
  ```

---

## 4. Actual Code Walkthrough

### Code Excerpt: Expansion Loop with Drift Prevention
```python
# Lines 76-100 in nlp/query_expansion.py
# Iterate over synonym triggers (longest trigger phrases first)
sorted_triggers = sorted(self.synonym_graph.keys(), key=len, reverse=True)

for trigger in sorted_triggers:
    if len(expanded_terms) >= max_terms:
        break
        
    # Match whole-word boundary
    pattern = r"\b" + re.escape(trigger.lower()) + r"\b"
    if re.search(pattern, q_lower):
        target_terms = self.synonym_graph[trigger]
        for term in target_terms:
            term_clean = term.strip()
            term_lower = term_clean.lower()
            
            # Avoid adding term if already present in original query or already selected
            if term_lower in q_lower or term_lower in seen_terms:
                continue
                
            expanded_terms.append(term_clean)
            seen_terms.add(term_lower)
            expansion_sources[term_clean] = f"Triggered by concept '{trigger}'"
            
            if len(expanded_terms) >= max_terms:
                break
```
- **Explanation**: Loops through triggers, matches word boundaries, skips terms already present in the question, and caps additions at exactly 3 terms.
- **Why is this needed?**: Protects the BM25 and vector search engines from topic dilution.

---

## 5. Practical Example

### Input Query:
```text
"Can government tap my phone calls?"
```

### Processing:
- Detects trigger phrase `"tap my phone"` / `"phone tapping"`.
- Candidate terms from graph: `["Right to Privacy", "Article 21", "Section 5(2) Telegraph Act"]`.
- Appends terms up to ceiling 3.

### Output:
```python
{
    "original_query": "Can government tap my phone calls?",
    "expanded_query": "can government tap my phone calls? Right to Privacy Article 21 Section 5(2) Telegraph Act",
    "expanded_terms": [
        "Right to Privacy",
        "Article 21",
        "Section 5(2) Telegraph Act"
    ],
    "expansion_sources": {
        "Right to Privacy": "Triggered by concept 'phone tapping'",
        "Article 21": "Triggered by concept 'phone tapping'",
        "Section 5(2) Telegraph Act": "Triggered by concept 'phone tapping'"
    },
    "was_expanded": True
}
```

---

## 6. Connection to Other Files

- **Called by**: [`rag/pipeline.py`](../../rag/pipeline.py) (Stage 6 query expansion).
- **Feeds into**: [`routing/query_router.py`](../../routing/query_router.py) and [`retrieval/hybrid_retriever.py`](../../retrieval/hybrid_retriever.py) as the primary search query.
- **Proceed to**: [**`language_detection.md`**](language_detection.md) to inspect how incoming language scripts and Hinglish tokens are identified.

