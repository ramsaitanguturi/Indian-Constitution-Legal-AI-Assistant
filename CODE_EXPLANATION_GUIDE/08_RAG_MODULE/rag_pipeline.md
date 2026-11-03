# End-to-End Legal RAG Pipeline: `rag/pipeline.py`

[Back to RAG Module Overview](README.md) • [Back to Main Index](../README.md)

---

## 1. Basic Introduction

### What is this file?
`rag/pipeline.py` is the **Master Orchestrator** of the Indian Constitution Legal AI Assistant. It coordinates all Stage 2 (NLP understanding), Stage 3 (hybrid retrieval & reranking), and Stage 4 (grounded generation, verification, and abstention) components into a seamless, deterministic 16-stage execution pipeline.

### Why does this file exist?
A production-grade Legal AI assistant cannot be built as a loose script. It requires:
1. **Strict sequencing**: Preprocessing $\to$ NER $\to$ Linking $\to$ Intent $\to$ Expansion $\to$ Routing $\to$ Retrieval $\to$ Fusion $\to$ Boost $\to$ Rerank $\to$ Recovery $\to$ Generation $\to$ Validation $\to$ Confidence $\to$ Gating.
2. **Dynamic router parameter injection**: Query routing decisions must dynamically adjust retrieval parameters (e.g. enabling entity boost for statutory queries or filtering by document type).
3. **Structured result encapsulation**: The output must be encapsulated in an immutable, serializable dataclass (`PipelineResult`) containing all intermediate audit logs.
4. **Early and late abstention**: Speculative or out-of-scope queries must be intercepted at the earliest possible stage to minimize latency and eliminate hallucination risk.

---

## 2. Imports and Dependencies

```python
# rag/pipeline.py L22-L39
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional

from nlp.language_detection import detect_language
from nlp.preprocessing import normalize_legal_text
from nlp.legal_ner import get_legal_ner
from nlp.entity_linking import get_entity_linker
from nlp.intent_classifier import get_intent_classifier
from nlp.query_expansion import get_query_expander
from routing.query_router import get_query_router, RoutingDecision
from retrieval.hybrid_retriever import HybridRetriever
from rag.parent_child import ParentChildRecovery
from rag.generator import GroundedGenerator
from rag.citation_validator import CitationValidator
from rag.confidence import ConfidenceEstimator
from rag.abstention import AbstentionManager
```

Every major module in the repository converges in this orchestrator.

---

## 3. Data Structure: `PipelineResult`

```python
# Lines 41-73
@dataclass
class PipelineResult:
    """Structured outcome of the end-to-end Legal RAG pipeline."""
    original_query: str
    normalized_query: str
    language: Dict[str, Any]
    intent: Dict[str, Any]
    entities: Dict[str, List[str]]
    linked_entities: List[Dict[str, Any]]
    expanded_query: str
    routing_decision: Dict[str, Any]
    retrieved_chunks: List[Dict[str, Any]]
    reranked_chunks: List[Dict[str, Any]]
    parent_context: Dict[str, Any]
    citations: List[Dict[str, Any]]
    generated_answer: str
    citation_validation: Dict[str, Any]
    confidence: Dict[str, Any]
    abstained: bool
    abstention_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def is_success(self) -> bool:
        return not self.abstained and bool(self.generated_answer)
```
- **Why this structure is critical**: It provides 100% transparency. Every intermediate computation (detected language, extracted entities, routing strategy, individual chunk scores, confidence breakdowns, validation verdicts) is retained for UI display or automated benchmark evaluation.

---

## 4. Class: `LegalRAGPipeline`

### Constructor `__init__(...)` (Lines 80-108)
Initializes and wires up all modular components:
```python
        # NLP Understanding components (Stage 2)
        self.legal_ner = get_legal_ner()
        self.entity_linker = get_entity_linker()
        self.intent_classifier = get_intent_classifier()
        self.query_expander = get_query_expander()

        # Routing component (Stage 4)
        self.query_router = get_query_router()

        # Retrieval & Reranker component (Stage 3)
        self.retriever = retriever or HybridRetriever()

        # Context Recovery & Grounding components (Stage 4)
        self.parent_store = parent_store or getattr(self.retriever, "parent_store", {})
        self.parent_recovery = ParentChildRecovery(parent_store=self.parent_store)
        self.generator = generator or GroundedGenerator()
        self.citation_validator = CitationValidator(parent_store=self.parent_store)
        self.confidence_estimator = ConfidenceEstimator()
        self.abstention_manager = AbstentionManager(
            strict_citation_validation=strict_citation_validation
        )
```

---

## 5. Master Execution Flow: `run(...)`

```python
def run(
    self,
    query: str,
    dynamic_api_key: Optional[str] = None,
    override_top_k: Optional[int] = None,
) -> PipelineResult
```

### Complete 16-Stage Execution Trace:

1. **Language Detection (Line 129)**: Calls `detect_language(raw_query)`. Identifies script (Latin/Devanagari) and code-switching (Hinglish).
2. **Text Preprocessing (Line 132)**: Normalizes quotes, expands abbreviations (`"Art."` $\to$ `"Article"`), and lowercases tokens.
3. **Legal NER (Line 135)**: Extracts 10 entity categories (`ARTICLE`, `CASE`, `AMENDMENT`, etc.).
4. **Entity Linking (Line 138)**: Maps surface mentions to canonical knowledge base IDs (`"art_21"`, `"case_puttaswamy_2017"`).
5. **Intent Classification (Line 141)**: Classifies user intent into one of 11 classes (`ARTICLE_LOOKUP`, `CASE_LAW_QUERY`, `CONSTITUTIONAL_PROCEDURE`, `OUT_OF_SCOPE`, etc.).
6. **Query Expansion (Lines 144-145)**: Enriches statutory synonyms with maximum 3 term additions.
7. **Query Routing (Lines 148-156)**: Maps query attributes to an optimal retrieval strategy (`CONSTITUTIONAL_FOCUSED`, `CASE_LAW_FOCUSED`, etc.).
8. **Early Router Abstention Check (Lines 159-194)**: If query is `OUT_OF_SCOPE` or empty, immediately halts and returns a safe refusal notice without calling expensive retrieval or LLM endpoints.
9. **Dynamic Retriever Parameter Injection (Lines 199-229)**: Dynamically injects router parameters (`use_bm25`, `use_dense`, `entity_boost_weight`, `filter_doc_type`) into the retriever inside a `try...finally` block to guarantee state restoration.
10. **Hybrid Retrieval, RRF Fusion & Entity Boosting (Line 215)**: Executes dense + BM25 search, Cormack RRF fusion, and additive entity scoring.
11. **Cross-Encoder Reranking (Line 215)**: Re-scores top 30 candidates using `ms-marco-MiniLM-L-6-v2` down to top 5.
12. **Retrieval Abstention Check (Lines 242-277)**: If 0 chunks retrieved or top score below minimum threshold, safely returns an abstention notice.
13. **Parent Context Recovery (Line 280)**: Hydrates full parent documents and deduplicates records.
14. **Grounded Generation (Lines 283-288)**: Invokes `GroundedGenerator.generate()` with prompt-level zero-hallucination constraints.
15. **Citation & Proposition Validation (Lines 291-295)**: Verifies that cited document IDs exist and claims are not contradicted.
16. **Confidence Scoring & Post-Generation Gating (Lines 298-344)**: Computes 6-signal composite confidence. If score $< 0.30$, withholds answer and outputs safe notice; otherwise returns complete `PipelineResult`.

---

## 6. Actual Code Walkthrough

### Code Excerpt: Dynamic Parameter Injection (Lines 199-229)
```python
        # Dynamic parameter injection based on router decision
        orig_bm25 = self.retriever.use_bm25
        orig_dense = self.retriever.use_dense
        orig_rrf = self.retriever.use_rrf
        orig_eb = self.retriever.use_entity_boost
        orig_eb_wt = self.retriever.entity_boost_weight
        orig_reranker = self.retriever.use_reranker

        try:
            self.retriever.use_bm25 = routing_obj.use_bm25
            self.retriever.use_dense = routing_obj.use_dense
            self.retriever.use_rrf = routing_obj.use_rrf
            self.retriever.use_entity_boost = routing_obj.use_entity_boost
            self.retriever.entity_boost_weight = routing_obj.entity_boost_weight
            self.retriever.use_reranker = routing_obj.use_reranker

            reranked_chunks = self.retriever.retrieve(
                query=retrieval_query,
                entities=linked_entities or entities,
                top_k=target_top_k,
                filter_doc_type=routing_obj.filter_doc_type,
            )
        finally:
            # Restore retriever defaults
            self.retriever.use_bm25 = orig_bm25
            self.retriever.use_dense = orig_dense
            self.retriever.use_rrf = orig_rrf
            self.retriever.use_entity_boost = orig_eb
            self.retriever.entity_boost_weight = orig_eb_wt
            self.retriever.use_reranker = orig_reranker
```
- **Why this design is elegant**: The `HybridRetriever` is a shared singleton. If Query 1 requires `filter_doc_type="judgment"` and Query 2 is a generic constitutional question, using `try...finally` ensures that thread-safe defaults are restored even if retrieval throws an exception.

---

## 7. Viva Presentation & Defense Q&A

### Q1: What happens if a user inputs "How to bake a chocolate cake?"
> **Student Answer**:
> *"The pipeline detects that the query has zero legal entities and classifies its intent as `OUT_OF_SCOPE`. At Stage 8 (Early Router Abstention Check), `abstention_manager.evaluate()` immediately triggers. It stops execution before running ChromaDB or LLM calls, returning a safe scope notice in under 5 milliseconds. This protects server resources and prevents speculative off-topic responses."*

### Q2: Why is the pipeline encapsulated in a `PipelineResult` dataclass?
> **Student Answer**:
> *"In legal AI, explainability and reproducibility are just as critical as accuracy. A simple string answer is un-auditable. `PipelineResult` packages the exact intermediate state across all 16 stages—including extracted entities, routing strategy, individual chunk scores, confidence breakdown, and NLI verification verdicts. This allows the Streamlit UI to render transparent diagnostic tabs and enables our automated benchmark suite to evaluate individual subcomponents in isolation."*

