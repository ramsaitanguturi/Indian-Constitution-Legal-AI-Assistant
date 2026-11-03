# Code Explanation: `nlp/legal_ner.py` 🏷️

> **Source File**: [`nlp/legal_ner.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/legal_ner.py)  
> **Lines of Code**: 446 lines  
> **Primary Responsibility**: Domain-specific Legal Named Entity Recognition (NER) extracting 10 entity categories using high-precision regex patterns, dynamic corpus gazetteers, and span collision resolution.

---

## 1. Basic Introduction

### What is this file?
[`nlp/legal_ner.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/legal_ner.py) is the domain-specific information extraction engine for the assistant. Standard off-the-shelf NER libraries (like spaCy's `en_core_web_sm`) are trained on generic news corpora and fail catastrophically on Indian legal texts:
- Generic models label `"Article 21"` as a `PRODUCT` or `LAW`.
- Generic models label `"Kesavananda Bharati"` as a generic `PERSON` rather than a landmark `CASE`.
- Generic models completely ignore Indian statutory structures like clauses, amendments, and legal concepts.

[`nlp/legal_ner.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/legal_ner.py) extracts **10 specialized legal entity classes** with exact character offsets (`start`, `end`) and normalized values, achieving a **Macro-F1 of 0.8496**.

---

## 2. The 10 Legal Entity Classes

| Entity Category | What It Detects | Example Surface Forms |
|---|---|---|
| `ARTICLE` | Constitutional articles, clauses, and Preamble. | `Article 21`, `Art. 19(1)(a)`, `Preamble`, `Article 32 to 35` |
| `SECTION` | Statutory sections from Central Acts. | `Section 165`, `Section 124A`, `Sec. 66A`, `Section 377` |
| `AMENDMENT` | Constitutional Amendment Acts. | `42nd Amendment`, `First Amendment Act`, `103rd Constitutional Amendment` |
| `CASE` | Landmark Supreme Court decisions and precedents. | `Kesavananda Bharati`, `Puttaswamy`, `Maneka Gandhi v. Union of India` |
| `PERSON` | Justices, historical drafters, and constitutional figures. | `Dr. B. R. Ambedkar`, `Justice D.Y. Chandrachud`, `Nani Palkhivala` |
| `COURT` | Judicial institutions and forums. | `Supreme Court of India`, `Delhi High Court`, `Constituent Assembly` |
| `RIGHT` | Specific fundamental and legal rights. | `right to privacy`, `freedom of speech`, `right to personal liberty` |
| `LEGAL_CONCEPT`| Legal doctrines, tests, and Latin maxims. | `basic structure`, `due process of law`, `habeas corpus`, `proportionality` |
| `ACT` | Central legislation and statutory codes. | `Code of Criminal Procedure`, `Indian Penal Code`, `Aadhaar Act` |
| `DATE` | Specific dates, years, and enactment years. | `26 January 1950`, `1973`, `24 August 2017` |

---

## 3. Class Structure: `LegalNER`

### Constructor: `__init__()` (Lines 129–142)
1. Initializes default curated lists for courts, persons, rights, concepts, acts, and cases.
2. Calls `self._load_corpus_gazetteers()`: Inspects `data/judgments/supreme_court_landmarks.json` and `data/constitution/amendments.json` to automatically absorb case names, acts, and keywords directly from the active legal database.
3. Calls `self._sort_gazetteers()`: Sorts all gazetteer phrases by character length descending so that multi-word entities (like *"Kesavananda Bharati v. State of Kerala"*) are matched before substrings (*"Kesavananda"*).

---

## 4. Key Methods in `LegalNER`

### 1. `extract_spans(text: str) -> List[Dict[str, Any]]` (Lines 207–389)
- **The Core Extraction Algorithm**:
  - **Step 1: Formal Regex Scanning**:
    - `ARTICLE_PATTERN`: Matches `Article 21`, `Art. 19(1)(a)`, `Preamble`.
    - `SECTION_PATTERN`: Matches `Section 165`, `Sec. 124A`.
    - `AMENDMENT_PATTERN`: Matches `42nd Amendment Act`.
    - `DATE_PATTERN`: Matches dates and landmark years.
    - `PERSON_TITLE_PATTERN`: High-priority regex matching judicial titles (`Justice D.Y. Chandrachud`, `Dr. B. R. Ambedkar`).
  - **Step 2: Gazetteer Matching**:
    - Scans text for registered cases, courts, rights, concepts, and acts using word-boundary matching `\b`.
    - Contextual disambiguation for *"Maneka Gandhi"*: checks preceding words (`"in"`) and succeeding words (`"v."`, `"vs."`, `"case"`) to distinguish between the **person** and the **case law**.
  - **Step 3: Span Collision Resolution (Non-Overlapping Spans)**:
    - Multiple patterns may match overlapping character ranges (e.g., *"Justice K.S. Puttaswamy v. Union of India"* contains a `PERSON`, a `CASE`, and `"Union of India"`).
    - Assigns priority weights: `ARTICLE` (10), `SECTION` (9), `AMENDMENT` (8), `PERSON with Title` (7.5), `CASE` (7), `RIGHT` (6), `ACT` (5), `PERSON` (4), `COURT` (3), `LEGAL_CONCEPT` (2), `DATE` (1).
    - Sorts candidate spans by:
      1. Longest span first (`-(end - start)`)
      2. Highest priority score (`-priority`)
      3. Start position (`start`)
    - Accepts non-overlapping spans and filters out collided substrings.
- **Return**: Ordered list of non-overlapping span dictionaries.

---

### 2. `extract_entities(text: str) -> Dict[str, List[str]]` (Lines 390–413)
- Calls `extract_spans(text)` and groups normalized values into a dictionary of the 10 target categories.
- Deduplicates values within each category.

---

### 3. `extract_legacy_entities(text: str) -> Dict[str, List[str]]` (Lines 415–435)
- Backward-compatible wrapper returning the 3-key dictionary expected by legacy tests: `{"articles": [...], "cases": [...], "concepts": [...]}`.

---

## 5. Actual Code Walkthrough

### Code Excerpt: Span Collision Resolution
```python
# Lines 363-385 in nlp/legal_ner.py
# Sort candidates so superior matches are accepted first
raw_candidates.sort(
    key=lambda c: (
        -(c["end"] - c["start"]),  # Longest span first
        -get_priority(c),          # Highest priority
        c["start"]
    )
)

selected_spans: List[Dict[str, Any]] = []
occupied_ranges: List[Tuple[int, int]] = []

for cand in raw_candidates:
    c_start, c_end = cand["start"], cand["end"]
    # Check overlap with already chosen spans
    overlap = False
    for o_start, o_end in occupied_ranges:
        if not (c_end <= o_start or c_start >= o_end):
            overlap = True
            break
    if not overlap:
        selected_spans.append(cand)
        occupied_ranges.append((c_start, c_end))
```
- **Explanation**: Guarantees that if a phrase matches both a broad legal concept and an exact landmark case, the longest, highest-priority legal entity is preserved without overlapping tokens.

---

## 6. Practical Example

### Query:
`"In Puttaswamy, did the Supreme Court hold right to privacy under Article 21 to be part of basic structure?"`

### Extracted Entities:
```python
{
    "ARTICLE": ["Article 21"],
    "CASE": ["Puttaswamy"],
    "COURT": ["Supreme Court"],
    "RIGHT": ["right to privacy"],
    "LEGAL_CONCEPT": ["basic structure"],
    "SECTION": [], "PERSON": [], "AMENDMENT": [], "ACT": [], "DATE": []
}
```

---

## 7. Connection to Other Files

- **Called by**:
  - [`rag/pipeline.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/rag/pipeline.py) (Stage 3 NER extraction)
  - [`nlp/entity_linking.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/entity_linking.py) (feeds extracted entities to linker)
  - [`retrieval/entity_boost.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/entity_boost.py) (applies $+0.15$ ranking boost)
- **Proceed to**: [**`entity_linking.md`**](entity_linking.md) to inspect how surface entity mentions are linked to canonical statutory document IDs.

