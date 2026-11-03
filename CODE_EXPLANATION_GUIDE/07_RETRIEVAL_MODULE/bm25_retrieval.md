# Code Explanation: `retrieval/bm25_retriever.py` 📖

> **Source File**: [`retrieval/bm25_retriever.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/bm25_retriever.py)  
> **Lines of Code**: 198 lines  
> **Primary Responsibility**: Sparse lexical keyword retrieval using BM25Okapi, statutory compound tokenization, score normalization to $[0, 1]$, and standardized candidate formatting.

---

## 1. Basic Introduction

### What is this file?
[`retrieval/bm25_retriever.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/bm25_retriever.py) defines the sparse lexical search engine. It indexes the text of all 7,470 child passages using the industry-standard **BM25Okapi** algorithm ($k_1=1.5, b=0.75$).

### Why does this file exist?
While dense vector embeddings capture high-level concepts, they struggle with exact statutory numbers (*"Article 21"* vs *"Article 21A"* or *"Section 165"* vs *"Section 166"*). Furthermore, Indian judgments carry neutral legal citations such as `1973 INSC 258` that embedding bi-encoders do not encode well.

[`retrieval/bm25_retriever.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/bm25_retriever.py) introduces a **custom legal compound tokenizer** that explicitly preserves statutory compound tokens so that exact statutory references receive massive term frequency relevance scores.

---

## 2. The Compound Legal Tokenizer: `simple_tokenize`

Standard English tokenizers split `Article 21` into `["article", "21"]`. Because `"article"` appears thousands of times across the Constitution, its inverse document frequency (IDF) drops near zero.

[`simple_tokenize`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/bm25_retriever.py#L21-L40) solves this by appending synthetic compound tokens:
```python
# Lines 21-40 in retrieval/bm25_retriever.py
def simple_tokenize(text: str) -> List[str]:
    if not text:
        return []
    text_lower = text.lower()
    tokens = re.findall(r"\b\w+\b", text_lower)

    # 1. Synthesize compound Article tokens (e.g. 'article_21')
    for m in re.findall(r'\b(?:article|art\.?)\s*(\d+[a-z]?)\b', text_lower):
        tokens.append(f"article_{m}")

    # 2. Synthesize compound Section tokens (e.g. 'section_165')
    for m in re.findall(r'\b(?:section|sec\.?)\s*(\d+[a-z]?)\b', text_lower):
        tokens.append(f"section_{m}")

    # 3. Synthesize Amendment tokens (e.g. '42th_amendment')
    for m in re.findall(r'\b(\d+)(?:st|nd|rd|th)\s+amendment\b', text_lower):
        tokens.append(f"{m}th_amendment")

    # 4. Synthesize Neutral Supreme Court Citations (e.g. '1973insc258')
    for m in re.findall(r'\b(\d{4}insc\d+)\b', text_lower):
        tokens.append(m)

    return tokens
```

- When indexing Article 21, the chunk receives the token `article_21`.
- When the user searches *"What is Article 21?"*, the query generates `article_21`.
- Because `article_21` appears only in Article 21 and its direct case precedents, its BM25 relevance score spikes dramatically, completely eliminating Anchor Confusion!

---

## 3. Class Structure: `BM25Retriever`

### Constructor: `__init__(bm25_index=None, child_chunks=None, parent_store=None, k1=1.5, b=0.75)` (Lines 49–67)
- Sets hyperparameters $k_1=1.5$ (governs term frequency saturation) and $b=0.75$ (governs document length penalty).
- If `bm25_index` or `child_chunks` are missing, calls `_initialize_from_corpus()` to load the production corpus.

---

## 4. Key Method: `retrieve(query, top_k=20, filter_doc_type=None)`

- **Lines in Source**: [Lines 91–198](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/bm25_retriever.py#L91-L198)
- **Input Parameters**:
  - `query` (str): Search string.
  - `top_k` (int): Number of candidates (default 20).
  - `filter_doc_type` (Optional[str]): Metadata filter.

### Execution Algorithm:
1. Calls `simple_tokenize(query)`.
2. Computes raw BM25 scores: `raw_scores = self.bm25_index.get_scores(tokens)`.
3. Filters for chunks with positive scores (`score > 0.0`).
4. Optionally filters by `doc_type` if specified.
5. Sorts positive indices descending by score.
6. **Score Normalization**:
   - BM25 scores are unbounded positive numbers (e.g. $14.82$ or $3.21$).
   - Normalizes scores to $[0.0, 1.0]$ relative to the top candidate score:
     $$\text{Normalized\_Score} = \frac{\text{raw\_score}}{\text{max\_score}}$$
7. Hydrates parent metadata and formats candidate dictionaries.

---

## 5. Actual Code Walkthrough

### Code Excerpt: Score Normalization and Candidate Schema
```python
# Lines 153-187 in retrieval/bm25_retriever.py
max_score = float(raw_scores[ranked_indices[0]]) if ranked_indices else 1.0

results: List[Dict[str, Any]] = []
for rank, idx in enumerate(ranked_indices, start=1):
    chunk = self.child_chunks[idx]
    chunk_id = chunk.get("child_id", f"chunk_{idx}")
    parent_id = chunk.get("parent_id", "")
    raw_s = float(raw_scores[idx])

    # Normalized score bounded in [0.0, 1.0]
    normalized_score = round(raw_s / max_score, 4) if max_score > 0 else 0.0

    parent_data = self.parent_store.get(parent_id, {})
    metadata = {
        "parent_id": parent_id,
        "article_number": chunk.get("article_number", parent_data.get("article_number", "")),
        "case_name": chunk.get("case_name", parent_data.get("case_name", "")),
        "title": chunk.get("title", parent_data.get("title", "")),
        "raw_bm25_score": raw_s,
        "parent_data": parent_data,
    }

    candidate = {
        "document_id": parent_id,
        "chunk_id": chunk_id,
        "score": normalized_score,
        "rank": rank,
        "text": chunk.get("text", ""),
        "doc_type": chunk.get("doc_type", "legal_document"),
        "metadata": metadata,
    }
```
- **Explanation**: Normalizes raw BM25 scores to a $[0, 1]$ range so downstream components can compare candidates on a uniform scale.

---

## 6. Practical Example

### Query:
`"Section 165 search by police officer"`

### Execution:
1. `simple_tokenize()` generates: `['section', '165', 'search', 'by', 'police', 'officer', 'section_165']`.
2. BM25 locates chunk `child_act_crpc_1973_s_165_0` because it contains the exact token `section_165`.
3. Score is computed, normalized to `1.0`, and assigned Rank 1.

---

## 7. Connection to Other Files

- **Called by**: [`retrieval/hybrid_retriever.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/hybrid_retriever.py) (retrieves top 30 sparse candidates).
- **Benchmarked in**: [`experiments/experiment_01_bm25.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/experiments/experiment_01_bm25.py).
- **Proceed to**: [**`hybrid_retrieval.md`**](hybrid_retrieval.md) to inspect how BM25 and Dense search are fused and reranked.

