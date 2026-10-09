"""
Legal Named Entity Recognition (NER) Benchmark Evaluator for Indian Constitutional Law.

Evaluates:
- Exact entity span matching (start, end, label)
- Category-level Precision, Recall, and F1 across all 10 legal entity categories:
  - ARTICLE
  - CASE
  - PERSON
  - COURT
  - LEGAL_CONCEPT
  - RIGHT
  - AMENDMENT
  - ACT
  - SECTION
  - DATE
- Micro-average and Macro-average metrics
- Strict handling of unannotated queries (no fabricated annotations)
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

from config import NER_BENCHMARK_PATH
from evaluation.metrics import calculate_ner_metrics, ALL_LEGAL_ENTITY_TYPES
from nlp.legal_ner import LegalNER, get_legal_ner


class NEREvaluator:
    """
    Evaluator for Legal Named Entity Recognition systems.
    """

    def __init__(
        self,
        benchmark_path: Optional[Union[str, Path]] = None,
        ner_instance: Optional[LegalNER] = None,
    ):
        self.benchmark_path = Path(benchmark_path or NER_BENCHMARK_PATH)
        self.ner_instance = ner_instance or get_legal_ner()
        self.gold_records: List[Dict[str, Any]] = []
        self.load_benchmark()

    def load_benchmark(self) -> None:
        """Loads annotated NER benchmark from JSON."""
        if self.benchmark_path.exists():
            with open(self.benchmark_path, "r", encoding="utf-8") as f:
                self.gold_records = json.load(f)
        else:
            self.gold_records = []

    def get_evaluable_records(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Separates verified benchmark records from those requiring human annotation."""
        verified = []
        queued = []
        for rec in self.gold_records:
            status = rec.get("human_annotation_status", "verified")
            if status == "verified":
                verified.append(rec)
            else:
                queued.append(rec)
        return verified, queued

    def evaluate(
        self,
        exact_span_match: bool = True,
        experiment_name: str = "hybrid_legal_ner_eval"
    ) -> Dict[str, Any]:
        """
        Executes NER evaluation across benchmark records.
        
        Args:
            exact_span_match: If True, requires exact character start and end match.
            experiment_name: Name of experiment for reporting.
            
        Returns:
            Dictionary containing metrics breakdown across all 10 entity categories.
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
            text = item["text"]

            # Extract predicted entity spans
            spans = self.ner_instance.extract_spans(text)
            predicted_records.append({
                "id": qid,
                "text": text,
                "entities": spans
            })

        latency = round(time.time() - start_time, 3)

        # Calculate metrics using standard entity-level metric formula
        metrics = calculate_ner_metrics(
            gold_annotations=verified_records,
            predicted_annotations=predicted_records,
            exact_span_match=exact_span_match
        )

        return {
            "experiment_name": experiment_name,
            "status": "COMPLETED",
            "exact_span_match": exact_span_match,
            "sample_count": len(verified_records),
            "requires_human_annotation_count": len(queued_records),
            "total_latency_seconds": latency,
            "metrics": metrics,
            "category_coverage": {
                cat: metrics["per_class"].get(cat, {}).get("support", 0)
                for cat in ALL_LEGAL_ENTITY_TYPES
            }
        }
