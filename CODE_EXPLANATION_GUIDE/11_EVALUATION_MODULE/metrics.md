# Mathematical Evaluation Metrics: `evaluation/metrics.py`

[Back to Evaluation Overview](README.md) • [Back to Main Index](../README.md)

---

## 1. Basic Introduction

### What is this file?
`evaluation/metrics.py` is the **Mathematical Evaluation Engine** of the project. It provides strict, zero-external-dependency mathematical implementations for all information retrieval metrics (Hit@K, Recall@K, Precision@K, MRR, DCG@K, NDCG@K), Named Entity Recognition metrics (Micro/Macro F1 across 10 classes), classification metrics (Confusion Matrix, Macro/Weighted F1), entity linking accuracy, and grounded RAG citation precision.

### Why is a dedicated metrics module needed?
Third-party libraries (like `scikit-learn` or `trec_eval`) often make domain-incompatible assumptions:
- In Information Retrieval, standard libraries cannot handle canonical alias maps (e.g. treating `child_const_art_021_cl_0` as a miss for `parent_const_art_021`).
- Standard DCG implementations don't deduplicate multiple child hits from the same document, artificially inflating NDCG scores.
- Standard NLP toolkits don't support custom legal span matching with 10 fine-grained categories.

`evaluation/metrics.py` provides transparent, fully auditable mathematical formulas matching international IR and NLP standards (TREC, SemEval, CoNLL).

---

## 2. Imports and Dependencies

```python
# evaluation/metrics.py L13-L15
import math
from typing import Dict, List, Any, Optional, Set, Union, Tuple
```
- Completely free of external evaluation frameworks—relies strictly on standard Python `math` and typed collections.

---

## 3. Information Retrieval Metrics (Formulas & Implementations)

### 3.1 Hit@K (Binary Hit Rate)
Measures whether at least one relevant document was found within the top-$K$ retrieved results:
$$\text{Hit}@K = \begin{cases} 1.0 & \text{if } |\text{Retrieved}_{[:K]} \cap \text{Relevant}| > 0 \\ 0.0 & \text{otherwise} \end{cases}$$

```python
# Lines 21-43
def hit_at_k(retrieved_ids: List[str], relevant_ids: Union[Set[str], List[str]], k: int, alias_map: Optional[Dict[str, str]] = None) -> float:
    if k <= 0 or not retrieved_ids or not relevant_ids:
        return 0.0
    if alias_map:
        rel_set = {alias_map.get(d, d) for d in relevant_ids}
        top_k = [alias_map.get(d, d) for d in retrieved_ids[:k]]
    else:
        rel_set = set(relevant_ids) if not isinstance(relevant_ids, set) else relevant_ids
        top_k = retrieved_ids[:k]
    return 1.0 if any(doc_id in rel_set for doc_id in top_k) else 0.0
```

---

### 3.2 Recall@K and Precision@K

$$\text{Recall}@K = \frac{|\text{Unique}(\text{Retrieved}_{[:K]}) \cap \text{Relevant}|}{|\text{Relevant}|}$$

$$\text{Precision}@K = \frac{|\text{Retrieved}_{[:K]} \cap \text{Relevant}|}{K}$$

- **Deduplication Safeguard**: Lines 68-69 compute `unique_hits = set(top_k) & rel_set`. If two child chunks belonging to the same relevant parent are retrieved, `set(top_k)` ensures the relevant parent is counted **only once**, preventing artificial recall inflation.

---

### 3.3 Reciprocal Rank (RR) and Mean Reciprocal Rank (MRR)

Reciprocal Rank is the inverse of the rank position of the **first** relevant document:
$$\text{RR} = \frac{1}{\min_{i: d_i \in \text{Relevant}} (\text{rank}_i)}$$
Mean Reciprocal Rank (MRR) averages RR across all $N$ benchmark queries:
$$\text{MRR} = \frac{1}{N} \sum_{q=1}^{N} \text{RR}_q$$
- First relevant document at Rank 1 $\to \text{RR} = 1.0$
- First relevant document at Rank 2 $\to \text{RR} = 0.5$
- First relevant document at Rank 5 $\to \text{RR} = 0.2$
- No relevant document in retrieved list $\to \text{RR} = 0.0$

---

### 3.4 Discounted Cumulative Gain (DCG@K) & NDCG@K

Discounted Cumulative Gain rewards retrieving highly relevant documents near the top of the list while discounting documents appearing lower down using a logarithmic penalty:
$$\text{DCG}@K = \sum_{i=1}^{K} \frac{2^{\text{rel}_i} - 1}{\log_2(i + 1)}$$
Where $\text{rel}_i$ is the graded relevance of the document at rank $i$ (e.g., $3$ for primary statutes, $1$ for secondary context, $0$ for irrelevant).

Normalized DCG divides DCG by the Ideal DCG (IDCG@K), which is the DCG obtained by sorting all ground-truth relevant documents in perfect descending order:
$$\text{NDCG}@K = \frac{\text{DCG}@K}{\text{IDCG}@K}$$

#### Implementation Code Walkthrough (Lines 163-174):
```python
    top_k = retrieved_ids[:k]
    dcg = 0.0
    seen_canonical = set()
    for i, doc_id in enumerate(top_k, start=1):
        can_id = alias_map.get(doc_id, doc_id) if alias_map else doc_id
        if can_id in seen_canonical:
            continue
        seen_canonical.add(can_id)
        rel = score_dict.get(can_id, score_dict.get(doc_id, 0.0))
        gain = (2.0 ** rel) - 1.0
        discount = math.log2(i + 1)
        dcg += gain / discount
    return dcg
```
- **Why `seen_canonical` prevents false inflation**: If chunk 1 and chunk 2 of Article 21 appear at Rank 1 and Rank 2, naive DCG would count the Grade 3 relevance score twice! `seen_canonical` guarantees that each document gains relevance points **only once** at its highest rank.

---

## 4. Legal Named Entity Recognition (NER) Metrics

Evaluates predictions across all 10 legal entity categories (`ARTICLE`, `CASE`, `PERSON`, `COURT`, `LEGAL_CONCEPT`, `RIGHT`, `AMENDMENT`, `ACT`, `SECTION`, `DATE`).

```python
def calculate_ner_metrics(
    gold_annotations: List[Dict[str, Any]],
    predicted_annotations: List[Dict[str, Any]],
    exact_span_match: bool = True
) -> Dict[str, Any]
```

### Micro vs Macro Averaging:
- **Per-Class Metrics**: Computes $\text{Precision}_c = \frac{\text{TP}_c}{\text{TP}_c + \text{FP}_c}$, $\text{Recall}_c = \frac{\text{TP}_c}{\text{TP}_c + \text{FN}_c}$, and $\text{F1}_c = \frac{2 P_c R_c}{P_c + R_c}$.
- **Macro-F1**: Arithmetic unweighted mean across all 10 categories:
  $$\text{Macro-F1} = \frac{1}{C} \sum_{c=1}^{C} \text{F1}_c$$
  Treats frequent categories (`ARTICLE`) and rare categories (`COURT`) with equal importance.
- **Micro-F1**: Aggregates total true positives, false positives, and false negatives globally before computing F1. Dominated by frequent categories.

---

## 5. Summary Metric Comparison Table

| Metric | Target Range | Interpretation in Legal Context |
| :--- | :--- | :--- |
| **Hit@5** | $0.0 - 1.0$ | Did the top 5 search results include at least one relevant constitutional document? |
| **MRR** | $0.0 - 1.0$ | How quickly does an attorney see the first relevant statute? (Target $\ge 0.70$). |
| **NDCG@10** | $0.0 - 1.0$ | Are primary constitutional authorities placed above tangential precedents? |
| **NER Macro-F1** | $0.0 - 1.0$ | Can the system extract all 10 entity categories without bias toward frequent classes? |
| **Intent Macro-F1**| $0.0 - 1.0$ | Does the router classify user goals accurately across all 8 intent types? |
| **Citation Precision**| $1.00$ | What percentage of generated citations actually exist in the database and evidence pool? |

---

## 6. Viva Presentation & Defense Q&A

### Q1: Why is NDCG@10 preferred over simple Precision@10 in legal search?
> **Student Answer**:
> *"Precision@10 is position-unaware: it gives the exact same score whether the primary constitutional article appears at Rank 1 or Rank 10. In a legal assistant, Rank 1 is vastly more important because attorneys and generative models read top documents first. NDCG@10 employs a logarithmic discount ($\frac{1}{\log_2(i+1)}$) and supports graded relevance (3 for primary statute, 1 for secondary case). It mathematically penalizes systems that bury primary authorities down at Rank 8 or 9."*

### Q2: Why did you implement exact span matching in `calculate_ner_metrics`?
> **Student Answer**:
> *"In legal informatics, partial entity matches can be misleading. For example, if the gold text is 'Article 21A' (Right to Education) and an extractor predicts 'Article 21' (Right to Life), token-overlap matching would count that as a positive match even though they are completely different constitutional provisions! Our `exact_span_match=True` parameter mandates that the predicted character offsets `(start, end, label)` match the gold span exactly, ensuring strict evaluation fidelity."*

