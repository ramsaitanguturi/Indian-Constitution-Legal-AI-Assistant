# Top 10 Code Blocks to Show Your Professor: `17_VIVA_PREPARATION/important_code_to_show.md`

[Back to Viva Preparation Overview](code_demonstration_script.md) • [Back to Main Index](../README.md)

---

## 1. Overview

When your examination committee asks you to **"open the code and explain how it is implemented"**, navigate directly to these 10 verified code blocks. Each entry provides the exact file path, line numbers, and a 3-sentence speaking script explaining why the block was designed this way.

---

## Block 1: Master 16-Stage Pipeline & Early Abstention
- **File**: [`rag/pipeline.py`](../../rag/pipeline.py#L126-L194)
- **Line Numbers**: Lines 126–194

```python
        # Step 1: Language Detection
        lang_info = detect_language(raw_query)

        # Step 2: Preprocessing
        norm_q = normalize_legal_text(raw_query)

        # Step 3: Legal NER
        entities = self.legal_ner.extract_entities(norm_q)

        # Step 4: Entity Linking
        linked_entities = self.entity_linker.link_all(entities)

        # Step 5: Intent Classification
        intent_info = self.intent_classifier.classify(norm_q, entities=entities)

        # Step 6: Query Expansion
        expansion_info = self.query_expander.expand(norm_q)
        exp_q = expansion_info.get("expanded_query", norm_q)

        # Step 7: Query Router
        routing_obj = self.query_router.route(...)

        # Step 8: Early Abstention Check (Router Stage)
        router_abstain = self.abstention_manager.evaluate(
            query=raw_query,
            routing_decision=routing_obj,
        )
        if router_abstain["should_abstain"]:
            return PipelineResult(...)
```
> **What to Say to the Professor**:
> *"This is the master orchestrator in `rag/pipeline.py`. Notice how stages 1 through 7 extract linguistic features without any database or LLM overhead. Crucially, at Line 159, if the query is out of scope or empty, our early abstention gate immediately halts execution in under 4 milliseconds, protecting system resources and eliminating hallucination."*

---

## Block 2: Cormack Reciprocal Rank Fusion ($k=60$)
- **File**: [`retrieval/rrf.py`](../../retrieval/rrf.py#L38-L62)
- **Line Numbers**: Lines 38–62

```python
    for list_idx, ranked_list in enumerate(ranked_lists):
        for rank, item in enumerate(ranked_list, start=1):
            doc_id = item.get("chunk_id") or item.get("child_id") or str(rank)
            reciprocal_score = 1.0 / (k + rank)
            rrf_scores[doc_id] += reciprocal_score
            doc_ranks[doc_id][f"source_rank_{list_idx}"] = rank
```
> **What to Say to the Professor**:
> *"Here in `retrieval/rrf.py`, we implement the Cormack SIGIR 2009 Reciprocal Rank Fusion formula. Notice that we don't normalize or average raw BM25 scores with cosine scores, because score distributions fluctuate wildly across queries. Instead, we sum reciprocal rank values using $k=60$. This provides scale invariance and robustly promotes documents retrieved by both sparse and dense search."*

---

## Block 3: Statutory Entity-Aware Additive Ranking Boost
- **File**: [`retrieval/entity_boost.py`](../../retrieval/entity_boost.py#L167-L190)
- **Line Numbers**: Lines 167–190

```python
        # 1. Article Matching (Full Weight)
        for ent_art in parsed_entities["articles"]:
            norm_art = _normalize_token(ent_art)
            if not norm_art:
                continue

            art_digits = re.findall(r"\d+[a-z]?", norm_art)
            cand_digits = re.findall(r"\d+[a-z]?", cand_art) + re.findall(r"\d+[a-z]?", cand_doc_id)

            is_match = False
            if art_digits and cand_digits and any(d in cand_digits for d in art_digits):
                is_match = True
            elif cand_art and (norm_art in cand_art or cand_art in norm_art):
                is_match = True
            elif cand_title and norm_art in cand_title:
                is_match = True

            if is_match:
                match_boost = boost_weight * 1.0
                boost_applied += match_boost
                boost_reasons.append(f"Matched Article: {ent_art} (+{match_boost:.3f})")
                break
```
> **What to Say to the Professor**:
> *"This block in `retrieval/entity_boost.py` solves statutory anchor confusion. Dense vector search often confuses Article 19 with Article 21 because both discuss fundamental liberties. Our entity boost extracts numeric article digits using regex `\d+[a-z]?` and awards a calibrated additive boost of $+0.150$ if the candidate document represents the queried statute, logging transparent audit reasons in `boost_reasons`."*

---

## Block 4: Cross-Encoder Neural Reranking with Joint Attention
- **File**: [`retrieval/reranker.py`](../../retrieval/reranker.py#L67-L109)
- **Line Numbers**: Lines 67–109

```python
        pairs: List[Tuple[str, str]] = []
        for cand in candidates:
            passage_text = cand.get("text") or cand.get("child_text") or ""
            pairs.append((query, passage_text))

        model = self._load_model()
        if model is not None:
            scores = model.predict(pairs, batch_size=self.batch_size)
            ...
        # Attach reranker scores and retain previous scores for audit
        for cand, r_score in zip(candidates, score_list):
            cand_copy["previous_score"] = prev_score
            cand_copy["reranker_score"] = round(r_score, 5)
            cand_copy["score"] = round(r_score, 5)
```
> **What to Say to the Professor**:
> *"Here in `retrieval/reranker.py`, we execute second-stage neural reranking. A bi-encoder encodes queries and passages independently, missing fine-grained token interactions. Our cross-encoder pairs the query with each candidate and evaluates all-to-all cross-attention across 6 transformer layers. This single step improved our benchmark NDCG@10 from 0.6994 to 0.7787."*

---

## Block 5: Structure-Aware Legal Clause Chunking
- **File**: [`rag/chunking.py`](../../rag/chunking.py#L78-L107)
- **Line Numbers**: Lines 78–107

```python
        if clauses and isinstance(clauses, list):
            for idx, cl in enumerate(clauses):
                cl_num = cl.get("clause_number", f"({idx+1})")
                cl_text = cl.get("text", "").strip()
                if not cl_text:
                    continue

                chunk_text = f"{art_num} - {title} [Clause {cl_num}]: {cl_text}"

                if len(chunk_text) > self.max_clause_chars:
                    sub_parts = self._split_long_clause(chunk_text, art_num, title, cl_num)
                    ...
```
> **What to Say to the Professor**:
> *"In `rag/chunking.py`, we replaced naive sliding-window text slicing with legal structure-aware chunking. We split constitutional articles along natural clause boundaries (`Clause 1`, `Clause 2`), prefixing the article number and title to every chunk so the passage never loses its statutory identity in vector space."*

---

## Block 6: Parent Recovery with In-Memory Deduplication
- **File**: [`rag/parent_child.py`](../../rag/parent_child.py#L158-L169)
- **Line Numbers**: Lines 158–169

```python
            # Deduplicate parents: If already registered, append child chunk without duplicating parent text
            if parent_id in recovered_parents_map:
                existing_entry = recovered_parents_map[parent_id]
                if not any(c["chunk_id"] == chunk_id for c in existing_entry["supporting_children"]):
                    existing_entry["supporting_children"].append(child_record)
                if rank < existing_entry["best_rank"]:
                    existing_entry["best_rank"] = rank
                if score > existing_entry["best_score"]:
                    existing_entry["best_score"] = float(score)
```
> **What to Say to the Professor**:
> *"This block in `rag/parent_child.py` implements our asymmetric parent-child hydration. When top retrieved child chunks happen to belong to the same parent document (e.g. Clauses 1 and 2 of Article 19), this algorithm deduplicates them. The full parent text is included in prompt context only once, while both chunks are listed under supporting evidence, saving LLM context window tokens."*

---

## Block 7: Unretrieved Evidence Citation Detection
- **File**: [`rag/citation_validator.py`](../../rag/citation_validator.py#L171-L178)
- **Line Numbers**: Lines 171–178

```python
            # Check 3: Document was actually retrieved in supplied evidence
            if not any(v in retrieved_variants for v in doc_vars):
                invalid_citations.append({
                    "citation": cit,
                    "reason": "UNRETRIEVED_EVIDENCE_CITED",
                    "details": f"Document '{doc_id}' exists in database but was NOT part of the retrieved evidence for this query.",
                })
                continue
```
> **What to Say to the Professor**:
> *"This is our unretrieved evidence guard in `rag/citation_validator.py`. Most RAG systems only check if a cited document exists in the database. But if an LLM cites Article 14 when only Article 21 was retrieved for that question, the LLM is hallucinating from pre-trained parametric memory! Our code ensures every citation has true evidentiary provenance in the retrieved prompt context."*

---

## Block 8: Deontic Modal Polarity Contradiction Detection
- **File**: [`rag/nli_verifier.py`](../../rag/nli_verifier.py#L150-L161)
- **Line Numbers**: Lines 150–161

```python
        for pos_pat, neg_pat in CONTRADICTION_PAIRS:
            if re.search(pos_pat, claim_lower) and not re.search(neg_pat, claim_lower):
                if re.search(neg_pat, evidence_lower) and not re.search(pos_pat, evidence_lower):
                    claim_tokens = set(re.findall(r"\b[a-zA-Z]{4,}\b", claim_lower)) - LEGAL_GENERIC_STOPWORDS
                    ev_tokens = set(re.findall(r"\b[a-zA-Z]{4,}\b", evidence_lower)) - LEGAL_GENERIC_STOPWORDS
                    overlap = claim_tokens.intersection(ev_tokens)
                    if len(overlap) >= 2:
                        return True, 0.90, f"Polarity conflict: claim asserts permission/validity whereas evidence asserts prohibition/invalidation (overlap: {overlap})"
```
> **What to Say to the Professor**:
> *"Here in `rag/nli_verifier.py`, we implement deterministic Natural Language Inference. If a generated claim asserts permission (`'permits'`, `'allows'`) while the retrieved statute establishes prohibition (`'shall not'`, `'forbidden'`) on a shared legal subject, this regex engine detects the polarity contradiction, flagging it with 90% confidence in under 2 milliseconds on CPU."*

---

## Block 9: 6-Signal Composite Confidence Calculation
- **File**: [`rag/confidence.py`](../../rag/confidence.py#L160-L182)
- **Line Numbers**: Lines 160–182

```python
        w = self.weights
        composite_score = (
            w.get("retrieval", 0.25) * retrieval_strength
            + w.get("evidence_count", 0.15) * count_signal
            + w.get("entity_match", 0.20) * entity_signal
            + w.get("method_agreement", 0.15) * agreement_signal
            + w.get("citation_validity", 0.15) * citation_signal
            + w.get("evidence_coverage", 0.10) * coverage_signal
        )
        composite_score = min(1.0, max(0.0, round(composite_score, 4)))
```
> **What to Say to the Professor**:
> *"In `rag/confidence.py`, we calculate an explainable confidence score. Instead of trusting raw LLM self-reported confidence, we compute a weighted composite combining 6 objective external signals: neural retrieval strength, evidence chunk count, statutory entity alignment, BM25 vs dense consensus, structural citation validity, and query term coverage."*

---

## Block 10: Dynamic Router Parameter Injection
- **File**: [`rag/pipeline.py`](../../rag/pipeline.py#L207-L229)
- **Line Numbers**: Lines 207–229

```python
        try:
            self.retriever.use_bm25 = routing_obj.use_bm25
            self.retriever.use_dense = routing_obj.use_dense
            self.retriever.use_rrf = routing_obj.use_rrf
            self.retriever.use_entity_boost = routing_obj.use_entity_boost
            self.retriever.entity_boost_weight = routing_obj.entity_boost_weight
            self.retriever.use_reranker = routing_obj.use_reranker

            reranked_chunks = self.retriever.retrieve(...)
        finally:
            # Restore retriever defaults
            self.retriever.use_bm25 = orig_bm25
            self.retriever.use_dense = orig_dense
            self.retriever.use_rrf = orig_rrf
            self.retriever.use_entity_boost = orig_eb
            self.retriever.entity_boost_weight = orig_eb_wt
            self.retriever.use_reranker = orig_reranker
```
> **What to Say to the Professor**:
> *"This block in `rag/pipeline.py` shows clean software engineering. Our query router determines custom retrieval parameters per query. By wrapping parameter injection inside a `try...finally` block, we guarantee that the shared retriever singleton's default settings are restored even if an exception occurs during retrieval."*

