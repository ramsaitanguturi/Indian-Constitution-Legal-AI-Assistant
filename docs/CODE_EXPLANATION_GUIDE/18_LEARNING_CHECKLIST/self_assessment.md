# Self-Assessment & Viva Readiness Diagnostic: `18_LEARNING_CHECKLIST/self_assessment.md`

[Back to Learning Checklist Overview](learning_roadmap.md) • [Back to Main Index](../README.md)

---

## 1. Overview & Instructions

Take this 20-question self-assessment test after completing the [8-Day Learning Roadmap](learning_roadmap.md).
- **Target Score**: 18 / 20 correct answers indicates you are 100% prepared to ace your viva voce and code demonstration.
- **Rules**: Answer the questions on paper before checking the Answer Key at the end of this document.

---

## 2. Diagnostic Quiz (20 Questions)

### Question 1 (Architecture):
What are the four tiers of the Indian Constitution Legal AI Assistant?
- (A) Frontend, Backend, Database, Cloud
- (B) Storage Tier, NLP Pipeline, Hybrid Retrieval & Reranker, Grounded Generation & Safety Subsystem
- (C) Bi-Encoder, Cross-Encoder, LLM, Streamlit
- (D) Data Collection, Model Training, Fine-Tuning, API Deployment

### Question 2 (Corpus Size):
How many total legal documents are indexed in the primary corpus?
- (A) 100 documents
- (B) 395 documents
- (C) 886 documents
- (D) 7,470 documents

### Question 3 (Information Retrieval Math):
In Cormack Reciprocal Rank Fusion, what is the score contribution of a document ranked #1 in a list when $k=60$?
- (A) $1.0000$
- (B) $\frac{1}{60} \approx 0.01667$
- (C) $\frac{1}{61} \approx 0.01639$
- (D) $0.5000$

### Question 4 (Ablation Gain):
What was the relative gain in NDCG@10 achieved by the Full Pipeline (+ Cross-Encoder) over the BM25 Baseline?
- (A) +4.6%
- (B) +11.6%
- (C) +27.5%
- (D) +41.9%

### Question 5 (Entity Boosting):
What is the default additive boost awarded when a candidate document matches an extracted constitutional Article or Landmark Case?
- (A) $+0.05$
- (B) $+0.15$
- (C) $+0.50$
- (D) $+1.00$

### Question 6 (Parent-Child Indexing):
Why does the system search 300-character child passages but hydrate 1,200-character parent documents?
- (A) Because ChromaDB cannot store strings longer than 300 characters.
- (B) To decouple retrieval precision (sharp dense embeddings) from generation context (complete statutory provisos).
- (C) Because the cross-encoder only accepts 300 characters.
- (D) To reduce Python RAM usage during training.

### Question 7 (Verification & Hallucination):
What constitutes an `UNRETRIEVED_EVIDENCE_CITED` failure in `CitationValidator`?
- (A) The cited document does not exist anywhere in Indian law.
- (B) The document exists in `parent_store.json`, but was NOT part of the retrieved evidence pool for that specific query.
- (C) The document ID has a typo in its prefix.
- (D) The model failed to provide a year for the judgment.

### Question 8 (Natural Language Inference):
How does `NLIVerifier` detect polarity contradictions?
- (A) By calculating sentiment analysis scores.
- (B) By comparing positive deontic modals (*"permits", "mandates"*) against negative modals (*"prohibits", "shall not"*) on propositions sharing substantive legal tokens.
- (C) By calling the Google Gemini API with a zero-shot prompt.
- (D) By running TF-IDF cosine similarity.

### Question 9 (Safety Gating):
At what threshold does `AbstentionManager` trigger late abstention based on composite confidence?
- (A) Score $< 0.10$
- (B) Score $< 0.30$
- (C) Score $< 0.50$
- (D) Score $< 0.70$

### Question 10 (Zero Data Leakage):
How is zero data leakage guaranteed in the intent classification evaluation?
- (A) By using 10-fold cross-validation.
- (B) By physically separating data into `intent_train.json` and `intent_test.json`, fitting vectorizers strictly on train, and asserting 0% token overlap.
- (C) By using an un-finetuned BERT model.
- (D) By evaluating on the training set.

### Question 11 (ChromaDB Vector Math):
How does `DenseRetriever` convert ChromaDB Cosine Distance $d$ into Similarity score $s$?
- (A) $s = \frac{1}{d}$
- (B) $s = 1.0 - d$
- (C) $s = \sqrt{d}$
- (D) $s = e^{-d}$

### Question 12 (Chunking Logic):
When chunking a constitutional article, what prefix is attached to every child chunk?
- (A) Nothing, only raw clause text is stored.
- (B) Timestamp and author name.
- (C) Article number and title (e.g., `Article 21 - Protection of life and personal liberty [Clause (1)]: ...`).
- (D) The full text of the Preamble.

### Question 13 (Query Routing):
If a user query mentions two landmark Supreme Court decisions (e.g. *Kesavananda Bharati* and *Minerva Mills*), which strategy does `QueryRouter` select?
- (A) `ARTICLE_SEARCH`
- (B) `OUT_OF_SCOPE`
- (C) `COMPARISON_SEARCH`
- (D) `PROCEDURE_SEARCH`

### Question 14 (Neural Reranker):
Which transformer model powers the second-stage neural reranker?
- (A) `gpt-4o-mini`
- (B) `cross-encoder/ms-marco-MiniLM-L-6-v2`
- (C) `BAAI/bge-m3`
- (D) `bert-base-uncased`

### Question 15 (Confidence Signals):
How many independent signals are combined by `ConfidenceEstimator`?
- (A) 2 signals
- (B) 4 signals
- (C) 6 signals
- (D) 10 signals

### Question 16 (Central Legislation):
How many Central Acts and statutory sections are ingested from India Code?
- (A) 5 Acts / 200 Sections
- (B) 10 Acts / 500 Sections
- (C) 17 Acts / 1,975 Sections
- (D) 50 Acts / 10,000 Sections

### Question 17 (Automated Testing):
How many automated Pytest tests exist in the codebase, and what is their pass rate?
- (A) 50 tests (80% passing)
- (B) 120 tests (95% passing)
- (C) 319 tests (100% passing)
- (D) 500 tests (90% passing)

### Question 18 (Offline Resilience):
What happens if the internet disconnects during a live demonstration when using the generator?
- (A) The system crashes with an uncaught `ConnectionError`.
- (B) It enters an infinite loop waiting for network reconnection.
- (C) `GroundedGenerator` catches the exception and seamlessly falls back to `_synthesize_grounded_offline()`, pulling verified text from `parent_store.json`.
- (D) It outputs an empty screen.

### Question 19 (Entity Recognition):
How many legal entity classes are recognized by `LegalNER`?
- (A) 3 classes (Person, Org, Location)
- (B) 5 classes
- (C) 10 classes
- (D) 20 classes

### Question 20 (Master Result):
What is the final NDCG@10 of the full pipeline and its baseline comparison?
- (A) 0.5484 (matches baseline)
- (B) 0.6558 (+19.6% over baseline)
- (C) 0.7787 (+41.9% gain over BM25 = 0.5484)
- (D) 0.9999 (perfect score)

---

## 3. Answer Key & Detailed Explanations

| Question | Correct Answer | Detailed Technical Justification |
| :---: | :---: | :--- |
| **1** | **(B)** | The system is architected into Storage, NLP Pipeline, Hybrid Retrieval & Reranker, and Grounded Generation & Safety Subsystems. |
| **2** | **(C)** | The corpus contains exactly 886 documents (477 Articles/Schedules, 106 Amendments, 286 Judgments, 17 Central Acts). 7,470 is the child passage count. |
| **3** | **(C)** | Cormack's RRF formula is $\frac{1}{k + \text{rank}}$. For Rank 1 with $k=60$, the score is $\frac{1}{60 + 1} = \frac{1}{61} \approx 0.01639$. |
| **4** | **(D)** | BM25 baseline NDCG@10 is 0.5484; Full Pipeline reaches 0.7787. Relative gain is $\frac{0.7787 - 0.5484}{0.5484} \approx +41.9\%$. |
| **5** | **(B)** | `ENTITY_BOOST_WEIGHT` is configured in `config.py` as $0.150$ ($1.0 \times 0.15$ for Articles/Cases; $0.5 \times 0.15 = 0.075$ for Concepts). |
| **6** | **(B)** | Decouples vector embedding sharpness (small 300-char chunks) from generative context completeness (full 1,200-char parent articles). |
| **7** | **(B)** | An unretrieved citation exists in the database, but was NOT retrieved in the evidence prompt for that query—indicating the LLM hallucinated from parametric memory. |
| **8** | **(B)** | Compares positive vs negative deontic modals across propositions sharing substantive legal tokens (excluding generic legal stop-words). |
| **9** | **(B)** | `CONFIDENCE_ABSTENTION_THRESHOLD` is set to $0.30$ in `config.py`. Scores below 0.30 fall into the `VERY_LOW` band and are withheld. |
| **10** | **(B)** | Datasets are physically split into disjoint JSON files, feature extractors fit strictly on train, and `audit_intent_leakage.py` asserts 0% token overlap. |
| **11** | **(B)** | ChromaDB Cosine Distance is $d = 1 - \cos \theta$. In `DenseRetriever`, similarity is inverted as $s = 1.0 - d = \cos \theta$. |
| **12** | **(C)** | Attaching article number and title ensures that small child chunks never lose their statutory identity in dense embedding space. |
| **13** | **(C)** | When multiple case mentions are detected, `QueryRouter` activates `COMPARISON_SEARCH`, widening candidate pool to 35 and final top-$K$ to 6. |
| **14** | **(B)** | Second-stage reranker uses `cross-encoder/ms-marco-MiniLM-L-6-v2`. `BAAI/bge-m3` is the bi-encoder used for first-stage dense search. |
| **15** | **(C)** | 6 signals: Retrieval Strength, Evidence Count, Entity Alignment, Method Agreement, Citation Validity, and Evidence Coverage. |
| **16** | **(C)** | Exactly 17 Central Acts comprising 1,975 sections from India Code (CrPC, IPC, IEA, CPC, RPA, RTI, Citizenship Act, etc.). |
| **17** | **(C)** | Exactly 319 automated tests across 28 test modules in `tests/`, passing at 100%. |
| **18** | **(C)** | `GroundedGenerator` catches network/API exceptions and seamlessly executes `_synthesize_grounded_offline()`, guaranteeing 100% offline resilience. |
| **19** | **(C)** | 10 categories: `ARTICLE`, `CASE`, `SECTION`, `ACT`, `AMENDMENT`, `RIGHT`, `COURT`, `PERSON`, `LEGAL_CONCEPT`, `DATE`. |
| **20** | **(C)** | Full pipeline achieves an NDCG@10 of 0.7787, representing a +41.9% improvement over the BM25 baseline (0.5484). |

---

## 4. Score Self-Diagnosis

- **18 – 20 Correct**: **Outstanding!** You possess comprehensive, master-level understanding of the architecture, algorithms, and code. You are ready to ace your viva.
- **15 – 17 Correct**: **Good!** Review the specific sections in `07_RETRIEVAL_MODULE/` or `08_RAG_MODULE/` where you missed questions.
- **Below 15 Correct**: Follow the [8-Day Learning Roadmap](learning_roadmap.md) to systematically study the code and architecture guides.

