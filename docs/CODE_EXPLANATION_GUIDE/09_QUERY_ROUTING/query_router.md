# Specialized NLP Query Router: `routing/query_router.py`

[Back to Query Routing Overview](README.md) • [Back to Main Index](../README.md)

---

## 1. Basic Introduction

### What is this file?
`routing/query_router.py` implements the **Specialized NLP Query Router**. It analyzes the structured linguistic outputs of Phase 2 (normalized text, detected language, extracted legal entities, canonical linked IDs, classified intent, and expanded synonyms) and deterministically generates a `RoutingDecision`.

### Why does this file exist?
Legal queries are heterogeneous:
- Query A: *"What is Article 21?"* (Exact statutory retrieval; searching judgments is unnecessary and dilutes top results).
- Query B: *"Compare Kesavananda Bharati with Minerva Mills regarding basic structure."* (Cross-case comparison; requires retrieving from both judgments, a wider candidate pool, and a comparative synthesis agent).
- Query C: *"Can police arrest without warrant?"* (Conceptual procedural question; requires cross-corpus retrieval across CrPC sections and Article 22).
- Query D: *"How to make pizza?"* (Completely non-legal; must be intercepted immediately).

`routing/query_router.py` dynamically adjusts the retrieval strategy, candidate pool size, document type filtering, and multi-agent persona to match the precise requirements of each query.

---

## 2. Imports and Dependencies

```python
# routing/query_router.py L15-L22
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Union

from config import (
    RETRIEVAL_CANDIDATE_POOL,
    FINAL_TOP_K,
    ENTITY_BOOST_WEIGHT,
)
```

| Import / Constant | Value / Role |
| :--- | :--- |
| `RETRIEVAL_CANDIDATE_POOL` | Default `30`. Baseline candidate pool size before cross-encoder reranking. |
| `FINAL_TOP_K` | Default `5`. Final number of reranked passages passed to context recovery. |
| `ENTITY_BOOST_WEIGHT` | Default `0.15`. Standard additive entity score boost. |

---

## 3. Data Structure: `RoutingDecision`

```python
# Lines 25-49
@dataclass
class RoutingDecision:
    """Deterministic routing decision dictating retrieval and generation execution."""
    strategy: str  # ARTICLE_SEARCH, CASE_SEARCH, COMPARISON_SEARCH, RIGHTS_SEARCH, PROCEDURE_SEARCH, HYBRID_SEARCH, OUT_OF_SCOPE
    retrieval_query: str
    filter_doc_type: Optional[str]  # "constitution", "judgment", or None
    use_bm25: bool = True
    use_dense: bool = True
    use_rrf: bool = True
    use_entity_boost: bool = True
    use_reranker: bool = True
    entity_boost_weight: float = ENTITY_BOOST_WEIGHT
    top_k_candidates: int = RETRIEVAL_CANDIDATE_POOL
    final_top_k: int = FINAL_TOP_K
    recommended_agent: str = "explanation_agent"
    requires_comparison: bool = False
    is_out_of_scope: bool = False
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
```

---

## 4. Class: `QueryRouter`

```python
class QueryRouter:
    """
    Deterministic, rule-driven NLP router for constitutional queries.
    Maps fine-grained intent, entity distributions, and linguistic signals to
    optimal retrieval parameters without stochastic LLM invocations.
    """
```

### The 7 Deterministic Routing Decision Rules:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           ROUTING DECISION TREE                                  │
├──────────────────────────┬──────────────────────┬───────────────┬────────────────┤
│ Condition                │ Strategy             │ Corpus Filter │ Target Agent   │
├──────────────────────────┼──────────────────────┼───────────────┼────────────────┤
│ 1. Empty / Unsupported   │ OUT_OF_SCOPE         │ None          │ Abstain        │
│    or OOS Intent         │                      │               │                │
├──────────────────────────┼──────────────────────┼───────────────┼────────────────┤
│ 2. CASE_COMPARISON or    │ COMPARISON_SEARCH    │ "judgment"    │ case_law_agent │
│    >= 2 Case Mentions    │ (Pool: 35, Top: 6)   │               │                │
├──────────────────────────┼──────────────────────┼───────────────┼────────────────┤
│ 3. ARTICLE_LOOKUP or     │ ARTICLE_SEARCH       │"constitution" │ article_agent  │
│    AMENDMENT_QUERY       │                      │               │                │
├──────────────────────────┼──────────────────────┼───────────────┼────────────────┤
│ 4. CASE_LAW_QUERY or     │ CASE_SEARCH          │ "judgment"    │ case_law_agent │
│    Single Case Mention   │                      │               │                │
├──────────────────────────┼──────────────────────┼───────────────┼────────────────┤
│ 5. CONSTITUTIONAL_       │ PROCEDURE_SEARCH     │"constitution" │ article_agent  │
│    PROCEDURE             │                      │               │                │
├──────────────────────────┼──────────────────────┼───────────────┼────────────────┤
│ 6. RIGHTS / DEFINITION   │ RIGHTS_SEARCH        │ None (Cross)  │ explanation_   │
│                          │                      │               │ agent          │
├──────────────────────────┼──────────────────────┼───────────────┼────────────────┤
│ 7. Default / Fallback    │ HYBRID_SEARCH        │ None (Cross)  │ explanation_   │
│                          │                      │               │ agent          │
└──────────────────────────┴──────────────────────┴───────────────┴────────────────┘
```

---

## 5. Actual Code Walkthrough

### Code Excerpt: Case Comparison Routing (Lines 168-189)
```python
        # 4. Decision: CASE COMPARISON
        if intent_label == "CASE_COMPARISON" or (len(case_mentions) >= 2):
            reasons.append("Case comparison intent or multiple landmark cases identified.")
            # For comparison, we need wider candidate pool and slightly more final results
            return RoutingDecision(
                strategy="COMPARISON_SEARCH",
                retrieval_query=exp_q,
                filter_doc_type="judgment",
                use_bm25=True,
                use_dense=True,
                use_rrf=True,
                use_entity_boost=True,
                use_reranker=True,
                entity_boost_weight=0.20,
                top_k_candidates=max(self.default_candidate_pool, 35),
                final_top_k=max(self.default_final_top_k, 6),
                recommended_agent="case_law_agent",
                requires_comparison=True,
                is_out_of_scope=False,
                reasons=reasons,
            )
```
- **Why expand pool to 35 and final_top_k to 6?**
  When comparing two major landmark judgments (e.g. *Kesavananda Bharati* and *Minerva Mills*), a standard top 5 might be dominated by 4 passages from one case and only 1 from the other. Expanding the pool to 35 candidates and final output to 6 ensures that both cases have sufficient evidence representation.
- **Higher Entity Boost ($0.20$ vs $0.15$)**: Ensures that passages from both named cases are aggressively promoted over generic doctrine texts.

### Code Excerpt: Article Query Normalization Choice (Lines 197-200)
```python
            # For exact article lookup, keep normalized query to avoid diluting specific article token
            target_q = norm_q if article_mentions else exp_q
            # When amendments are queried, do not filter strictly to 'constitution' so amendment docs can be retrieved
            doc_filter = None if (amendment_mentions or intent_label == "AMENDMENT_QUERY") else "constitution"
```
- **Why avoid query expansion for exact article lookups?**
  If a user searches *"Article 21"*, expanding the query with synonyms like *"life, liberty, habeas corpus, detention"* can dilute the exact token `"Article 21"`, causing BM25 to score long tangential judgment passages higher than the article text itself. Keeping `target_q = norm_q` preserves exact lexical anchoring.

---

## 6. Practical Working Example

### Query:
> *"What did the Supreme Court hold in Kesavananda Bharati regarding basic structure?"*

### Stage 2 NLP Context:
- `normalized_query`: `"what did the supreme court hold in kesavananda bharati regarding basic structure"`
- `intent`: `"CASE_LAW_QUERY"`
- `legal_entities`: `{"CASE": ["Kesavananda Bharati"], "LEGAL_CONCEPT": ["basic structure"]}`
- `expanded_query`: `"what did the supreme court hold in kesavananda bharati regarding basic structure constitutional amendment judicial review"`

### Routing Execution:
1. Matches Rule 6: `CASE_SEARCH`.
2. Sets `filter_doc_type = "judgment"` (excludes irrelevant constitutional articles).
3. Sets `recommended_agent = "case_law_agent"`.
4. Boosts weight to `0.20`.
5. Logs transparent reason: `"Query targets judicial precedent or case law (intent='CASE_LAW_QUERY', cases=['Kesavananda Bharati'])."`.

---

## 7. Viva Presentation & Defense Q&A

### Q1: Why not use an LLM Agent (like LangChain RouterAgent) to decide where to route queries?
> **Student Answer**:
> *"An LLM call to route a query adds 800 to 1,500 milliseconds of latency, consumes external API quota, and introduces stochastic non-determinism. Our `QueryRouter` is a deterministic NLP rule-engine that runs locally in less than 0.1 milliseconds. It uses the exact entities and intent classified in Stage 2 to make 100% reproducible routing decisions. This makes the system faster, cost-free, and provably reliable."*

### Q2: How does the router interact with the `LegalRAGPipeline`?
> **Student Answer**:
> *"In Stage 7 of `LegalRAGPipeline.run()`, the pipeline receives the `RoutingDecision`. If `is_out_of_scope == True`, it triggers early abstention at Stage 8. Otherwise, it dynamically injects the router's retrieval parameters (`use_bm25`, `filter_doc_type`, `entity_boost_weight`) into `HybridRetriever` before executing search, restoring retriever defaults immediately afterwards inside a `try...finally` block."*

