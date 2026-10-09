"""
Canonical Entity Linking Benchmark Evaluator for Indian Constitutional Law.

Evaluates:
- Exact canonical entity ID resolution (must match canonical ID, not just surface string)
- Unknown / Ambiguous out-of-KB entity rejection rate
- Category-level breakdown across:
  - Articles (e.g. 'Art 21' -> ARTICLE_21)
  - Cases (e.g. 'Right to Privacy case' -> CASE_PUTTASWAMY_2017)
  - Amendments (e.g. '42nd Amendment' -> AMENDMENT_42)
  - Legal Concepts & Doctrines (e.g. 'basic structure doctrine' -> CONCEPT_BASIC_STRUCTURE)
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

from config import ENTITY_LINKING_BENCHMARK_PATH
from evaluation.metrics import calculate_entity_linking_metrics
from nlp.entity_linking import EntityLinker, get_entity_linker


class EntityLinkingEvaluator:
    """
    Evaluator for canonical legal entity linking.
    """

    def __init__(
        self,
        benchmark_path: Optional[Union[str, Path]] = None,
        linker_instance: Optional[EntityLinker] = None,
    ):
        self.benchmark_path = Path(benchmark_path or ENTITY_LINKING_BENCHMARK_PATH)
        self.linker = linker_instance or get_entity_linker()
        self.benchmark_records: List[Dict[str, Any]] = []
        self.load_benchmark()

    def load_benchmark(self) -> None:
        """Loads entity linking benchmark queries."""
        if self.benchmark_path.exists():
            with open(self.benchmark_path, "r", encoding="utf-8") as f:
                self.benchmark_records = json.load(f)
        else:
            self.benchmark_records = []

    def get_evaluable_records(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Separates verified records from queued unannotated records."""
        verified = []
        queued = []
        for rec in self.benchmark_records:
            status = rec.get("human_annotation_status", "verified")
            if status == "verified":
                verified.append(rec)
            else:
                queued.append(rec)
        return verified, queued

    def evaluate(self, experiment_name: str = "canonical_entity_linking_eval") -> Dict[str, Any]:
        """
        Runs entity linking benchmark evaluation.
        
        Evaluates whether:
        1. Surface mentions are mapped to the correct canonical entity ID.
        2. Merely detecting surface text is NOT counted as successful linking;
           canonical ID must be exact.
        3. Unknown/out-of-KB mentions resolve to None.
        """
        verified_records, queued_records = self.get_evaluable_records()

        if not verified_records:
            return {
                "experiment_name": experiment_name,
                "status": "NO_VERIFIED_RECORDS",
                "sample_count": 0,
                "requires_human_annotation_count": len(queued_records),
                "metrics": {}
            }

        start_time = time.time()
        predicted_records: List[Dict[str, Any]] = []

        for item in verified_records:
            qid = item["id"]
            mention = item["mention"]
            etype = item.get("entity_type")

            # Link entity via EntityLinker
            linked = self.linker.link_entity(mention, entity_type=etype if etype != "UNKNOWN" else None)
            pred_id = linked["entity_id"] if linked else None

            predicted_records.append({
                "id": qid,
                "mention": mention,
                "entity_type": etype,
                "predicted_canonical_id": pred_id
            })

        latency = round(time.time() - start_time, 3)
        metrics = calculate_entity_linking_metrics(verified_records, predicted_records)

        return {
            "experiment_name": experiment_name,
            "status": "COMPLETED",
            "sample_count": len(verified_records),
            "requires_human_annotation_count": len(queued_records),
            "total_latency_seconds": latency,
            "avg_latency_ms": round((latency / len(verified_records)) * 1000, 2),
            "metrics": metrics,
            "predictions": predicted_records
        }
