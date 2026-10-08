# NLP Capstone Upgrade Specification
## Indian Constitution Legal AI Assistant

> **Purpose:** This document is the implementation context for upgrading the existing repository into an NLP-focused B.Tech semester capstone.
>
> **Important:** Do NOT rebuild the project from scratch. Preserve the existing working RAG foundation and upgrade it systematically.
>
> **Chosen direction:** Specialized NLP Query Router + strong quantitative NLP/IR evaluation.
>
> **Target project title:**
>
> **Entity-Aware Hybrid Retrieval and Reranking Framework for Indian Constitutional Question Answering**
>
> The system should remain a practical legal QA application, but the academic contribution must be the NLP pipeline and experimental evaluation rather than the UI or an agentic architecture.

---

# 1. Current Project: What Must Be Preserved

The existing repository already contains a useful foundation. Preserve and improve these components instead of replacing them unnecessarily:

- Parent-child RAG architecture
- ChromaDB/vector retrieval
- Sentence-transformer embeddings
- BM25 lexical retrieval
- Reciprocal Rank Fusion (RRF)
- Legal metadata
- Constitutional article retrieval
- Case-law retrieval
- Source/citation display
- Streamlit interface
- Gemini/LLM generation
- Offline/fallback behavior where already implemented
- Existing tests that are still valid
- Existing modular backend structure

Do NOT spend the majority of the project on frontend redesign.

The capstone should become an **NLP/Information Retrieval research prototype**, not just a chatbot.

---

# 2. Target Final Architecture

Implement this architecture:

```text
                         USER QUERY
                             |
                             v
                  +-----------------------+
                  | Language Detection    |
                  +-----------+-----------+
                              |
                              v
                  +-----------------------+
                  | Query Preprocessing   |
                  +-----------+-----------+
                              |
                              v
                  +-----------------------+
                  | Legal NER             |
                  | + Entity Linking      |
                  +-----------+-----------+
                              |
                              v
                  +-----------------------+
                  | Intent Classification |
                  +-----------+-----------+
                              |
                              v
                  +-----------------------+
                  | Query Expansion       |
                  +-----------+-----------+
                              |
                 +------------+------------+
                 |                         |
                 v                         v
          +-------------+           +-------------+
          | BM25 Search |           | Dense Search|
          +------+------+           +------+------+
                 |                         |
                 +------------+------------+
                              |
                              v
                       RRF Fusion
                              |
                              v
                    Legal Entity Boost
                              |
                              v
                        Reranker
                              |
                              v
                     Top Evidence
                              |
                              v
                 Parent Context Recovery
                              |
                              v
                    Grounded Generator
                              |
                              v
                  Citation / Evidence Check
                              |
                              v
                    Confidence / Abstention
                              |
                              v
                           ANSWER
```

The **core academic contribution** is:

```text
Legal Entity Extraction
        +
Intent Classification
        +
Query Expansion
        +
Hybrid Lexical/Semantic Retrieval
        +
RRF
        +
Legal Entity-Aware Ranking
        +
Quantitative Evaluation
```

---

# 3. Important Architectural Decision

## Do NOT create a large autonomous multi-agent architecture.

The previous implementation contains Article Agent, Case Agent, and Explanation Agent concepts.

For the capstone, treat these as **specialized query-routing modules**, not autonomous agents.

Use terminology such as:

- Query Router
- Intent Classifier
- Article Retrieval Module
- Case Retrieval Module
- Explanation Module

Avoid making "multi-agent AI" the central contribution.

The NLP pipeline is the central contribution.

---

# 4. Project Goals

The upgraded project must demonstrate that:

1. Legal entities can be extracted from natural-language queries.
2. Legal queries can be classified into meaningful intents.
3. Query expansion improves legal retrieval.
4. Hybrid BM25 + dense retrieval performs better than either method alone.
5. RRF improves candidate retrieval.
6. Legal entity information improves ranking.
7. A reranker improves top-k relevance.
8. Parent-child retrieval preserves sufficient legal context.
9. The system can refuse to answer when evidence is insufficient.
10. The system can provide source-backed answers.
11. Each major NLP/retrieval component can be evaluated independently.

---

# 5. Repository Structure

Refactor toward this structure:

```text
Indian-Constitution-Legal-AI-Assistant/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── .env.example
│
├── data/
│   ├── constitution/
│   │   ├── articles.json
│   │   ├── parts.json
│   │   ├── schedules.json
│   │   └── amendments.json
│   │
│   ├── judgments/
│   │   ├── supreme_court/
│   │   └── landmark_cases/
│   │
│   ├── benchmark/
│   │   ├── retrieval_queries.json
│   │   ├── classification_queries.json
│   │   ├── ner_queries.json
│   │   └── qa_queries.json
│   │
│   └── annotations/
│       ├── ner_annotations.json
│       └── relevance_labels.json
│
├── nlp/
│   ├── __init__.py
│   ├── preprocessing.py
│   ├── legal_ner.py
│   ├── entity_linking.py
│   ├── intent_classifier.py
│   ├── query_expansion.py
│   └── language_detection.py
│
├── retrieval/
│   ├── __init__.py
│   ├── bm25_retriever.py
│   ├── dense_retriever.py
│   ├── rrf.py
│   ├── entity_boost.py
│   ├── reranker.py
│   └── hybrid_retriever.py
│
├── rag/
│   ├── __init__.py
│   ├── ingestion.py
│   ├── chunking.py
│   ├── parent_child.py
│   ├── context_builder.py
│   ├── generator.py
│   ├── citation_validator.py
│   └── confidence.py
│
├── routing/
│   ├── __init__.py
│   └── query_router.py
│
├── evaluation/
│   ├── __init__.py
│   ├── retrieval_eval.py
│   ├── ner_eval.py
│   ├── classification_eval.py
│   ├── qa_eval.py
│   ├── metrics.py
│   └── report.py
│
├── experiments/
│   ├── experiment_01_bm25.py
│   ├── experiment_02_dense.py
│   ├── experiment_03_hybrid.py
│   ├── experiment_04_rrf.py
│   ├── experiment_05_entity_boost.py
│   ├── experiment_06_reranker.py
│   ├── experiment_07_ner.py
│   └── experiment_08_intent.py
│
├── scripts/
│   ├── build_corpus.py
│   ├── ingest_data.py
│   ├── create_benchmark.py
│   └── run_all_evaluations.py
│
├── tests/
│   ├── test_ner.py
│   ├── test_intent.py
│   ├── test_entity_linking.py
│   ├── test_retrieval.py
│   ├── test_reranker.py
│   ├── test_chunking.py
│   ├── test_citations.py
│   └── test_abstention.py
│
└── docs/
    ├── architecture.md
    ├── dataset.md
    ├── evaluation.md
    ├── experiments.md
    └── research_contribution.md
```

Do not force every file to be created if an existing file already performs the same responsibility. Refactor existing modules where appropriate.

---

# 6. Dataset Upgrade — CRITICAL

The existing sample corpus is too small for a capstone.

Do NOT delete the sample data immediately. Keep it as a small test fixture if useful.

Build a substantially larger legal corpus.

## Constitution corpus

Target:

- Complete constitutional Articles/provisions available in the selected authoritative corpus
- Parts
- Schedules
- Important constitutional amendments
- Structured article/clause metadata

The ingestion system should preserve:

```json
{
  "document_id": "...",
  "document_type": "constitution_article",
  "article_number": "21",
  "part": "III",
  "title": "...",
  "text": "...",
  "source": "...",
  "source_date": "...",
  "version": "..."
}
```

## Case-law corpus

Target approximately:

**100–300 judgments/case documents**

A smaller curated corpus is acceptable if the documents are high quality and well annotated, but 5 judgments is not sufficient.

Prioritize cases related to constitutional rights, amendments, judicial review, fundamental rights, privacy, equality, speech, liberty, federalism, and separation of powers.

Case metadata should include, where available:

```json
{
  "document_id": "...",
  "document_type": "judgment",
  "case_name": "...",
  "citation": "...",
  "court": "Supreme Court of India",
  "year": 1973,
  "date": "...",
  "judges": [],
  "bench_size": 13,
  "articles_referred": [],
  "acts_referred": [],
  "facts": "...",
  "issues": [],
  "arguments": [],
  "ratio_decidendi": "...",
  "judgment": "...",
  "verdict": "...",
  "precedents_followed": [],
  "precedents_overruled": [],
  "keywords": [],
  "source": "..."
}
```

Do not fabricate metadata. Missing metadata must be represented as null/empty fields.

---

# 7. Data Provenance

Every legal document must have provenance metadata.

At minimum:

```text
source
source_type
retrieval_date
document_version
document_id
```

The project documentation must explain:

```text
Source
  -> Collection
  -> Cleaning
  -> Normalization
  -> Structure extraction
  -> Chunking
  -> Embedding/indexing
```

The system must not silently alter legal text.

Keep original text and processed text separately when practical.

---

# 8. Structure-Aware Legal Chunking

The current character-based chunking is only a baseline.

Implement structure-aware chunking.

## Constitution

Prefer:

```text
Article
  -> Clause
      -> Sub-clause
```

Do not blindly split legal provisions in the middle of a clause when structure information is available.

## Judgments

Prefer sections such as:

```text
Case
  -> Facts
  -> Issues
  -> Arguments
  -> Reasoning
  -> Ratio Decidendi
  -> Judgment
  -> Precedents
```

If section labels are unavailable, use robust fallback chunking.

## Metadata inheritance

Every child chunk must inherit parent metadata.

Example:

```json
{
  "child_id": "...",
  "parent_id": "...",
  "document_type": "judgment",
  "case_name": "...",
  "year": 1973,
  "section": "ratio_decidendi",
  "text": "..."
}
```

---

# 9. Correct the Token/Character Documentation

Do not describe:

```text
300 characters
```

as:

```text
300 tokens
```

They are different.

Document all chunking parameters accurately:

```text
chunking_unit
chunk_size
overlap
tokenizer
minimum_chunk_size
maximum_chunk_size
```

---

# 10. Legal NER Module

Create:

```text
nlp/legal_ner.py
```

The system must extract at least:

```text
ARTICLE
CASE
PERSON
COURT
LEGAL_CONCEPT
RIGHT
AMENDMENT
ACT
SECTION
DATE
```

Example:

Input:

```text
What did Puttaswamy decide about privacy under Article 21?
```

Expected normalized output:

```json
{
  "ARTICLE": ["Article 21"],
  "CASE": ["Puttaswamy"],
  "LEGAL_CONCEPT": ["privacy"],
  "RIGHT": ["right to privacy"]
}
```

## Implementation

Use a hybrid design:

```text
Rule-based extraction
+
NER model where practical
+
Entity normalization/linking
```

Do not remove the existing rule-based patterns. Reuse them as part of the hybrid system.

## Evaluation

Create annotated NER examples and calculate:

- Precision
- Recall
- F1

Report both per-entity and overall scores where possible.

---

# 11. Entity Linking

Create:

```text
nlp/entity_linking.py
```

Map extracted mentions to canonical legal entities.

Example:

```text
"Art 21"
"Article 21"
"Art. 21"
```

should map to:

```text
ARTICLE_21
```

Similarly:

```text
"Puttaswamy"
"Justice K.S. Puttaswamy"
"Puttaswamy case"
```

should map to one canonical case identifier where unambiguous.

The entity linker should use the corpus metadata rather than a hardcoded list wherever possible.

---

# 12. Intent Classification

Create:

```text
nlp/intent_classifier.py
```

Use these initial intent classes:

```text
ARTICLE_LOOKUP
CASE_LAW_QUERY
CASE_COMPARISON
LEGAL_EXPLANATION
RIGHTS_QUERY
AMENDMENT_QUERY
PRECEDENT_QUERY
DEFINITION_QUERY
CONSTITUTIONAL_PROCEDURE
MULTI_DOCUMENT_QUERY
```

Allow an:

```text
UNKNOWN / OUT_OF_SCOPE
```

class.

---

# 13. Intent Classifier Strategy

Implement a baseline first.

### Baseline

Keyword/rule-based classifier.

Then implement a real ML classifier.

Recommended progression:

```text
Rule baseline
     ↓
TF-IDF + Logistic Regression
     ↓
Transformer-based classifier if dataset size supports it
```

Do not use a complex model without enough labeled data.

The final report must compare at least:

```text
Rule baseline
vs
ML classifier
```

Metrics:

- Accuracy
- Macro Precision
- Macro Recall
- Macro F1
- Confusion Matrix

Macro F1 is particularly important because class distributions may be uneven.

---

# 14. Query Expansion

Create:

```text
nlp/query_expansion.py
```

The query expansion module should map natural language to legal terminology.

Example:

```text
"Can the government take away privacy?"
```

may expand to concepts such as:

```text
privacy
right to privacy
Article 21
personal liberty
Puttaswamy
```

Do not blindly append unrelated terms.

Expansion must be:

- deterministic where possible
- traceable
- testable
- based on entity linking, legal terminology, or semantic similarity

The final system should be able to show the expanded terms for debugging/evaluation.

---

# 15. Language Detection

Create:

```text
nlp/language_detection.py
```

At minimum, identify:

```text
English
Unknown
```

If multilingual support is implemented, support additional languages deliberately.

Do not make multilingual support a blocking requirement for the first release.

---

# 16. BM25 Retrieval

Create or refactor:

```text
retrieval/bm25_retriever.py
```

It must provide a clean API such as:

```python
retrieve(query, top_k=20)
```

Return structured results:

```python
{
    "document_id": "...",
    "chunk_id": "...",
    "score": 0.0,
    "rank": 1,
    "metadata": {...}
}
```

Do not return only raw strings.

---

# 17. Dense Retrieval

Create/refactor:

```text
retrieval/dense_retriever.py
```

Use the existing embedding infrastructure where appropriate.

It must expose the same result interface as BM25.

This is necessary so the evaluation framework can compare retrieval methods consistently.

---

# 18. RRF

Keep the existing RRF implementation, but isolate it:

```text
retrieval/rrf.py
```

Implement:

```python
fuse(result_lists, k=...)
```

Make RRF parameters configurable.

Do not hardcode experimental parameters.

---

# 19. Entity-Aware Ranking

Create:

```text
retrieval/entity_boost.py
```

After RRF, increase ranking priority when retrieved metadata matches extracted query entities.

Example:

```text
Query:
Article 21 privacy Puttaswamy

Retrieved:
Article 21 -> strong entity match
Puttaswamy -> strong entity match
Unrelated Article 32 -> weaker match
```

The boost must be:

- configurable
- explainable
- independently evaluable

Do not allow entity boosting to completely override relevance.

---

# 20. Reranker

Create:

```text
retrieval/reranker.py
```

Add a cross-encoder or other appropriate reranking model.

Pipeline:

```text
BM25
  +
Dense
  ↓
RRF
  ↓
20-50 candidates
  ↓
Reranker
  ↓
Top 5-10
```

The exact candidate size must be configurable.

Do not rerank the entire corpus.

---

# 21. Hybrid Retriever

Create:

```text
retrieval/hybrid_retriever.py
```

It should orchestrate:

```text
Query
 -> BM25
 -> Dense
 -> RRF
 -> Entity Boost
 -> Reranker
 -> Top K
```

It should expose configuration switches so experiments can disable individual components.

Example concept:

```python
HybridRetriever(
    use_bm25=True,
    use_dense=True,
    use_rrf=True,
    use_entity_boost=True,
    use_reranker=True
)
```

This is required for ablation experiments.

---

# 22. Query Router

Create:

```text
routing/query_router.py
```

The router should call:

```text
preprocessing
    ↓
NER
    ↓
entity linking
    ↓
intent classification
    ↓
query expansion
    ↓
retrieval
```

The router should return a structured query object.

Example:

```json
{
  "original_query": "...",
  "language": "en",
  "intent": "RIGHTS_QUERY",
  "entities": {
    "ARTICLE": ["Article 21"],
    "CASE": ["Puttaswamy"],
    "LEGAL_CONCEPT": ["privacy"]
  },
  "expanded_query": "...",
  "retrieval_query": "..."
}
```

---

# 23. Parent-Child RAG

Keep the existing parent-child architecture.

Required behavior:

```text
Child chunks
    ↓
retrieval
    ↓
top relevant children
    ↓
group by parent
    ↓
recover appropriate parent context
    ↓
context construction
```

Avoid passing huge unrelated parent documents to the LLM.

Context selection must remain relevance-aware.

---

# 24. Grounded Generation

Keep the existing LLM generation layer.

Improve the prompt to explicitly require:

1. Answer only from retrieved evidence.
2. Do not invent constitutional provisions.
3. Do not invent case facts.
4. Clearly distinguish retrieved facts from explanation.
5. Include source references.
6. State insufficient evidence when evidence is inadequate.

Do not claim "zero hallucination".

Use language such as:

> Evidence-grounded legal QA prototype.

---

# 25. Citation Validation

Create:

```text
rag/citation_validator.py
```

The validator should check whether cited sources actually exist in the retrieved evidence.

At minimum:

```text
Generated citation
       ↓
Does source ID exist?
       ↓
Does source belong to retrieved context?
       ↓
Valid / Invalid
```

If possible, also check whether the cited passage has textual support.

---

# 26. Confidence and Abstention

Create:

```text
rag/confidence.py
```

The system must not answer confidently when retrieval quality is poor.

Implement a configurable threshold.

Example:

```text
High retrieval confidence
    -> answer

Low retrieval confidence
    -> abstain / request clarification
```

Possible output:

```text
"I could not find sufficient evidence in the constitutional
knowledge base to answer this question reliably."
```

The exact threshold must be configurable and evaluated.

---

# 27. Out-of-Scope Detection

The system should distinguish:

```text
In-domain constitutional question
```

from:

```text
Unrelated question
```

Example:

```text
"What is Article 21?"
```

-> in scope.

```text
"Who won yesterday's cricket match?"
```

-> out of scope.

This should be handled before expensive retrieval where practical.

---

# 28. Benchmark Dataset

This is a mandatory capstone component.

Create:

```text
data/benchmark/
```

with a manually curated evaluation set.

Target:

### Retrieval benchmark

At least:

**200 queries**

Each query must have:

```json
{
  "query_id": "Q001",
  "query": "...",
  "relevant_document_ids": ["..."],
  "relevant_chunk_ids": ["..."],
  "intent": "RIGHTS_QUERY"
}
```

### Intent benchmark

Target:

**200–500 labeled queries**

Balanced across the defined intent classes as much as practical.

### NER benchmark

Target:

**100+ annotated queries**

with entity spans and labels.

### QA benchmark

Target:

**100+ questions**

with reference evidence and expected answer points.

A smaller benchmark can be used if annotation time becomes a constraint, but do not eliminate evaluation entirely.

---

# 29. Data Splitting

For supervised NLP components, avoid leakage.

Use:

```text
Train
Validation
Test
```

Do not create test examples by simply paraphrasing training examples without controlling leakage.

For retrieval evaluation, keep a fixed held-out benchmark.

Document the split strategy.

---

# 30. Retrieval Evaluation

Create:

```text
evaluation/retrieval_eval.py
```

Calculate at minimum:

```text
Hit Rate@5
Hit Rate@10
Recall@5
Recall@10
MRR
NDCG@5
NDCG@10
```

Use the same benchmark for every retrieval configuration.

---

# 31. Retrieval Experiments

Implement the following experiments:

## Experiment 1

```text
BM25 only
```

## Experiment 2

```text
Dense only
```

## Experiment 3

```text
BM25 + Dense
```

## Experiment 4

```text
BM25 + Dense + RRF
```

## Experiment 5

```text
RRF + Entity Boost
```

## Experiment 6

```text
RRF + Entity Boost + Reranker
```

The final table should compare:

```text
Method
Recall@5
Recall@10
MRR
NDCG@5
NDCG@10
```

---

# 32. NER Evaluation

Create:

```text
evaluation/ner_eval.py
```

Report:

```text
Overall Precision
Overall Recall
Overall F1
```

and:

```text
ARTICLE F1
CASE F1
COURT F1
PERSON F1
LEGAL_CONCEPT F1
RIGHT F1
...
```

This is important because Legal NER is one of the project's NLP contributions.

---

# 33. Intent Classification Evaluation

Create:

```text
evaluation/classification_eval.py
```

Report:

```text
Accuracy
Macro Precision
Macro Recall
Macro F1
Confusion Matrix
```

Compare:

```text
Rule baseline
vs
ML classifier
```

---

# 34. QA Evaluation

Create:

```text
evaluation/qa_eval.py
```

Evaluate:

```text
Answer Relevance
Groundedness
Citation Accuracy
Evidence Coverage
```

Automated metrics may include:

```text
ROUGE
BERTScore
```

but these should not be the only evaluation.

Use human evaluation for a small sample.

Recommended human evaluation dimensions:

```text
Correctness: 1-5
Relevance: 1-5
Groundedness: 1-5
Citation usefulness: 1-5
```

---

# 35. Ablation Study

This is mandatory.

Remove one component at a time.

Example:

```text
Full system
    ↓
remove NER
    ↓
measure performance

Full system
    ↓
remove entity boost
    ↓
measure performance

Full system
    ↓
remove reranker
    ↓
measure performance

Full system
    ↓
remove dense retrieval
    ↓
measure performance
```

The report should show which components actually contribute.

Do not claim a component improves performance until the experiment demonstrates it.

---

# 36. Experiment Reproducibility

Every experiment should have:

```text
configuration
dataset version
model name
retrieval parameters
random seed where applicable
metrics
timestamp
output result
```

Save results as JSON/CSV.

Example:

```text
experiments/results/
├── retrieval_results.csv
├── ner_results.json
├── classification_results.json
└── qa_results.json
```

---

# 37. Visualization

Create plots/tables for:

1. Recall@K comparison
2. MRR comparison
3. NDCG comparison
4. NER F1 by entity type
5. Intent confusion matrix
6. Ablation results

These can be displayed in the Streamlit evaluation page or generated by evaluation scripts.

---

# 38. Streamlit UI Changes

Keep the existing UI.

Add an optional:

## NLP Analysis panel

Show:

```text
Detected Intent
Extracted Entities
Linked Entities
Expanded Query
Retrieval Method
Top Sources
Confidence
```

Example:

```text
Intent:
RIGHTS_QUERY

Entities:
ARTICLE → Article 21
CASE → Puttaswamy
CONCEPT → Privacy

Expanded Query:
privacy right Article 21 Puttaswamy personal liberty

Retrieved Evidence:
1. Article 21
2. Puttaswamy
3. Maneka Gandhi
```

This is useful for demonstrating the NLP contribution to examiners.

---

# 39. Evaluation Dashboard

Add an evaluation page only after the backend evaluation works.

Display:

```text
Retrieval Performance
---------------------
BM25           0.xx
Dense          0.xx
Hybrid         0.xx
Hybrid + NER   0.xx
Final          0.xx
```

Do not hardcode values.

Read them from saved experiment results.

---

# 40. Configuration

Move tunable parameters into configuration.

Examples:

```text
EMBEDDING_MODEL
RERANKER_MODEL
TOP_K_BM25
TOP_K_DENSE
RRF_K
RERANK_TOP_K
FINAL_TOP_K
ENTITY_BOOST_WEIGHT
ABSTENTION_THRESHOLD
CHUNK_SIZE
CHUNK_OVERLAP
```

Do not scatter magic numbers throughout the code.

---

# 41. Testing Requirements

Add tests for:

### NER

- Article extraction
- Case extraction
- Concept extraction
- Multiple entities

### Entity linking

- Article aliases
- Case aliases
- Unknown entities

### Intent classifier

- Each intent
- Unknown intent

### Retrieval

- BM25 result format
- Dense result format
- RRF
- entity boost
- reranker

### RAG

- parent recovery
- citation validation
- abstention

### Regression

Existing working functionality must continue to work.

---

# 42. Error Handling

The system must gracefully handle:

- empty query
- extremely long query
- missing vector database
- unavailable LLM
- missing metadata
- malformed documents
- no retrieval results
- low-confidence retrieval
- unknown entities
- unsupported intent

Do not allow a malformed document to crash the entire ingestion process.

---

# 43. Logging

Add structured logging for development/debugging.

Useful fields:

```text
query
intent
entities
retrieval_method
retrieved_document_ids
retrieval_scores
reranker_scores
confidence
citation_status
latency
```

Do not log API keys or secrets.

---

# 44. Performance

Do not sacrifice retrieval quality just for speed.

Still track:

```text
NER latency
classification latency
BM25 latency
dense retrieval latency
reranking latency
LLM latency
total latency
```

A performance table can be included as an optional engineering evaluation.

---

# 45. README Rewrite

Rewrite the README around the research contribution.

Recommended sections:

```text
1. Project Overview
2. Problem Statement
3. Research Motivation
4. Research Questions
5. Contributions
6. System Architecture
7. NLP Pipeline
8. Dataset
9. Legal NER
10. Intent Classification
11. Query Expansion
12. Hybrid Retrieval
13. RRF
14. Entity-Aware Ranking
15. Reranking
16. Parent-Child RAG
17. Evaluation Methodology
18. Experimental Results
19. Limitations
20. Future Work
21. Installation
22. Usage
23. Project Structure
24. Reproducibility
```

Do not describe the system as "zero hallucination" or "100% accurate".

---

# 46. Research Contributions

The final README/paper should identify contributions clearly.

Potential contributions:

### Contribution 1

Hybrid lexical-semantic retrieval for Indian constitutional documents.

### Contribution 2

Legal entity-aware retrieval using extracted constitutional entities.

### Contribution 3

Intent-aware legal query processing.

### Contribution 4

Structure-aware parent-child legal retrieval.

### Contribution 5

Quantitative comparison of BM25, dense, hybrid, RRF, entity-aware, and reranked retrieval.

### Contribution 6

Evidence-grounded legal QA with citation validation and abstention.

Only claim contributions that are actually implemented and experimentally demonstrated.

---

# 47. Research Questions

Use these as the project's primary research questions:

### RQ1

Does hybrid lexical + dense retrieval outperform individual BM25 and dense retrieval for Indian constitutional queries?

### RQ2

Does legal entity extraction improve retrieval performance?

### RQ3

Does entity-aware ranking improve MRR/NDCG over RRF alone?

### RQ4

Does reranking improve the relevance of the final top-k evidence?

### RQ5

How accurately can the system classify different types of constitutional legal queries?

### RQ6

How accurately can legal entities be extracted from natural-language constitutional questions?

---

# 48. Important Scope Restriction

Do not turn the project into a generic legal chatbot.

The primary scope is:

```text
Indian Constitution
+
Indian constitutional jurisprudence
+
NLP question understanding
+
legal information retrieval
+
evidence-grounded QA
```

Do not add unrelated domains unless they directly support the research.

---

# 49. What NOT to do

Do NOT:

- rebuild the whole project from scratch
- remove the existing RAG system without reason
- focus heavily on UI
- add unnecessary autonomous agents
- add voice/image features
- add random AI features
- claim zero hallucination
- fabricate legal data
- fabricate evaluation scores
- hardcode experimental results
- call a keyword list "machine-learning NER"
- call a keyword router a transformer classifier
- report only LLM-generated evaluation
- use the same examples for development and final test without controlling leakage

---

# 50. Implementation Order

Implement in this exact priority order.

## Phase 1 — Repository audit

1. Run existing application.
2. Run existing tests.
3. Document current behavior.
4. Identify reusable modules.
5. Do not delete working functionality.

## Phase 2 — Corpus

6. Build/ingest larger Constitution corpus.
7. Build/ingest case corpus.
8. Add provenance metadata.
9. Implement structure-aware chunking.
10. Rebuild indexes.

## Phase 3 — NLP

11. Implement preprocessing.
12. Implement hybrid Legal NER.
13. Implement entity linking.
14. Implement intent classification baseline.
15. Implement ML intent classifier.
16. Implement query expansion.

## Phase 4 — Retrieval

17. Standardize BM25 API.
18. Standardize dense API.
19. Refactor RRF.
20. Implement entity-aware boost.
21. Implement reranker.
22. Build configurable hybrid retriever.

## Phase 5 — RAG

23. Integrate query router.
24. Integrate parent-child context recovery.
25. Improve grounded generation.
26. Add citation validation.
27. Add confidence and abstention.

## Phase 6 — Evaluation

28. Build benchmark dataset.
29. Build retrieval evaluation.
30. Build NER evaluation.
31. Build intent evaluation.
32. Build QA evaluation.
33. Run baseline experiments.
34. Run ablation experiments.
35. Save results.

## Phase 7 — UI and documentation

36. Add NLP analysis panel.
37. Add evaluation dashboard.
38. Rewrite README.
39. Write architecture documentation.
40. Write experiment documentation.
41. Prepare final report.

---

# 51. Definition of Done

The project is considered capstone-ready only when all of the following are true:

## Dataset

- [ ] Constitution corpus substantially expanded
- [ ] At least ~100 case documents or a justified curated alternative
- [ ] Provenance metadata exists
- [ ] Reproducible ingestion exists

## NLP

- [ ] Legal NER implemented
- [ ] Entity linking implemented
- [ ] Intent classifier implemented
- [ ] Query expansion implemented
- [ ] NER benchmark exists
- [ ] Intent benchmark exists

## Retrieval

- [ ] BM25 works independently
- [ ] Dense retrieval works independently
- [ ] RRF works
- [ ] Entity boost works
- [ ] Reranker works
- [ ] Hybrid retriever is configurable

## RAG

- [ ] Parent-child retrieval works
- [ ] Grounded generation works
- [ ] Citation validation works
- [ ] Confidence/abstention works

## Evaluation

- [ ] Retrieval benchmark exists
- [ ] Retrieval metrics implemented
- [ ] NER metrics implemented
- [ ] Intent metrics implemented
- [ ] QA evaluation implemented
- [ ] Ablation study completed
- [ ] Results saved reproducibly

## Documentation

- [ ] README updated
- [ ] Architecture documented
- [ ] Dataset documented
- [ ] Experiments documented
- [ ] Research questions documented
- [ ] Limitations documented
- [ ] No fabricated claims/results

---

# 52. Expected Final Demonstration

The final demo should show at least these cases.

## Demo 1 — Article query

```text
What is Article 21 of the Constitution?
```

Show:

- intent
- Article entity
- retrieved evidence
- answer
- citation

## Demo 2 — Natural language legal query

```text
Can the government take away my right to privacy?
```

Show:

- entity extraction
- query expansion
- Article 21 retrieval
- Puttaswamy retrieval
- grounded answer

## Demo 3 — Case query

```text
What did Kesavananda Bharati establish?
```

Show:

- case entity
- case retrieval
- relevant constitutional provisions
- answer

## Demo 4 — Multi-document query

```text
How are Kesavananda Bharati and Minerva Mills related?
```

Show:

- multiple case entities
- multi-document retrieval
- comparison intent
- evidence from both cases

## Demo 5 — Out-of-domain query

```text
Who won yesterday's cricket match?
```

Show:

```text
Out of scope
```

## Demo 6 — Insufficient evidence

Provide a question that is not sufficiently supported by the corpus.

Show:

```text
Insufficient evidence
```

This is a key demonstration of responsible retrieval-based QA.

---

# 53. Final Academic Positioning

The project should NOT be presented as:

> "A chatbot using Gemini and RAG."

It should be presented as:

> **An NLP-based legal question answering system that investigates whether legal entity-aware hybrid retrieval improves Indian constitutional document retrieval and evidence-grounded question answering.**

The LLM is a component.

The research is:

```text
NLP
+
Information Retrieval
+
Legal Entity Recognition
+
Intent Classification
+
Hybrid Retrieval
+
Reranking
+
Evaluation
```

---

# 54. Final Target Architecture Summary

```text
USER
 |
 v
Preprocessing
 |
 v
Legal NER
 |
 v
Entity Linking
 |
 v
Intent Classification
 |
 v
Query Expansion
 |
 +----------------------+
 |                      |
 v                      v
BM25                 Dense Retrieval
 |                      |
 +----------+-----------+
            |
            v
       RRF Fusion
            |
            v
     Entity-Aware Boost
            |
            v
        Reranker
            |
            v
       Top Evidence
            |
            v
 Parent Context Recovery
            |
            v
     Grounded Generator
            |
            v
   Citation Validation
            |
            v
 Confidence / Abstention
            |
            v
         ANSWER
```

---

# 55. One Critical Instruction for Implementation

**Do not implement everything in one pass.**

Work incrementally.

After each major phase:

```text
implement
→ run tests
→ run application
→ verify behavior
→ commit changes
→ move to next phase
```

Existing working functionality must not be broken just to introduce a new module.

If a new ML component is unavailable or its dataset is insufficient, retain a clearly documented baseline rather than adding a fake/placeholder implementation.

The final repository must contain **real implementations and real experimental results**, not placeholder files.

---

# 56. Final Success Criterion

The final project should allow the team to answer these questions in a viva:

1. Why is BM25 useful for legal retrieval?
2. Why is dense retrieval useful?
3. Why combine them?
4. What is RRF?
5. Why is legal NER useful?
6. How does entity linking work?
7. Why is intent classification required?
8. Why is query expansion useful?
9. Why is reranking necessary?
10. Why use parent-child RAG?
11. How did you construct your benchmark?
12. What is Recall@K?
13. What is MRR?
14. What is NDCG?
15. Why did your final model outperform the baselines?
16. What happens when NER is removed?
17. What happens when dense retrieval is removed?
18. What happens when reranking is removed?
19. How do you detect insufficient evidence?
20. How do you prevent unsupported answers?
21. What are the limitations?
22. What is your actual NLP contribution?

If the final system and experiments can answer these questions with measured evidence, the project is suitable for an NLP B.Tech semester capstone.

---

# 57. Do Not Invent Results

This is mandatory.

Until experiments are actually run, use:

```text
TBD
```

or:

```text
To be evaluated
```

Never put invented values such as:

```text
Recall@10 = 94.7%
F1 = 96.2%
```

The numbers must come from the evaluation scripts.

