# Viva Defense & Capstone Examination Guide
## Entity-Aware Hybrid Retrieval and Reranking Framework for Indian Constitutional Question Answering

**Project Title**: Indian Constitution Legal AI Assistant  
**Research Topic**: Entity-Aware Hybrid Retrieval and Reranking Framework for Indian Constitutional Question Answering  
**Target Milestone**: B.Tech Senior Capstone Viva & Faculty Defense  
**Audience**: Senior NLP Researchers, Faculty Review Committee, Project Examiners  

---

## 1. 60-Second Elevator Pitch

> *"General-purpose chatbots hallucinate legal statutes, while traditional keyword search fails to understand conversational citizen queries. In this project, we designed and empirically evaluated an Entity-Aware Hybrid Retrieval and Reranking Framework specifically tailored to Indian Constitutional Law. We combine sparse BM25 lexical search with dense vector embeddings using Reciprocal Rank Fusion, inject an additive rank boost for recognized legal entities, and rerank candidates using a neural Cross-Encoder. To guarantee evidentiary reliability, our system features hierarchical parent-child context recovery, structural citation validation, explainable confidence estimation, and automated abstention for out-of-scope inquiries. On a 200-query constitutional benchmark, our full reranked pipeline achieves an MRR of 0.8583 and an NDCG@10 of 0.7787, with 254 passing automated tests and a live Streamlit diagnostic dashboard."*

---

## 2. 3-Minute Comprehensive Project Summary

> *"Good morning, esteemed committee members. Our project addresses a fundamental challenge at the intersection of Natural Language Processing and Information Retrieval: question answering over hierarchical statutory law and judicial precedent.*
>
> *Indian Constitutional Law presents three distinct NLP hurdles. First, constitutional text is heavily structured into nested clauses and sub-clauses, meaning standard fixed-length chunking either cuts clauses in half or dilutes vector embeddings. Second, citizen questions exhibit high vocabulary mismatch: citizens describe situations colloquially—such as 'can police tap my phone'—whereas the Constitution speaks of 'personal liberty under Article 21'. Pure keyword search yields zero matches, while pure dense vector retrieval struggles to distinguish exact statutory anchors like 'Article 21' from 'Article 21A'. Third, general LLMs hallucinate case citations and constitutional holdings, creating severe legal risks.*
>
> *To solve these issues, we developed an end-to-end 16-stage pipeline:
> 1. In NLP Query Understanding, we perform legal text normalization, extract entities across 10 categories using hybrid regex and corpus gazetteers (Macro-F1 0.8496), link surface mentions to canonical IDs, classify intent across 11 classes using TF-IDF and Logistic Regression (84.85% accuracy), and expand queries using a controlled legal synonym graph.
> 2. In Information Retrieval, we implement a multi-stage funnel: BM25Okapi and ChromaDB dense embeddings retrieve candidates independently, merged via Reciprocal Rank Fusion with $k=60$. Detected legal entities receive an additive $+0.15$ boost. A Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) reranks the top 30 candidates to top 5, lifting NDCG@10 to 0.7787.
> 3. In Generation and Reliability, fine-grained child chunks are hydrated back to full parent Articles and Judgments. The grounded generator synthesizes answers bounded strictly by evidence. A structural citation validator confirms that all citations exist in the verified database and retrieved context, while a 6-signal confidence estimator triggers automated abstention on out-of-scope or unevidenced inputs.
>
> *All components are covered by 254 passing automated tests, zero mock data, and an interactive Streamlit UI featuring a live 10-Stage Pipeline Inspector and Empirical Evaluation Dashboard. Thank you, and I look forward to your questions."*

---

## 3. 10-Minute Slide Presentation Outline

| Slide # | Slide Title | Visual / Content Elements | Speaking Points (Time) |
|:---:|---|---|---|
| **1** | Title & Research Title | Title, Student Name, Guide Name, Institution, Academic Year | Introduce the research title and focus on Indian Constitutional Law (0:30) |
| **2** | Motivation & Problem Statement | Venn diagram: Citizen Phrasing vs. Statutory Language vs. Hallucination Risk | Explain vocabulary mismatch and statutory structure challenges (1:00) |
| **3** | Core Research Questions | RQ1 (RRF), RQ2 (NER Boost), RQ3 (Cross-Encoder), RQ4 (Intent), RQ5 (Grounding) | State the 5 experimental hypotheses (1:00) |
| **4** | System Architecture | Mermaid flowchart of 16-stage pipeline (from query to abstention) | Walk through the three tiers: NLP, Retrieval, and RAG Grounding (1:30) |
| **5** | Corpus & Hierarchical Chunking | Diagram showing Parent Article hydrating 3 Child Chunks | Justify small chunks for retrieval vs. large parent docs for LLM generation (1:00) |
| **6** | NLP Query Understanding | Table of 10 NER classes, TF-IDF + LogReg confusion matrix | Highlight resolution of judge names (`PERSON_TITLE_PATTERN`) and 84.85% intent accuracy (1:00) |
| **7** | Information Retrieval & RRF | Mathematical formulas for BM25, Cosine Sim, RRF ($k=60$), Entity Boost ($+0.15$) | Explain why rank fusion avoids brittle score calibration across disparate metrics (1:30) |
| **8** | Neural Reranking & Latency | Bi-Encoder vs. Cross-Encoder diagram; CPU latency profile bar chart | Explain cross-attention accuracy gains (+5.9% NDCG@10) vs. ~892 ms latency trade-off (1:00) |
| **9** | Empirical Results & Ablation | Retrieval results comparison table (Exp 1 to Exp 6) with canonical labels | Show progressive lifts: BM25 (0.7197) $\to$ RRF (0.7262) $\to$ Full (0.7787) NDCG@10 (1:00) |
| **10** | Conclusion, Limitations & Viva | Summary table, 254 pytest pass, known limitations (10% uncataloged targets, CPU bound) | Conclude honestly on academic contributions and invite viva questions (0:30) |

---

## 4. Live Demonstration Script

1. **Step 1 — Main UI Overview**: Open `http://localhost:8501`. Point out the header, dark legal theme, sidebar system metrics (**270 Parent Contexts**, **1,001 Child Chunks**), and Architecture Engine selection.
2. **Step 2 — Landmark Case Query**: Click preset button *"Privacy under Art. 21 (Puttaswamy)"*. Click Submit.
   - Show Strategy badge (`CASE_SEARCH`), Intent badge (`CASE_LAW_QUERY`), Confidence badge (`HIGH (85%)`), and Citation badge (`✅ Citations Validated`).
   - Show entity pills: `📜 Article 21`, `⚖️ Puttaswamy`, `💡 Privacy`.
   - Show grounded legal synthesis and verified citation tags.
3. **Step 3 — 10-Stage Pipeline Diagnostic Inspector**: Expand *"🔬 NLP Pipeline Diagnostic Inspector"*.
   - Tab 1: Show original query, normalized tokens, and detected language.
   - Tab 2: Show top retrieved candidates, BM25 ranks, vector ranks, RRF scores, entity boost flags, and Cross-Encoder rerank scores.
   - Tab 4: Show verified citations matched against `parent_store.json`.
   - Tab 5: Show the 6-signal confidence breakdown table.
4. **Step 4 — Landmark Case Comparator**: Click Tab 2 (*"⚖️ Case Comparator"*).
   - Select *Kesavananda Bharati* (Case A) and *Minerva Mills* (Case B).
   - Demonstrate the side-by-side comparative analysis of facts, ratios, and amending limits.
5. **Step 5 — Constitution & Cases Database Explorer**: Click Tab 3 (*"📜 Constitution & Cases Database"*).
   - Display the searchable pandas dataframe of all 137 articles and 104 judgments.
6. **Step 6 — Empirical Research Dashboard**: Click Tab 5 (*"📊 Empirical Research Dashboard"*).
   - Show the interactive retrieval comparison chart (Exp 1 to Exp 6), NDCG@10 vs. Latency curve, intent classification matrix, and benchmark integrity status.
7. **Step 7 — Automated Abstention**: Return to Tab 1. Type an out-of-scope question: *"What is the penalty for dishonour of cheques under Section 138 of Negotiable Instruments Act?"*. Click Submit.
   - Show the yellow warning banner: **`🛡️ System Refusal / Abstention Notice`**.
   - Explain why the system safely abstained to eliminate commercial law hallucinations.

---

## 5. Comprehensive Viva Questions & Answers (40 Questions across 10 Categories)

### Category 1: Project Motivation & Research Novelty

#### Q1: What is the core problem your project solves that ChatGPT or Gemini does not?
- **Short Answer**: General LLMs generate plausible but fabricated citations and holdings without verified provenance. Our system grounds every claim strictly in an authenticated constitutional database, validates structural citations, and safely abstains when evidence is insufficient.
- **Deeper Explanation**: In legal informatics, ungrounded generation carries severe liability. An LLM might cite non-existent paragraphs or confuse the 7-judge bench in *Maneka Gandhi* with the 9-judge bench in *Puttaswamy*. Our system enforces strict RAG: it retrieves verified parent documents from `parent_store.json`, forces the generator into a closed-world context prompt, and runs a structural citation validator before presenting results to the user.
- **Code Reference**: [`rag/generator.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/rag/generator.py#L45-L95), [`rag/citation_validator.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/rag/citation_validator.py#L35-L80).
- **Follow-up Question**: *"Does your citation validator verify that the legal claim is semantically true?"*  
  *Answer*: No. As documented in our research audit, the validator performs structural provenance and retrieval-set inclusion checks. It confirms the document exists and was in the evidence pool, but does not execute atomic sentence-level Natural Language Inference (NLI).

#### Q2: What is your primary research contribution?
- **Short Answer**: An entity-aware hybrid retrieval and reranking framework that integrates domain-specific Legal NER and canonical linking into Reciprocal Rank Fusion, followed by neural cross-attention reranking and hierarchical context recovery.
- **Deeper Explanation**: Rather than treating legal retrieval as generic text matching, we treat legal entities (e.g. `Article 21`, `42nd Amendment`, `Kesavananda Bharati`) as high-priority statutory anchors. By applying an entity-aware boost ($+0.15$) to candidates matching linked entities, we elevate statutory targets that semantic vectors often rank lower due to generic wording.
- **Code Reference**: [`retrieval/entity_boost.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/entity_boost.py#L35-L75).
- **Follow-up Question**: *"Why not just filter by metadata rather than boosting?"*  
  *Answer*: Hard metadata filtering causes zero-recall failures if a citizen's query mentions an entity merely as context or omits it entirely. Soft additive boosting prioritizes matching documents while preserving fallback recall for unannotated passages.

#### Q3: Why is Indian Constitutional Law a distinct NLP domain compared to US or UK law?
- **Short Answer**: The Indian Constitution is the longest written national constitution in the world, featuring heavily nested articles, extensive judicial doctrinal review (e.g., the Basic Structure Doctrine), and extensive multilingual borrowing.
- **Deeper Explanation**: Unlike the US Constitution (7 Articles and 27 Amendments), the Indian Constitution originally had 395 Articles across 22 Parts and 8 Schedules, expanding to over 448 Articles today. Articles contain sub-clauses with differing standards of judicial review (e.g., Article 19(1)(a) speech right vs. Article 19(2) reasonable restrictions). Precedents heavily reinterpret text without textual amendment (e.g., *Puttaswamy* deriving privacy from Article 21).
- **Code Reference**: [`data/constitution/articles.json`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/data/constitution/articles.json), [`data/judgments/supreme_court_landmarks.json`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/data/judgments/supreme_court_landmarks.json).
- **Follow-up Question**: *"Does your system handle vernacular Indian languages like Hindi?"*  
  *Answer*: The language detection module (`nlp/language_detection.py`) identifies non-English queries and routes them cleanly. While full multilingual embeddings were beyond the current scope, the framework is designed to accept multilingual models like IndicBERT.

#### Q4: Who are the target users of this system?
- **Short Answer**: Law students, legal researchers, civic educators, and citizens seeking verified constitutional information with transparent citations.
- **Deeper Explanation**: The system bridges lay conversational inquiries and formal constitutional text. For a citizen, it translates informal phrases like 'phone tapping' into Article 21 privacy doctrines. For a law student, it provides side-by-side case comparisons and traceable citation paths.
- **Code Reference**: [`app.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/app.py#L298-L306).

---

### Category 2: Architecture & Software Engineering

#### Q5: Walk through the complete data flow for a user query.
- **Short Answer**: User Query $\to$ Language Detection $\to$ Normalization $\to$ Legal NER $\to$ Entity Linking $\to$ Intent Classification $\to$ Query Expansion $\to$ Query Router $\to$ BM25 & Dense Search $\to$ RRF Fusion $\to$ Entity Boosting $\to$ Cross-Encoder Reranking $\to$ Parent Context Recovery $\to$ Grounded Generation $\to$ Citation Validation $\to$ Confidence Estimation $\to$ Abstention or Answer $\to$ UI.
- **Deeper Explanation**: The pipeline processes text through 16 deterministic steps. Preprocessing normalizes legal abbreviations (`Art.` $\to$ `Article`). Legal NER extracts entities, which are linked to canonical IDs. The router selects retrieval parameters. Dual retrievers fetch 30 candidates, which are fused via RRF ($k=60$), boosted ($+0.15$), and reranked using `ms-marco-MiniLM-L-6-v2` down to 5. Winning child passages hydrate full parent records from `parent_store.json`. The generator synthesizes an answer, citations are verified against context, confidence is calculated, and if confidence $< 0.30$, the system abstains.
- **Code Reference**: [`rag/pipeline.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/rag/pipeline.py#L109-L210).
- **Follow-up Question**: *"Is this pipeline synchronous or asynchronous?"*  
  *Answer*: It executes synchronously in Python on request. Candidate retrieval runs sequentially with low latency (~20 ms), while cross-encoder reranking runs in PyTorch on CPU (~892 ms).

#### Q6: Why did you replace autonomous multi-agent routing with a deterministic query router?
- **Short Answer**: Autonomous multi-agent loops introduce non-deterministic execution paths, high token latency, and unpredictable routing failures. A deterministic NLP router executes in sub-millisecond time with transparent, explainable logic.
- **Deeper Explanation**: Earlier prototypes used LLM-based autonomous agents to decide whether to query articles or cases. In adversarial testing, autonomous agents occasionally looped, chose arbitrary tools, or failed to route edge-case queries. In `routing/query_router.py`, we map intent and entity signals directly to structured retrieval strategies (`ARTICLE_SEARCH`, `CASE_SEARCH`, `COMPARISON_SEARCH`, `OUT_OF_SCOPE`) deterministically.
- **Code Reference**: [`routing/query_router.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/routing/query_router.py#L40-L115).
- **Follow-up Question**: *"Did you delete the legacy multi-agent code?"*  
  *Answer*: No. To maintain backward compatibility and support ablation comparisons, the legacy multi-agent classes in `agents.py` were retained as facade wrappers and can be toggled via the UI sidebar.

#### Q7: How does your system maintain backward compatibility?
- **Short Answer**: Through modular facade modules (`ingestion.py`, `retriever.py`, `agents.py`) that re-export classes from the new modular subpackages (`rag/`, `retrieval/`, `routing/`).
- **Deeper Explanation**: When refactoring monolithic scripts into modular subpackages, legacy tests and existing imports could break. We kept `ingestion.py`, `retriever.py`, and `agents.py` at the root as facades that delegate to `rag/ingestion.py`, `retrieval/hybrid_retriever.py`, and `routing/query_router.py`. All 254 pytest test cases pass across both interfaces.
- **Code Reference**: [`ingestion.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/ingestion.py#L32-L49), [`retriever.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retriever.py#L20-L45).

#### Q8: What design patterns did you employ across the codebase?
- **Short Answer**: Facade pattern (backward compatibility), Strategy pattern (retrieval algorithms), Pipeline pattern (end-to-end execution), and Factory/Singleton pattern (cached model loaders).
- **Deeper Explanation**: In `retrieval/hybrid_retriever.py`, individual retrieval strategies (BM25, Dense, RRF, Reranker) are injected and controlled via boolean flags, implementing the Strategy pattern. In `rag/pipeline.py`, results flow sequentially through the Pipeline pattern. In `nlp/legal_ner.py` and `retrieval/reranker.py`, `get_*` functions cache loaded model instances in memory, avoiding redundant weights reload.
- **Code Reference**: [`rag/pipeline.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/rag/pipeline.py#L74-L108).

---

### Category 3: NLP & Legal NER

#### Q9: Explain how your Legal NER system works from first principles.
- **Short Answer**: It is a hybrid architecture combining high-precision regular expressions for structured statutory citations with corpus-derived gazetteers for judicial precedents and legal concepts, resolved via longest-match priority.
- **Deeper Explanation**: General-domain NER models (like standard spaCy) misclassify legal terms—tagging "Article 21" as `CARDINAL` or "Supreme Court" as a generic `ORG`. Statutory law follows predictable syntactical conventions. We use regex patterns for `ARTICLE` (`Article \d+[A-Z]?`), `AMENDMENT`, `SECTION`, `ACT`, and `DATE`. For unstructured entities like `CASE`, `COURT`, `RIGHT`, and `LEGAL_CONCEPT`, we extract curated gazetteers from the ingested corpus. When matches overlap, our tokenizer prioritizes longest-match spans.
- **Code Reference**: [`nlp/legal_ner.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/legal_ner.py#L65-L160).
- **Follow-up Question**: *"How do you evaluate NER performance?"*  
  *Answer*: We evaluate exact character span offsets (`exact_span_match=True`) against 105 gold annotated queries in `data/annotations/ner_annotations.json`, achieving 0.8714 Micro-F1 and 0.8496 Macro-F1 across 10 categories.

#### Q10: How did you fix the `PERSON` extraction failure where F1 was initially 0.0000?
- **Short Answer**: We introduced a judicial title regex pattern (`PERSON_TITLE_PATTERN`) and context disambiguation to separate personal names from case titles.
- **Deeper Explanation**: In early evaluations, `PERSON` scored 0.0000 because gold annotations contained judge names (e.g., *Justice H.R. Khanna*, *Dr. B.R. Ambedkar*) that lacked exact gazetteer matches or were misclassified as cases. We implemented `PERSON_TITLE_PATTERN` matching prefixes like `Chief Justice`, `Justice`, or `Dr.` followed by capitalized names. We also added disambiguation for ambiguous names like *Maneka Gandhi* (checking for "in" or "v." to decide between `PERSON` and `CASE`). This raised `PERSON` F1 from 0.0000 to 0.8966.
- **Code Reference**: [`nlp/legal_ner.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/legal_ner.py#L90-L125), [`docs/NER_ERROR_ANALYSIS.md`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/docs/NER_ERROR_ANALYSIS.md#L18-L32).

#### Q11: What is Canonical Entity Linking and why is it necessary?
- **Short Answer**: Entity Linking resolves informal or variant surface mentions to unambiguous, canonical corpus identifiers stored in `parent_store.json`.
- **Deeper Explanation**: Users query using various surface forms: *"Art 21"*, *"Article 21"*, *"Puttaswamy privacy case"*, or *"Aadhaar ruling"*. If retrieval relied solely on string matching, each alias would retrieve disjoint subsets. Our entity linker (`nlp/entity_linking.py`) maintains an alias dictionary mapping surface variants to canonical parent IDs (`const_art_021`, `case_sc_puttaswamy_privacy_2017`). It achieves 86.67% linking accuracy and 100% rejection on out-of-KB entities.
- **Code Reference**: [`nlp/entity_linking.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/entity_linking.py#L40-L105).

#### Q12: How does your Intent Classifier work, and why did you choose Logistic Regression over a Transformer?
- **Short Answer**: We extract unigram and bigram TF-IDF features and train a regularized Logistic Regression model over 11 classes, achieving 84.85% test accuracy and 0.7591 cross-validation accuracy.
- **Deeper Explanation**: With a curated training set of 187 queries across 11 classes, fine-tuning a 110M-parameter Transformer (like BERT) leads to severe catastrophic overfitting and training instability. TF-IDF + Logistic Regression provides an optimal bias-variance trade-off, executes inference in under 1 millisecond, requires no GPU, and offers transparent feature coefficients.
- **Code Reference**: [`nlp/intent_classifier.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/nlp/intent_classifier.py#L45-L115).
- **Follow-up Question**: *"What are the 11 intent classes?"*  
  *Answer*: `ARTICLE_LOOKUP`, `CASE_LAW_QUERY`, `CASE_COMPARISON`, `LEGAL_EXPLANATION`, `RIGHTS_QUERY`, `AMENDMENT_QUERY`, `PRECEDENT_QUERY`, `DEFINITION_QUERY`, `CONSTITUTIONAL_PROCEDURE`, `MULTI_DOCUMENT_QUERY`, `OUT_OF_SCOPE`.

---

### Category 4: Embeddings & Dense Retrieval

#### Q13: Explain embeddings from first principles.
- **Short Answer**: An embedding model maps variable-length text into a dense, continuous vector space where semantically similar texts are placed close together as measured by cosine similarity.
- **Deeper Explanation**: Dense models pass tokens through a transformer encoder to produce contextual hidden states, which are pooled (typically mean pooling) into a fixed-dimensional vector $\mathbf{v} \in \mathbb{R}^d$. Semantic similarity corresponds to the cosine of the angle between vectors:
  $$\text{CosineSim}(\mathbf{q}, \mathbf{d}) = \frac{\mathbf{q} \cdot \mathbf{d}}{\|\mathbf{q}\| \|\mathbf{d}\|}$$
  This allows the system to match paraphrased queries (e.g. *"government wiretapping"*) to target articles (Article 21) even when lexical token overlap is zero.
- **Code Reference**: [`retrieval/dense_retriever.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/dense_retriever.py#L40-L85).

#### Q14: Which embedding model does your repository use and what are its dimensions?
- **Short Answer**: `sentence-transformers/all-MiniLM-L6-v2`, producing 384-dimensional dense vectors.
- **Deeper Explanation**: `all-MiniLM-L6-v2` is a 6-layer distilled transformer trained on over 1 billion sentence pairs for contrastive semantic similarity. It balances high retrieval performance with lightweight CPU footprint (22.7M parameters, ~80 MB disk size), producing 384-dimensional unit-normalized embeddings.
- **Code Reference**: [`config.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/config.py#L38).
- **Follow-up Question**: *"Why didn't you use a legal-specific model like InLegalBERT for embeddings?"*  
  *Answer*: `InLegalBERT` is trained with masked language modeling (MLM) for classification and token extraction; it is not fine-tuned with contrastive loss for dense passage retrieval. Without expensive DPR fine-tuning, off-the-shelf sentence transformers like MiniLM outperform raw domain BERT models on semantic search.

#### Q15: How is ChromaDB configured and persisted?
- **Short Answer**: ChromaDB is initialized as a local `PersistentClient` targeting the `chroma_db/` directory, using the `indian_legal_rag` collection with cosine distance.
- **Deeper Explanation**: ChromaDB persists an SQLite database (`chroma.sqlite3`) and an HNSW (Hierarchical Navigable Small World) index graph on disk. Cosine distance is used (`"hnsw:space": "cosine"`). Since Chroma returns distance $\delta \in [0, 2]$, our retriever converts distance to similarity using $s = 1 - \delta$.
- **Code Reference**: [`retrieval/dense_retriever.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/dense_retriever.py#L45-L70).

---

### Category 5: BM25 & Information Retrieval

#### Q16: State the BM25 formula and define every variable.
- **Short Answer**: BM25 scores a document $D$ against query terms $Q = \{q_1, \dots, q_n\}$:
  $$\text{BM25}(D, Q) = \sum_{i=1}^n \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$
- **Deeper Explanation**:
  - $f(q_i, D)$ is the term frequency of $q_i$ in document $D$.
  - $|D|$ is the length of document $D$ in tokens, and $\text{avgdl}$ is the average document length across the corpus.
  - $\text{IDF}(q_i) = \ln\left(1 + \frac{N - n(q_i) + 0.5}{n(q_i) + 0.5}\right)$, measuring term rarity across $N$ corpus documents.
  - $k_1 = 1.5$ controls term frequency saturation. Higher $k_1$ allows repeated terms to contribute more score.
  - $b = 0.75$ controls document length normalization. If $b=1$, documents are fully scaled by length; if $b=0$, length normalization is disabled.
- **Code Reference**: [`retrieval/bm25_retriever.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/bm25_retriever.py#L35-L50), [`config.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/config.py#L54-L55).

#### Q17: Why is BM25 essential in legal retrieval when we already have dense vectors?
- **Short Answer**: Legal queries depend on exact alphanumeric statutory tokens ("Article 21A", "Section 66A", "Part IVA") that dense vector embeddings blur into semantic neighbors. BM25 provides exact statutory discrimination.
- **Deeper Explanation**: Dense bi-encoders map "Article 21" (Life & Liberty) and "Article 21A" (Right to Education) to almost identical vector neighborhoods because they share 90% of their character sequence and appear in similar constitutional contexts. BM25 treats `"21"` and `"21a"` as distinct inverted index terms, guaranteeing exact statutory matching.
- **Code Reference**: [`retrieval/bm25_retriever.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/bm25_retriever.py#L75-L115).

#### Q18: What tokenizer does your BM25 implementation use?
- **Short Answer**: A punctuation-preserving regex tokenizer (`\b\w+\b`) that lowercases terms and retains alphanumeric identifiers like section and article numbers.
- **Deeper Explanation**: Standard English stopword filters often strip words that carry legal significance (e.g. "not", "under", "in"). Our tokenizer in `retrieval/bm25_retriever.py` uses clean regex token extraction without aggressive stemming, ensuring statutory references like `368` or `21` remain unstemmed.
- **Code Reference**: [`retrieval/bm25_retriever.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/bm25_retriever.py#L21-L26).

---

### Category 6: RRF, Entity Boosting & Reranking

#### Q19: State the Reciprocal Rank Fusion (RRF) equation and explain why it is superior to linear score addition.
- **Short Answer**: 
  $$\text{RRF}(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$
  RRF is superior because it operates on relative ordinal ranks rather than arbitrary score distributions, avoiding brittle normalization.
- **Deeper Explanation**: BM25 produces unbounded positive scores ($[0, \infty)$), whereas cosine similarity is bounded in $[-1, 1]$. Linearly combining them ($\alpha \cdot \text{BM25} + (1-\alpha) \cdot \text{Dense}$) requires min-max normalization, which is sensitive to outliers and query distribution shifts. RRF converts scores into ranks $r_m(d) \in \{1, 2, \dots, K\}$. The hyperparameter $k = 60$ prevents top-ranked documents from dominating while giving balanced fusion.
- **Code Reference**: [`retrieval/rrf.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/rrf.py#L25-L65).
- **Follow-up Question**: *"Why is k set to 60? Is it mathematically optimal?"*  
  *Answer*: No, $k=60$ is a standard empirical default introduced by Cormack et al. (2009). It acts as a smoothing factor. It is a tunable hyperparameter, not a universal mathematical constant.

#### Q20: How does Entity Boosting work and what is the exact formula?
- **Short Answer**: If a retrieved candidate document matches an entity extracted and linked from the query, its fusion score receives an additive boost of $\omega = 0.15$.
  $$\text{Score}_{\text{boosted}}(d) = \text{Score}_{\text{RRF}}(d) + 0.15 \cdot \mathbb{I}(d \in \text{LinkedEntities}(Q))$$
- **Deeper Explanation**: In `retrieval/entity_boost.py`, we check candidate metadata (`article_number`, `case_name`, `amendment_number`) against canonical IDs extracted by Stage 2. If a match is detected, the boost is added, promoting the statutory target into the top candidate pool.
- **Code Reference**: [`retrieval/entity_boost.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/entity_boost.py#L35-L70).
- **Follow-up Question**: *"What is the risk of entity boosting?"*  
  *Answer*: Over-boosting. If a query mentions an article in passing (e.g. *"Is the Governor's discretion under Article 163 subject to judicial review like Article 356?"*), boosting Article 356 could displace the primary target (Article 163). We mitigated this by setting a moderate weight ($\omega = 0.15$).

#### Q21: What is the fundamental difference between a Bi-Encoder and a Cross-Encoder?
- **Short Answer**: A Bi-Encoder encodes query and document into separate vector representations independently; a Cross-Encoder feeds query and document together into the transformer, computing full all-to-all cross-attention across all tokens.
- **Deeper Explanation**:
  - **Bi-Encoder** (e.g., `all-MiniLM-L6-v2`): Computes $\mathbf{u} = \text{BERT}(Q)$ and $\mathbf{v} = \text{BERT}(D)$ separately. Similarity is a simple dot product $\mathbf{u} \cdot \mathbf{v}$. This allows offline indexing and fast MIPS search ($O(1)$ lookup via HNSW), but misses word-level interactions between query and passage.
  - **Cross-Encoder** (e.g., `ms-marco-MiniLM-L-6-v2`): Concatenates tokens $[CLS] \circ Q \circ [SEP] \circ D \circ [SEP]$. Every token in the query attends to every token in the passage in every transformer layer, capturing fine-grained syntactical negation, qualifiers, and statutory constraints.
- **Code Reference**: [`retrieval/reranker.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/reranker.py#L30-L75).

#### Q22: Why not run the Cross-Encoder over the entire corpus instead of just 30 candidates?
- **Short Answer**: Computational complexity. Running cross-attention over 1,001 passages on CPU takes over 40 seconds per query, making interactive execution impossible.
- **Deeper Explanation**: Cross-Encoder inference cannot be precomputed; it must evaluate all candidate pairs on the fly. Evaluating 1,001 pairs requires 1,001 transformer forward passes. By using BM25 and dense retrieval to prune the corpus to a candidate pool of 30 ($N=30$), we achieve high candidate recall ($>0.90$) while keeping reranking latency under 1 second on CPU (~892 ms median).
- **Code Reference**: [`config.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/config.py#L63), [`retrieval/reranker.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/retrieval/reranker.py#L50-L65).

---

### Category 7: RAG Generation, Citations & Abstention

#### Q23: What is Hierarchical Parent-Child Context Recovery?
- **Short Answer**: We retrieve using fine-grained child chunks (~300 chars) for high-precision vector and keyword matching, but supply full parent documents (~1,200 chars) to the LLM generator for complete legal coherence.
- **Deeper Explanation**: Child chunks contain precise semantic vectors without multi-topic noise. However, an LLM generating legal analysis from a 300-character fragment lacks surrounding clauses, procedural caveats, and judgment holdings. In `rag/parent_child.py`, winning child chunks are mapped back to their parent IDs (`parent_id`) in `parent_store.json`. Duplicate parent records are consolidated, and full parent context is provided to the generation prompt.
- **Code Reference**: [`rag/parent_child.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/rag/parent_child.py#L30-L85).

#### Q24: What happens if the Gemini API key is missing or the external call fails?
- **Short Answer**: The system gracefully falls back to an offline, deterministic Legal Synthesis Engine (`HeuristicLegalSynthesizer`), ensuring 100% availability with zero external API dependencies.
- **Deeper Explanation**: In `rag/generator.py`, if `GEMINI_API_KEY` is not detected in `.env` or Streamlit secrets, or if an API call times out / raises an exception, the pipeline routes to `HeuristicLegalSynthesizer`. This synthesizer extracts relevant clauses, facts, and ratios from retrieved parent documents and formats a structured markdown response with full source citations.
- **Code Reference**: [`rag/generator.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/rag/generator.py#L110-L165).

#### Q25: Explain how Structural Citation Validation works.
- **Short Answer**: It parses citations from the generated answer, verifies that cited document IDs exist in `parent_store.json`, and confirms that each cited authority was present in the hydrated evidence pool for that specific query.
- **Deeper Explanation**: The validator (`rag/citation_validator.py`) uses regex to parse citations (e.g. `[Doc: const_art_021]`, `[Case: Puttaswamy]`). It performs a two-tier check:
  1. *Corpus Verification*: Does the document exist in the verified database?
  2. *Provenance Inclusion*: Was the document retrieved in the top-$K$ context for this query?
  If an answer cites a case that was not retrieved, it is flagged as an ungrounded citation (`invalid_citations`).
- **Code Reference**: [`rag/citation_validator.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/rag/citation_validator.py#L40-L110).

#### Q26: Does your citation validator verify factual claim-level semantic entailment?
- **Short Answer**: No. It verifies structural provenance and retrieval inclusion. Factual claim-level semantic entailment requires an NLI cross-encoder, which is identified as future research.
- **Deeper Explanation**: As demonstrated in our adversarial audit (`docs/RAG_GROUNDING_AUDIT.md`), structural validation confirms that the document was present in context, but does not prove that every generated sentence logically follows from the text. This scientific limitation is explicitly disclosed in the research documentation and UI caption.
- **Code Reference**: [`docs/RAG_GROUNDING_AUDIT.md`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/docs/RAG_GROUNDING_AUDIT.md#L15-L25).

#### Q27: How is the confidence score calculated, and is it a calibrated probability?
- **Short Answer**: Confidence is an explainable weighted heuristic composite over 6 signals; it is explicitly disclosed as an uncalibrated heuristic, not a mathematically calibrated probability.
- **Deeper Explanation**: In `rag/confidence.py`, the score is computed as:
  $$C = 0.25 \cdot s_{\text{retrieval}} + 0.15 \cdot s_{\text{count}} + 0.20 \cdot s_{\text{entity}} + 0.15 \cdot s_{\text{agreement}} + 0.15 \cdot s_{\text{citation}} + 0.10 \cdot s_{\text{coverage}}$$
  Because these scores are not mapped through Platt scaling or isotonic regression on a held-out calibration set, we explicitly state that $C$ is a transparent decision heuristic, not a frequentist probability.
- **Code Reference**: [`rag/confidence.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/rag/confidence.py#L35-L95).

#### Q28: Under what conditions does the system trigger automated abstention?
- **Short Answer**: The system abstains if the query is classified as `OUT_OF_SCOPE`, if zero documents are retrieved, if retrieval scores fall below `MIN_RETRIEVAL_SCORE_THRESHOLD = 0.005`, or if overall confidence $< 0.30$.
- **Deeper Explanation**: Rather than forcing a hallucinated answer when a user asks about criminal law or non-existent articles, `rag/abstention.py` gates generation. If abstention is triggered, the system sets `abstained = True` and returns a standardized safe refusal message. In adversarial testing, it achieved 100% accuracy on out-of-scope queries.
- **Code Reference**: [`rag/abstention.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/rag/abstention.py#L35-L80).

---

### Category 8: Evaluation & Research Validity

#### Q29: What is the difference between original relevance labels and canonical labels in your benchmark?
- **Short Answer**: Original labels contained 171 shorthand unpadded aliases (`parent_const_art_14`), which treated zero-padded corpus IDs (`parent_const_art_014`) as missed retrievals. Canonical labels resolved these discrepancies.
- **Deeper Explanation**: Forensic audit revealed that early benchmark files had unpadded identifiers. Because our corpus strictly zero-pads articles (e.g. `parent_const_art_014`), retrievers returning the correct article were penalized by set intersection matching, artificially depressing Recall@10 to 0.5064. Once canonicalized in `relevance_labels_v2_canonicalized.json`, true Recall@10 was verified at **0.7478** (and BM25 at **0.7003**).
- **Code Reference**: [`data/annotations/relevance_labels_v2_canonicalized.json`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/data/annotations/relevance_labels_v2_canonicalized.json), [`docs/BENCHMARK_QUALITY_REPORT.md`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/docs/BENCHMARK_QUALITY_REPORT.md#L15-L25).

#### Q30: Why is Recall@10 bounded at ~0.75 across all 200 retrieval queries?
- **Short Answer**: Exactly 20 queries (10% of the benchmark) target constitutional provisions outside our 137-article ingested corpus (e.g., Articles 148, 174, 311). No retriever can retrieve unindexed documents.
- **Deeper Explanation**: Our 200-query benchmark includes queries across the entire Constitution. Because the active database covers 137 articles, those 20 queries have zero relevant documents in the corpus. When evaluated solely on in-corpus queries (180 queries), our Cross-Encoder achieves **0.9333 Hit@10** and **0.7781 Recall@10**.
- **Code Reference**: [`docs/INDEPENDENT_AUDIT_REPORT.md`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/docs/INDEPENDENT_AUDIT_REPORT.md#L30-L40).

#### Q31: Did you evaluate statistical significance for your retrieval improvements?
- **Short Answer**: No formal paired t-test or Wilcoxon signed-rank test was conducted; we report observational performance across the 200 benchmark queries and transparently disclose this in our documentation.
- **Deeper Explanation**: With 200 queries, while the lift from BM25 (0.7197 NDCG@10) to Cross-Encoder (0.7787 NDCG@10) is consistent (+5.90%), claiming statistical significance at $p < 0.05$ without formal hypothesis testing is an academic overclaim. We treat the results as verified empirical observations.
- **Code Reference**: [`docs/evaluation.md`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/docs/evaluation.md#L25-L35).

#### Q32: How did you ensure zero data leakage in your intent classification evaluation?
- **Short Answer**: We used stratified holdout splitting (80/20) and 5-fold cross-validation with a fixed seed (`EVAL_RANDOM_SEED = 42`), fitting the TF-IDF vectorizer exclusively on training folds.
- **Deeper Explanation**: In `evaluation/intent_eval.py`, the `TfidfVectorizer` and `LogisticRegression` model are fitted inside each cross-validation fold pipeline exclusively on training queries. Test fold queries are never exposed during vocabulary construction or IDF weighting, guaranteeing zero feature leakage.
- **Code Reference**: [`evaluation/intent_eval.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/evaluation/intent_eval.py#L40-L95).

---

### Category 9: Deployment & Scalability

#### Q33: How does the application perform on Streamlit Community Cloud without SQLite issues?
- **Short Answer**: We include a `pysqlite3` shim at the very top of `app.py` that dynamically patches Python's SQLite module to satisfy ChromaDB's requirement ($\ge 3.35.0$).
- **Deeper Explanation**: Standard Debian Linux images on Streamlit Community Cloud use system SQLite 3.31, which causes ChromaDB to crash on import. By putting `import pysqlite3` and `sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')` at lines 12–17 of `app.py`, the cloud deployment transparently uses the newer bundled SQLite library.
- **Code Reference**: [`app.py`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/app.py#L11-L17).

#### Q34: What is the steady-state memory and CPU footprint of the system?
- **Short Answer**: Peak memory is ~310 MB on startup, and steady-state CPU query latency has a median of ~1.48 seconds end-to-end.
- **Deeper Explanation**: Memory is dominated by PyTorch model weights: `all-MiniLM-L6-v2` (~80 MB) and `ms-marco-MiniLM-L-6-v2` (~88 MB). ChromaDB and BM25 indices occupy minimal RAM (< 30 MB). Because inference runs on CPU, warm queries complete in ~1.48 seconds without requiring GPU infrastructure.
- **Code Reference**: [`docs/REPRODUCIBILITY_REPORT.md`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/docs/REPRODUCIBILITY_REPORT.md#L27-L40).

#### Q35: How would you scale this system from 100 judgments to 50,000 judgments?
- **Short Answer**: Decouple ChromaDB into a distributed vector database (such as Milvus, Qdrant, or Pinecone), shard the BM25 index via Elasticsearch/OpenSearch, and quantize the Cross-Encoder using ONNX Runtime or TensorRT.
- **Deeper Explanation**: At 50,000 judgments (~500,000 chunks), in-memory BM25 Okapi and local SQLite ChromaDB would face memory and search latency bottlenecks. We would transition BM25 to an inverted index cluster (Elasticsearch) and dense search to an HNSW cluster (Qdrant). For reranking, ONNX INT8 quantization with GPU batching would reduce 30-candidate rerank latency from ~890 ms to < 50 ms.
- **Code Reference**: [`docs/architecture.md`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/docs/architecture.md#L125-L135).

---

### Category 10: Limitations & Future Work

#### Q36: What is the single biggest limitation of the current repository?
- **Short Answer**: Incomplete corpus coverage: the database indexes 137 articles out of 395 numbered constitutional articles, and the Cross-Encoder operates on CPU with ~892 ms median latency.
- **Deeper Explanation**: While the 137 articles cover 100% of Fundamental Rights, Directive Principles, and the Higher Judiciary, large statutory areas (Finance, State Services, Special Provisions) are missing. This restricts the prototype's utility to constitutional core subjects and bounds retrieval recall on general queries.
- **Code Reference**: [`docs/INDEPENDENT_AUDIT_REPORT.md`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/docs/INDEPENDENT_AUDIT_REPORT.md#L80-L86).

#### Q37: Why did you conclude that the repository is NOT ready for commercial legal production?
- **Short Answer**: Because commercial legal advice requires 100% statutory coverage, atomic claim-level semantic entailment verification, and sub-100ms latency, which this academic B.Tech prototype does not yet provide.
- **Deeper Explanation**: An AI system used by lawyers or judges cannot afford missing 258 constitutional articles or lacking sentence-level entailment verification. Recommending this system for actual legal counsel would carry severe professional liability risks. It is a high-quality academic research prototype, not a commercial enterprise product.
- **Code Reference**: [`docs/INDEPENDENT_AUDIT_REPORT.md`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/docs/INDEPENDENT_AUDIT_REPORT.md#L20-L26).

#### Q38: How would you implement Natural Language Inference (NLI) for claim-level entailment in the future?
- **Short Answer**: Segment generated answers into atomic sentences, pair each sentence with its cited passage, and classify each pair as `ENTAILMENT`, `NEUTRAL`, or `CONTRADICTION` using a fine-tuned NLI Cross-Encoder.
- **Deeper Explanation**: Using a model like `deberta-v3-large` fine-tuned on legal MNLI, the system would extract each claim $c_i$ and its attributed context passage $p_j$. If $P(\text{Entailment} \mid p_j, c_i) < 0.85$, the sentence would be flagged or pruned before display.
- **Code Reference**: [`docs/RAG_GROUNDING_AUDIT.md`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/docs/RAG_GROUNDING_AUDIT.md#L15-L25).

#### Q39: What would you do differently if you started this project again?
- **Short Answer**: Ingest the complete Constitution from day one before creating benchmarks, and use synthetic diverse query generation rather than repetitive template queries.
- **Deeper Explanation**: Creating benchmarks while the corpus was still evolving led to 20 queries targeting uncataloged provisions and shorthand identifier mismatches. Building a normalized, complete corpus first would have eliminated alias discrepancy issues early. Additionally, using diverse paraphrasing models for benchmark construction would reduce the 53% *"What/Explain"* template concentration.
- **Code Reference**: [`docs/BENCHMARK_QUALITY_REPORT.md`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/docs/BENCHMARK_QUALITY_REPORT.md#L20-L38).

#### Q40: What grade or outcome do you believe this capstone merits?
- **Short Answer**: An exceptional high-pass or honors grade for a B.Tech NLP capstone, based on its genuine 16-stage implementation, 254 passing tests, honest ablation benchmarks, and transparent disclosure of scientific limitations.
- **Deeper Explanation**: Unlike typical capstone projects that wrap an OpenAI API key in a trivial Streamlit box with zero evaluation, this repository implements genuine information retrieval algorithms (BM25, ChromaDB, RRF, Cross-Encoder, Legal NER), trains a custom intent classifier, curates four domain benchmark datasets, provides dual canonical evaluations, includes a live 10-stage diagnostic inspector, and demonstrates rigorous academic honesty regarding its boundaries.
- **Code Reference**: All 20 test suites in [`tests/`](file:///c:/Users/ramsa/Desktop/Indian%20Constitution%20Legal%20AI%20Assistant/tests).

---

## 6. Examiner Quick-Reference Matrix

| Topic | Primary File | Key Parameter / Equation | Benchmark Performance |
|---|---|---|---|
| **BM25 Lexical** | `retrieval/bm25_retriever.py` | $k_1 = 1.5, b = 0.75$ | Hit@1: 0.7900, MRR: 0.8271, Latency: 3.75 ms |
| **Dense Vector** | `retrieval/dense_retriever.py` | `all-MiniLM-L6-v2` (384-d, Cosine) | Hit@1: 0.8100, MRR: 0.8385, Latency: 17.73 ms |
| **RRF Fusion** | `retrieval/rrf.py` | $\sum \frac{1}{60 + r_m(d)}$ | Hit@1: 0.8100, MRR: 0.8396, Latency: 21.89 ms |
| **Entity Boost** | `retrieval/entity_boost.py` | $\text{Score} + 0.15$ | Hit@1: 0.8200, MRR: 0.8421, Latency: 68.03 ms |
| **Cross-Encoder** | `retrieval/reranker.py` | `ms-marco-MiniLM-L-6-v2` (Top 30 $\to$ 5) | Hit@1: **0.8400**, MRR: **0.8583**, NDCG@10: **0.7787** |
| **Legal NER** | `nlp/legal_ner.py` | 10 classes, exact span matching | Micro-F1: **0.8714**, Macro-F1: **0.8496** |
| **Intent Class** | `nlp/intent_classifier.py` | TF-IDF (1,2) + LogReg ($C=1.0$) | Test Acc: **0.8485**, 5-Fold CV: **0.7591** |
| **Confidence** | `rag/confidence.py` | 6 weighted signals ($C \ge 0.30$) | Abstention Acc: **1.0000** |
| **Test Suite** | `tests/` | 20 test files | **254 / 254 passed** in pytest (0 errors) |
