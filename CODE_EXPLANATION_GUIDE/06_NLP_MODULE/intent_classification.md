# Code Explanation: `nlp/intent_classifier.py` 🎯

> **Source File**: [`nlp/intent_classifier.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/intent_classifier.py)  
> **Lines of Code**: 441 lines  
> **Primary Responsibility**: Dual-tier intent classification combining deterministic domain rules with a supervised Scikit-learn Machine Learning pipeline (TF-IDF + Logistic Regression).

---

## 1. Basic Introduction

### What is this file?
[`nlp/intent_classifier.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/intent_classifier.py) identifies the legal purpose and research goal behind a user's query. It categorizes incoming questions into one of **10 constitutional intent classes** or detects that the question is **`OUT_OF_SCOPE`**.

### Why does this file exist?
Different legal questions demand fundamentally different retrieval strategies:
- If a user asks *"Show me the text of Article 21"*, the system needs exact statutory lookup.
- If a user asks *"Compare A.K. Gopalan with Maneka Gandhi"*, the system must retrieve both judgments and structure a side-by-side comparative analysis.
- If a user asks *"What is the recipe for a chocolate cake?"*, the system must immediately identify the query as `OUT_OF_SCOPE` to trigger automated safe abstention.

[`nlp/intent_classifier.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/intent_classifier.py) implements a **hybrid consensus architecture**: a deterministic rule baseline and a trained machine learning classifier cross-verify each other.

---

## 2. The 11 Intent Classes

| Intent Class | Description | Example Query |
|---|---|---|
| `ARTICLE_LOOKUP` | Direct inquiry into the wording or clauses of a specific constitutional article. | *"What is the exact text of Article 32?"* |
| `CASE_LAW_QUERY` | Inquiries regarding Supreme Court rulings, facts, or verdicts. | *"What did the Supreme Court hold in Puttaswamy?"* |
| `CASE_COMPARISON` | Comparing ratios, doctrines, or shifts between two or more landmark judgments. | *"Compare the doctrine of personal liberty in Gopalan and Maneka Gandhi."* |
| `LEGAL_EXPLANATION` | Conceptual or doctrinal explanations (e.g. Basic Structure, Due Process). | *"Explain the doctrine of severability under Article 13."* |
| `RIGHTS_QUERY` | Questions regarding fundamental rights, civil liberties, or police search powers. | *"Can police search my house without a warrant under Article 21?"* |
| `AMENDMENT_QUERY` | Inquiries concerning Constitutional Amendment Acts and provisions modified. | *"What changes were introduced by the 42nd Amendment Act?"* |
| `PRECEDENT_QUERY` | Questions about overruling, judicial reconsiderations, or binding precedents. | *"Did Kesavananda Bharati overrule Golaknath?"* |
| `DEFINITION_QUERY` | Formal definitions of legal terms (e.g. 'State', 'Money Bill'). | *"What is the definition of 'State' under Article 12?"* |
| `CONSTITUTIONAL_PROCEDURE` | Institutional mechanisms (impeachment, emergency proclamation, judicial appointments). | *"What is the procedure for presidential impeachment under Article 61?"* |
| `MULTI_DOCUMENT_QUERY` | Harmonizing multiple statutes and constitutional articles simultaneously. | *"Synthesize the interplay between Articles 14, 19, and 21 (Golden Triangle)."* |
| `OUT_OF_SCOPE` | Non-legal, conversational, or unrelated inquiries (cooking, sports, coding). | *"How do I bake a chocolate cake with cherries?"* |

---

## 3. Classes in `nlp/intent_classifier.py`

### Class 1: `RuleBasedIntentClassifier`
- **Lines in Source**: [Lines 44–177](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/intent_classifier.py#L44-L177)
- **Purpose**: A deterministic regex and keyword rule engine. Serves as a transparent baseline and instant filter for obvious patterns.
- **Rule Pattern Lists**:
  - `COMPARISON_MARKERS`: `compare`, `versus`, `difference between`, `shift from`, `gopalan vs`.
  - `PROCEDURE_MARKERS`: `procedure to`, `process to`, `impeach`, `dissolve`, `promulgate`.
  - `PRECEDENT_MARKERS`: `overrule`, `set aside`, `binding precedent`, `earlier ruling`.
  - `DEFINITION_MARKERS`: `define`, `definition of`, `what is meant by`.
  - `AMENDMENT_MARKERS`: `\d{1,3}(?:st|nd|rd|th)? amendment`, `amendment act`.
  - `OUT_OF_SCOPE_MARKERS`: `recipe`, `pizza`, `weather`, `python`, `coding`, `cricket`, `movie`, `repair`.
- **Method `classify(query, entities)`**:
  - Evaluates patterns in strict priority order.
  - Returns a tuple: `(intent_label, confidence, rationale)`.

---

### Class 2: `MLIntentClassifier`
- **Lines in Source**: [Lines 179–292](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/intent_classifier.py#L179-L292)
- **Purpose**: A statistical Machine Learning text classification pipeline built with Scikit-learn.
- **Pipeline Architecture (`build_pipeline`)**:
  ```python
  Pipeline([
      ("tfidf", TfidfVectorizer(
          ngram_range=(1, 2),        # Unigrams + Bigrams
          min_df=1,
          sublinear_tf=True,         # Sublinear TF scaling (1 + log(tf))
          strip_accents="unicode"
      )),
      ("clf", LogisticRegression(
          C=2.0,                     # Regularization strength
          max_iter=1000,
          class_weight="balanced",   # Balanced class weights for minority classes
          random_state=42
      ))
  ])
  ```
- **Methods**:
  - `train_on_benchmark(benchmark_path)`: Fits the pipeline on the benchmark classification dataset (`data/benchmark/classification_queries.json`). Computes training accuracy and Macro-F1.
  - `predict(query)`: Predicts the intent string.
  - `predict_proba(query)`: Returns a probability dictionary across all classes.
  - `save_model(path)` / `load_model(path)`: Persists and deserializes the model via `pickle`.

---

### Class 3: `HybridIntentClassifier`
- **Lines in Source**: [Lines 294–430](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/intent_classifier.py#L294-L430)
- **Purpose**: The master orchestrator combining the Rule baseline and the ML classifier with an intelligent arbitration strategy and a **Spurious Out-of-Scope Guard**.

#### Arbitration Logic (`classify` method):
1. **Immediate Rule Decision**: If rule classifier detects an explicit `OUT_OF_SCOPE` keyword (e.g. `recipe`, `pizza`) with confidence $\ge 0.90$, it returns `OUT_OF_SCOPE` immediately.
2. **Spurious Out-of-Scope Guard** (Lines 372–377):
   - Machine learning models can occasionally produce false-positive `OUT_OF_SCOPE` predictions on rare legal phrasing.
   - If the ML model predicts `OUT_OF_SCOPE`, but the query actually contains recognized legal entities (`Article 21`, `Puttaswamy`) or the rule classifier identified a legal pattern, **the system overrides the ML error and protects the legal query**.
3. **Consensus**: If both models agree on the intent, it returns that label with `method="consensus"` and maximum confidence.
4. **High-Confidence ML**: If ML confidence $\ge 0.50$, ML prediction takes precedence.
5. **Fallback to Rule**: If ML is uncertain but the rule pattern has confidence $\ge 0.85$, rule intent takes precedence.

---

## 4. Actual Code Walkthrough

### Code Excerpt: Spurious Out-of-Scope Protection
```python
# Lines 366-377 in nlp/intent_classifier.py
has_legal_entities = bool(
    entities and any(
        entities.get(k) for k in ("ARTICLE", "CASE", "AMENDMENT", "RIGHT", "LEGAL_CONCEPT", "articles", "cases", "concepts")
    )
)

# Spurious out-of-scope guard: if ML says OUT_OF_SCOPE but query has legal entities or valid legal rule intent
if top_ml_label == "OUT_OF_SCOPE" and (has_legal_entities or (rule_label != "OUT_OF_SCOPE" and rule_conf >= 0.70)):
    final_intent = rule_label if rule_label != "OUT_OF_SCOPE" else "LEGAL_EXPLANATION"
    final_conf = max(rule_conf, 0.70)
    method = "rule"
    explanation = f"Protected legal query from spurious OUT_OF_SCOPE: {rule_exp}"
```
- **Explanation**: If an ML model mistakenly flags a complex legal question as out-of-scope, the presence of extracted entities (`Article`, `Case`, `Right`) forces the system to preserve the legal inquiry.
- **Why is this needed?**: Prevents erroneous abstentions on valid citizen questions.

---

## 5. Practical Example

### Query:
`"Compare the right to personal liberty in A.K. Gopalan and Maneka Gandhi"`

### Processing:
- `RuleBasedIntentClassifier`: Matches `"compare"` and `"A.K. Gopalan and Maneka"` $\to$ `CASE_COMPARISON` (Confidence $0.90$).
- `MLIntentClassifier`: Bigram `"compare the"` and terms `"gopalan"`, `"maneka"` $\to$ `CASE_COMPARISON` (Probability $0.94$).
- `HybridIntentClassifier`: Both models agree $\to$ Consensus!

### Output Dictionary:
```python
{
    "intent": "CASE_COMPARISON",
    "confidence": 0.94,
    "method": "consensus",
    "rule_intent": "CASE_COMPARISON",
    "ml_intent": "CASE_COMPARISON",
    "probabilities": {
        "CASE_COMPARISON": 0.9412,
        "CASE_LAW_QUERY": 0.0315,
        "RIGHTS_QUERY": 0.0152
    },
    "is_out_of_scope": False,
    "explanation": "Consensus between ML (0.94) and rule baseline (0.90): CASE_COMPARISON"
}
```

---

## 6. Connection to Other Files

- **Called by**: [`rag/pipeline.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/rag/pipeline.py) (Stage 5 intent classification).
- **Feeds into**: [`routing/query_router.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/routing/query_router.py) to decide the retrieval strategy.
- **Evaluated by**: [`evaluation/intent_eval.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/evaluation/intent_eval.py) across 5-fold Stratified Cross-Validation (Macro-F1 0.8485).
- **Proceed to**: [**`entity_recognition.md`**](entity_recognition.md) to inspect the 10-class Legal Named Entity Recognition engine.

