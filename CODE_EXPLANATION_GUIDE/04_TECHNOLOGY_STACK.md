# 04: Technology Stack & Technical Dependencies 🛠️

---

## 1. Complete Technology Stack Matrix

This project uses an intentionally curated, modern, production-grade Python stack designed for **high-accuracy legal retrieval, offline capability, reproducible evaluation, and zero-crash execution**.

| Technology | Exact Version / Dependency | Role in Architecture | Why It Was Chosen Over Alternatives |
|---|---|---|---|
| **Python** | `3.10+` (Developed on `3.12.10`) | Core programming language | Modern typing support, high-performance runtime, rich NLP ecosystem. |
| **Streamlit** | `>= 1.30.0` (Running `1.64.0`) | Interactive web application UI | Fast, reactive, stateful UI development with Python; eliminated need for complex React/Node frontends. |
| **ChromaDB** | `>= 0.4.22` (Running `1.5.9`) | Persistent vector database | Embedded, local SQLite-backed vector store; requires no external Docker or cloud daemon (unlike Pinecone or Qdrant). |
| **Rank-BM25** | `>= 0.2.2` | Sparse lexical keyword retrieval | Pure-Python BM25Okapi implementation; easy to augment with custom statutory compound tokenization. |
| **Sentence-Transformers** | `>= 2.2.2` | Dense embedding and cross-encoder inference | Standard Hugging Face library for running transformer bi-encoders and cross-attention rerankers. |
| **BAAI/bge-m3** | Pretrained Model (1024-d) | Primary dense semantic embedding model | State-of-the-art multilingual and multi-granularity model supporting long legal contexts up to 8,192 tokens. |
| **all-MiniLM-L6-v2** | Pretrained Model (384-d) | Lightweight baseline embedding model | Extremely fast CPU inference (384 dimensions) for resource-constrained environments. |
| **ms-marco-MiniLM-L-6-v2** | Pretrained Cross-Encoder | Neural query-passage reranker | Evaluates full joint cross-attention over top-30 candidate pairs, lifting NDCG@10 to 0.7787. |
| **Scikit-Learn** | `>= 1.4.0` (Running `1.9.1`) | Machine learning & evaluation | TF-IDF vectorization, Logistic Regression intent classification, stratified cross-validation, and metrics. |
| **PyTorch** | `>= 2.0.0` (`torch+cpu`) | Deep learning tensor engine | Multi-threaded CPU forward-pass execution for SentenceTransformer inference without requiring an Nvidia GPU. |
| **Pydantic** | `>= 2.0.0` (Pydantic V2) | Strict schema validation | Enforces type integrity and document constraints on `LegalDocument`, `ChildChunk`, and `PipelineResult`. |
| **LangChain Core & Google GenAI** | `>= 0.1.0` / `>= 1.0.0` | LLM prompt templating & invocation | Provides structured prompt chaining for Google Gemini (`gemini-3.8-flash`) with automatic fallback to offline synthesis. |
| **Google Generative AI** | `>= 0.7.0` | Official Google Gemini SDK | Direct low-latency API integration for generative legal answer synthesis. |
| **Pandas & NumPy** | `>= 2.0.0` / `>= 1.24.0` | Data manipulation & vector math | Fast tabular manipulation of benchmark results, cosine similarity vector calculations, and array slicing. |
| **Pytest** | `>= 8.0.0` (Running `9.1.0`) | Automated test framework | Powers the 319-test automated regression, integrity, and smoke test suite with 100% pass rate. |
| **python-dotenv** | `>= 1.0.0` | Environment variable management | Loads `.env` secrets (such as `GEMINI_API_KEY`) securely into runtime configuration. |

---

## 2. Deep Dive: Key Technical Choices & Justifications

### 2.1 Why ChromaDB Instead of Pinecone or Milvus?
1. **Zero External Infrastructure**: Pinecone is a closed-source cloud SaaS requiring paid subscriptions and network calls for every query. Milvus requires complex Docker container orchestration. ChromaDB runs embedded directly inside the Python process using a local SQLite file (`chroma_db/chroma.sqlite3`).
2. **Offline Capable**: Students, evaluators, and judges can run the entire system on a laptop without internet connectivity.
3. **Deterministic Persistence**: ChromaDB saves all vectors to disk permanently, meaning embeddings are computed once during ingestion and loaded instantly during application runtime.

### 2.2 Why Both BM25 and BGE-M3 (Hybrid Search)?
- **BM25** excels at exact keyword matches (statutory numbers, specific case names like *"Kesavananda"*). However, it fails completely when a user describes a situation using colloquial language (*"Can police take my laptop"*).
- **Dense Vector Search (`BAAI/bge-m3`)** excels at capturing conceptual semantics (understanding that *"taking private belongings"* relates to *"seizure of property"* and *"personal liberty"*). However, it struggles with exact section numbers (confusing *Article 21* with *Article 21A*).
- **The Hybrid Synthesis**: By pairing both models through **Reciprocal Rank Fusion (RRF)** ($k=60$) and an additive Legal Entity Boost ($+0.15$), the system gets the best of both worlds: conceptual semantic understanding without losing statutory precision.

### 2.3 Why a Cross-Encoder Reranker?
- In standard Bi-Encoder dense search, the query vector $\vec{q}$ and document vector $\vec{d}$ are computed **independently**:
  $$\text{Score} = \cos(\vec{q}, \vec{d}) = \frac{\vec{q} \cdot \vec{d}}{\|\vec{q}\| \|\vec{d}\|}$$
  Because $\vec{q}$ and $\vec{d}$ are compressed into fixed-size vectors separately, subtle interactions between specific words are lost.
- A **Cross-Encoder** feeds the query and document **together** into the transformer as a single concatenated input sequence:
  $$\text{Input} = \text{[CLS]} + \text{Query} + \text{[SEP]} + \text{Document} + \text{[SEP]}$$
  Every query token attends directly to every document token via full cross-attention. This produces vastly superior relevance judgments, lifting NDCG@10 from **0.5484** (BM25) and **0.6558** (Hybrid RRF) to **0.7787** (Full Pipeline).

### 2.4 Why Parent-Child Chunking Instead of Single-Chunk RAG?
- **The Dilemma**:
  - If you chunk text into **small pieces** (~300 characters), your vector search is very precise, but when the LLM receives the small chunk to generate an answer, it lacks surrounding context (e.g., missing exceptions or qualifying provisos).
  - If you chunk text into **large pieces** (~2,000 characters), the embeddings become diluted with unrelated paragraphs, and retrieval accuracy drops sharply.
- **The Solution (Parent-Child Architecture)**:
  - You index **small, structure-aware child chunks** (~300 characters) in ChromaDB and BM25 for maximum retrieval precision.
  - When a child chunk wins, you look up its `parent_id` in `parent_store.json` and dynamically pass the **entire parent Article or Judgment** (~1,200 characters) to the generator.
  - Result: **Laser-accurate retrieval + Complete legal context!**

---

## 3. Dependencies File: `requirements.txt`

The actual [`requirements.txt`](../requirements.txt) in the repository root contains:

```text
streamlit>=1.30.0
pysqlite3-binary; sys_platform == 'linux'
chromadb>=0.4.22
rank-bm25>=0.2.2
sentence-transformers>=2.2.2
langchain>=0.1.0
langchain-community>=0.0.10
langchain-core>=0.1.10
langchain-google-genai>=1.0.0
google-generativeai>=0.7.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.4.0
pytest>=8.0.0
```

> [!NOTE]
> The line `pysqlite3-binary; sys_platform == 'linux'` is a specialized patch for Linux servers and Streamlit Cloud. Standard Linux distributions often ship with an older SQLite version ($< 3.35.0$) that ChromaDB rejects. This package safely patches Python's standard `sqlite3` module at runtime (see [`app.py`](../app.py#L6-L12)). On Windows, standard Python already ships with a modern SQLite engine, so this dependency is safely skipped.

---

## 4. What's Next?

Now that you understand the architectural foundations and technical stack, proceed to **Part II: Deep Codebase Walkthroughs**, starting with [**`05_MAIN_APPLICATION/app_py.md`**](05_MAIN_APPLICATION/app_py.md).

