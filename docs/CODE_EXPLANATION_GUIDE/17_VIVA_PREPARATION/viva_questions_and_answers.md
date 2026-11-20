# Master Viva Questions and Answers (80+ Questions): `17_VIVA_PREPARATION/viva_questions_and_answers.md`

[Back to Viva Preparation Overview](code_demonstration_script.md) • [Back to Main Index](../README.md)

---

## Category 1: Project Motivation, Problem Statement & Legal Domain

### Q1: What is the core objective of your project?
- **Short Answer**: To build an entity-aware, hybrid retrieval-augmented generation assistant for Indian Constitutional Law that eliminates legal hallucinations, solves statutory anchor confusion, and achieves provable citation validity.
- **Detailed Answer**: Laypersons and law students struggle to query constitutional law due to vocabulary mismatch and complex cross-references between the Constitution, amendments, judicial precedents, and central acts like CrPC. Generic LLMs hallucinate non-existent articles and invert judicial holdings. Our assistant combines sparse BM25, 1024-d dense BGE-M3 vectors, Cormack RRF fusion ($k=60$), statutory entity boosting (+0.15), cross-encoder neural reranking, and proposition-level NLI verification to achieve an NDCG@10 of 0.7787 with 100% citation validity.

### Q2: Why is Indian Constitutional Law particularly challenging for standard AI?
- **Short Answer**: Because of discrete alphanumeric statutory numbering, clause-level qualifications, evolving amendments, and binding judicial precedents that alter statutory interpretation.
- **Detailed Answer**: First, the Constitution has alphanumeric insertions (Article 21 vs 21A) where an extra letter denotes a completely distinct fundamental right. Second, clauses contain negative provisos (*"except according to procedure established by law"*). Third, common law doctrine dictates that Supreme Court judgments (e.g. *Maneka Gandhi*, *Puttaswamy*) define the operational scope of statutes. Dense vectors often confuse articles because judicial vocabulary is shared across Part III.

### Q3: What is "Statutory Anchor Confusion"?
- **Short Answer**: The failure of dense vector models to distinguish between discrete statutory provisions that share similar rhetorical vocabulary.
- **Detailed Answer**: In embedding space, Article 21 (Personal Liberty) and Article 19 (Freedom of Speech) have high cosine similarity because both discuss fundamental rights, state restrictions, and individual freedoms. A dense retriever frequently retrieves Article 19 for an Article 21 query. We solve this through our `Statutory Entity Boost` (+0.150 additive score when candidate metadata matches extracted query entities).

### Q4: Why is fine-tuning an LLM insufficient compared to RAG?
- **Short Answer**: Fine-tuning bakes knowledge into parametric weights, which still hallucinate, cannot cite sources verifiably, and require costly retraining whenever amendments are enacted.
- **Detailed Answer**: Fine-tuning adjusts model weights but does not eliminate parametric hallucination. A fine-tuned model cannot provide dynamic, auditable provenance links to specific paragraphs. In contrast, our RAG framework keeps knowledge external in `data/parent_store.json` and ChromaDB. When new amendments are passed (e.g. 106th Amendment), we simply ingest the document without retraining any neural networks.

### Q5: How large is your legal corpus?
- **Short Answer**: 886 documents containing ~5.82 million characters, indexed into 7,470 child passages.
- **Detailed Answer**: The corpus includes: (1) 477 Constitutional Articles and Schedules from the Legislative Department, (2) 106 Constitutional Amendment Acts from the Gazette of India, (3) 286 Supreme Court decisions (including 103 full-text SCR PDF rulings from AWS Open Data), and (4) 17 Central Acts from India Code comprising 1,975 sections (CrPC, IPC, IEA, CPC, RPA, etc.).

---

## Category 2: Architecture & System Design

### Q6: Can you explain your 4-tier architecture?
- **Short Answer**: Tier 1 is Storage (ChromaDB + `parent_store.json`), Tier 2 is NLP Understanding, Tier 3 is Hybrid Retrieval & Reranking, and Tier 4 is Grounded Generation & Safety Gating.
- **Detailed Answer**:
  - *Tier 1 (Storage)*: 886 parent documents in `parent_store.json` and 7,470 child chunks in ChromaDB.
  - *Tier 2 (NLP)*: Preprocessing, 10-class Legal NER, canonical entity linking, hybrid intent classification, and synonym expansion.
  - *Tier 3 (Retrieval)*: BM25 + BGE-M3 dense search fused via RRF ($k=60$), entity boosting (+0.15), and cross-encoder reranking down to top 5.
  - *Tier 4 (RAG & Safety)*: Parent recovery, zero-temperature generation, structural citation validation, NLI claim verification, and 5-stage abstention.

### Q7: Why do you use a two-stage retrieval pipeline instead of reranking all 7,470 chunks?
- **Short Answer**: Cross-encoders have $O(N \cdot L^2)$ computational complexity; scoring 7,470 chunks would take 20 seconds. Two-stage retrieval gives cross-encoder accuracy in 120 milliseconds.
- **Detailed Answer**: Bi-encoders and BM25 are fast first-stage filters: they retrieve 30 candidate passages in 45 milliseconds. The Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) performs all-to-all cross-attention on only those 30 candidate pairs, which takes ~75 milliseconds. This hybrid two-stage design achieves 99% of full cross-encoder accuracy with 100x lower latency.

### Q8: What is Asymmetric Parent-Child indexing?
- **Short Answer**: Indexing small child chunks (~300 chars) for high vector search precision, but hydrating the full parent document (~1,200 chars) for generative prompt context.
- **Detailed Answer**: If you embed large 2,000-character documents, the vector averages across multiple topics (embedding dilution), harming retrieval precision. If you embed small 300-character chunks and feed only them to an LLM, the model lacks surrounding context. Asymmetric RAG decouples retrieval from generation: we search across 7,470 small child chunks, but hydrate the complete parent document from `parent_store.json` for LLM generation.

### Q9: How do you prevent duplicate parent documents in prompt context?
- **Short Answer**: `ParentChildRecovery.recover()` deduplicates parent IDs in memory, appending multiple child chunks under a single parent record.
- **Detailed Answer**: If Clause (1) and Clause (2) of Article 19 are both in the top 5 retrieved chunks, our deduplication algorithm registers `parent_const_art_019` only once. It includes the complete parent text once while listing both chunks under `Exact Supporting Evidence Passages`, saving prompt tokens.

### Q10: What is the purpose of `rag/ui_formatter.py`?
- **Short Answer**: It acts as a ViewModel, transforming the technical `PipelineResult` dataclass into strongly-typed presentation cards (`FormattedLegalAnswer`, `FormattedProvision`, `FormattedJudgment`).
- **Detailed Answer**: It cleanly decouples execution logic from presentation. It parses direct answers, executive legal summaries, and statutory exceptions, ensuring that if an answer is abstained, empty UI boxes are never rendered.

---

## Category 3: Natural Language Processing (Stage 2)

### Q11: What entity categories does your `LegalNER` module extract?
- **Short Answer**: 10 fine-grained categories: `ARTICLE`, `CASE`, `SECTION`, `ACT`, `AMENDMENT`, `RIGHT`, `COURT`, `PERSON`, `LEGAL_CONCEPT`, and `DATE`.
- **Detailed Answer**: It extracts statutory anchors (`Article 21`, `Section 165`), landmark case titles (`Kesavananda Bharati`), enactments (`CrPC`), constitutional rights (`Right to Privacy`), courts (`Supreme Court`), and legal doctrines (`Basic Structure`). It combines compiled regex with dynamic gazetteers loaded from `parent_store.json`.

### Q12: How does `LegalNER` handle overlapping entity spans?
- **Short Answer**: It uses a greedy span collision resolution algorithm where the longest character span wins.
- **Detailed Answer**: In the phrase *"Constitution (Forty-fourth Amendment) Act, 1978"*, regex might match both *"Forty-fourth Amendment"* (`AMENDMENT`) and the full act title (`ACT`). The `_resolve_span_collisions()` method sorts candidate spans descending by length (`end - start`) and discards any overlapping shorter spans.

### Q13: What is Entity Linking and why is it needed in legal AI?
- **Short Answer**: Mapping informal user surface mentions to unambiguous canonical knowledge base identifiers.
- **Detailed Answer**: Users refer to laws using informal names: *"puttaswamy case"*, *"aadhaar judgment"*, *"right to privacy case"*. All three refer to the same canonical entity: `case_puttaswamy_2017`. `EntityLinker` uses `alias_index.json` to resolve these surface forms to canonical IDs, enabling downstream entity boosting and parent retrieval.

### Q14: How does your `HybridIntentClassifier` work?
- **Short Answer**: A two-tier classifier: fast deterministic regex patterns for statutory lookups, with a TF-IDF Logistic Regression model for natural language queries.
- **Detailed Answer**: If a query matches clear statutory templates (e.g. *"What is Article..."*), it classifies immediately via `RuleBasedIntentClassifier`. Ambiguous conceptual queries fall back to `MLIntentClassifier`, trained strictly on `intent_train.json`. A guard asserts that any query containing valid legal entities is never classified as out-of-scope.

### Q15: Why limit query expansion to a maximum of 3 terms?
- **Short Answer**: To prevent query drift in dense and sparse retrieval.
- **Detailed Answer**: Unconstrained query expansion introduces semantic noise. If a query about *"habeas corpus"* expands into 10 terms including *"detention, arrest, police, jail, prison, bail, magistrate"*, the original statutory focus is diluted. `QueryExpander` limits expansions to at most 3 domain-verified synonyms from `legal_synonyms.json`.

---

## Category 4: Information Retrieval & RRF Math (Stage 3)

### Q16: Why combine BM25 and Dense vector search?
- **Short Answer**: BM25 excels at exact keyword and section matches; dense BGE-M3 vectors excel at semantic paraphrases. Together, they eliminate each other's weaknesses.
- **Detailed Answer**: When a user queries *"Article 21A"*, BM25 matches the exact alphanumeric token `21A`, whereas dense search might blur into Article 21. When a user asks *"Can state tap my phone?"*, dense search maps this to wiretapping and privacy under Article 21, whereas BM25 finds zero keyword matches. Hybrid search captures both.

### Q17: What is Cormack Reciprocal Rank Fusion and what is its formula?
- **Short Answer**: An unsupervised, rank-based fusion method combining rankings from multiple retrieval systems without score normalization.
- **Detailed Answer**:
  $$\text{RRF Score}(d) = \sum_{m \in M} \frac{1}{k + \text{rank}_m(d)}$$
  Where $k$ is a smoothing constant set to $60$. It was introduced by Cormack, Clarke, and Buettcher at SIGIR 2009. Documents appearing near the top of both lists receive massive reciprocal uplifts, while outlier documents appearing in only one list are dampened.

### Q18: Why is $k=60$ used in RRF?
- **Short Answer**: Empirical IR literature proves $k=60$ prevents top-ranked items from completely dominating the score while providing smooth decay for lower ranks.
- **Detailed Answer**: If $k$ is very small (e.g. $k=1$), Rank 1 gets score $1.0$ and Rank 2 gets $0.5$ (a 50% drop), which over-penalizes Rank 2. With $k=60$, Rank 1 gets $\frac{1}{61} \approx 0.01639$ and Rank 2 gets $\frac{1}{62} \approx 0.01612$, rewarding consensus across systems rather than giving extreme monopoly to a single Rank 1.

### Q19: How does your Statutory Entity Boost work mathematically?
- **Short Answer**: It adds $+0.150$ to the candidate score if metadata matches query statutory articles or cases, and $+0.075$ if it matches legal concepts.
- **Detailed Answer**: After RRF scores are computed (bounded around $0.01$ to $0.03$), `apply_entity_boost()` inspects candidate `article_number`, `case_name`, and doc IDs. If a candidate matches an extracted entity, $\Delta s = 0.150$ is added. Because base RRF scores are small, $+0.150$ acts as an authoritative prior, elevating the exact statute to the top of the pool.

### Q20: What is the difference between Cosine Distance and Cosine Similarity in ChromaDB?
- **Short Answer**: Cosine Distance is $d = 1 - \cos \theta$ (lower is better, range $[0, 2]$); Cosine Similarity is $s = 1 - d = \cos \theta$ (higher is better, range $[-1, 1]$).
- **Detailed Answer**: ChromaDB calculates distance $d(\vec{u}, \vec{v}) = 1 - \frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\| \|\vec{v}\|}$. When two vectors are identical, $d=0$. In `DenseRetriever`, we convert distance to similarity $s = 1.0 - d$ so that candidates can be sorted in descending order of relevance.

---

## Category 5: Cross-Encoders & Neural Reranking

### Q21: What is the fundamental architectural difference between a Bi-Encoder and a Cross-Encoder?
- **Short Answer**: Bi-encoders encode query and document separately into vectors (independent attention); Cross-encoders feed query and document together through all self-attention layers (joint cross-attention).
- **Detailed Answer**:
  - *Bi-Encoder (BGE-M3)*: Computes $\vec{q} = \text{BERT}(Q)$ and $\vec{d} = \text{BERT}(D)$ separately. Score is $\cos(\vec{q}, \vec{d})$. Fast, but tokens in $Q$ cannot interact with tokens in $D$ during encoding.
  - *Cross-Encoder (`ms-marco-MiniLM-L-6-v2`)*: Computes $\text{Score} = \text{BERT}([CLS] Q [SEP] D [SEP])$. Every word in the query directly attends to every word in the document across all 6 layers. This captures complex sentence structure, negation, and legal conditions.

### Q22: Why did adding the Cross-Encoder increase NDCG@10 from 0.6994 to 0.7787?
- **Short Answer**: Because it resolved legal conditions, exceptions, and procedural qualifiers that bi-encoders missed.
- **Detailed Answer**: In legal search, documents often share high lexical and semantic overlap with the query but differ on crucial conditions (e.g. *warrant required* vs *warrantless search exceptions*). The Cross-Encoder's full cross-attention successfully distinguishes between a general arrest rule and a specific emergency exception, promoting the exact matching section to Rank 1.

---

## Category 6: Grounded Generation, Citations & Hallucination Prevention

### Q23: What prompt constraints do you enforce in `GROUNDED_RAG_PROMPT`?
- **Short Answer**: Zero external knowledge, mandatory bracketed citations `[Doc: <doc_id>]`, 3-part section separation, and explicit declaration of insufficient evidence.
- **Detailed Answer**: The prompt instructs the model to act as a senior Constitutional Law Scholar with zero external hallucination. It mandates: (1) Answer strictly using provided source documents, (2) Under NO circumstances cite unprovided articles or cases, (3) Use bracketed citation keys `[Doc: <doc_id>]` on every claim, and (4) Output *"INSUFFICIENT EVIDENCE"* if evidence is lacking.

### Q24: What is an "Unretrieved Citation" and how do you detect it?
- **Short Answer**: When the LLM cites a genuine legal document that exists in the database, but was NOT part of the retrieved evidence for that specific query.
- **Detailed Answer**: Most RAG systems only check whether a cited document exists in their database. But if an LLM cites Article 14 when only Article 21 was retrieved for that question, the LLM is hallucinating from pre-trained memory! In `rag/citation_validator.py`, Check 3 verifies that every cited document ID is present in `retrieved_parent_ids`. If not, it is flagged as `UNRETRIEVED_EVIDENCE_CITED` and rejected.

### Q25: How does your `NLIVerifier` detect polarity contradictions?
- **Short Answer**: By comparing deontic modal verbs (positive vs negative) on propositions that share substantive legal content words.
- **Detailed Answer**: It compiles sets of positive modals (`"shall"`, `"permits"`, `"constitutional"`) and negative modals (`"prohibits"`, `"cannot"`, `"unconstitutional"`). If an answer claim asserts permission while the retrieved statute asserts prohibition on a proposition sharing $\ge 2$ substantive tokens (excluding generic legal stop-words), it flags an explicit polarity conflict with confidence 0.90.

### Q26: What are the 6 signals used by `ConfidenceEstimator`?
- **Short Answer**:
  1. Retrieval strength (sigmoid of cross-encoder logit, weight 0.25)
  2. Evidence chunk count (weight 0.15)
  3. Entity alignment (weight 0.20)
  4. Method agreement (Jaccard overlap of BM25 and dense, weight 0.15)
  5. Citation integrity (structural validation score, weight 0.15)
  6. Query evidence coverage (weight 0.10)

### Q27: What is the 5-stage defensive abstention gate?
- **Short Answer**: Five sequential checkpoints that safely withhold answers if: (0) Query is empty, (1) Query is out of scope, (2) Retrieval score is below threshold, (3) Parent context is missing, or (4/5) Citations fail validation or confidence $< 0.30$.
- **Detailed Answer**: Enforced by `AbstentionManager`. Early gates (0 and 1) execute before ChromaDB or LLM calls to save latency. Late gates (4 and 5) evaluate generated text. If any gate fails, the system withholds generation and returns a safe, transparent explanation.

---

## Category 7: Evaluation, Benchmarks & Metrics

### Q28: How did you guarantee zero data leakage in your evaluation?
- **Short Answer**: By physically splitting datasets into disjoint JSON files (`intent_train.json`, `intent_val.json`, `intent_test.json`) and fitting feature extractors strictly on the training partition.
- **Detailed Answer**: Our script `audit_intent_leakage.py` computes the mathematical set intersection between training and test token sequences, asserting 0% overlap. Machine learning models were fitted strictly on train, and evaluated solely on unseen test queries. Gold IR queries were written by legal experts as natural user questions rather than copying text from the corpus.

### Q29: What is the difference between MRR and NDCG@10?
- **Short Answer**: MRR evaluates the rank of only the first relevant document; NDCG@10 evaluates the ranked quality of all top-10 documents using graded relevance and logarithmic discounting.
- **Detailed Answer**: Mean Reciprocal Rank is $\frac{1}{\text{rank}_1}$, which is ideal when a user only needs a single correct answer. NDCG@10 uses graded relevance ($3, 2, 1, 0$) and logarithmic discounting ($\frac{2^{\text{rel}}-1}{\log_2(i+1)}$), evaluating whether primary authorities appear above secondary authorities throughout the top 10.

### Q30: What is your primary quantitative result?
- **Short Answer**: Full pipeline achieved an NDCG@10 of **0.7787**, a **+41.9% improvement over the BM25 baseline (0.5484)**, with **100% citation validity** across 319 passing tests.
- **Detailed Answer**: On our 100-query gold constitutional benchmark, BM25 scored 0.5484, Dense BGE-M3 scored 0.5739, Hybrid RRF scored 0.6558, Entity Boosting reached 0.6994, and Full Pipeline (+ Cross-Encoder) reached **0.7787**, with Mean Reciprocal Rank increasing from 0.4912 to **0.7420** (+51.1%).

