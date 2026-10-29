"""
Information Retrieval Benchmark Evaluator for Indian Constitutional Law.

Evaluates:
- BM25 Okapi baseline
- Dense Semantic Retrieval (ChromaDB + all-MiniLM-L6-v2)
- BM25 + Dense (without RRF)
- Reciprocal Rank Fusion (RRF)
- Legal Entity Boost
- Cross-Encoder Reranking
- Full End-to-End Hybrid Pipeline

Metrics:
- Hit@1, Hit@3, Hit@5, Hit@10
- Recall@5, Recall@10
- MRR (Mean Reciprocal Rank)
- NDCG@5, NDCG@10
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Union, Tuple

from config import (
    RETRIEVAL_BENCHMARK_PATH,
    RELEVANCE_LABELS_PATH,
    PARENT_STORE_PATH,
)
from evaluation.metrics import (
    hit_at_k,
    recall_at_k,
    precision_at_k,
    reciprocal_rank,
    ndcg_at_k,
    aggregate_retrieval_metrics,
)


class RetrievalEvaluator:
    """
    Evaluator for Information Retrieval models against gold-standard relevance judgments.
    """

    def __init__(
        self,
        benchmark_path: Optional[Union[str, Path]] = None,
        relevance_labels_path: Optional[Union[str, Path]] = None,
        parent_store: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.benchmark_path = Path(benchmark_path or RETRIEVAL_BENCHMARK_PATH)
        self.relevance_labels_path = Path(relevance_labels_path or RELEVANCE_LABELS_PATH)
        self.parent_store = parent_store or {}

        if not self.parent_store and os.path.exists(PARENT_STORE_PATH):
            try:
                with open(PARENT_STORE_PATH, "r", encoding="utf-8") as f:
                    self.parent_store = json.load(f)
            except Exception:
                pass

        self.queries: List[Dict[str, Any]] = []
        self.relevance_labels: Dict[str, Dict[str, float]] = {}
        self.canonical_map: Dict[str, str] = self._build_canonical_map()
        self.load_benchmark()

    def _build_canonical_map(self) -> Dict[str, str]:
        """Constructs verified canonical document mappings across constitutional articles and judgments."""
        m: Dict[str, str] = {}
        # From parent_store
        for k, v in self.parent_store.items():
            pid = v.get("parent_id")
            if pid:
                m[k] = pid
                m[k.lower()] = pid

        # Canonical rules for articles
        import re
        for k in list(m.keys()):
            if k.startswith("parent_const_art_"):
                suffix = k[len("parent_const_art_"):]
                if suffix.isdigit():
                    num = int(suffix)
                    m[f"parent_const_art_{num}"] = m[k]
                    m[f"parent_const_art_{str(num).zfill(3)}"] = m[k]
                else:
                    match = re.match(r"^(\d+)([a-zA-Z]+)$", suffix)
                    if match:
                        n, s = int(match.group(1)), match.group(2)
                        canon = m[k]
                        m[f"parent_const_art_{n}{s.lower()}"] = canon
                        m[f"parent_const_art_{n}{s.upper()}"] = canon
                        m[f"parent_const_art_{str(n).zfill(3)}{s.lower()}"] = canon
                        m[f"parent_const_art_{str(n).zfill(3)}{s.upper()}"] = canon

        # Explicit verified case mappings
        case_mappings = {
            'parent_case_kesavananda': 'parent_case_sc_kesavananda_1973',
            'parent_case_maneka': 'parent_case_sc_maneka_gandhi_1978',
            'parent_case_puttaswamy': 'parent_case_sc_puttaswamy_privacy_2017',
            'parent_case_minerva': 'parent_case_sc_minerva_mills_1980',
            'parent_case_bommai': 'parent_case_sc_sr_bommai_1994',
            'parent_case_sc_ak_gopalan_1950': 'parent_sc_fulltext_1950insc13_1950_1_88_334',
            'parent_case_ak': 'parent_sc_fulltext_1950insc13_1950_1_88_334',
            'parent_case_sc_romesh_thappar_1950': 'parent_sc_fulltext_1950insc14_1950_1_594_605',
            'parent_case_romesh': 'parent_sc_fulltext_1950insc14_1950_1_594_605',
            'parent_case_sc_brij_bhushan_1950': 'parent_sc_fulltext_1950insc15_1950_1_605_620',
            'parent_case_brij': 'parent_sc_fulltext_1950insc15_1950_1_605_620',
            'parent_case_sc_champakam_dorairajan_1951': 'parent_sc_fulltext_1951insc26_1951_1_525_533',
            'parent_case_champakam': 'parent_sc_fulltext_1951insc26_1951_1_525_533',
            'parent_case_sc_shankari_prasad_1951': 'parent_sc_fulltext_1951insc47_1952_1_89_109',
            'parent_case_shankari': 'parent_sc_fulltext_1951insc47_1952_1_89_109',
            'parent_case_sc_adr_voter_rights_2002': 'parent_case_sc_adr_2002',
            'parent_case_adr': 'parent_case_sc_adr_2002',
            'parent_case_sc_bennett_coleman_1972': 'parent_case_sc_bennett_coleman_1973',
            'parent_case_bennett': 'parent_case_sc_bennett_coleman_1973',
            'parent_case_sc_ep_royappa_1974': 'parent_case_sc_royappa_1974',
            'parent_case_ep': 'parent_case_sc_royappa_1974',
            'parent_case_sc_kharak_singh_1962': 'parent_case_sc_kharak_singh_1963',
            'parent_case_kharak': 'parent_case_sc_kharak_singh_1963',
            'parent_case_sc_m_nagaraj_2006': 'parent_case_sc_nagaraj_2006',
            'parent_case_m': 'parent_case_sc_nagaraj_2006',
            'parent_case_sc_njac_fourth_judges_2015': 'parent_case_sc_fourth_judges_njac_2015',
            'parent_case_njac': 'parent_case_sc_fourth_judges_njac_2015',
            'parent_case_sc_scara_second_judges_1993': 'parent_case_sc_second_judges_1993',
            'parent_case_scara': 'parent_case_sc_second_judges_1993',
            'parent_case_sc_sp_gupta_1981': 'parent_case_sc_first_judges_1981',
            'parent_case_sp': 'parent_case_sc_first_judges_1981',
            'parent_case_adm': 'parent_case_sc_adm_jabalpur_1976',
            'parent_case_anuradha': 'parent_case_sc_anuradha_bhasin_2020',
            'parent_case_aruna': 'parent_case_sc_aruna_shanbaug_2011',
            'parent_case_bandhua': 'parent_case_sc_bandhua_mukti_1984',
            'parent_case_bijoe': 'parent_case_sc_bijoe_emmanuel_1986',
            'parent_case_common': 'parent_case_sc_common_cause_2018',
            'parent_case_dk': 'parent_case_sc_dk_basu_1997',
            'parent_case_francis': 'parent_case_sc_francis_coralie_1981',
            'parent_case_golak': 'parent_case_sc_golak_nath_1967',
            'parent_case_indira': 'parent_case_sc_indira_gandhi_1975',
            'parent_case_indra': 'parent_case_sc_indra_sawhney_1992',
            'parent_case_ir': 'parent_case_sc_ir_coelho_2007',
            'parent_case_jallikattu': 'parent_case_sc_jallikattu_2014',
            'parent_case_janhit': 'parent_case_sc_janhit_abhiyan_2022',
            'parent_case_jarnail': 'parent_case_sc_jarnail_singh_2018',
            'parent_case_joseph': 'parent_case_sc_joseph_shine_2018',
            'parent_case_kihoto': 'parent_case_sc_kihoto_hollohan_1992',
            'parent_case_lily': 'parent_case_sc_lily_thomas_2013',
            'parent_case_navtej': 'parent_case_sc_navtej_johar_2018',
            'parent_case_nct': 'parent_case_sc_nct_delhi_2018',
            'parent_case_olga': 'parent_case_sc_olga_tellis_1985',
            'parent_case_pucl': 'parent_case_sc_pucl_nota_2013',
            'parent_case_sabarimala': 'parent_case_sc_sabarimala_2018',
            'parent_case_sajjan': 'parent_case_sc_sajjan_singh_1965',
            'parent_case_sakal': 'parent_case_sc_sakal_papers_1962',
            'parent_case_selvi': 'parent_case_sc_selvi_2010',
            'parent_case_shayara': 'parent_case_sc_shayara_bano_2017',
            'parent_case_shirur': 'parent_case_sc_shirur_mutt_1954',
            'parent_case_shreya': 'parent_case_sc_shreya_singhal_2015',
            'parent_case_sr': 'parent_case_sc_sr_bommai_1994',
            'parent_case_sunil': 'parent_case_sc_sunil_batra_1978',
            'parent_case_third': 'parent_case_sc_third_judges_1998',
            'parent_case_vishaka': 'parent_case_sc_vishaka_1997',
            'parent_case_waman': 'parent_case_sc_waman_rao_1981',
        }
        m.update(case_mappings)
        return m

    def resolve_canonical_id(self, doc_id: str) -> str:
        """Resolves alias or legacy document ID to verified canonical parent ID."""
        if not doc_id:
            return ""
        return self.canonical_map.get(doc_id, self.canonical_map.get(doc_id.lower(), doc_id))

    def load_benchmark(self) -> None:
        """Loads benchmark queries and graded relevance labels."""
        if self.benchmark_path.exists():
            with open(self.benchmark_path, "r", encoding="utf-8") as f:
                self.queries = json.load(f)
        else:
            self.queries = []

        if self.relevance_labels_path.exists():
            with open(self.relevance_labels_path, "r", encoding="utf-8") as f:
                self.relevance_labels = json.load(f)
        else:
            self.relevance_labels = {}

    def get_evaluable_queries(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Partitions queries into verified evaluable queries and queries requiring human annotation.
        Prevents fabricated results by explicitly excluding unannotated queries.
        """
        evaluable = []
        requires_annotation = []

        for q in self.queries:
            status = q.get("human_annotation_status", "verified")
            has_relevant = len(q.get("relevant_documents", [])) > 0 or q.get("query_id") in self.relevance_labels

            if status == "verified" and has_relevant:
                evaluable.append(q)
            else:
                requires_annotation.append(q)

        return evaluable, requires_annotation

    def evaluate_retriever(
        self,
        retriever_instance: Any,
        experiment_name: str = "retriever_evaluation",
        top_k: int = 10,
        eval_queries: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Executes evaluation against an instantiated retriever.
        
        Args:
            retriever_instance: Object with `.retrieve(query, top_k=...)` method.
            experiment_name: Descriptive name for experiment logging.
            top_k: Number of candidates to retrieve per query.
            eval_queries: Optional override of queries to evaluate.
            
        Returns:
            Dictionary with aggregated metrics, query breakdown, and reproducibility metadata.
        """
        evaluable, queued = self.get_evaluable_queries()
        queries_to_eval = eval_queries if eval_queries is not None else evaluable

        if not queries_to_eval:
            return {
                "experiment_name": experiment_name,
                "status": "NO_EVALUABLE_QUERIES",
                "sample_count": 0,
                "requires_annotation_count": len(queued),
                "metrics": aggregate_retrieval_metrics([]),
                "query_details": []
            }

        start_time = time.time()
        query_level_metrics: List[Dict[str, float]] = []
        query_details: List[Dict[str, Any]] = []

        for q in queries_to_eval:
            qid = q["query_id"]
            query_str = q["query"]

            # Ground truth targets
            gold_docs = set(q.get("relevant_documents", []))
            gold_chunks = set(q.get("relevant_chunks", []))
            graded_labels = self.relevance_labels.get(qid, {d: 1.0 for d in gold_docs})

            # Execute retrieval
            try:
                retrieved_results = retriever_instance.retrieve(query_str, top_k=top_k)
            except TypeError:
                retrieved_results = retriever_instance.retrieve(query_str)

            # Extract retrieved IDs (both document/parent level and chunk level)
            retrieved_doc_ids: List[str] = []
            retrieved_chunk_ids: List[str] = []

            for item in retrieved_results:
                if isinstance(item, dict):
                    pid = item.get("parent_id")
                    cid = item.get("chunk_id")
                    can_pid = self.resolve_canonical_id(pid) if pid else None
                    target_pid = can_pid or pid
                    if target_pid and target_pid not in retrieved_doc_ids:
                        retrieved_doc_ids.append(target_pid)
                    if cid and cid not in retrieved_chunk_ids:
                        retrieved_chunk_ids.append(cid)
                elif isinstance(item, (list, tuple)) and len(item) >= 1:
                    cid = item[0]
                    retrieved_chunk_ids.append(cid)
                    # Lookup parent from parent store if available
                    if self.parent_store and cid in self.parent_store:
                        pid = self.parent_store[cid].get("parent_id")
                        can_pid = self.resolve_canonical_id(pid) if pid else None
                        target_pid = can_pid or pid
                        if target_pid and target_pid not in retrieved_doc_ids:
                            retrieved_doc_ids.append(target_pid)

            # For document-level evaluation: use retrieved_doc_ids; fallback to chunk IDs
            eval_ids = retrieved_doc_ids if retrieved_doc_ids else retrieved_chunk_ids
            # Canonicalize gold target set
            raw_gold = list(gold_docs if gold_docs else gold_chunks)
            eval_gold = []
            for d in raw_gold:
                cd = self.resolve_canonical_id(d)
                if cd and cd not in eval_gold:
                    eval_gold.append(cd)

            # Compute metrics for this query
            h1 = hit_at_k(eval_ids, eval_gold, 1, alias_map=self.canonical_map)
            h3 = hit_at_k(eval_ids, eval_gold, 3, alias_map=self.canonical_map)
            h5 = hit_at_k(eval_ids, eval_gold, 5, alias_map=self.canonical_map)
            h10 = hit_at_k(eval_ids, eval_gold, 10, alias_map=self.canonical_map)

            r5 = recall_at_k(eval_ids, eval_gold, 5, alias_map=self.canonical_map)
            r10 = recall_at_k(eval_ids, eval_gold, 10, alias_map=self.canonical_map)

            rr = reciprocal_rank(eval_ids, eval_gold, alias_map=self.canonical_map)

            ndcg5 = ndcg_at_k(eval_ids, graded_labels, 5, alias_map=self.canonical_map)
            ndcg10 = ndcg_at_k(eval_ids, graded_labels, 10, alias_map=self.canonical_map)

            # Compute first hit rank (1-indexed, None if not in retrieved list)
            gold_set = set(eval_gold)
            first_hit_rank = None
            for rank_idx, item_id in enumerate(eval_ids, start=1):
                can_item = self.resolve_canonical_id(item_id)
                if item_id in gold_set or can_item in gold_set:
                    first_hit_rank = rank_idx
                    break

            qm = {
                "Hit@1": h1,
                "Hit@3": h3,
                "Hit@5": h5,
                "Hit@10": h10,
                "Recall@5": r5,
                "Recall@10": r10,
                "MRR": rr,
                "NDCG@5": ndcg5,
                "NDCG@10": ndcg10
            }
            query_level_metrics.append(qm)

            query_details.append({
                "query_id": qid,
                "query": query_str,
                "intent": q.get("intent", ""),
                "gold_relevant": eval_gold,
                "retrieved_top_5": eval_ids[:5],
                "retrieved_top_10": eval_ids[:10],
                "first_hit_rank": first_hit_rank,
                "metrics": qm
            })

        latency = round(time.time() - start_time, 3)
        aggregated = aggregate_retrieval_metrics(query_level_metrics)

        return {
            "experiment_name": experiment_name,
            "status": "COMPLETED",
            "sample_count": len(query_level_metrics),
            "requires_human_annotation_count": len(queued),
            "total_latency_seconds": latency,
            "avg_latency_ms": round((latency / len(query_level_metrics)) * 1000, 2),
            "metrics": aggregated,
            "query_details": query_details
        }
