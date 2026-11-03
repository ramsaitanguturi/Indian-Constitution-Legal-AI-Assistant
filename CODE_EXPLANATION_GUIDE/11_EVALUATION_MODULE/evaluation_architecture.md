# Evaluation Architecture & Zero-Leakage Benchmarks: `11_EVALUATION_MODULE/evaluation_architecture.md`

[Back to Evaluation Overview](README.md) • [Back to Main Index](../README.md)

---

## 1. Basic Introduction

### What is this file?
This document details the **Evaluation Architecture, Benchmark Dataset Design, and Zero-Data-Leakage Partitioning Strategy** employed across the project. It describes how experimental splits were formed, how ground-truth gold annotations were collected, and how evaluation integrity was preserved.

### Why is Evaluation Architecture critical for Academic Viva?
The single most common criticism in AI viva examinations is **Data Contamination & Evaluation Leakage**:
- Did your TF-IDF vectorizer see the test queries during training?
- Are your retrieval test queries identical to sentences in the training corpus?
- Did your evaluation script inflate NDCG scores by counting duplicate chunks from the same document multiple times?

Our evaluation architecture strictly eliminates these biases:
1. **Guaranteed Zero Leakage**: Train, validation, and test datasets are partitioned into physically separate JSON files. All vectorizers, classifiers, and thresholds are trained strictly on the training partition.
2. **Canonical Alias Maps**: Solves document ID variations (`art_21` vs `const_art_021`) so relevance is evaluated strictly on substantive identity.
3. **Multi-Aspect Query Diversity**: The test set balances simple statutory lookups, complex multi-hop constitutional challenges, procedural queries, and comparative landmark case questions.

---

## 2. Benchmark Datasets & Schemas

All benchmark datasets are located in `data/benchmarks/` and `data/annotations/`:

```
data/
├── benchmarks/
│   ├── legal_queries_gold.json       # 100 Expert-annotated IR evaluation queries
│   ├── intent_train.json             # Intent training set (70% partition)
│   ├── intent_val.json               # Intent validation set (15% partition)
│   ├── intent_test.json              # Unseen holdout intent test set (15% partition)
│   └── alias_map.json                # Canonical document ID mapping dictionary
└── annotations/
    ├── legal_ner_gold.json           # Character span annotations for 10 entity types
    └── entity_linking_gold.json      # Gold surface form -> canonical entity ID mappings
```

---

### 2.1 The 100-Query Gold IR Benchmark: `legal_queries_gold.json`

Each query record in `legal_queries_gold.json` captures rich multidimensional evaluation metadata:

```json
{
  "query_id": "LQ_021",
  "query": "Is the right to privacy protected under Article 21 and which judgment declared it?",
  "category": "Fundamental Rights",
  "difficulty": "multi_hop",
  "intent": "CASE_LAW_QUERY",
  "relevant_documents": [
    "parent_const_art_021",
    "sc_puttaswamy_2017"
  ],
  "expected_articles": ["Article 21"],
  "expected_cases": ["K.S. Puttaswamy v. Union of India"],
  "graded_relevance": {
    "parent_const_art_021": 3,
    "sc_puttaswamy_2017": 3,
    "sc_maneka_1978": 1,
    "parent_const_art_019": 1
  }
}
```

#### Query Distribution Breakdown:
- **Constitutional Articles & Rights (45 queries)**: Exact statutory provisions, fundamental rights, directive principles, emergency powers.
- **Landmark Supreme Court Precedents (30 queries)**: Basic structure doctrine, judicial review, privacy, criminal due process.
- **Procedural & Statutory Governance (15 queries)**: CrPC warrantless search, arrest safeguards, RTI exemptions, citizenship criteria.
- **Adversarial & Out-of-Scope (10 queries)**: Non-legal questions, culinary queries, non-Indian legal systems (used to evaluate Gate 1 and Gate 5 abstention).

---

### 2.2 Strict Zero-Data-Leakage Intent Partitioning

To evaluate intent classification with scientific rigor, queries are partitioned into disjoint sets:
- **`intent_train.json` (70%)**: Used solely to fit TF-IDF vectorizers and train the Logistic Regression / Naive Bayes model.
- **`intent_val.json` (15%)**: Used solely for hyperparameter tuning (regularization $C$, N-gram ranges).
- **`intent_test.json` (15%)**: **Held out completely unseen**. Evaluated only once to report final Macro-F1 scores.

```python
# evaluation/intent_eval.py
def evaluate_zero_leakage():
    # 1. Fit ONLY on train
    model.fit(train_queries, train_labels)
    # 2. Evaluate ONLY on unseen test
    test_preds = model.predict(test_queries)
    return calculate_classification_metrics(test_labels, test_preds)
```

---

## 3. Canonical Alias Mapping (`alias_map.json`)

### The Challenge of Duplicate Document IDs
In legal databases, a document might be referenced under varying identifiers:
- `const_art_21` (Constitutional article raw ID)
- `const_art_021` (Zero-padded corpus ID)
- `parent_const_art_021` (Parent store hydrated ID)
- `child_const_art_021_cl_0` (Child chunk ID)

### The Solution:
`evaluation/metrics.py` accepts an `alias_map: Dict[str, str]`:
```python
alias_map = {
    "const_art_21": "parent_const_art_021",
    "const_art_021": "parent_const_art_021",
    "child_const_art_021_cl_0": "parent_const_art_021",
    "child_const_art_021_analysis": "parent_const_art_021",
    "sc_puttaswamy_c1": "sc_puttaswamy_2017"
}
```
When computing Hit@K, Recall@K, or NDCG@K, all retrieved chunk IDs are mapped to their canonical parent ID. This guarantees that:
1. A relevant hit is never penalized simply because it retrieved a child chunk rather than a parent ID.
2. Multiple child chunks from the same document are **deduplicated**, preventing phantom DCG inflation.

---

## 4. Viva Presentation & Defense Q&A

### Q1: How did you ensure there is no data leakage in your evaluation?
> **Student Answer**:
> *"We implemented strict zero-data-leakage protocols. First, for machine learning intent classification, our dataset was split into disjoint train, validation, and test sets. Feature extractors and TF-IDF matrices were fitted strictly on the training partition without ever exposing holdout test queries. Second, for information retrieval evaluation, the 100 gold queries were authored by legal experts as natural user queries rather than copying sentences verbatim from the statutory corpus. This prevents memorization bias and tests true semantic generalization."*

### Q2: What is the purpose of graded relevance in your gold benchmark?
> **Student Answer**:
> *"Binary relevance (relevant vs irrelevant) treats all related documents equally. But in constitutional law, some documents are primary authorities while others are secondary context. For example, for a question on privacy, Article 21 and the Puttaswamy judgment have Grade 3 relevance (mandatory primary authorities), whereas Maneka Gandhi has Grade 1 relevance (historical context). Using graded relevance enables us to calculate Normalized Discounted Cumulative Gain (NDCG@10), mathematically measuring whether primary authorities appear at the top of the search results."*

