"""
Streamlit Web Application for the Indian Constitution Legal AI Assistant.
Features:
- Conversational QA with Multi-Agent Routing (Article, Case-Law, Explanation Agents)
- Parent-Child RAG Source Attribution tabs (Child passages + Full Parent context)
- Side-by-side Landmark Case Comparator
- Constitutional Articles & SC Judgments Explorer
- Rich UI with dark theme, glassmorphism badges, and custom CSS
"""

# Linux / Streamlit Cloud SQLite3 compatibility patch for ChromaDB
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import json
import streamlit as st
import pandas as pd

from config import DEFAULT_TOP_K, GEMINI_API_KEY, DEFAULT_LLM_MODEL
from ingestion import ParentChildIngestor
from retriever import HybridRRFRetriever, LegalNERExtractor
from agents import MultiAgentRouter

# Configure Streamlit Page
st.set_page_config(
    page_title="Indian Constitution Legal AI Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Legal Theme Aesthetics
CUSTOM_CSS = """
<style>
    /* Dark Deep Navy Theme Styling */
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main Header Styling */
    .main-header {
        background: linear-gradient(135deg, #161b22 0%, #1f2937 50%, #0d1117 100%);
        padding: 1.8rem 2rem;
        border-radius: 12px;
        border: 1fr solid #30363d;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        margin-bottom: 2rem;
        text-align: center;
    }
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #d4af37 0%, #f3e5ab 50%, #e6ca65 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: 0.5px;
    }
    .main-subtitle {
        color: #8b949e;
        font-size: 1.05rem;
        margin-top: 0.4rem;
    }

    /* Glassmorphic Metric Cards */
    .metric-card {
        background: rgba(22, 27, 34, 0.75);
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #d4af37;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Agent Badge Styling */
    .agent-badge {
        display: inline-block;
        padding: 0.35rem 0.85rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .badge-article {
        background-color: rgba(56, 139, 253, 0.15);
        color: #58a6ff;
        border: 1px solid #1f6feb;
    }
    .badge-case {
        background-color: rgba(212, 175, 55, 0.15);
        color: #d4af37;
        border: 1px solid #b89628;
    }
    .badge-explain {
        background-color: rgba(46, 160, 67, 0.15);
        color: #3fb950;
        border: 1px solid #238636;
    }

    /* Entity Pills */
    .entity-pill {
        display: inline-block;
        background-color: #21262d;
        border: 1px solid #30363d;
        color: #c9d1d9;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.8rem;
        margin-right: 0.4rem;
        margin-bottom: 0.4rem;
    }

    /* Source Attribution Expanders */
    .source-card {
        background-color: #161b22;
        border-left: 4px solid #d4af37;
        padding: 1rem;
        border-radius: 4px;
        margin-bottom: 0.8rem;
    }

    /* Comparison Table Styling */
    .comp-box {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 1.2rem;
        height: 100%;
    }
    .comp-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #d4af37;
        border-bottom: 1px solid #30363d;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# Initialize Core RAG Components with Caching
@st.cache_resource(show_spinner="[SYSTEM] Initializing Parent-Child RAG Engine & Embedding Models...")
def load_rag_pipeline():
    ingestor = ParentChildIngestor()
    ingestor.run_pipeline()
    retriever = HybridRRFRetriever(ingestor)
    router = MultiAgentRouter()
    return ingestor, retriever, router


ingestor, retriever, router = load_rag_pipeline()


# HEADER SECTION
st.markdown(
    """
    <div class="main-header">
        <h1 class="main-title">⚖️ Indian Constitution Legal AI Assistant</h1>
        <div class="main-subtitle">
            Advanced Hierarchical Parent-Child RAG | Hybrid BM25 + Dense Vector Search (RRF) | Legal Multi-Agent Router
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# SIDEBAR CONFIGURATION
with st.sidebar:
    st.image("https://img.icons8.com/color/96/scales.png", width=64)
    st.title("⚙️ Control Panel")
    
    st.markdown("---")
    st.subheader("🤖 Agent Configuration")
    agent_override = st.selectbox(
        "Agent Selection Mode",
        options=["Auto-route", "Article Agent", "Case-Law Agent", "Explanation Agent"],
        help="Auto-route classifies queries automatically using Legal NER & keywords, or manually override to a specific specialized agent."
    )

    st.markdown("---")
    st.subheader("🔍 Retrieval Hyper-Parameters")
    top_k = st.slider("Top-K Retrieved Contexts", min_value=2, max_value=8, value=DEFAULT_TOP_K)

    st.markdown("---")
    st.subheader("📊 System Metrics")
    m1, m2 = st.columns(2)
    with m1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{len(ingestor.parent_store)}</div>
                <div class="metric-label">Parent Contexts</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with m2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{len(ingestor.child_chunks)}</div>
                <div class="metric-label">Child Chunks</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.subheader("🔑 Google Gemini API")
    user_api_key = st.text_input(
        "Gemini API Key (Optional)",
        type="password",
        value=GEMINI_API_KEY or "",
        help="Enter your Google AI Studio API Key. If left blank, the app uses the offline zero-cost Legal Synthesis Engine."
    )
    if user_api_key and len(user_api_key.strip()) > 5:
        st.success(f"🟢 Gemini Active (`{DEFAULT_LLM_MODEL}`)")
    else:
        st.info("ℹ️ Offline Synthesis Mode (Free / Zero-cost)")

    st.markdown("---")
    st.caption("🔒 **Security & Grounding**: Strict context enforcement (Zero Hallucination mode enabled).")


# MAIN NAVIGATION TABS
tab1, tab2, tab3, tab4 = st.tabs([
    "💬 Ask Assistant & RAG Query",
    "⚖️ Case Comparator",
    "📜 Constitution & Cases Database",
    "🏗️ RAG Architecture & Methodology"
])


# ---------------------------------------------------------
# TAB 1: ASK ASSISTANT & RAG QUERY
# ---------------------------------------------------------
with tab1:
    st.subheader("🔍 Ask a Legal Question or Search Articles / Cases")
    
    # Preset Query Gallery
    st.markdown("**Sample Benchmark Queries:**")
    col1, col2, col3 = st.columns(3)
    preset_q = ""
    with col1:
        if st.button("📌 Privacy under Art. 21 (Puttaswamy)", use_container_width=True):
            preset_q = "What did the Supreme Court rule regarding the Right to Privacy under Article 21 in the Puttaswamy judgment?"
        if st.button("📌 Basic Structure (Kesavananda)", use_container_width=True):
            preset_q = "Explain the Basic Structure Doctrine established in Kesavananda Bharati v. State of Kerala."
    with col2:
        if st.button("📌 Due Process (Maneka Gandhi)", use_container_width=True):
            preset_q = "How did Maneka Gandhi v. Union of India expand Article 21 and create the Golden Triangle?"
        if st.button("📌 Remedies under Article 32", use_container_width=True):
            preset_q = "What constitutional writs are guaranteed under Article 32 and why did Dr. Ambedkar call it the heart and soul?"
    with col3:
        if st.button("📌 Compare Kesavananda vs Minerva Mills", use_container_width=True):
            preset_q = "Compare Kesavananda Bharati and Minerva Mills regarding Parliament's power to amend the Constitution."
        if st.button("📌 Status of Article 370", use_container_width=True):
            preset_q = "What are the provisions and historical context of Article 370?"

    # Search Bar Input
    user_query = st.text_input(
        "Enter your legal prompt or constitutional question:",
        value=preset_q if preset_q else "",
        placeholder="e.g. Can Parliament amend Fundamental Rights under Article 368?",
        key="user_search_input"
    )

    if st.button("🚀 Submit Query to RAG Pipeline", type="primary", use_container_width=True) or user_query:
        if user_query.strip():
            with st.spinner("⚡ Executing Legal NER, Hybrid RRF Retrieval, & Multi-Agent Routing..."):
                # Step 1: Legal NER & Hybrid Retrieval
                retrieval_output = retriever.retrieve(user_query, top_k=top_k)
                entities = retrieval_output["entities"]
                context_docs = retrieval_output["results"]

                # Step 2: Route & Classify Query
                classified_agent = router.classify_query(user_query, entities, override_mode=agent_override)

                # Step 3: Execute Agent Generation
                agent_result = router.execute_agent(
                    classified_agent,
                    user_query,
                    context_docs,
                    entities,
                    dynamic_api_key=user_api_key
                )

            # DISPLAY RESULTS
            st.markdown("---")

            # Agent Badge & Extracted Entities
            b_class = "badge-article" if classified_agent == "article_agent" else ("badge-case" if classified_agent == "case_law_agent" else "badge-explain")
            model_info = f"🧠 {agent_result.get('model_name', 'AI Engine')}"
            st.markdown(
                f"""
                <span class="agent-badge {b_class}">
                    🤖 Active Agent: {agent_result['agent_name']}
                </span>
                <span class="agent-badge" style="background-color: rgba(139, 148, 158, 0.15); color: #c9d1d9; border: 1px solid #30363d;">
                    {model_info}
                </span>
                """,
                unsafe_allow_html=True
            )

            # Extracted Legal Entities
            st.markdown("**Extracted Legal Entities (NER):**")
            ent_str = ""
            for art in entities.get("articles", []):
                ent_str += f'<span class="entity-pill">📜 {art}</span>'
            for c_name in entities.get("cases", []):
                ent_str += f'<span class="entity-pill">⚖️ {c_name}</span>'
            for concept in entities.get("concepts", []):
                ent_str += f'<span class="entity-pill">💡 {concept.title()}</span>'
            
            if ent_str:
                st.markdown(ent_str, unsafe_allow_html=True)
            else:
                st.caption("No specific named articles or cases detected in query.")

            st.markdown("<br>", unsafe_allow_html=True)

            # Agent Answer Response
            st.markdown(agent_result["response"])

            # EXPANDABLE SOURCE ATTRIBUTION TABS (Parent-Child RAG)
            st.markdown("---")
            st.subheader("📚 Source Attribution & RAG Provenance")
            st.caption("Parent-Child RAG: Precision Child passages were matched via Hybrid RRF Search and expanded into full Parent contexts below.")

            for r_idx, doc in enumerate(context_docs, start=1):
                pdata = doc.get("parent_data", {})
                title_label = f"Result #{r_idx} | RRF Score: {doc['rrf_score']} | "
                if doc["doc_type"] == "constitution":
                    title_label += f"📜 {pdata.get('article_number')} - {pdata.get('title')}"
                else:
                    title_label += f"⚖️ {pdata.get('case_name')} ({pdata.get('year')})"

                with st.expander(title_label):
                    col_c, col_p = st.columns([1, 1])
                    with col_c:
                        st.markdown("##### 🔍 Retrieved Child Chunk (Vector + BM25 Match)")
                        st.info(f"\"{doc['child_text']}\"")
                        st.markdown(f"**RRF Fusion Score**: `{doc['rrf_score']}`")
                        st.markdown(f"**BM25 Rank**: `{doc['bm25_rank']}` | **Vector Rank**: `{doc['vector_rank']}`")

                    with col_p:
                        st.markdown("##### 📖 Hydrated Parent Document (Full Context)")
                        if doc["doc_type"] == "constitution":
                            st.markdown(f"**Article Number**: {pdata.get('article_number')}")
                            st.markdown(f"**Part**: {pdata.get('part')}")
                            st.markdown(f"**Category**: {pdata.get('category')}")
                            st.markdown(f"**Full Text**:\n> *{pdata.get('raw_text')}*")
                            if pdata.get("explanation"):
                                st.markdown(f"**Explanation**: {pdata.get('explanation')}")
                        else:
                            st.markdown(f"**Case Name**: {pdata.get('case_name')}")
                            st.markdown(f"**Citation**: `{pdata.get('citation')}`")
                            st.markdown(f"**Bench**: {pdata.get('bench')}")
                            st.markdown(f"**Ratio Decidendi**: {pdata.get('ratio_decidendi')}")
                            st.markdown(f"**Verdict**: {pdata.get('verdict')}")


# ---------------------------------------------------------
# TAB 2: CASE COMPARATOR
# ---------------------------------------------------------
with tab2:
    st.subheader("⚖️ Landmark Supreme Court Case Comparator")
    st.caption("Select two landmark Supreme Court judgments for side-by-side comparative analysis.")

    judg_data = [p for p in ingestor.parent_store.values() if p.get("doc_type") == "judgment"]
    case_names = [j["case_name"] for j in judg_data]

    if len(case_names) >= 2:
        c1, c2 = st.columns(2)
        with c1:
            case_a_name = st.selectbox("Select Primary Case (Case A):", options=case_names, index=0)
        with c2:
            case_b_name = st.selectbox("Select Comparison Case (Case B):", options=case_names, index=1 if len(case_names) > 1 else 0)

        case_a = next((j for j in judg_data if j["case_name"] == case_a_name), None)
        case_b = next((j for j in judg_data if j["case_name"] == case_b_name), None)

        if case_a and case_b:
            st.markdown("<br>", unsafe_allow_html=True)
            col_left, col_right = st.columns(2)

            with col_left:
                st.markdown(
                    f"""
                    <div class="comp-box">
                        <div class="comp-title">🏛️ {case_a['case_name']}</div>
                        <p><strong>Year:</strong> {case_a['year']} | <strong>Bench:</strong> {case_a['bench']}</p>
                        <p><strong>Citation:</strong> <code>{case_a['citation']}</code></p>
                        <p><strong>Articles Referred:</strong> {', '.join(case_a.get('articles_referred', []))}</p>
                        <hr style="border-color: #30363d;">
                        <p><strong>Facts:</strong><br>{case_a['facts']}</p>
                        <hr style="border-color: #30363d;">
                        <p><strong>Ratio Decidendi:</strong><br>{case_a['ratio_decidendi']}</p>
                        <hr style="border-color: #30363d;">
                        <p><strong>Verdict:</strong><br>{case_a['verdict']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col_right:
                st.markdown(
                    f"""
                    <div class="comp-box">
                        <div class="comp-title">🏛️ {case_b['case_name']}</div>
                        <p><strong>Year:</strong> {case_b['year']} | <strong>Bench:</strong> {case_b['bench']}</p>
                        <p><strong>Citation:</strong> <code>{case_b['citation']}</code></p>
                        <p><strong>Articles Referred:</strong> {', '.join(case_b.get('articles_referred', []))}</p>
                        <hr style="border-color: #30363d;">
                        <p><strong>Facts:</strong><br>{case_b['facts']}</p>
                        <hr style="border-color: #30363d;">
                        <p><strong>Ratio Decidendi:</strong><br>{case_b['ratio_decidendi']}</p>
                        <hr style="border-color: #30363d;">
                        <p><strong>Verdict:</strong><br>{case_b['verdict']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )


# ---------------------------------------------------------
# TAB 3: CONSTITUTION & CASES DATABASE
# ---------------------------------------------------------
with tab3:
    st.subheader("📜 Constitutional Articles & Judgments Database Explorer")
    
    sub_tab1, sub_tab2 = st.tabs(["Constitutional Articles", "Landmark Supreme Court Judgments"])

    with sub_tab1:
        const_records = [p for p in ingestor.parent_store.values() if p.get("doc_type") == "constitution"]
        df_const = pd.DataFrame(const_records)[["article_number", "title", "part", "category", "raw_text", "explanation"]]
        df_const.columns = ["Article Number", "Title", "Part", "Category", "Text", "Explanation"]
        st.dataframe(df_const, use_container_width=True, height=450)

    with sub_tab2:
        judg_records = [p for p in ingestor.parent_store.values() if p.get("doc_type") == "judgment"]
        df_judg = pd.DataFrame(judg_records)[["case_name", "citation", "year", "bench", "ratio_decidendi", "verdict"]]
        df_judg.columns = ["Case Name", "Citation", "Year", "Bench", "Ratio Decidendi", "Verdict"]
        st.dataframe(df_judg, use_container_width=True, height=450)


# ---------------------------------------------------------
# TAB 4: RAG ARCHITECTURE & METHODOLOGY
# ---------------------------------------------------------
with tab4:
    st.subheader("🏗️ System Architecture & Advanced RAG Technical Specs")
    
    st.markdown("""
    ### 1. Data Layer & Hierarchical Parent-Child RAG
    - **Parent Store**: Stores full Constitutional Articles (Parts, Text, Explanations, Historical Context) and complete Supreme Court Judgment ratios and facts.
    - **Child Chunks**: Passages (~300 characters) are generated from parent texts with chunk overlaps. Child chunks store references to their parent `parent_id`.
    - **Embeddings**: Local `sentence-transformers/all-MiniLM-L6-v2` dense vector representations stored in **ChromaDB**.

    ### 2. Hybrid Retrieval Engine & Reciprocal Rank Fusion (RRF)
    - **Sparse Search**: **BM25Okapi** keyword scoring with legal text tokenization ($k_1=1.5, b=0.75$).
    - **Dense Search**: Cosine similarity embedding search via **ChromaDB**.
    - **Reciprocal Rank Fusion (RRF)**:
      Combines sparse and dense ranks according to:
      $$RRF\\_Score(d) = \\sum_{m \\in M} \\frac{1}{k + r_m(d)}$$
      where $k = 60$.
    - **Legal Named Entity Recognition (NER)**: Identifies Article numbers (e.g. *Article 21*), landmark case names (e.g. *Puttaswamy*), and legal concepts, applying rank boosting for exact metadata matches.

    ### 3. Multi-Agent Router
    - **Article Agent**: Provides detailed constitutional provisions, clauses, and amendments.
    - **Case-Law Agent**: Summarizes judgments, facts, ratios decidendi, and precedent comparisons.
    - **Explanation Agent**: Simplifies complex legal legalese into accessible plain English/Hindi for citizens and students.
    """)
