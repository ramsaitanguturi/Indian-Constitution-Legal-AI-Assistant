# Code Explanation: `nlp/preprocessing.py` 🧹

> **Source File**: [`nlp/preprocessing.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/preprocessing.py)  
> **Lines of Code**: 183 lines  
> **Primary Responsibility**: Unicode normalization, typographic quote standardization, statutory abbreviation expansion, structure-preserving query tokenization, and legal stopword filtering.

---

## 1. Basic Introduction

### What is this file?
[`nlp/preprocessing.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/preprocessing.py) provides the foundational text cleaning and tokenization utilities for the entire legal assistant. It prepares both incoming user queries and statutory legal corpus passages before they are passed to Named Entity Recognition, Intent Classification, or Information Retrieval.

### Why does this file exist?
Legal text downloaded from government repositories (such as the Supreme Court of India SCR PDFs or India Code) is filled with formatting inconsistencies:
1. **Typographic / Curly Quotes**: Characters like `“` (`\u201c`), `”` (`\u201d`), `‘` (`\u2018`), and non-breaking spaces (`\u00a0`) cause standard string comparisons and regex to fail.
2. **Dense Legal Acronyms**: Law reports and legal practitioners frequently use abbreviations: `Art. 21`, `Sec. 124A`, `u/a 21`, `r/w`, `CJI`, `SC`, `UOI`. A dense vector model or BM25 index might miss the connection between `Art.` and `Article`.
3. **Compound Legal Identifiers**: Standard English tokenizers split `Article 19(1)(a)` into separate tokens `['Article', '19', '1', 'a']`, destroying the compound statutory citation.

[`nlp/preprocessing.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/preprocessing.py) solves all these issues cleanly and deterministically.

---

## 2. Imports and Dependencies

```python
import re                 # Regular expression pattern matching and substitution
import unicodedata        # Unicode character database and NFKC normalization
from typing import List, Dict, Tuple, Optional # Type hints
```

- **`unicodedata`**: Provides `unicodedata.normalize("NFKC", text)` which performs Compatibility Decomposition followed by Canonical Composition, converting combined characters and ligatures into standard equivalents.
- **`re`**: Used for compiled regex replacement of legal acronyms and compound token parsing.

---

## 3. Important Constants & Mapping Dictionaries

### `LEGAL_ABBREVIATIONS` (Lines 13–49)
A curated dictionary mapping common Indian legal abbreviations to their full canonical terms:
- **Judicial & Institutional**:
  - `\bS\.?C\.?I\.?\b` $\to$ `"Supreme Court of India"`
  - `\bS\.?C\.?\b` $\to$ `"Supreme Court"`
  - `\bH\.?C\.?\b` $\to$ `"High Court"`
  - `\bC\.?J\.?I\.?\b` $\to$ `"Chief Justice of India"`
  - `\bU\.?O\.?I\.?\b` $\to$ `"Union of India"`
  - `\bG\.?O\.?I\.?\b` $\to$ `"Government of India"`
  - `\bC\.?O\.?I\.?\b` $\to$ `"Constitution of India"`
- **Constitutional & Statutory**:
  - `\bArts?\.(?!\w)` and `\bArts?\b` $\to$ `"Article"`
  - `\bSecs?\.(?!\w)` and `\bSecs?\b` $\to$ `"Section"`
  - `\bCls?\.(?!\w)` and `\bCls?\b` $\to$ `"Clause"`
  - `\bu/a\b` or `\bU/A\b` $\to$ `"under Article"`
  - `\bu/s\b` or `\bU/S\b` $\to$ `"under Section"`
  - `\br/w\b` or `\bR/W\b` $\to$ `"read with"`
- **Pre-compilation (`_COMPILED_ABBREVIATIONS`)** (Lines 52–55): Pre-compiles all patterns with `re.IGNORECASE` at import time, ensuring that runtime execution takes microseconds.

---

## 4. Functions in `nlp/preprocessing.py`

### 1. `clean_unicode_and_quotes(text: str) -> str`
- **Lines in Source**: [Lines 58–88](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/preprocessing.py#L58-L88)
- **What it does**:
  1. Runs `unicodedata.normalize("NFKC", text)`.
  2. Iterates through a character map replacing curved single/double quotes (`\u2018`, `\u2019`, `\u201c`, `\u201d`), en-dashes (`\u2013`), em-dashes (`\u2014`), horizontal ellipses (`\u2026`), non-breaking spaces (`\u00a0`), zero-width spaces (`\u200b`), and Byte Order Marks (`\ufeff`) with standard ASCII equivalents.
- **Return**: Cleaned ASCII-compatible string.

---

### 2. `expand_legal_abbreviations(text: str) -> str`
- **Lines in Source**: [Lines 90–103](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/preprocessing.py#L90-L103)
- **What it does**: Iterates through `_COMPILED_ABBREVIATIONS` and replaces acronyms with their expanded forms. For example: `"Art. 21 u/a COI"` becomes `"Article 21 under Article Constitution of India"`.
- **Return**: String with standard statutory terms.

---

### 3. `normalize_legal_text(text: str, expand_abbreviations: bool = True, lowercase: bool = False) -> str`
- **Lines in Source**: [Lines 105–141](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/preprocessing.py#L105-L141)
- **What it does**: The master normalization pipeline:
  1. Calls `clean_unicode_and_quotes()`.
  2. Calls `expand_legal_abbreviations()` if `expand_abbreviations=True`.
  3. Collapses multiple whitespace characters (`re.sub(r"[ \t]+", " ", cleaned)`).
  4. Collapses excessive newlines.
  5. Optionally converts text to lowercase if `lowercase=True`.
- **Return**: Normalized string ready for NER, intent classification, and search.

---

### 4. `tokenize_query(text: str) -> List[str]`
- **Lines in Source**: [Lines 143–157](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/preprocessing.py#L143-L157)
- **What it does**: Uses regex `r"\b\w+(?:\([^)]+\))+|\b\w+\b|[^\w\s]"` to split text while keeping compound statutory clause citations intact (e.g. `Article 19(1)(a)` remains a single unit `19(1)(a)` rather than splitting into 4 pieces).
- **Return**: List of token strings.

---

### 5. `extract_keywords(text: str, stop_words: Optional[set] = None) -> List[str]`
- **Lines in Source**: [Lines 159–183](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/preprocessing.py#L159-L183)
- **What it does**: Filters out common English grammatical stopwords (`the`, `is`, `which`, `above`) while explicitly retaining substantive legal terms (`privacy`, `bail`, `warrant`, `equality`).
- **Return**: List of lowercase alphanumeric keywords of length $> 1$.

---

## 5. Actual Code Walkthrough

### Code Excerpt: Unicode Cleaning & Character Map
```python
# Lines 67-87 in nlp/preprocessing.py
# NFKC normalizes compatibility characters
text = unicodedata.normalize("NFKC", text)

# Map curved quotes, apostrophes, dashes, bullets
charmap = {
    "\u2018": "'",  # Left single quotation mark
    "\u2019": "'",  # Right single quotation mark
    "\u201a": "'",  # Single low-9 quotation mark
    "\u201c": '"',  # Left double quotation mark
    "\u201d": '"',  # Right double quotation mark
    "\u201e": '"',  # Double low-9 quotation mark
    "\u2013": "-",  # En dash
    "\u2014": "-",  # Em dash
    "\u2026": "...",  # Horizontal ellipsis
    "\u00a0": " ",  # Non-breaking space
    "\u200b": "",   # Zero-width space
    "\ufeff": "",   # Byte order mark
}
for orig, repl in charmap.items():
    text = text.replace(orig, repl)
```
- **Explanation**: Standardizes varied typographic representations into plain ASCII characters.
- **Why is this needed?**: PDF text extraction often inserts invisible zero-width spaces or non-breaking spaces that break word boundary regex `\b`.
- **What happens next**: Cleaned string is passed to abbreviation expansion.

---

## 6. Practical Example

### Raw User Query:
```text
"“Can cops search without warrant u/a Art. 21 r/w Sec. 165 CrPC?”"
```

### Step 1: `clean_unicode_and_quotes`:
- Replaces curved quotes `“` and `”` with `"`.
- Text: `"\"Can cops search without warrant u/a Art. 21 r/w Sec. 165 CrPC?\""`

### Step 2: `expand_legal_abbreviations`:
- `u/a` $\to$ `under Article`
- `Art.` $\to$ `Article`
- `r/w` $\to$ `read with`
- `Sec.` $\to$ `Section`
- `CrPC` $\to$ `Code of Criminal Procedure`

### Final Normalized Output:
```text
"Can cops search without warrant under Article Article 21 read with Section 165 Code of Criminal Procedure?"
```

---

## 7. Connection to Other Files

- **Called by**:
  - [`rag/pipeline.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/rag/pipeline.py) (Stage 2 preprocessing)
  - [`nlp/intent_classifier.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/intent_classifier.py)
  - [`nlp/query_expansion.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/query_expansion.py)
  - [`routing/query_router.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/routing/query_router.py)
- **Proceed to**: [**`intent_classification.md`**](intent_classification.md) to inspect how intent classification is handled.

