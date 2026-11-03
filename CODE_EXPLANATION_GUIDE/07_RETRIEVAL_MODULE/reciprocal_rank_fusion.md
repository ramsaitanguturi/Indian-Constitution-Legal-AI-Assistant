# Code Explanation: `retrieval/rrf.py` ⚖️

> **Source File**: [`retrieval/rrf.py`](../../retrieval/rrf.py)  
> **Lines of Code**: 113 lines  
> **Primary Responsibility**: Mathematical rank reciprocity fusion combining disparate scoring distributions (BM25 vs. Dense vectors) into a unified, scale-invariant ranking.

---

## 1. Basic Introduction

### What is this file?
[`retrieval/rrf.py`](../../retrieval/rrf.py) implements **Reciprocal Rank Fusion (RRF)**, a mathematical rank aggregation algorithm developed by Cormack, Clarke, and Buettcher (SIGIR 2009).

### Why does this file exist?
When combining BM25 keyword search with dense vector search, you encounter the **Score Calibration Problem**:
- BM25 produces unbounded positive scores (e.g. $18.42$, $4.15$, $0.80$).
- Dense vector models produce cosine similarity scores bounded between $-1.0$ and $+1.0$ (or distances between $0.0$ and $2.0$).
- If you simply add them together ($\text{BM25} + \text{Dense}$), the larger BM25 scores will completely overwhelm the dense vector scores.
- Even min-max score normalization fails if one distribution contains extreme statistical outliers.

**Reciprocal Rank Fusion (RRF)** solves this by **discarding raw scores entirely** and evaluating candidates solely based on their **ordinal rank positions** ($1, 2, 3, \dots, N$).

---

## 2. Mathematical Formulation of RRF

For any document $d$ appearing across multiple ranked candidate lists $\mathcal{L} = \{L_1, L_2, \dots, L_m\}$:

$$\text{RRF\_Score}(d) = \sum_{L \in \mathcal{L}} \frac{1}{k + \text{rank}_L(d)}$$

Where:
- $\text{rank}_L(d)$ is the 1-indexed rank of document $d$ in list $L$ (e.g., $1$ for 1st place, $2$ for 2nd place).
- $k$ is a constant smoothing hyperparameter (in our system, $k = 60$).

### Why is $k = 60$ the Standard?
If $k = 0$, Rank 1 receives score $1.0$, while Rank 2 receives score $0.50$ (a massive 50% drop). Setting $k = 60$ smooths the progression:
- Rank 1 receives: $\frac{1}{60 + 1} = \frac{1}{61} \approx 0.01639$
- Rank 2 receives: $\frac{1}{60 + 2} = \frac{1}{62} \approx 0.01613$
- If a document appears at **Rank 1 in both BM25 and Dense**:
  $$\text{Score} = \frac{1}{61} + \frac{1}{61} \approx 0.03279$$
This strongly rewards documents supported by **both** retrieval methods while preventing high-ranked outliers from dominating.

---

## 3. Functions in `retrieval/rrf.py`

### 1. `get_candidate_key(candidate: Dict[str, Any]) -> str` (Lines 11–18)
- Extracts a unique candidate identifier string from varying keys (`chunk_id`, `child_id`, `document_id`, `id`).

---

### 2. `fuse(rank_lists: List[List[Dict[str, Any]]], k: int = 60) -> List[Dict[str, Any]]` (Lines 21–113)
- **Algorithm**:
  1. Validates `k > 0` (defaults to `RRF_K = 60`).
  2. Initializes `rrf_scores`, `candidate_records`, and `source_ranks`.
  3. Iterates over each ranked list (e.g., List 0 = BM25, List 1 = Dense):
     - For each candidate at 1-indexed position `item_rank`:
       - Calculates reciprocal rank: $\frac{1.0}{k + \text{item\_rank}}$.
       - Accumulates score: `rrf_scores[cand_key] += reciprocal_rank`.
       - Records source rank: `source_ranks[cand_key]["list_0"] = item_rank`.
       - Deep merges candidate metadata (retains text, merges metadata dictionaries).
  4. Sorts all unique candidates descending by fused RRF score:
     ```python
     sorted_items = sorted(rrf_scores.items(), key=lambda kv: kv[1], reverse=True)
     ```
  5. Updates final ranks ($1, 2, \dots, N$) and attaches `meta["source_ranks"]` for complete audit transparency.
  6. Returns fused candidate list.

---

## 4. Actual Code Walkthrough

### Code Excerpt: RRF Reciprocal Rank Accumulation
```python
# Lines 55-66 in retrieval/rrf.py
# Use explicit 'rank' if provided, otherwise derive from 1-indexed list position
item_rank = item.get("rank")
if not isinstance(item_rank, int) or item_rank < 1:
    item_rank = item_idx + 1

reciprocal_rank = 1.0 / (effective_k + item_rank)
rrf_scores[cand_key] = rrf_scores.get(cand_key, 0.0) + reciprocal_rank

if cand_key not in source_ranks:
    source_ranks[cand_key] = {}
source_ranks[cand_key][f"list_{list_idx}"] = item_rank
```
- **Explanation**: Computes the reciprocal fraction for each candidate and accumulates it into a global dictionary.
- **Why is this needed?**: Guarantees that documents appearing in both sparse and dense candidate pools are ranked higher than documents appearing in only one.

---

## 5. Practical Example

### Suppose Candidate Passages are retrieved:
- **Passage A** (Article 21):
  - Ranked #1 in BM25 ($\text{rank} = 1$)
  - Ranked #2 in Dense ($\text{rank} = 2$)
  - $\text{RRF Score} = \frac{1}{60 + 1} + \frac{1}{60 + 2} = 0.016393 + 0.016129 = \mathbf{0.032522}$
- **Passage B** (General Privacy article):
  - Ranked #1 in Dense ($\text{rank} = 1$)
  - Did NOT appear in top-30 of BM25
  - $\text{RRF Score} = 0 + \frac{1}{60 + 1} = \mathbf{0.016393}$
- **Passage C** (Specific procedural rule):
  - Ranked #5 in BM25 ($\text{rank} = 5$)
  - Ranked #10 in Dense ($\text{rank} = 10$)
  - $\text{RRF Score} = \frac{1}{65} + \frac{1}{70} = 0.015385 + 0.014286 = \mathbf{0.029671}$

### Final RRF Ranking:
1. **Passage A** (Score: $0.032522$) — *Winner because both methods agreed!*
2. **Passage C** (Score: $0.029671$) — *Ranked 2nd because supported by both methods.*
3. **Passage B** (Score: $0.016393$) — *Ranked 3rd.*

---

## 6. Connection to Other Files

- **Called by**: [`retrieval/hybrid_retriever.py`](../../retrieval/hybrid_retriever.py) (Step 3 candidate merging).
- **Benchmarked in**: [`experiments/experiment_04_rrf.py`](../../experiments/experiment_04_rrf.py) (shows NDCG@10 jumping from 0.5739 to **0.6558**).
- **Proceed to**: [**`entity_boosting.md`**](entity_boosting.md) to inspect how legal entities receive additive ranking boosts.

