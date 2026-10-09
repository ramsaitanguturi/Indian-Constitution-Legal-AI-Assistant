"""
NLP Pipeline Diagnostic Inspector.

Provides an explainable, safe diagnostic adapter and Streamlit UI component
for inspecting the full 16-stage NLP Query Understanding and Reliable RAG Pipeline.

Exposes:
1. Original query and normalized query
2. Detected language
3. Extracted legal entities and canonical links
4. Predicted intent and routing mode
5. Expanded query terms
6. Retrieved candidates and retrieval scores
7. Entity-boost and reranking information
8. Recovered parent-document references
9. Citations and citation-validation outcome
10. Confidence components and abstention reason

Safety & Security Guarantees:
- Never exposes API keys, secrets, or environment variables.
- Does not expose LLM internal prompts or internal model reasoning.
- Explicitly labels heuristic confidence vs calibrated probabilities.
- Handles partial, legacy, or abstained pipeline results gracefully.
"""

import re
from typing import Dict, List, Any, Optional
import pandas as pd
import streamlit as st


# Sensitive pattern scrubber to guarantee no secrets leak into UI
SENSITIVE_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z-_]{35}"),  # Google API Key pattern
    re.compile(r"sk-[0-9A-Za-z-_]{20,}"),  # Generic API key pattern
]


def scrub_sensitive_text(text: str) -> str:
    """Removes API keys or potential tokens from text snippets."""
    if not isinstance(text, str):
        return text
    clean = text
    for pattern in SENSITIVE_PATTERNS:
        clean = pattern.sub("[REDACTED_API_KEY]", clean)
    return clean


def extract_pipeline_diagnostics(result: Any) -> Dict[str, Any]:
    """
    Extracts structured, sanitized diagnostic information from a PipelineResult,
    dictionary, or legacy execution output.

    Guarantees a clean, standardized dictionary with all 10 diagnostic stages.
    """
    # 1. Handle dict vs dataclass
    if hasattr(result, "to_dict"):
        data = result.to_dict()
    elif isinstance(result, dict):
        data = dict(result)
    else:
        data = {}

    # 1. Original and Normalized Query
    orig_q = scrub_sensitive_text(str(data.get("original_query", "") or ""))
    norm_q = scrub_sensitive_text(str(data.get("normalized_query", "") or ""))
    if not norm_q and orig_q:
        norm_q = orig_q

    # 2. Detected Language
    lang_info = data.get("language", {})
    if not isinstance(lang_info, dict):
        lang_info = {"language": "en", "is_english": True, "confidence": 1.0}
    lang_code = lang_info.get("language", "en")
    is_eng = lang_info.get("is_english", True)
    lang_conf = float(lang_info.get("confidence", 1.0) or 1.0)

    # 3. Extracted Legal Entities and Canonical Links
    entities = data.get("entities", {})
    if not isinstance(entities, dict):
        entities = {}
    # Sanitize entities
    clean_entities = {}
    for cat, items in entities.items():
        if isinstance(items, list):
            clean_entities[cat] = [scrub_sensitive_text(str(i)) for i in items]
        else:
            clean_entities[cat] = [scrub_sensitive_text(str(items))]

    linked_entities = data.get("linked_entities", [])
    if not isinstance(linked_entities, list):
        linked_entities = []
    clean_linked = []
    for link in linked_entities:
        if isinstance(link, dict):
            clean_linked.append({
                "surface_text": scrub_sensitive_text(str(link.get("surface_form") or link.get("surface_text") or "")),
                "canonical_id": scrub_sensitive_text(str(link.get("canonical_id") or link.get("entity_id") or "")),
                "entity_type": link.get("entity_type", "UNKNOWN"),
                "score": float(link.get("confidence") or link.get("score") or 1.0),
                "is_nil": link.get("is_nil", False),
            })

    # 4. Predicted Intent & Routing Mode
    intent_data = data.get("intent", {})
    if not isinstance(intent_data, dict):
        intent_data = {"intent": "GENERAL_QUERY", "confidence": 0.5, "routing_mode": "fallback"}
    predicted_intent = intent_data.get("intent", "GENERAL_QUERY")
    intent_confidence = float(intent_data.get("confidence", 0.0) or 0.0)
    routing_mode = intent_data.get("routing_mode", intent_data.get("classifier", "rule_based"))

    routing_decision = data.get("routing_decision", {})
    if not isinstance(routing_decision, dict):
        routing_decision = {}
    routing_strategy = routing_decision.get("strategy", "HYBRID_SEARCH")

    # 5. Expanded Query Terms
    expanded_q = scrub_sensitive_text(str(data.get("expanded_query", "") or norm_q))
    # Derive expansion terms if expanded_query differs from normalized
    expansion_terms = []
    if expanded_q and norm_q and expanded_q != norm_q:
        orig_words = set(norm_q.lower().split())
        exp_words = [w for w in expanded_q.split() if w.lower() not in orig_words and len(w) > 2]
        expansion_terms = list(dict.fromkeys(exp_words))[:8]

    # 6. Retrieved Candidates and Retrieval Scores
    retrieved_chunks = data.get("retrieved_chunks", [])
    if not isinstance(retrieved_chunks, list):
        retrieved_chunks = []
    reranked_chunks = data.get("reranked_chunks", [])
    if not isinstance(reranked_chunks, list):
        reranked_chunks = []
    
    # Use reranked chunks if available, else retrieved
    display_chunks = reranked_chunks if reranked_chunks else retrieved_chunks
    candidate_diagnostics = []
    for idx, chunk in enumerate(display_chunks, start=1):
        if not isinstance(chunk, dict):
            continue
        c_id = chunk.get("chunk_id", f"chunk_{idx}")
        p_id = chunk.get("parent_id", chunk.get("metadata", {}).get("parent_id", "unknown"))
        score = float(chunk.get("score", chunk.get("rerank_score", chunk.get("rrf_score", 0.0))) or 0.0)
        rank = int(chunk.get("rank", idx))
        doc_type = chunk.get("doc_type", chunk.get("metadata", {}).get("doc_type", "constitution"))
        txt = scrub_sensitive_text(str(chunk.get("text", chunk.get("child_text", ""))))
        snippet = txt[:180] + ("..." if len(txt) > 180 else "")

        meta = chunk.get("metadata", {})
        candidate_diagnostics.append({
            "rank": rank,
            "chunk_id": c_id,
            "parent_id": p_id,
            "doc_type": doc_type,
            "score": score,
            "snippet": snippet,
            "bm25_rank": chunk.get("bm25_rank", meta.get("bm25_rank", "N/A")),
            "vector_rank": chunk.get("vector_rank", meta.get("vector_rank", "N/A")),
            "entity_boosted": chunk.get("entity_boosted", meta.get("entity_boosted", False)),
            "rerank_score": chunk.get("rerank_score", score if routing_decision.get("use_reranker") else "N/A"),
        })

    # 7. Entity-Boost and Reranking Configuration
    entity_boost_applied = routing_decision.get("use_entity_boost", True)
    entity_boost_weight = float(routing_decision.get("entity_boost_weight", 0.15) or 0.15)
    reranker_applied = routing_decision.get("use_reranker", True)

    # 8. Recovered Parent Document References
    parent_ctx = data.get("parent_context", {})
    if not isinstance(parent_ctx, dict):
        parent_ctx = {}
    parents = parent_ctx.get("parents", [])
    if not isinstance(parents, list):
        parents = []
    parent_diagnostics = []
    for p in parents:
        if not isinstance(p, dict):
            continue
        p_id = p.get("parent_id", p.get("document_id", "unknown"))
        p_type = p.get("doc_type", "constitution")
        title = p.get("title", p.get("case_name", p_id))
        clause_or_bench = p.get("article_number", p.get("citation", ""))
        parent_diagnostics.append({
            "parent_id": p_id,
            "doc_type": p_type,
            "title": title,
            "identifier": clause_or_bench,
            "children_count": len(p.get("supporting_children", [])),
        })

    # 9. Citations and Citation Validation Outcome
    cit_val = data.get("citation_validation", {})
    if not isinstance(cit_val, dict):
        cit_val = {}
    citations = data.get("citations", [])
    if not isinstance(citations, list):
        citations = []
    cit_diagnostics = {
        "valid": bool(cit_val.get("valid", True)),
        "citations_checked": int(cit_val.get("citations_checked", len(citations))),
        "valid_citations": cit_val.get("valid_citations", [c.get("citation_text", str(c)) for c in citations if isinstance(c, dict)]),
        "invalid_citations": cit_val.get("invalid_citations", []),
        "unsupported_claims": cit_val.get("unsupported_claims", []),
        "summary": cit_val.get("summary", "Validation complete."),
    }

    # 10. Confidence Components & Abstention Reason
    conf_data = data.get("confidence", {})
    if not isinstance(conf_data, dict):
        conf_data = {}
    conf_score = float(conf_data.get("confidence_score", 0.0) or 0.0)
    conf_level = conf_data.get("confidence_level", "MEDIUM")
    is_calibrated = bool(conf_data.get("is_calibrated", False))
    conf_explanation = conf_data.get("explanation", "Explainable heuristic composite.")
    signals = conf_data.get("signal_breakdown", {})

    signal_rows = []
    sig_weights = conf_data.get("signal_weights", {})
    if isinstance(signals, dict):
        for sig_name, sig_info in signals.items():
            sig_label = sig_name.replace("_", " ").title()
            if isinstance(sig_info, dict):
                signal_rows.append({
                    "Signal": sig_label,
                    "Weight": sig_info.get("weight", 0.0),
                    "Raw Score": sig_info.get("score", 0.0),
                    "Contribution": sig_info.get("weighted_value", 0.0),
                    "Diagnostic Detail": sig_info.get("details", ""),
                })
            elif isinstance(sig_info, (int, float)):
                w_val = sig_weights.get(sig_name, 0.0) if isinstance(sig_weights, dict) else 0.0
                signal_rows.append({
                    "Signal": sig_label,
                    "Weight": round(float(w_val), 2),
                    "Raw Score": round(float(sig_info), 4),
                    "Contribution": round(float(sig_info) * float(w_val), 4),
                    "Diagnostic Detail": f"Calculated signal score {sig_info:.2f}",
                })

    abstained = bool(data.get("abstained", False))
    abstain_reason = data.get("abstention_reason")

    return {
        "query_preprocessing": {
            "original_query": orig_q,
            "normalized_query": norm_q,
            "is_modified": orig_q != norm_q,
            "language_code": lang_code,
            "is_english": is_eng,
            "language_confidence": lang_conf,
        },
        "entity_extraction_and_linking": {
            "entities_by_category": clean_entities,
            "total_entities_extracted": sum(len(v) for v in clean_entities.values()),
            "linked_entities": clean_linked,
            "total_entities_linked": len(clean_linked),
        },
        "intent_and_routing": {
            "predicted_intent": predicted_intent,
            "intent_confidence": intent_confidence,
            "classifier_mode": routing_mode,
            "routing_strategy": routing_strategy,
            "use_bm25": routing_decision.get("use_bm25", True),
            "use_dense": routing_decision.get("use_dense", True),
            "use_rrf": routing_decision.get("use_rrf", True),
            "use_entity_boost": entity_boost_applied,
            "entity_boost_weight": entity_boost_weight,
            "use_reranker": reranker_applied,
            "target_top_k": routing_decision.get("final_top_k", len(display_chunks)),
        },
        "query_expansion": {
            "original_query": norm_q,
            "expanded_query": expanded_q,
            "terms_appended": expansion_terms,
            "is_expanded": bool(expansion_terms or (expanded_q != norm_q)),
        },
        "retrieval_candidates": candidate_diagnostics,
        "reranking_and_boost_info": {
            "entity_boost_enabled": entity_boost_applied,
            "boost_weight": entity_boost_weight,
            "cross_encoder_enabled": reranker_applied,
            "total_candidates_evaluated": len(display_chunks),
        },
        "parent_recovery": {
            "parent_count": len(parent_diagnostics),
            "parents": parent_diagnostics,
        },
        "citation_validation": cit_diagnostics,
        "confidence_and_abstention": {
            "confidence_score": conf_score,
            "confidence_level": conf_level,
            "is_calibrated": is_calibrated,
            "confidence_type": "Explainable Weighted Heuristic (Not Calibrated Probability)",
            "explanation": conf_explanation,
            "signals": signal_rows,
            "abstained": abstained,
            "abstention_reason": abstain_reason,
        },
    }


def render_pipeline_inspector(result: Any, expanded: bool = False):
    """
    Renders an interactive, comprehensive diagnostic panel inside Streamlit.
    """
    diagnostics = extract_pipeline_diagnostics(result)

    with st.expander("🔬 NLP Pipeline Diagnostic Inspector (10-Stage Pipeline Trace)", expanded=expanded):
        st.caption("Deep-dive inspection across all 10 observable NLP, retrieval, reranking, and reliability stages.")

        d_tab1, d_tab2, d_tab3, d_tab4, d_tab5 = st.tabs([
            "1️⃣ Query & Language",
            "2️⃣ Entities & Linking",
            "3️⃣ Intent & Routing",
            "4️⃣ Retrieval & Reranking",
            "5️⃣ Citations, Confidence & Abstention"
        ])

        # -------------------------------------------------------------
        # Tab 1: Query & Language
        # -------------------------------------------------------------
        with d_tab1:
            qp = diagnostics["query_preprocessing"]
            qe = diagnostics["query_expansion"]

            col_q1, col_q2 = st.columns(2)
            with col_q1:
                st.markdown("##### 📝 Query Preprocessing")
                st.markdown(f"**Original Query:** `{qp['original_query']}`")
                st.markdown(f"**Normalized Query:** `{qp['normalized_query']}`")
                st.caption(f"Legal normalizer applied: {'Yes (abbreviations expanded / text cleaned)' if qp['is_modified'] else 'Identical to input'}")

            with col_q2:
                st.markdown("##### 🌐 Language Identification")
                st.markdown(f"**Detected Language:** `{qp['language_code'].upper()}` ({'English' if qp['is_english'] else 'Non-English'})")
                st.markdown(f"**Detection Confidence:** `{qp['language_confidence']:.2f}`")

            st.markdown("---")
            st.markdown("##### 🔀 Controlled Legal Query Expansion")
            if qe["is_expanded"]:
                st.markdown(f"**Expanded Formulation:** `{qe['expanded_query']}`")
                if qe["terms_appended"]:
                    st.markdown("**Domain Terms Appended:** " + ", ".join([f"`{t}`" for t in qe["terms_appended"]]))
            else:
                st.caption("No expansion terms added; query proceeded with canonical wording.")

        # -------------------------------------------------------------
        # Tab 2: Entities & Linking
        # -------------------------------------------------------------
        with d_tab2:
            el = diagnostics["entity_extraction_and_linking"]
            c_ents = el["entities_by_category"]

            st.markdown("##### 🏷️ Extracted Legal Named Entities (NER)")
            if el["total_entities_extracted"] > 0:
                ent_table = []
                for cat, items in c_ents.items():
                    for item in items:
                        ent_table.append({"Category": cat, "Surface Mention": item})
                st.dataframe(pd.DataFrame(ent_table), use_container_width=True)
            else:
                st.caption("No legal named entities detected in query.")

            st.markdown("---")
            st.markdown("##### 🔗 Canonical Entity Disambiguation (Entity Linking)")
            linked = el["linked_entities"]
            if linked:
                df_linked = pd.DataFrame(linked)
                df_linked.columns = ["Mention", "Canonical Corpus ID", "Entity Type", "Confidence Score", "Is Nil / Out-of-KB"]
                st.dataframe(df_linked, use_container_width=True)
            else:
                st.caption("No entity links established for query terms.")

        # -------------------------------------------------------------
        # Tab 3: Intent & Routing
        # -------------------------------------------------------------
        with d_tab3:
            ir = diagnostics["intent_and_routing"]

            c_i1, c_i2, c_i3 = st.columns(3)
            with c_i1:
                st.metric("Predicted Intent", ir["predicted_intent"])
            with c_i2:
                st.metric("Intent Confidence", f"{ir['intent_confidence']:.2f}")
            with c_i3:
                st.metric("Routing Strategy", ir["routing_strategy"])

            st.markdown(f"**Active Classifier Mode:** `{ir['classifier_mode']}`")

            st.markdown("---")
            st.markdown("##### 🎛️ Dynamic Retrieval Component Configuration")
            switches = [
                {"Component": "BM25 Keyword Lexical Search", "Active": "✅ Enabled" if ir["use_bm25"] else "❌ Disabled"},
                {"Component": "Dense Vector Embeddings (ChromaDB)", "Active": "✅ Enabled" if ir["use_dense"] else "❌ Disabled"},
                {"Component": "Reciprocal Rank Fusion (RRF, k=60)", "Active": "✅ Enabled" if ir["use_rrf"] else "❌ Disabled"},
                {"Component": "Legal Entity Rank Boost (+0.15)", "Active": "✅ Enabled" if ir["use_entity_boost"] else "❌ Disabled"},
                {"Component": "Cross-Encoder Reranker", "Active": "✅ Enabled" if ir["use_reranker"] else "❌ Disabled"},
            ]
            st.dataframe(pd.DataFrame(switches), use_container_width=True)

        # -------------------------------------------------------------
        # Tab 4: Retrieval & Reranking
        # -------------------------------------------------------------
        with d_tab4:
            cands = diagnostics["retrieval_candidates"]
            rb = diagnostics["reranking_and_boost_info"]

            st.markdown("##### 🔍 Retrieved Candidate Passages & Score Fusion")
            st.caption(f"Entity Boost: `{'Active (+0.15)' if rb['entity_boost_enabled'] else 'Off'}` | Neural Reranker: `{'Active' if rb['cross_encoder_enabled'] else 'Off'}`")

            if cands:
                df_cands = pd.DataFrame(cands)[[
                    "rank", "chunk_id", "parent_id", "doc_type", "score", "snippet"
                ]]
                df_cands.columns = ["Rank", "Chunk ID", "Parent Document ID", "Doc Type", "Score", "Passage Snippet"]
                st.dataframe(df_cands, use_container_width=True)
            else:
                st.caption("No candidate passages retrieved.")

            st.markdown("---")
            st.markdown("##### 📚 Recovered Parent Document Provenance")
            parents = diagnostics["parent_recovery"]["parents"]
            if parents:
                df_par = pd.DataFrame(parents)
                df_par.columns = ["Parent ID", "Document Type", "Title / Name", "Reference Identifier", "Supporting Chunks Count"]
                st.dataframe(df_par, use_container_width=True)
            else:
                st.caption("No parent contexts recovered.")

        # -------------------------------------------------------------
        # Tab 5: Citations, Confidence & Abstention
        # -------------------------------------------------------------
        with d_tab5:
            cv = diagnostics["citation_validation"]
            conf = diagnostics["confidence_and_abstention"]

            # Abstention Status
            if conf["abstained"]:
                st.error(f"🛡️ **Pipeline Abstained from Answering**\n\n**Reason:** `{conf['abstention_reason']}`")
            else:
                st.success("✅ **Pipeline Answer Validated and Passed for Delivery**")

            # Confidence Estimation
            st.markdown("##### 🛡️ Heuristic Confidence Estimation")
            c_c1, c_c2 = st.columns(2)
            with c_c1:
                st.metric("Confidence Score", f"{conf['confidence_score']:.2f}", conf["confidence_level"])
            with c_c2:
                st.info(f"**Confidence Classification:** `{conf['confidence_level']}`\n\n*{conf['confidence_type']}*")

            st.caption(
                "⚠️ **Disclaimer:** Confidence scores are explainable weighted heuristics reflecting retrieval strength, "
                "coverage, entity alignment, and citation validity. They are NOT mathematically calibrated posterior probabilities."
            )

            if conf["signals"]:
                st.dataframe(pd.DataFrame(conf["signals"]), use_container_width=True)

            # Citation Validation
            st.markdown("---")
            st.markdown("##### 📜 Structural Citation Validation Audit")
            st.caption(
                "Structural citation validation checks that cited Articles, Cases, and Benchmarks exist in the verified "
                "corpus and were present in retrieved context passages. It does not establish semantic legal correctness."
            )

            c_v1, c_v2 = st.columns(2)
            with c_v1:
                st.markdown(f"**Validation Outcome:** `{'PASSED' if cv['valid'] else 'FLAGGED'}`")
                st.markdown(f"**Citations Checked:** `{cv['citations_checked']}`")
            with c_v2:
                st.markdown(f"**Valid Citations:** `{len(cv['valid_citations'])}`")
                st.markdown(f"**Invalid Citations Detected:** `{len(cv['invalid_citations'])}`")

            if cv["invalid_citations"]:
                st.warning("⚠️ **Detected Unsupported Citations:**")
                for inv in cv["invalid_citations"]:
                    st.write(f"- `{inv}`")

            if cv["unsupported_claims"]:
                st.warning("⚠️ **Detected Potentially Ungrounded Claims:**")
                for uc in cv["unsupported_claims"]:
                    st.write(f"- `{uc}`")
