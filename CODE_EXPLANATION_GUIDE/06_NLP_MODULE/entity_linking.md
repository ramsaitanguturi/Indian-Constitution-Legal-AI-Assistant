# Code Explanation: `nlp/entity_linking.py` 🔗

> **Source File**: [`nlp/entity_linking.py`](../../nlp/entity_linking.py)  
> **Lines of Code**: 450 lines  
> **Primary Responsibility**: Canonical entity resolution mapping informal aliases, colloquial nicknames, and statutory abbreviations to unique database entity IDs with structured legal metadata.

---

## 1. Basic Introduction

### What is this file?
[`nlp/entity_linking.py`](../../nlp/entity_linking.py) is the **Canonical Entity Linking Engine** for the legal assistant. While Named Entity Recognition (NER) detects that a word is an entity, Entity Linking answers the question: **Which exact statutory document in our database does this refer to?**

### Why does this file exist?
Legal users and citizens refer to landmark cases and provisions using dozens of different surface aliases:
- *"The Aadhaar Judgment"*
- *"The Privacy Case"*
- *"Puttaswamy"*
- *"Puttaswamy (2017)"*
- *"Justice K.S. Puttaswamy v. Union of India"*

All 5 of these phrases refer to the exact same landmark decision: `CASE_PUTTASWAMY_2017` (`(2017) 10 SCC 1`). Without entity linking, a search for *"Aadhaar Judgment"* might completely miss documents tagged with *"Justice K.S. Puttaswamy"*.

[`nlp/entity_linking.py`](../../nlp/entity_linking.py) links surface mentions to canonical entity IDs with **86.67% linking accuracy**, retrieving document IDs, citations, judicial benches, and core legal principles.

---

## 2. Architecture of the Entity Registry

The `EntityLinker` maintains two core in-memory indexes:
1. `entity_registry: Dict[str, Dict[str, Any]]`:
   - Maps unique `entity_id` $\to$ Complete legal entity record.
   - Example: Key `"CASE_PUTTASWAMY_2017"` maps to `{canonical_name: "Justice K.S. Puttaswamy v. Union of India", citation: "(2017) 10 SCC 1", year: 2017, bench: "9-Judge Bench", ratio_decidendi: "..."}`.
2. `alias_index: Dict[str, str]`:
   - Maps normalized alias string $\to$ `entity_id`.
   - Examples:
     - `"privacy case"` $\to$ `"CASE_PUTTASWAMY_2017"`
     - `"aadhaar judgment"` $\to$ `"CASE_PUTTASWAMY_2017"`
     - `"passport case"` $\to$ `"CASE_MANEKA_1978"`
     - `"mandal case"` $\to$ `"CASE_INDRA_SAWHNEY_1992"`
     - `"triple talaq case"` $\to$ `"CASE_SHAYARA_BANO_2017"`
     - `"section 66a case"` $\to$ `"CASE_SHREYA_SINGHAL_2015"`
     - `"basic structure case"` $\to$ `"CASE_KESAVANANDA_1973"`

---

## 3. Important Methods in `EntityLinker`

### 1. `_normalize_key(text: str) -> str` (Lines 37–46)
- Lowercases, removes punctuation (`re.sub(r"[^\w\s]", "", text)`), and collapses whitespace.
- Transforms `"Art. 21(1)"` into `"art 211"` or `"Privacy Case!"` into `"privacy case"`.

### 2. `_seed_foundational_concepts()` (Lines 47–148)
- Seeds foundational Indian legal doctrines:
  - `CONCEPT_BASIC_STRUCTURE` (Originating: *Kesavananda Bharati*, Core: Article 368)
  - `RIGHT_PRIVACY` (Originating: *Puttaswamy*, Core: Article 21)
  - `RIGHT_LIFE_LIBERTY` (Core: Article 21)
  - `RIGHT_EQUALITY` (Core: Article 14)
  - `RIGHT_FREE_SPEECH` (Core: Article 19(1)(a))
  - `CONCEPT_JUDICIAL_REVIEW` (Core: Articles 13, 32, 226)
  - `CONCEPT_DUE_PROCESS` (Originating: *Maneka Gandhi*, Core: Article 21)

### 3. `_build_index_from_corpus()` (Lines 150–331)
- Reads active JSON files from `data/`:
  - `articles.json`: Dynamically creates records for `ARTICLE_1` through `ARTICLE_395` (and amendments up to `ARTICLE_477`), mapping aliases like `"art 21"`, `"article 21 of the constitution"`.
  - `amendments.json`: Indexes `AMENDMENT_1` through `AMENDMENT_106`.
  - `supreme_court_landmarks.json`: Indexes landmark case titles, lead parties, and popular shorthands.

### 4. `link_entity(mention: str, entity_type: Optional[str] = None) -> Optional[Dict[str, Any]]` (Lines 332–409)
- **Multi-Stage Linking Resolution**:
  1. **Exact Alias Match**: Checks if normalized mention exists in `self.alias_index`. If found, returns record with `confidence = 1.0`.
  2. **Heuristic Normalization for Articles**: If mention contains `Art. 21(1)`, extracts digits `21` and checks for `ARTICLE_21` (`confidence = 0.95`).
  3. **Heuristic Normalization for Amendments**: If mention contains `42nd Amendment`, extracts `42` and checks for `AMENDMENT_42` (`confidence = 0.95`).
  4. **Fuzzy / Substring Match**: Searches registered aliases for strong substring inclusion with `confidence = 0.85`.
  5. Returns `None` if unresolved.

### 5. `link_all(extracted_entities: Dict[str, List[str]]) -> List[Dict[str, Any]]` (Lines 410–430)
- Takes the entity dictionary from `LegalNER.extract_entities()` and resolves all mentions across categories, deduplicating entity IDs.

---

## 4. Actual Code Walkthrough

### Code Excerpt: Landmark Case Alias Resolution
```python
# Lines 249-267 in nlp/entity_linking.py
if "puttaswamy" in lower_name and ("privacy" in doc_id or year == 2017):
    eid = "CASE_PUTTASWAMY_2017"
    aliases = [
        case_name, "Justice K.S. Puttaswamy", "Puttaswamy", "Puttaswamy case",
        "Aadhaar case", "privacy judgment", "privacy case"
    ]
elif "kesavananda" in lower_name:
    eid = "CASE_KESAVANANDA_1973"
    aliases = [
        case_name, "Kesavananda Bharati", "Kesavananda",
        "fundamental rights case", "basic structure case"
    ]
elif "maneka gandhi" in lower_name:
    eid = "CASE_MANEKA_1978"
    aliases = [case_name, "Maneka Gandhi", "Maneka Gandhi case", "passport case"]
```
- **Explanation**: Binds popular informal descriptions (*"passport case"*, *"basic structure case"*) to deterministic database IDs.
- **Why is this needed?**: Enables researchers who only remember the informal case name to retrieve the correct Supreme Court holding immediately.

---

## 5. Practical Example

### Input Mention:
`"passport case"`

### Linking Execution:
1. `_normalize_key("passport case")` $\to$ `"passport case"`.
2. Matches `self.alias_index["passport case"]` $\to$ `"CASE_MANEKA_1978"`.
3. Looks up record in `self.entity_registry`.

### Output Linked Record:
```python
{
    "entity_id": "CASE_MANEKA_1978",
    "canonical_name": "Maneka Gandhi v. Union of India",
    "entity_type": "CASE",
    "surface_form": "passport case",
    "confidence": 1.0,
    "metadata": {
        "document_id": "parent_case_sc_maneka_gandhi_1978",
        "citation": "(1978) 1 SCC 248",
        "year": 1978,
        "bench": "7-Judge Bench",
        "ratio_decidendi": "Procedure established by law under Article 21 must be just, fair and reasonable, not arbitrary or oppressive..."
    }
}
```

---

## 6. Connection to Other Files

- **Input from**: [`nlp/legal_ner.py`](../../nlp/legal_ner.py) (receives extracted surface mentions).
- **Feeds into**:
  - [`routing/query_router.py`](../../routing/query_router.py) (uses linked IDs for strategy selection)
  - [`retrieval/entity_boost.py`](../../retrieval/entity_boost.py) (uses linked IDs for $+0.15$ score boosting)
  - [`rag/confidence.py`](../../rag/confidence.py) (validates entity alignment)
- **Proceed to**: [**`query_expansion.md`**](query_expansion.md) to inspect how informal inquiries are enriched with formal statutory synonyms.

