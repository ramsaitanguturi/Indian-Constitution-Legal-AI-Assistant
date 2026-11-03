# Parent-Child Context Recovery: `rag/parent_child.py`

[Back to RAG Module Overview](README.md) • [Back to Main Index](../README.md)

---

## 1. Basic Introduction

### What is this file?
`rag/parent_child.py` implements the **Parent-Child Context Recovery Engine**. After the hybrid retriever and neural reranker select the winning top child passages, this module looks up the original full parent documents in `parent_store.json`, deduplicates redundant parent records, constructs an exact audit trail of supporting evidence, and renders structured prompt context for the LLM generator.

### Why is Parent-Child Recovery necessary?
In standard RAG, the same chunks used for vector search are sent to the LLM. This leads to two major dilemmas:
1. **The Retrieval-Generation Dilemma**:
   - Small chunks (100–300 chars) are ideal for retrieval because embeddings are sharp and focused. But generating an answer solely from a 200-character snippet results in superficial, truncated explanations.
   - Large chunks (2,000 chars) provide sufficient context for generation, but suffer from "embedding dilution"—the vector averages out many disparate topics, leading to poor retrieval precision.
2. **Context Duplication & Token Waste**:
   If top 5 retrieved child passages happen to come from Clauses (1), (2), and (3) of Article 19, a naive pipeline would feed the LLM repetitive fragments of Article 19 three times, exhausting token limits without adding context.

`ParentChildRecovery` solves both problems:
- Pinpoint retrieval uses small child passages (~300 chars).
- Generation receives the hydrated, deduplicated parent document (~1,200 chars), with exact child evidence passages clearly highlighted beneath each document.

---

## 2. Imports and Dependencies

```python
# rag/parent_child.py L8-L15
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from config import PARENT_STORE_PATH
```

| Import / Constant | Explanation |
| :--- | :--- |
| `PARENT_STORE_PATH` | Defined in `config.py` as `'data/parent_store.json'`. File containing all 886 complete parent documents indexed by canonical IDs. |
| `json`, `os` | Used to load the 886-document parent dictionary into memory during initialization. |

---

## 3. Class: `ParentChildRecovery`

```python
class ParentChildRecovery:
    """
    Manages the recovery, deduplication, and provenance tracking of parent documents
    associated with retrieved child passages.
    """
```

### 3.1 Constructor `__init__(parent_store: Optional[Dict] = None)`
Loads `parent_store.json` into an in-memory dictionary. If fewer than 20 records are present (e.g. fresh installation), it gracefully invokes `ProductionIngestor.process_parent_child_chunks()` to dynamically populate parent records.

---

### 3.2 Method: `_resolve_parent_record(raw_id: str, chunk: Dict) -> Tuple[str, Dict]`

In real-world retrieval, IDs can experience slight formatting discrepancies (e.g., zero-padding differences: `art_021` vs `art_21`, or prefix differences: `const_art_21` vs `parent_const_art_021`).

`_resolve_parent_record()` performs multi-tier key resolution:
1. **Direct & Prefix Check**: Checks `raw_id`, `parent_id`, `f"parent_{raw_id}"`, or `raw_id.replace("parent_", "")`.
2. **Zero-Padding Normalization**: Uses regex `_0+(\d+)` to test both padded and unpadded forms.
3. **Metadata Fallback**: Matches `metadata["article_number"]` or `metadata["case_name"]` against store entries.
4. **Embedded Data Fallback**: Recovers from `chunk["parent_data"]` if pre-attached.

---

### 3.3 Method: `recover(ranked_chunks: List[Dict]) -> Dict[str, Any]`

Takes the top retrieved and reranked child chunks and constructs a clean recovery package:
- **`parents`**: Deduplicated list of parent document dictionaries.
- **`child_evidence`**: List of exact child passages with rank, score, clause ID, and text.
- **`child_to_parent_map`**: Map of `child_id -> parent_id`.
- **`provenance_records`**: Audit records for explainability logging.
- **`formatted_context`**: Clean markdown string ready for prompt injection.

#### Deduplication Algorithm (Lines 158-169):
```python
            # Deduplicate parents: If already registered, append child chunk without duplicating parent text
            if parent_id in recovered_parents_map:
                existing_entry = recovered_parents_map[parent_id]
                if not any(c["chunk_id"] == chunk_id for c in existing_entry["supporting_children"]):
                    existing_entry["supporting_children"].append(child_record)
                # Keep highest score / best rank
                if rank < existing_entry["best_rank"]:
                    existing_entry["best_rank"] = rank
                if score > existing_entry["best_score"]:
                    existing_entry["best_score"] = float(score)
            else:
                # Register parent for the first time...
```
If chunks from Clause 1 and Clause 2 of Article 21 are both retrieved, Article 21 appears **only once** in `parents`, with both chunks listed under `supporting_children`.

---

### 3.4 Method: `format_context_for_prompt(parents: List[Dict]) -> str`

Formats the recovered parent documents into an authoritative markdown block injected into the LLM prompt.

```markdown
=== SOURCE DOCUMENT 1 [DocID: parent_const_art_021] ===
Document Type: CONSTITUTION
Title / Name: Protection of life and personal liberty
Article Number: Article 21
Part: Part III
Category: Fundamental Rights
Full Statutory Text:
> No person shall be deprived of his life or personal liberty except according to procedure established by law.
Legal Explanation:
Article 21 provides procedural and substantive protections against arbitrary executive deprivation...

Exact Retrieved Child Evidence Passages:
  * [Evidence 1.1 | ChunkID: child_const_art_021_cl_0 | Rank 1]: "Article 21 - Protection of life and personal liberty [Clause (1)]: No person shall be deprived..."
```

---

## 4. Practical Working Example

### Input Chunks (from Reranker Top 3):
1. `child_const_art_021_cl_0` (Article 21 Clause 1, Rank 1)
2. `child_const_art_021_analysis` (Article 21 Analysis, Rank 2)
3. `child_sc_puttaswamy_ratio` (Puttaswamy Ratio, Rank 3)

### Output of `ParentChildRecovery.recover()`:
- `parent_count`: **2** (Article 21 is deduplicated!).
- `child_count`: **3**.
- `parents[0]`: Contains full text, historical context, and both child passages 1 and 2.
- `parents[1]`: Contains Puttaswamy case details, bench composition, facts, and ratio decidendi.

---

## 5. Viva Presentation & Defense Q&A

### Q1: What is Parent-Child indexing and why is it superior to flat chunking?
> **Student Answer**:
> *"In a flat RAG pipeline, whatever passage is retrieved is fed directly to the model. In legal texts, this causes either context fragmentation (if chunks are small) or semantic dilution (if chunks are large). Parent-child retrieval decouples the retrieval representation from the generation context. We search across small child chunks (300 characters) for optimal semantic matching, but pass the complete, deduplicated parent document (1,200 characters) to the LLM. This provides comprehensive legal context without duplicating identical sections."*

### Q2: What happens if two retrieved child chunks belong to the same parent document?
> **Student Answer**:
> *"Our `ParentChildRecovery` module deduplicates them. It recognizes that both chunks share the same `parent_id`. It includes the parent document text only once in the prompt context, while attaching both chunks to the parent's `supporting_children` evidence list. This prevents prompt clutter, saves LLM context window tokens, and ensures the LLM sees the complete statute only once."*

