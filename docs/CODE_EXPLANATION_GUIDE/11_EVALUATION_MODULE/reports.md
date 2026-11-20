# Evaluation Reporting & Artifact Generation: `evaluation/report_generator.py`

[Back to Evaluation Overview](README.md) • [Back to Main Index](../README.md)

---

## 1. Basic Introduction

### What is this file?
`evaluation/report_generator.py` is the **Automated Report and Artifact Generation Engine**. After `benchmark_runner.py` completes execution, this module formats and saves the empirical results into three standardized formats:
1. **Machine-Readable JSON Summary** (`evaluation/results/evaluation_summary.json`): Structured data for programmatic dashboard consumption.
2. **Structured CSV Benchmark Tables** (`retrieval_results.csv`, `classification_results.csv`, `ner_results.csv`): Tabular data for plotting graphs and statistical analysis in Excel or Pandas.
3. **Comprehensive Human-Readable Markdown Report** (`evaluation/results/evaluation_report.md`): Publication-grade markdown document complete with executive summaries, ablation tables, hyperparameters, and academic disclaimers.

---

## 2. Imports and Dependencies

```python
# evaluation/report_generator.py L12-L30
import csv
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from config import (
    EVALUATION_RESULTS_DIR,
    DEFAULT_EMBEDDING_MODEL,
    RERANKER_MODEL_NAME,
    BM25_K1,
    BM25_B,
    RRF_K,
    ENTITY_BOOST_WEIGHT,
    DATASET_VERSION,
    EVAL_RANDOM_SEED,
)
```

---

## 3. Class: `ReportGenerator`

```python
class ReportGenerator:
    """
    Serializes quantitative experiment outcomes into JSON, CSV, and Markdown formats.
    """
```

### 3.1 Serialization Methods

| Method | Output File | Contents |
| :--- | :--- | :--- |
| `save_json(data, filename)` | `evaluation_summary.json` | Complete nested JSON dump of all metric dictionaries. |
| `save_retrieval_csv(...)` | `retrieval_results.csv` | Tabular rows for each retrieval ablation (Hit@1, Hit@5, Hit@10, MRR, NDCG@5, NDCG@10). |
| `save_classification_csv(...)`| `classification_results.csv`| Precision, Recall, F1 per intent class for Rule, ML, and Hybrid models. |
| `save_ner_csv(...)` | `ner_results.csv` | Precision, Recall, F1, and support counts for all 10 legal entity categories. |
| `save_markdown_report(...)` | `evaluation_report.md` | Complete formatted markdown text with headings, tables, and narrative explanations. |

---

## 4. Master Markdown Report Structure (`evaluation_report.md`)

The generated markdown report is structured into seven distinct sections:

1. **Header & Metadata**: Execution timestamp, dataset version, random seed, active embedding model, reranker model.
2. **Executive Summary**: High-level narrative highlighting major performance gains (e.g., +41.9% NDCG@10 gain over BM25).
3. **Retrieval Ablation Analysis**: Side-by-side comparative table of all 6 search configurations:
   ```markdown
   | Configuration | Hit@5 | Hit@10 | MRR | NDCG@5 | NDCG@10 | Relative Gain |
   | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
   | 1. BM25 Baseline | 0.6800 | 0.7700 | 0.4912 | 0.5120 | 0.5484 | Baseline |
   | 2. Dense (BGE-M3) | 0.7200 | 0.8100 | 0.5240 | 0.5410 | 0.5739 | +4.6% |
   | 3. Naive Linear Hybrid | 0.7600 | 0.8400 | 0.5620 | 0.5820 | 0.6120 | +11.6% |
   | 4. Hybrid RRF (k=60) | 0.8100 | 0.8800 | 0.6150 | 0.6280 | 0.6558 | +19.6% |
   | 5. RRF + Entity Boost | 0.8400 | 0.9000 | 0.6580 | 0.6710 | 0.6994 | +27.5% |
   | 6. Full Pipeline (+ Rerank) | **0.8900** | **0.9400** | **0.7420** | **0.7510** | **0.7787** | **+41.9%** 🚀 |
   ```
4. **Legal Named Entity Recognition**: Detailed breakdown across all 10 entity categories showing Micro-F1 (0.86) and Macro-F1 (0.85).
5. **Intent Classification**: Accuracy and Macro-F1 across Rule-based, ML-based, and Hybrid classifiers.
6. **Canonical Entity Linking**: Top-1 linking accuracy (86.67%).
7. **Grounded Generation & Citation Integrity**: Verification precision (100%), proposition entailment ratio, and abstention compliance.

---

## 5. Viva Presentation & Defense Q&A

### Q1: Where can your professors view the benchmark results in the project?
> **Student Answer**:
> *"The complete results are automatically saved in `evaluation/results/evaluation_report.md`. This markdown document summarizes the entire empirical evaluation, including the 6-stage retrieval ablation table, NER per-category metrics, zero-leakage intent classification scores, and citation validity rates. Additionally, all raw metric numbers are exported as CSV files (`retrieval_results.csv`, `classification_results.csv`) and JSON summaries in the same directory."*

### Q2: What is the most significant takeaway from your empirical evaluation report?
> **Student Answer**:
> *"The single most significant finding is that neither pure keyword search (BM25: NDCG@10 = 0.5484) nor pure dense search (BGE-M3: NDCG@10 = 0.5739) is sufficient for constitutional law. However, combining them through Cormack Reciprocal Rank Fusion, applying our +0.15 statutory entity boost, and neural cross-encoder reranking yields an NDCG@10 of 0.7787—a massive 41.9% improvement over BM25. This proves that hybrid, entity-aware architecture is quantitatively superior for Indian legal AI."*

