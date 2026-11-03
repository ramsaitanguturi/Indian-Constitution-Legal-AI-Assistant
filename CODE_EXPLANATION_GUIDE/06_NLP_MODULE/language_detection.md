# Code Explanation: `nlp/language_detection.py` 🌐

> **Source File**: [`nlp/language_detection.py`](../../nlp/language_detection.py)  
> **Lines of Code**: 144 lines  
> **Primary Responsibility**: Script identification, Unicode character block analysis, English grammatical pattern matching, and transliterated Hinglish detection.

---

## 1. Basic Introduction

### What is this file?
[`nlp/language_detection.py`](../../nlp/language_detection.py) is the entry-gate linguistic classifier for the assistant. It analyzes incoming queries to determine whether they are written in:
1. **English** (`en`)
2. **Hindi / Devanagari** (`hi`)
3. **Transliterated Hinglish** (`hinglish`)
4. **Other Indic Scripts** (`bengali`, `tamil`, `telugu`)
5. **Unknown / Unintelligible** (`unknown`)

### Why does this file exist?
In India, legal queries are frequently typed in Romanized Hindi (*"kya police bina warrant ke ghar search kar sakti hai?"*) or Devanagari Hindi (*"क्या पुलिस बिना वारंट के घर की तलाशी ले सकती है?"*). If an unsupported language (or random non-alphabetic gibberish) is fed to the embedding models, it leads to low-relevance results.

[`nlp/language_detection.py`](../../nlp/language_detection.py) provides deterministic language identification without requiring heavy, slow third-party dependencies (like `langdetect` or `fasttext`).

---

## 2. Key Constants & Word Sets

### 1. `ENGLISH_INDICATORS` (Lines 13–19)
A set of 34 high-frequency English grammatical and legal tokens:
```python
{
    "the", "is", "what", "which", "how", "why", "who", "whom", "can", "does",
    "explain", "under", "article", "constitution", "court", "judgment", "rights",
    "fundamental", "liberty", "law", "supreme", "bench", "decide", "decision",
    "ruling", "between", "versus", "against", "state", "union", "india", "case",
    "privacy", "speech", "equality", "amendment", "act", "section", "citizen"
}
```

### 2. `HINGLISH_INDICATORS` (Lines 22–25)
A set of 18 common Romanized Hindi functional words:
```python
{
    "kya", "kyon", "kaise", "samvidhan", "adhikar", "kanoon", "hoga", "hota",
    "hai", "hain", "ke", "ki", "ka", "mein", "par", "se", "aur", "nahi"
}
```

---

## 3. Functions in `nlp/language_detection.py`

### 1. `detect_script(text: str) -> str`
- **Lines in Source**: [Lines 28–57](../../nlp/language_detection.py#L28-L57)
- **What it does**: Inspects Unicode ranges of characters in the string:
  - Devanagari: `\u0900` to `\u097F`
  - Bengali: `\u0980` to `\u09FF`
  - Tamil: `\u0B80` to `\u0BFF`
  - Telugu: `\u0C00` to `\u0C7F`
  - Latin: `[a-zA-Z]`
- **Decision Logic**:
  - If Devanagari characters $> 30\%$ of total letters $\to$ `"devanagari"`.
  - If other Indic characters $> 30\%$ $\to$ returns that script name.
  - If Latin characters $\ge 70\%$ $\to$ `"latin"`.
  - Otherwise returns `"mixed"` or `"symbols_or_numbers"`.

---

### 2. `detect_language(text: str) -> Dict[str, Any]`
- **Lines in Source**: [Lines 59–144](../../nlp/language_detection.py#L59-L144)
- **What it does**:
  1. Calls `detect_script()`.
  2. If script is `devanagari`, returns `language="hi"`, `is_english=False`, `confidence=0.95`.
  3. If script is Latin:
     - Extracts lowercase alphabetic tokens.
     - Computes intersection with `ENGLISH_INDICATORS` and `HINGLISH_INDICATORS`.
     - If `hinglish_matches >= 2` and exceeds English matches $\to$ returns `language="hinglish"`.
     - If English indicators match or token count $\ge 3$ $\to$ returns `language="en"` with calibrated confidence.
- **Return Value**:
  ```python
  {
      "language": "en" | "hi" | "hinglish" | "unknown",
      "is_english": bool,
      "confidence": float,
      "script": str,
      "reason": str
  }
  ```

---

## 4. Actual Code Walkthrough

### Code Excerpt: Unicode Character Block & Script Logic
```python
# Lines 35-54 in nlp/language_detection.py
devanagari_chars = len(re.findall(r"[\u0900-\u097F]", text))
bengali_chars = len(re.findall(r"[\u0980-\u09FF]", text))
tamil_chars = len(re.findall(r"[\u0B80-\u0BFF]", text))
telugu_chars = len(re.findall(r"[\u0C00-\u0C7F]", text))
latin_chars = len(re.findall(r"[a-zA-Z]", text))

total_letters = devanagari_chars + bengali_chars + tamil_chars + telugu_chars + latin_chars
if total_letters == 0:
    return "symbols_or_numbers"
    
if devanagari_chars / total_letters > 0.3:
    return "devanagari"
if latin_chars / total_letters >= 0.7:
    return "latin"
```
- **Explanation**: Uses mathematical Unicode character proportions to identify the writing script directly from the raw character stream.
- **Why is this needed?**: Completely immune to network failures, requires zero external model downloads, and executes in less than 1 millisecond.

---

## 5. Practical Example

### Query 1: English Query
- Input: `"What are fundamental rights under Article 21?"`
- Script: `latin` (100%)
- English Indicators: `['what', 'are', 'fundamental', 'rights', 'under', 'article']`
- Result:
  ```python
  {"language": "en", "is_english": True, "confidence": 0.98, "script": "latin"}
  ```

### Query 2: Devanagari Hindi Query
- Input: `"अनुच्छेद 21 के तहत क्या अधिकार हैं?"`
- Script: `devanagari` (100%)
- Result:
  ```python
  {"language": "hi", "is_english": False, "confidence": 0.95, "script": "devanagari"}
  ```

### Query 3: Transliterated Hinglish Query
- Input: `"kya police bina warrant ke mera ghar search kar sakti hai?"`
- Script: `latin`
- Hinglish Matches: `['kya', 'ke', 'hai']`
- Result:
  ```python
  {"language": "hinglish", "is_english": False, "confidence": 0.75, "script": "latin"}
  ```

---

## 6. Connection to Other Files

- **Called by**: [`rag/pipeline.py`](../../rag/pipeline.py) as Stage 1 before preprocessing.
- **Feeds into**: [`routing/query_router.py`](../../routing/query_router.py) to confirm supported language.
- **Proceed to**: [**`07_RETRIEVAL_MODULE/README.md`**](../07_RETRIEVAL_MODULE/README.md) to explore the Information Retrieval subsystem.

