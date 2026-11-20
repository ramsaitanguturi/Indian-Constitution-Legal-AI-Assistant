# Query Routing Subsystem: `09_QUERY_ROUTING/`

[Back to Main Index](../README.md)

---

## 1. Subsystem Overview

The **Query Routing Subsystem** bridges Phase 2 (Natural Language Understanding) with Phase 3 (Retrieval & Reranking). Instead of running an identical static search for every query, the router analyzes:
- The normalized query string
- The detected language and script
- Extracted and canonically linked legal entities
- The classified user intent
- Expanded query synonyms

It then outputs a deterministic, strongly typed `RoutingDecision` that dictates:
1. **Retrieval Strategy**: (`ARTICLE_SEARCH`, `CASE_SEARCH`, `COMPARISON_SEARCH`, `RIGHTS_SEARCH`, `PROCEDURE_SEARCH`, `HYBRID_SEARCH`, `OUT_OF_SCOPE`).
2. **Corpus Filter**: Whether to restrict search strictly to constitutional articles (`filter_doc_type="constitution"`), judicial precedents (`filter_doc_type="judgment"`), or search the entire legal corpus.
3. **Retrieval Parameters**: Overrides for candidate pool size ($K=30$ vs $35$), entity boost weight ($0.15$ vs $0.20$), and final rerank count ($K=5$ vs $6$).
4. **Target Multi-Agent Persona**: (`article_agent`, `case_law_agent`, `explanation_agent`).
5. **Early Scope Guard**: Intercepts off-topic queries immediately to trigger early abstention before calling ChromaDB or LLM endpoints.

---

## 2. Directory Contents

| File | Repo Path | Responsibility |
| :--- | :--- | :--- |
| [query_router.md](query_router.md) | `routing/query_router.py` | Complete technical breakdown of `QueryRouter` class, `RoutingDecision` dataclass, decision rules, and code walkthrough. |

---

## 3. Why Deterministic NLP Routing over LLM Routing?

Many general AI frameworks use an LLM call to decide where to route a query (e.g., prompting GPT-4: *"Choose which database to query"*). In our system, routing is **strictly deterministic**:
- **0ms Overhead**: Evaluates in $< 0.1$ milliseconds on CPU via rule-driven logic over Stage 2 features.
- **100% Predictable**: Eliminates non-deterministic LLM routing errors where an article query might randomly be routed to a case database.
- **Cost-Free**: Requires zero external API tokens.

