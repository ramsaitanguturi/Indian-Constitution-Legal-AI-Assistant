"""
Streamlit Web Application for the Indian Constitution Legal AI Assistant.
A minimal, clean, professional legal research assistant interface.
"""

# Linux / Streamlit Cloud SQLite3 compatibility patch for ChromaDB
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st
import pandas as pd
import chromadb

from config import (
    DEFAULT_TOP_K,
    GEMINI_API_KEY,
    DEFAULT_LLM_MODEL,
    DEFAULT_EMBEDDING_MODEL,
    CHROMA_PERSIST_DIR,
    get_chroma_collection_name,
)
from ingestion import ParentChildIngestor
from retriever import HybridRRFRetriever
from agents import MultiAgentRouter
from rag.pipeline import get_legal_rag_pipeline, LegalRAGPipeline, PipelineResult
from rag.ui_formatter import format_legal_pipeline_result, FormattedLegalAnswer
from rag.pipeline_inspector import render_pipeline_inspector

# -----------------------------------------------------------------------------
# Streamlit Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Indian Constitution Legal AI Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# Minimal, Professional Legal-Tech Styling (Dark Theme Compatible)
# -----------------------------------------------------------------------------
MINIMAL_CSS = """
<style>
    /* Dark Theme Base */
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Minimal Compact Header */
    .app-header {
        padding: 0.8rem 0 1.2rem 0;
        border-bottom: 1px solid #21262d;
        margin-bottom: 1.5rem;
    }
    .app-title {
        font-size: 1.85rem;
        font-weight: 700;
        color: #f0f6fc;
        letter-spacing: -0.02em;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .app-subtitle {
        color: #8b949e;
        font-size: 0.95rem;
        margin: 0.35rem 0 0 0;
        font-weight: 400;
    }

    /* Section Headings */
    .legal-section-header {
        font-size: 1.15rem;
        font-weight: 600;
        color: #f0f6fc;
        border-bottom: 1px solid #30363d;
        padding-bottom: 0.4rem;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
        letter-spacing: -0.01em;
    }

    /* Direct Answer Box */
    .direct-answer-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-left: 3px solid #d4af37;
        border-radius: 6px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 1.2rem;
        line-height: 1.6;
        font-size: 1.02rem;
        color: #e6edf3;
    }

    /* Source & Citation Cards */
    .source-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.6rem;
    }
    .source-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 0.4rem;
        margin-bottom: 0.5rem;
    }
    .source-title {
        font-weight: 600;
        font-size: 0.95rem;
        color: #f0f6fc;
    }
    .source-id-tag {
        font-family: monospace;
        font-size: 0.78rem;
        background-color: #21262d;
        color: #8b949e;
        padding: 0.15rem 0.45rem;
        border-radius: 4px;
        border: 1px solid #30363d;
    }
    .source-excerpt {
        font-size: 0.88rem;
        color: #c9d1d9;
        line-height: 1.5;
        border-left: 2px solid #58a6ff;
        padding-left: 0.75rem;
        margin: 0.4rem 0;
        font-style: italic;
    }

    /* Subtle Metadata Badges */
    .badge-verified {
        display: inline-block;
        font-size: 0.75rem;
        padding: 0.15rem 0.5rem;
        border-radius: 12px;
        background-color: rgba(46, 160, 67, 0.15);
        color: #3fb950;
        border: 1px solid rgba(46, 160, 67, 0.4);
        font-weight: 500;
    }
    .badge-warning {
        display: inline-block;
        font-size: 0.75rem;
        padding: 0.15rem 0.5rem;
        border-radius: 12px;
        background-color: rgba(210, 153, 34, 0.15);
        color: #e3b341;
        border: 1px solid rgba(210, 153, 34, 0.4);
        font-weight: 500;
    }

    /* Structured Provision / Judgment Blocks */
    .provision-block, .judgment-block {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 0.85rem 1.1rem;
        margin-bottom: 0.75rem;
        font-size: 0.92rem;
        line-height: 1.55;
    }
    .provision-title, .judgment-title {
        font-weight: 600;
        color: #d4af37;
        margin-bottom: 0.4rem;
        font-size: 0.98rem;
    }
    .provision-meta, .judgment-meta {
        color: #8b949e;
        font-size: 0.82rem;
        margin-bottom: 0.4rem;
    }

    /* Exceptions Block */
    .exception-item {
        background-color: rgba(22, 27, 34, 0.6);
        border-left: 3px solid #e3b341;
        border-radius: 4px;
        padding: 0.7rem 1rem;
        margin-bottom: 0.6rem;
        font-size: 0.92rem;
        line-height: 1.5;
    }

    /* Text Area Styling */
    .stTextArea textarea {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 6px !important;
        color: #e6edf3 !important;
        font-size: 0.98rem !important;
    }
    .stTextArea textarea:focus {
        border-color: #58a6ff !important;
        box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.2) !important;
    }

    /* Button Styling */
    .stButton button[kind="primary"] {
        background-color: #238636 !important;
        border: 1px solid rgba(240, 246, 252, 0.1) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        padding: 0.55rem 1.2rem !important;
        font-size: 0.95rem !important;
    }
    .stButton button[kind="primary"]:hover {
        background-color: #2ea043 !important;
    }

    /* Remove unnecessary top space */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1080px !important;
    }

    /* -------------------------------------------------------------
       Compact Technical Metrics Dashboard
       ------------------------------------------------------------- */
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 0.6rem 0.8rem !important;
        margin-bottom: 0.35rem !important;
        min-height: 72px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    label[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] p,
    div[data-testid="stMetricLabel"] span,
    div[data-testid="stMetricLabel"] div {
        font-size: 13px !important;
        font-weight: 500 !important;
        color: #8b949e !important;
        line-height: 1.25 !important;
        margin: 0 !important;
        padding: 0 !important;
        letter-spacing: 0.01em;
    }

    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] > div,
    div[data-testid="stMetricValue"] p,
    div[data-testid="stMetricValue"] span {
        font-size: 19px !important;
        font-weight: 600 !important;
        color: #f0f6fc !important;
        white-space: normal !important;
        word-break: break-word !important;
        overflow-wrap: break-word !important;
        text-overflow: unset !important;
        overflow: visible !important;
        line-height: 1.3 !important;
        margin: 0.15rem 0 0 0 !important;
        padding: 0 !important;
    }

    div[data-testid="stMetricDelta"],
    div[data-testid="stMetricDelta"] p,
    div[data-testid="stMetricDelta"] span,
    div[data-testid="stMetricDelta"] div {
        font-size: 12px !important;
        font-weight: 500 !important;
        margin-top: 0.15rem !important;
        line-height: 1.2 !important;
        display: inline-flex !important;
        align-items: center !important;
    }

    div[data-testid="stMetricDelta"] svg {
        width: 12px !important;
        height: 12px !important;
        margin-right: 2px !important;
    }

    /* Supporting Metadata Captions (12-13px) */
    .stCaption,
    div[data-testid="stCaptionContainer"] p,
    div[data-testid="stCaptionContainer"] span {
        font-size: 12.5px !important;
        color: #8b949e !important;
        line-height: 1.4 !important;
    }

    /* Technical Details Expander & Container */
    div[data-testid="stExpander"] {
        border: 1px solid #30363d !important;
        border-radius: 6px !important;
        background-color: #0d1117 !important;
        margin-top: 0.8rem !important;
    }
    div[data-testid="stExpander"] details {
        border-radius: 6px !important;
        background-color: transparent !important;
    }
    div[data-testid="stExpander"] summary {
        background-color: #161b22 !important;
        color: #c9d1d9 !important;
        font-size: 0.92rem !important;
        font-weight: 600 !important;
        padding: 0.6rem 0.8rem !important;
        border-radius: 6px !important;
    }
    div[data-testid="stExpander"] summary:hover,
    div[data-testid="stExpander"] summary:focus,
    div[data-testid="stExpander"] summary:active {
        background-color: #21262d !important;
        color: #f0f6fc !important;
    }
    div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        padding: 0.75rem 0.9rem !important;
    }
</style>
"""

st.markdown(MINIMAL_CSS, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Initialize RAG Pipeline (Cached)
# -----------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def load_rag_pipeline():
    """
    Initializes and caches the Legal RAG Pipeline, Ingestor, Retriever, and Router.
    Ensures that vector store and embeddings are loaded only once.
    """
    client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
    col_name = get_chroma_collection_name(DEFAULT_EMBEDDING_MODEL)

    is_populated = False
    try:
        col = client.get_collection(col_name)
        if col.count() > 0:
            is_populated = True
    except Exception:
        col = None
        is_populated = False

    ingestor = ParentChildIngestor(model_name=DEFAULT_EMBEDDING_MODEL)
    if is_populated:
        ingestor.load_parent_store()
        ingestor.process_parent_child_chunks()
        ingestor.build_bm25_index()
        ingestor.collection = col
    else:
        ingestor.run_pipeline()

    retriever = HybridRRFRetriever(ingestor, embedding_model_name=DEFAULT_EMBEDDING_MODEL)
    router = MultiAgentRouter()
    stage4_pipeline = get_legal_rag_pipeline()
    return ingestor, retriever, router, stage4_pipeline


with st.spinner("Initializing legal knowledge base and retrieval engine..."):
    ingestor, retriever, router, stage4_pipeline = load_rag_pipeline()

# -----------------------------------------------------------------------------
# Session State Management
# -----------------------------------------------------------------------------
if "current_result" not in st.session_state:
    st.session_state.current_result = None
if "current_formatted" not in st.session_state:
    st.session_state.current_formatted = None
if "current_query" not in st.session_state:
    st.session_state.current_query = ""

# -----------------------------------------------------------------------------
# Compact Header
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="app-header">
        <h1 class="app-title">⚖️ Indian Constitution Legal AI Assistant</h1>
        <p class="app-subtitle">
            AI-powered legal research grounded in the Indian Constitution and Supreme Court judgments.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------------------------------
# Compact Sidebar Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.subheader("⚙️ Research Settings")
    top_k = st.slider(
        "Retrieval Sources (Top-K)",
        min_value=2,
        max_value=6,
        value=DEFAULT_TOP_K,
        help="Number of retrieved constitutional and judicial sources to consider."
    )

    user_api_key = st.text_input(
        "Google Gemini API Key (Optional)",
        type="password",
        value=GEMINI_API_KEY or "",
        help="Optional API Key for generative LLM expansion. Leave blank to use the offline deterministic Grounded Legal Engine."
    )
    if user_api_key and len(user_api_key.strip()) > 5:
        st.caption(f"🟢 Gemini Active (`{DEFAULT_LLM_MODEL}`)")
    else:
        st.caption("🔒 Offline Grounded Synthesis Engine (Zero-Cost / Deterministic)")

    st.markdown("---")
    st.caption(
        f"**Corpus Status**: {len(ingestor.parent_store)} verified parent documents, "
        f"{len(ingestor.child_chunks)} indexed passages.\n\n"
        f"**Embeddings**: `BGE-M3` (Dense) + BM25Okapi (Sparse RRF)."
    )

# -----------------------------------------------------------------------------
# Main Question Input
# -----------------------------------------------------------------------------
user_input = st.text_area(
    "Legal Question",
    placeholder="Ask a question about the Indian Constitution, fundamental rights, or landmark judgments...",
    height=100,
    label_visibility="collapsed",
    key="legal_query_input"
)

col_btn, _ = st.columns([1, 4])
with col_btn:
    ask_clicked = st.button("Ask Assistant", type="primary", use_container_width=True)

# -----------------------------------------------------------------------------
# Query Execution Workflow
# -----------------------------------------------------------------------------
if ask_clicked:
    query_str = user_input.strip()
    if query_str:
        with st.spinner("Analyzing constitutional provisions and case precedents..."):
            pipeline_result = stage4_pipeline.run(
                query_str,
                dynamic_api_key=user_api_key,
                override_top_k=top_k,
            )
            formatted_answer = format_legal_pipeline_result(pipeline_result)

            st.session_state.current_result = pipeline_result
            st.session_state.current_formatted = formatted_answer
            st.session_state.current_query = query_str
    else:
        st.warning("Please enter a legal question or constitutional query.")

# -----------------------------------------------------------------------------
# Render Results (Direct Answer, Provisions, Judgments, Exceptions, Sources)
# -----------------------------------------------------------------------------
if st.session_state.current_formatted:
    ans: FormattedLegalAnswer = st.session_state.current_formatted
    raw_res: PipelineResult = st.session_state.current_result

    # 1. Abstention / Notice State
    if ans.is_abstained:
        st.warning(
            f"**Notice of Abstention**: {ans.abstention_reason or 'Unable to verify legal grounds'}\n\n"
            f"{ans.direct_answer}"
        )
    else:
        # 2. Section C: Answer Section
        st.markdown('<div class="legal-section-header">Direct Answer</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="direct-answer-card">{ans.direct_answer}</div>',
            unsafe_allow_html=True
        )

        # Relevant Legal Provisions (when available)
        if ans.provisions:
            st.markdown('<div class="legal-section-header">Relevant Legal Provisions</div>', unsafe_allow_html=True)
            for prov in ans.provisions:
                meta_parts = []
                if prov.part:
                    meta_parts.append(prov.part)
                if prov.category:
                    meta_parts.append(prov.category)
                if prov.document_id:
                    meta_parts.append(f"Doc ID: `{prov.document_id}`")
                meta_str = " • ".join(meta_parts)

                st.markdown(
                    f"""
                    <div class="provision-block">
                        <div class="provision-title">📜 {prov.title}</div>
                        <div class="provision-meta">{meta_str}</div>
                        <div>{prov.scope_and_guarantee}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # Relevant Judgments (when available)
        if ans.judgments:
            st.markdown('<div class="legal-section-header">Relevant Judgments</div>', unsafe_allow_html=True)
            for j in ans.judgments:
                meta_parts = []
                if j.citation:
                    meta_parts.append(f"Citation: `{j.citation}`")
                if j.bench:
                    meta_parts.append(f"Bench: {j.bench}")
                if j.document_id:
                    meta_parts.append(f"Doc ID: `{j.document_id}`")
                meta_str = " • ".join(meta_parts)

                ratio_html = f"<div style='margin-top: 0.4rem;'><strong>Ratio Decidendi:</strong> {j.ratio_decidendi}</div>" if j.ratio_decidendi else ""
                verdict_html = f"<div style='margin-top: 0.3rem;'><strong>Verdict:</strong> {j.verdict}</div>" if j.verdict else ""

                st.markdown(
                    f"""
                    <div class="judgment-block">
                        <div class="judgment-title">⚖️ {j.case_name} ({j.year})</div>
                        <div class="judgment-meta">{meta_str}</div>
                        {verdict_html}
                        {ratio_html}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # Important Exceptions or Limitations (when available)
        if ans.exceptions:
            st.markdown('<div class="legal-section-header">Important Exceptions & Limitations</div>', unsafe_allow_html=True)
            for exc in ans.exceptions:
                st.markdown(
                    f'<div class="exception-item">{exc}</div>',
                    unsafe_allow_html=True
                )

        # 3. Section D: Legal Sources & Citations
        st.markdown('<div class="legal-section-header">Legal Sources & Citations</div>', unsafe_allow_html=True)
        
        parents_recovered = raw_res.parent_context.get("parents", [])
        if parents_recovered:
            for idx, p in enumerate(parents_recovered, start=1):
                doc_type = p.get("doc_type", "constitution")
                doc_id = p.get("document_id") or p.get("parent_id", f"source_{idx}")
                
                # Title and metadata formatting
                if doc_type == "constitution":
                    art_num = p.get("article_number", "Article")
                    title = p.get("title", "")
                    card_title = f"📜 {art_num} — {title}"
                    meta_desc = f"{p.get('part', '')} • {p.get('category', '')}"
                elif doc_type == "judgment":
                    c_name = p.get("case_name", "Judgment")
                    yr = p.get("year", "")
                    cit = p.get("citation", "")
                    card_title = f"⚖️ {c_name} ({yr})"
                    meta_desc = f"Citation: {cit} • Bench: {p.get('bench', '')}"
                else:
                    card_title = f"📑 {p.get('title', doc_id)}"
                    meta_desc = "Statute / Code"

                # Compact default excerpt
                children = p.get("supporting_children", [])
                if children and children[0].get("text"):
                    excerpt = children[0]["text"].strip()
                elif p.get("raw_text"):
                    excerpt = p.get("raw_text").strip()
                elif p.get("ratio_decidendi"):
                    excerpt = p.get("ratio_decidendi").strip()
                else:
                    excerpt = p.get("explanation", "")

                if len(excerpt) > 260:
                    excerpt = excerpt[:257] + "..."

                # Render compact source card
                st.markdown(
                    f"""
                    <div class="source-card">
                        <div class="source-card-header">
                            <div>
                                <span class="source-title">{card_title}</span>
                                <span class="source-id-tag">{doc_id}</span>
                            </div>
                            <span class="badge-verified">✓ Verified Citation</span>
                        </div>
                        <div style="font-size: 0.8rem; color: #8b949e; margin-bottom: 0.3rem;">{meta_desc}</div>
                        <div class="source-excerpt">"{excerpt}"</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Independent Streamlit expander for full retrieved legal text
                with st.expander(f"View full legal source: {card_title}", expanded=False):
                    if doc_type == "constitution":
                        st.markdown(f"**Article**: {p.get('article_number')} | **Part**: {p.get('part')}")
                        st.markdown(f"**Full Constitutional Text**:\n\n> {p.get('raw_text') or p.get('full_text')}")
                        if p.get("explanation"):
                            st.markdown(f"**Constitutional Explanation**: {p.get('explanation')}")
                        if p.get("historical_context"):
                            st.markdown(f"**Historical Context & Amendments**: {p.get('historical_context')}")
                    elif doc_type == "judgment":
                        st.markdown(f"**Formal Citation**: `{p.get('citation')}` | **Bench**: {p.get('bench')}")
                        if p.get("verdict"):
                            st.markdown(f"**Verdict**: {p.get('verdict')}")
                        if p.get("ratio_decidendi"):
                            st.markdown(f"**Ratio Decidendi**:\n\n> {p.get('ratio_decidendi')}")
                        if p.get("facts"):
                            st.markdown(f"**Facts of the Case**: {p.get('facts')}")
                    else:
                        st.markdown(f"**Statutory Title**: {p.get('title')}")
                        st.markdown(f"**Full Text**:\n\n> {p.get('raw_text') or p.get('full_text')}")

                    if children:
                        st.markdown("**Retrieved Supporting Passages**:")
                        for ch in children:
                            st.caption(f"• `{ch.get('chunk_id')}` (Rerank score: `{ch.get('score', 0):.4f}`): {ch.get('text', '')[:200]}...")

        # 4. Section E: Technical Details Expander
        with st.expander("Technical Details & Verification Audit", expanded=False):
            col_t1, col_t2, col_t3, col_t4 = st.columns(4)
            with col_t1:
                st.metric("Strategy", ans.strategy)
            with col_t2:
                st.metric("Query Intent", ans.intent)
            with col_t3:
                st.metric("Confidence", f"{ans.confidence_score:.2f}", ans.confidence_level)
            with col_t4:
                st.metric("Citations Checked", f"{ans.citations_checked_count} Validated")

            st.caption(
                f"**Language**: `{ans.language}` | "
                f"**Parent Contexts Hydrated**: `{raw_res.parent_context.get('parent_count', 0)}` | "
                f"**Child Chunks Retrieved**: `{len(raw_res.retrieved_chunks)}`"
            )

            # Extracted Legal Entities
            if ans.extracted_entities:
                st.markdown("**Extracted Named Legal Entities:**")
                ent_items = []
                for k, vals in ans.extracted_entities.items():
                    if vals:
                        ent_items.append(f"**{k}**: {', '.join(vals)}")
                if ent_items:
                    st.markdown("\n".join(f"- {item}" for item in ent_items))
                else:
                    st.caption("No specific named legal entities detected in query.")

            # Citation validation findings
            if ans.invalid_citations:
                st.markdown("**Citation Warnings:**")
                for inv in ans.invalid_citations:
                    st.error(f"- `{inv.get('reason')}`: {inv.get('details')}")

            if ans.unsupported_claims:
                st.markdown("**Potential Ungrounded Claims:**")
                for uns in ans.unsupported_claims:
                    st.warning(f"- {uns}")
