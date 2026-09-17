# ⚖️ Indian Constitution Legal AI Assistant (Advanced RAG)

A production-ready, modular **Indian Constitution Legal AI Assistant** utilizing Advanced Retrieval-Augmented Generation (RAG) techniques, hierarchical Parent-Child chunking, Hybrid BM25 + Vector Search with Reciprocal Rank Fusion (RRF), Legal Named Entity Recognition (NER), and a Multi-Agent Router powered by **Google Gemini** (with zero-cost offline heuristic fallback).

---

## 🌟 Key Architectural Features

### 1. Hierarchical Parent-Child RAG
* **Parent Store**: Full Constitutional Articles and Supreme Court Judgments stored as complete context documents.
* **Child Chunks**: Passages (~200–300 tokens / 300 chars) indexed for precision vector and sparse keyword retrieval.
* **Provenance & Grounding**: Search matches high-precision child chunks, which automatically hydrate full Parent contexts for generation.

### 2. Hybrid Search Engine (BM25 + Dense Vector + RRF)
* **Sparse Search**: `rank_bm25` (BM25Okapi) keyword matching for exact legal terminology and Article numbers.
* **Dense Search**: `ChromaDB` with `sentence-transformers/all-MiniLM-L6-v2` dense vector embeddings.
* **Reciprocal Rank Fusion (RRF)**: Merges sparse and dense search rankings using $RRF\_Score(d) = \sum \frac{1}{k + r_m(d)}$.
* **Legal NER Pre-processing**: Extracts Articles (e.g. *Article 21*), Case Names (e.g. *Kesavananda Bharati*), and Legal Concepts to boost rank precision.

### 3. Multi-Agent Router
* **Article Agent**: Handles retrieval of exact Constitutional Articles, Clauses, Parts, and Amendments.
* **Case-Law Agent**: Summarizes landmark judgments, ratios decidendi, facts, bench details, and compares similar cases.
* **Explanation Agent**: Simplifies complex legalese into clear, empathetic plain language for citizens and students.
* **LLM Engine**: Powered by **Google Gemini** (`gemini-2.5-flash` / `gemini-1.5-flash`) via `langchain-google-genai`, with automatic fallback to an offline **Heuristic Legal Synthesizer** if no API key is provided.

### 4. Interactive Streamlit Interface
* **Auto-Routing vs Manual Agent Override**.
* **Expandable Source Attribution Tabs**: Inspect retrieved child passages alongside hydrated parent documents.
* **Side-by-Side Landmark Case Comparator**.
* **Database Explorer**: Interactive data tables for Constitution Articles and SC Judgments.
* **Live API Key Input**: Enter your Gemini key directly in the sidebar or load via `.env` / Streamlit secrets.

---

## 📁 Repository Structure

```
├── .env                          # Local environment variables (GEMINI_API_KEY)
├── .gitignore                    # Git ignore file for venv, caches, and secrets
├── config.py                     # Centralized settings, paths, & hyper-parameters
├── data/
│   ├── sample_constitution.json  # Curated Constitutional Articles dataset
│   └── sample_judgments.json     # Curated Supreme Court Judgments dataset
├── ingestion.py                  # Parent-Child chunking, ChromaDB & BM25 indexing
├── retriever.py                  # Legal NER & Hybrid RRF Search Engine
├── agents.py                     # Multi-Agent Router & Google Gemini LLM Engine
├── app.py                        # Streamlit Web User Interface
├── requirements.txt              # Dependencies list (cross-platform & Streamlit Cloud ready)
├── .streamlit/
│   └── secrets.toml.example      # Example secrets template for Streamlit Cloud
└── README.md                     # System documentation & setup guide
```

---

## 🛠️ Quickstart & Local Setup Guide

### 1. Prerequisites
Ensure you have Python 3.10+ installed.

### 2. Set Up Virtual Environment (`venv`)

**Windows PowerShell:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
Install all required libraries using `pip`:

```bash
pip install -r requirements.txt
```

### 4. (Optional) Configure Google Gemini API Key
You can get a free Google Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

1. Open the `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ```
2. Alternatively, enter the key directly in the Streamlit web sidebar when the application is running!
*(Note: If no key is entered, the app runs 100% offline using the built-in grounded Legal Synthesis Engine).*

### 5. Launch the Streamlit Web Application
Run the Streamlit app:

```bash
streamlit run app.py
```

Open your browser to `http://localhost:8501`.

---

## ☁️ Deploying to Streamlit Cloud

This repository is pre-configured for 1-click deployment on [Streamlit Community Cloud](https://share.streamlit.io):

1. **Push your code to GitHub**:
   Ensure `.gitignore` is present (so `venv/`, `.env`, and local caches are not committed).
2. **Create New App on Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io).
   - Select your GitHub repository and branch (`main`).
   - Set **Main file path** to: `app.py`.
3. **Set Secrets (Optional for Gemini)**:
   - In **Advanced Settings** -> **Secrets**, paste:
     ```toml
     GEMINI_API_KEY = "your-google-gemini-api-key"
     ```
4. **Deploy**:
   - Click **Deploy!**
   - The app will automatically install dependencies from `requirements.txt` (including `pysqlite3-binary` for Linux), initialize the parent-child vector index, and launch smoothly!

---

## 🧪 Verification & Testing

You can test individual modules directly from the command line:

* **Test Retriever & Legal NER**:
  ```bash
  python retriever.py
  ```

* **Test Multi-Agent Router**:
  ```bash
  python agents.py
  ```

* **Test Ingestion Pipeline**:
  ```bash
  python ingestion.py
  ```

---

## 📜 License
Developed for educational and legal research purposes under the MIT License.
