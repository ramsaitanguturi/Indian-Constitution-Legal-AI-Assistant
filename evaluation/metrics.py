"""
Mathematical Evaluation Metrics for Information Retrieval, Legal NLP, and Grounded RAG.

Covers:
1. Retrieval Metrics: Hit@K, Recall@K, Precision@K, MRR, DCG@K, NDCG@K
2. Named Entity Recognition: Exact span matching, Micro/Macro P/R/F1, per-category metrics
3. Intent Classification: Accuracy, Macro/Weighted P/R/F1, per-class breakdown, Confusion Matrix
4. Canonical Entity Linking: Exact linking accuracy, per-type accuracy, nil/unknown handling
5. Grounded RAG / Citations: Citation validity, citation precision, evidence coverage, abstention accuracy
6. Query Expansion: Expansion precision, useful vs distractor ratio
"""

import math
from typing import Dict, List, Any, Optional, Set, Union, Tuple


# =========================================================================
# 1. Information Retrieval Metrics
# =========================================================================

def hit_at_k(
    retrieved_ids: List[str],
    relevant_ids: Union[Set[str], List[str]],
    k: int
) -> float:
    """
    Hit@K (Binary): Returns 1.0 if at least one relevant document appears in top-K, else 0.0.
    
    Formula:
        Hit@K = 1 if |Retrieved[:K] ∩ Relevant| > 0 else 0
    """
    if k <= 0 or not retrieved_ids or not relevant_ids:
        return 0.0
    rel_set = set(relevant_ids) if not isinstance(relevant_ids, set) else relevant_ids
    top_k = retrieved_ids[:k]
    return 1.0 if any(doc_id in rel_set for doc_id in top_k) else 0.0


def recall_at_k(
    retrieved_ids: List[str],
    relevant_ids: Union[Set[str], List[str]],
    k: int
) -> float:
    """
    Recall@K: Proportion of relevant documents retrieved in top-K.
    
    Formula:
        Recall@K = |Retrieved[:K] ∩ Relevant| / |Relevant|
    """
    if k <= 0 or not relevant_ids:
        return 0.0
    if not retrieved_ids:
        return 0.0
    rel_set = set(relevant_ids) if not isinstance(relevant_ids, set) else relevant_ids
    if len(rel_set) == 0:
        return 0.0
    top_k = retrieved_ids[:k]
    hits = sum(1 for doc_id in top_k if doc_id in rel_set)
    return round(float(hits) / float(len(rel_set)), 4)


def precision_at_k(
    retrieved_ids: List[str],
    relevant_ids: Union[Set[str], List[str]],
    k: int
) -> float:
    """
    Precision@K: Proportion of top-K retrieved documents that are relevant.
    
    Formula:
        Precision@K = |Retrieved[:K] ∩ Relevant| / K
    """
    if k <= 0:
        return 0.0
    if not retrieved_ids or not relevant_ids:
        return 0.0
    rel_set = set(relevant_ids) if not isinstance(relevant_ids, set) else relevant_ids
    top_k = retrieved_ids[:k]
    hits = sum(1 for doc_id in top_k if doc_id in rel_set)
    return round(float(hits) / float(k), 4)


def reciprocal_rank(
    retrieved_ids: List[str],
    relevant_ids: Union[Set[str], List[str]]
) -> float:
    """
    Reciprocal Rank (RR): 1 / rank of the first relevant document (1-indexed).
    Returns 0.0 if no relevant document is found in retrieved results.
    
    Formula:
        RR = 1 / min_{i: retrieved[i] ∈ Relevant} (i + 1)
    """
    if not retrieved_ids or not relevant_ids:
        return 0.0
    rel_set = set(relevant_ids) if not isinstance(relevant_ids, set) else relevant_ids
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in rel_set:
            return round(1.0 / rank, 4)
    return 0.0


def mean_reciprocal_rank(reciprocal_ranks: List[float]) -> float:
    """Computes Mean Reciprocal Rank across queries."""
    if not reciprocal_ranks:
        return 0.0
    return round(float(sum(reciprocal_ranks)) / len(reciprocal_ranks), 4)


def dcg_at_k(
    retrieved_ids: List[str],
    relevance_scores: Union[Dict[str, float], Set[str], List[str]],
    k: int
) -> float:
    """
    Discounted Cumulative Gain (DCG@K) using standard logarithmic discount.
    
    Formula:
        DCG@K = sum_{i=1}^K (2^{rel_i} - 1) / log2(i + 1)
    """
    if k <= 0 or not retrieved_ids or not relevance_scores:
        return 0.0

    # Convert binary set/list to score dictionary
    if isinstance(relevance_scores, (set, list)):
        score_dict = {doc: 1.0 for doc in relevance_scores}
    else:
        score_dict = relevance_scores

    top_k = retrieved_ids[:k]
    dcg = 0.0
    for i, doc_id in enumerate(top_k, start=1):
        rel = score_dict.get(doc_id, 0.0)
        gain = (2.0 ** rel) - 1.0
        discount = math.log2(i + 1)
        dcg += gain / discount
    return dcg


def ndcg_at_k(
    retrieved_ids: List[str],
    relevance_scores: Union[Dict[str, float], Set[str], List[str]],
    k: int
) -> float:
    """
    Normalized Discounted Cumulative Gain (NDCG@K).
    
    Formula:
        NDCG@K = DCG@K / IDCG@K
    Returns 0.0 if IDCG@K == 0.0 (no relevant items exist).
    """
    if k <= 0 or not relevance_scores:
        return 0.0

    if isinstance(relevance_scores, (set, list)):
        score_dict = {doc: 1.0 for doc in relevance_scores}
    else:
        score_dict = relevance_scores

    # Ideal ranking: sort all non-zero relevance scores descending
    sorted_rels = sorted(score_dict.values(), reverse=True)
    if not sorted_rels or sorted_rels[0] <= 0.0:
        return 0.0

    idcg = 0.0
    for i, rel in enumerate(sorted_rels[:k], start=1):
        gain = (2.0 ** rel) - 1.0
        idcg += gain / math.log2(i + 1)

    if idcg <= 0.0:
        return 0.0

    dcg = dcg_at_k(retrieved_ids, score_dict, k)
    return round(float(dcg) / float(idcg), 4)


def aggregate_retrieval_metrics(query_metrics: List[Dict[str, float]]) -> Dict[str, float]:
    """Computes arithmetic mean for all retrieval metrics across benchmark queries."""
    if not query_metrics:
        return {
            "Hit@1": 0.0, "Hit@3": 0.0, "Hit@5": 0.0, "Hit@10": 0.0,
            "Recall@5": 0.0, "Recall@10": 0.0,
            "MRR": 0.0, "NDCG@5": 0.0, "NDCG@10": 0.0
        }
    n = len(query_metrics)
    keys = query_metrics[0].keys()
    agg = {}
    for key in keys:
        vals = [qm.get(key, 0.0) for qm in query_metrics]
        agg[key] = round(float(sum(vals)) / n, 4)
    return agg


# =========================================================================
# 2. Named Entity Recognition (NER) Metrics
# =========================================================================

ALL_LEGAL_ENTITY_TYPES = [
    "ARTICLE", "CASE", "PERSON", "COURT", "LEGAL_CONCEPT",
    "RIGHT", "AMENDMENT", "ACT", "SECTION", "DATE"
]


def calculate_ner_metrics(
    gold_annotations: List[Dict[str, Any]],
    predicted_annotations: List[Dict[str, Any]],
    exact_span_match: bool = True
) -> Dict[str, Any]:
    """
    Computes strict entity-level Precision, Recall, and F1 across all legal entity types.
    
    Args:
        gold_annotations: List of records with `id` and `entities`:
            [{"id": "...", "entities": [{"text": "...", "label": "...", "start": 0, "end": 10}]}]
        predicted_annotations: List of records matching gold format.
        exact_span_match: If True, matches (start, end, label).
                          If False, matches (label, text_lower).
                          
    Returns:
        Dictionary with overall Micro/Macro metrics and per-category breakdowns.
    """
    # Track True Positives, False Positives, False Negatives per entity category
    tp_per_cat: Dict[str, int] = {cat: 0 for cat in ALL_LEGAL_ENTITY_TYPES}
    fp_per_cat: Dict[str, int] = {cat: 0 for cat in ALL_LEGAL_ENTITY_TYPES}
    fn_per_cat: Dict[str, int] = {cat: 0 for cat in ALL_LEGAL_ENTITY_TYPES}
    support_per_cat: Dict[str, int] = {cat: 0 for cat in ALL_LEGAL_ENTITY_TYPES}

    pred_map = {item["id"]: item.get("entities", []) for item in predicted_annotations}

    for gold_item in gold_annotations:
        qid = gold_item["id"]
        gold_ents = gold_item.get("entities", [])
        pred_ents = pred_map.get(qid, [])

        if exact_span_match:
            gold_set = {(e["start"], e["end"], e["label"]) for e in gold_ents if "start" in e and "end" in e}
            pred_set = {(e["start"], e["end"], e["label"]) for e in pred_ents if "start" in e and "end" in e}
        else:
            gold_set = {(e["text"].strip().lower(), e["label"]) for e in gold_ents}
            pred_set = {(e["text"].strip().lower(), e["label"]) for e in pred_ents}

        # Track supports
        for item_tuple in gold_set:
            label = item_tuple[-1]
            if label not in support_per_cat:
                support_per_cat[label] = 0
                tp_per_cat[label] = 0
                fp_per_cat[label] = 0
                fn_per_cat[label] = 0
            support_per_cat[label] += 1

        # Matched true positives
        matched = gold_set.intersection(pred_set)
        for item_tuple in matched:
            label = item_tuple[-1]
            tp_per_cat[label] += 1

        # False positives (predicted but not in gold)
        fps = pred_set - gold_set
        for item_tuple in fps:
            label = item_tuple[-1]
            if label not in fp_per_cat:
                fp_per_cat[label] = 0
                tp_per_cat[label] = 0
                fn_per_cat[label] = 0
                support_per_cat[label] = 0
            fp_per_cat[label] += 1

        # False negatives (in gold but not predicted)
        fns = gold_set - pred_set
        for item_tuple in fns:
            label = item_tuple[-1]
            fn_per_cat[label] += 1

    # Per-category metrics
    per_class_results = {}
    f1_list, p_list, r_list = [], [], []

    for cat in sorted(set(ALL_LEGAL_ENTITY_TYPES).union(support_per_cat.keys())):
        tp = tp_per_cat.get(cat, 0)
        fp = fp_per_cat.get(cat, 0)
        fn = fn_per_cat.get(cat, 0)
        sup = support_per_cat.get(cat, 0)

        prec = float(tp) / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = float(tp) / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2.0 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        per_class_results[cat] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "support": sup,
            "tp": tp,
            "fp": fp,
            "fn": fn
        }

        # Include classes with support in macro calculations
        if sup > 0 or (tp + fp) > 0:
            f1_list.append(f1)
            p_list.append(prec)
            r_list.append(rec)

    # Micro aggregates
    total_tp = sum(tp_per_cat.values())
    total_fp = sum(fp_per_cat.values())
    total_fn = sum(fn_per_cat.values())

    micro_p = float(total_tp) / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    micro_r = float(total_tp) / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    micro_f1 = (2.0 * micro_p * micro_r) / (micro_p + micro_r) if (micro_p + micro_r) > 0 else 0.0

    # Macro aggregates
    macro_p = float(sum(p_list)) / len(p_list) if p_list else 0.0
    macro_r = float(sum(r_list)) / len(r_list) if r_list else 0.0
    macro_f1 = float(sum(f1_list)) / len(f1_list) if f1_list else 0.0

    return {
        "evaluation_definition": (
            f"Exact entity-level evaluation (matching: {'(start, end, label)' if exact_span_match else '(label, text)'}). "
            f"Precision = TP/(TP+FP), Recall = TP/(TP+FN), F1 = 2PR/(P+R)."
        ),
        "micro_precision": round(micro_p, 4),
        "micro_recall": round(micro_r, 4),
        "micro_f1": round(micro_f1, 4),
        "macro_precision": round(macro_p, 4),
        "macro_recall": round(macro_r, 4),
        "macro_f1": round(macro_f1, 4),
        "total_gold_entities": sum(support_per_cat.values()),
        "total_predicted_entities": total_tp + total_fp,
        "per_class": per_class_results
    }


# =========================================================================
# 3. Intent Classification Metrics
# =========================================================================

def calculate_classification_metrics(
    y_true: List[str],
    y_pred: List[str],
    classes: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Computes Accuracy, Macro/Weighted Precision/Recall/F1, and Confusion Matrix.
    Handles zero divisions, unknown classes, and empty inputs gracefully.
    """
    if not y_true or not y_pred:
        return {
            "sample_count": 0,
            "accuracy": 0.0,
            "macro_precision": 0.0,
            "macro_recall": 0.0,
            "macro_f1": 0.0,
            "weighted_f1": 0.0,
            "per_class": {},
            "classes": [],
            "confusion_matrix": []
        }

    assert len(y_true) == len(y_pred), f"Mismatched lengths: y_true={len(y_true)}, y_pred={len(y_pred)}"

    unique_classes = classes or sorted(list(set(y_true).union(set(y_pred))))
    total_samples = len(y_true)

    # Correct count
    correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    accuracy = float(correct) / total_samples

    # Confusion matrix & Per-class stats
    class_idx = {c: i for i, c in enumerate(unique_classes)}
    cm = [[0 for _ in range(len(unique_classes))] for _ in range(len(unique_classes))]

    for yt, yp in zip(y_true, y_pred):
        if yt in class_idx and yp in class_idx:
            cm[class_idx[yt]][class_idx[yp]] += 1

    per_class = {}
    macro_p_list, macro_r_list, macro_f1_list = [], [], []
    weighted_f1_sum = 0.0

    for idx, c in enumerate(unique_classes):
        tp = cm[idx][idx]
        fp = sum(cm[r][idx] for r in range(len(unique_classes)) if r != idx)
        fn = sum(cm[idx][c_col] for c_col in range(len(unique_classes)) if c_col != idx)
        support = sum(cm[idx])

        prec = float(tp) / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = float(tp) / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2.0 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        per_class[c] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "support": support
        }

        if support > 0 or (tp + fp) > 0:
            macro_p_list.append(prec)
            macro_r_list.append(rec)
            macro_f1_list.append(f1)
            weighted_f1_sum += f1 * support

    macro_p = float(sum(macro_p_list)) / len(macro_p_list) if macro_p_list else 0.0
    macro_r = float(sum(macro_r_list)) / len(macro_r_list) if macro_r_list else 0.0
    macro_f1 = float(sum(macro_f1_list)) / len(macro_f1_list) if macro_f1_list else 0.0
    weighted_f1 = float(weighted_f1_sum) / total_samples if total_samples > 0 else 0.0

    return {
        "sample_count": total_samples,
        "accuracy": round(accuracy, 4),
        "macro_precision": round(macro_p, 4),
        "macro_recall": round(macro_r, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "per_class": per_class,
        "classes": unique_classes,
        "confusion_matrix": cm
    }


# =========================================================================
# 4. Canonical Entity Linking Metrics
# =========================================================================

def calculate_entity_linking_metrics(
    eval_records: List[Dict[str, Any]],
    predicted_records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Evaluates Canonical Entity Linking performance.
    
    Checks exact canonical ID resolution, per-entity-type accuracy,
    and handling of out-of-KB / unknown entities (expected canonical ID is None).
    """
    if not eval_records:
        return {
            "sample_count": 0,
            "exact_linking_accuracy": 0.0,
            "correct_entity_id_rate": 0.0,
            "out_of_kb_rejection_accuracy": 0.0,
            "per_entity_type": {}
        }

    pred_map = {item["id"]: item.get("predicted_canonical_id") for item in predicted_records}

    total = len(eval_records)
    correct_total = 0
    nil_total = 0
    nil_correct = 0

    per_type_counts: Dict[str, Dict[str, int]] = {}

    for item in eval_records:
        qid = item["id"]
        etype = item.get("entity_type", "UNKNOWN")
        expected_id = item.get("expected_canonical_id")
        predicted_id = pred_map.get(qid)

        if etype not in per_type_counts:
            per_type_counts[etype] = {"total": 0, "correct": 0}
        per_type_counts[etype]["total"] += 1

        is_match = (expected_id == predicted_id)
        if is_match:
            correct_total += 1
            per_type_counts[etype]["correct"] += 1

        if expected_id is None:
            nil_total += 1
            if predicted_id is None:
                nil_correct += 1

    per_type_metrics = {}
    for etype, stats in per_type_counts.items():
        acc = float(stats["correct"]) / stats["total"] if stats["total"] > 0 else 0.0
        per_type_metrics[etype] = {
            "accuracy": round(acc, 4),
            "correct": stats["correct"],
            "total": stats["total"]
        }

    linking_acc = float(correct_total) / total if total > 0 else 0.0
    nil_acc = float(nil_correct) / nil_total if nil_total > 0 else 1.0

    return {
        "sample_count": total,
        "exact_linking_accuracy": round(linking_acc, 4),
        "correct_entity_id_rate": round(linking_acc, 4),
        "out_of_kb_rejection_accuracy": round(nil_acc, 4),
        "per_entity_type": per_type_metrics
    }


# =========================================================================
# 5. RAG / Grounding / Citation / Abstention Metrics
# =========================================================================

def calculate_rag_citation_metrics(
    eval_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Computes structural citation validity, precision, coverage, and abstention accuracy.
    
    IMPORTANT NOTE:
    Clearly distinguishes STRUCTURAL citation validation (checking that cited
    identifiers physically exist in retrieved corpus evidence) from SEMANTIC
    factual correctness. Structural validation does NOT prove legal correctness.
    """
    if not eval_results:
        return {
            "sample_count": 0,
            "citation_validity_rate": 0.0,
            "citation_precision": 0.0,
            "evidence_coverage": 0.0,
            "supported_claim_rate": 0.0,
            "unsupported_claim_rate": 0.0,
            "abstention_accuracy": 0.0,
            "structural_vs_semantic_note": (
                "Notice: Structural citation validation verifies evidence provenance "
                "and prevents fabricated citations. It does NOT claim semantic or substantive legal truth."
            )
        }

    total_questions = len(eval_results)
    total_citations_checked = 0
    total_valid_citations = 0

    total_retrieved_evidence = 0
    total_evidence_cited = 0

    total_supported_claims = 0
    total_unsupported_claims = 0
    total_claims = 0

    abstention_tests = 0
    correct_abstentions = 0

    for res in eval_results:
        # 1. Citations
        c_checked = res.get("citations_checked", 0)
        c_valid = res.get("valid_citations_count", 0)
        total_citations_checked += c_checked
        total_valid_citations += c_valid

        # 2. Evidence coverage
        ret_ev = res.get("retrieved_evidence_count", 0)
        ev_cited = res.get("cited_evidence_count", 0)
        total_retrieved_evidence += ret_ev
        total_evidence_cited += ev_cited

        # 3. Claims
        supp = res.get("supported_claims_count", 0)
        unsupp = res.get("unsupported_claims_count", 0)
        total_supported_claims += supp
        total_unsupported_claims += unsupp
        total_claims += (supp + unsupp)

        # 4. Abstention accuracy
        if "expected_action" in res and "actual_action" in res:
            abstention_tests += 1
            if res["expected_action"] == res["actual_action"]:
                correct_abstentions += 1

    validity_rate = (
        float(total_valid_citations) / total_citations_checked
        if total_citations_checked > 0 else 1.0
    )
    citation_prec = (
        float(total_valid_citations) / total_citations_checked
        if total_citations_checked > 0 else 1.0
    )
    evidence_cov = (
        float(total_evidence_cited) / total_retrieved_evidence
        if total_retrieved_evidence > 0 else 0.0
    )
    supp_rate = (
        float(total_supported_claims) / total_claims
        if total_claims > 0 else 1.0
    )
    unsupp_rate = (
        float(total_unsupported_claims) / total_claims
        if total_claims > 0 else 0.0
    )
    abstention_acc = (
        float(correct_abstentions) / abstention_tests
        if abstention_tests > 0 else 1.0
    )

    return {
        "sample_count": total_questions,
        "citation_validity_rate": round(validity_rate, 4),
        "citation_precision": round(citation_prec, 4),
        "evidence_coverage": round(evidence_cov, 4),
        "supported_claim_rate": round(supp_rate, 4),
        "unsupported_claim_rate": round(unsupp_rate, 4),
        "abstention_accuracy": round(abstention_acc, 4),
        "total_citations_checked": total_citations_checked,
        "total_valid_citations": total_valid_citations,
        "structural_vs_semantic_note": (
            "Notice: Structural citation validation verifies evidence provenance "
            "and prevents fabricated citations. It does NOT claim semantic or substantive legal truth."
        )
    }


# =========================================================================
# 6. Query Expansion Metrics
# =========================================================================

def calculate_query_expansion_metrics(
    expansion_eval_records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Evaluates controlled legal query expansion usefulness.
    Measures precision of expanded terms and detection of irrelevant terms.
    """
    if not expansion_eval_records:
        return {
            "sample_count": 0,
            "expansion_precision": 0.0,
            "drift_rate": 0.0,
            "average_terms_added": 0.0
        }

    total_expanded = 0
    useful_expanded = 0
    drift_terms = 0

    for rec in expansion_eval_records:
        exp_terms = rec.get("expanded_terms", [])
        gold_useful = set(rec.get("expected_useful_terms", []))
        distractors = set(rec.get("distractor_terms", []))

        total_expanded += len(exp_terms)
        for t in exp_terms:
            t_lower = t.strip().lower()
            # Useful if matches or contains any gold concept
            if any(u.lower() in t_lower or t_lower in u.lower() for u in gold_useful):
                useful_expanded += 1
            if any(d.lower() in t_lower for d in distractors):
                drift_rate += 1

    precision = float(useful_expanded) / total_expanded if total_expanded > 0 else 0.0
    drift_rate = float(drift_terms) / total_expanded if total_expanded > 0 else 0.0
    avg_terms = float(total_expanded) / len(expansion_eval_records) if expansion_eval_records else 0.0

    return {
        "sample_count": len(expansion_eval_records),
        "expansion_precision": round(precision, 4),
        "drift_rate": round(drift_rate, 4),
        "average_terms_added": round(avg_terms, 2)
    }
