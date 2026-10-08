"""
Parent-Child Context Recovery Module for Legal RAG.
Recovers full parent document context for winning child chunks,
preserves granular provenance, prevents duplicate parent contexts,
and formats grounded evidence for generation.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from config import PARENT_STORE_PATH


class ParentChildRecovery:
    """
    Manages the recovery, deduplication, and provenance tracking of parent documents
    associated with retrieved child passages.
    """

    def __init__(self, parent_store: Optional[Dict[str, Dict[str, Any]]] = None):
        self.parent_store = parent_store if parent_store is not None else {}
        if not self.parent_store and os.path.exists(PARENT_STORE_PATH):
            try:
                with open(PARENT_STORE_PATH, "r", encoding="utf-8") as f:
                    self.parent_store = json.load(f)
            except Exception:
                self.parent_store = {}

        # Also load from expanded production corpus if available
        from config import CONSTITUTION_ARTICLES_PATH
        if len(self.parent_store) < 20 and os.path.exists(CONSTITUTION_ARTICLES_PATH):
            try:
                from rag.ingestion import ProductionIngestor
                ingestor = ProductionIngestor(use_full_corpus=True)
                full_parents, _ = ingestor.process_parent_child_chunks()
                for k, v in full_parents.items():
                    if k not in self.parent_store:
                        self.parent_store[k] = v
            except Exception:
                pass

    def _resolve_parent_record(self, raw_id: str, chunk: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Resolves parent data across key variations (zero-padding, parent_ prefix)."""
        candidates = [
            raw_id,
            chunk.get("parent_id", ""),
            chunk.get("document_id", ""),
            f"parent_{raw_id}",
            raw_id.replace("parent_", ""),
            re.sub(r"_0+(\d+)", r"_\1", raw_id),
            re.sub(r"_(\d+)", lambda m: f"_{int(m.group(1)):03d}", raw_id),
        ]
        for c in candidates:
            if c and c in self.parent_store:
                return c, self.parent_store[c]

        # Match by metadata article_number or case_name
        meta = chunk.get("metadata", {})
        art = meta.get("article_number") or chunk.get("article_number")
        if art:
            for pid, pdata in self.parent_store.items():
                if pdata.get("article_number") == art:
                    return pid, pdata

        case = meta.get("case_name") or chunk.get("case_name")
        if case:
            case_lower = case.lower()
            for pid, pdata in self.parent_store.items():
                if pdata.get("case_name", "").lower() in case_lower or case_lower in pdata.get("case_name", "").lower():
                    return pid, pdata

        # Fallback to embedded parent_data if present
        if "parent_data" in chunk and isinstance(chunk["parent_data"], dict):
            pdata = chunk["parent_data"]
            pid = pdata.get("document_id", pdata.get("id", raw_id or "parent_doc"))
            return pid, pdata

        # Fallback minimal record
        fallback_id = raw_id or chunk.get("document_id") or "doc_unknown"
        return fallback_id, {
            "document_id": fallback_id,
            "title": chunk.get("title", fallback_id),
            "doc_type": chunk.get("doc_type", "legal_document"),
            "raw_text": chunk.get("text", chunk.get("child_text", "")),
        }

    def recover(self, ranked_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Recovers parent documents from winning child chunks, deduplicates them,
        and constructs an exact provenance map.

        Args:
            ranked_chunks: Ordered list of retrieved and reranked child chunk dictionaries.

        Returns:
            Dictionary containing:
            - parents: Deduplicated list of recovered parent records with supporting children
            - child_evidence: List of exact child passages with rank, score, and parent linkage
            - child_to_parent_map: Dict mapping child_id -> parent_id
            - provenance_records: Granular audit trail records
            - formatted_context: Rendered prompt context string for grounded generation
        """
        if not ranked_chunks:
            return {
                "parents": [],
                "parent_count": 0,
                "child_count": 0,
                "child_evidence": [],
                "child_to_parent_map": {},
                "provenance_records": [],
                "formatted_context": "",
            }

        recovered_parents_map: Dict[str, Dict[str, Any]] = {}
        child_evidence: List[Dict[str, Any]] = []
        child_to_parent_map: Dict[str, str] = {}
        provenance_records: List[Dict[str, Any]] = []

        for idx, chunk in enumerate(ranked_chunks):
            # Extract standard identifiers
            chunk_id = chunk.get("chunk_id") or chunk.get("child_id") or f"chunk_{idx}"
            raw_pid = chunk.get("parent_id") or chunk.get("document_id") or ""
            child_text = chunk.get("text") or chunk.get("child_text") or ""
            score = chunk.get("rerank_score", chunk.get("score", chunk.get("rrf_score", 0.0)))
            rank = chunk.get("rank", idx + 1)
            clause_id = chunk.get("clause_id") or chunk.get("metadata", {}).get("clause_id") or ""
            clause_type = chunk.get("clause_type") or chunk.get("metadata", {}).get("clause_type") or ""

            # Robust resolution of canonical parent document
            parent_id, parent_data = self._resolve_parent_record(raw_pid, chunk)

            child_to_parent_map[chunk_id] = parent_id

            child_record = {
                "chunk_id": chunk_id,
                "parent_id": parent_id,
                "rank": rank,
                "score": float(score),
                "text": child_text,
                "clause_id": clause_id,
                "clause_type": clause_type,
                "doc_type": parent_data.get("doc_type", chunk.get("doc_type", "unknown")),
            }
            child_evidence.append(child_record)

            provenance_records.append({
                "chunk_id": chunk_id,
                "parent_id": parent_id,
                "rank": rank,
                "score": float(score),
                "clause_id": clause_id,
                "source_title": parent_data.get("title") or parent_data.get("case_name") or parent_id,
            })

            # Deduplicate parents: If already registered, append child chunk without duplicating parent text
            if parent_id in recovered_parents_map:
                existing_entry = recovered_parents_map[parent_id]
                # Avoid duplicate child entries inside the parent
                if not any(c["chunk_id"] == chunk_id for c in existing_entry["supporting_children"]):
                    existing_entry["supporting_children"].append(child_record)
                # Keep highest score / best rank
                if rank < existing_entry["best_rank"]:
                    existing_entry["best_rank"] = rank
                if score > existing_entry["best_score"]:
                    existing_entry["best_score"] = float(score)
            else:
                doc_type = parent_data.get("doc_type", "constitution")
                title = parent_data.get("title") or parent_data.get("case_name") or parent_id
                art_num = parent_data.get("article_number", "")
                case_name = parent_data.get("case_name", "")
                citation = parent_data.get("citation", "")
                year = parent_data.get("year", "")
                bench = parent_data.get("bench", "")
                part = parent_data.get("part", "")
                category = parent_data.get("category", "")
                raw_text = parent_data.get("raw_text") or parent_data.get("full_text") or child_text
                full_text = parent_data.get("full_text") or parent_data.get("raw_text") or child_text
                explanation = parent_data.get("explanation", "")
                historical_context = parent_data.get("historical_context", "")
                facts = parent_data.get("facts", "")
                ratio = parent_data.get("ratio_decidendi", "")
                verdict = parent_data.get("verdict", "")
                takeaways = parent_data.get("key_takeaways", [])

                recovered_parents_map[parent_id] = {
                    "document_id": parent_id,
                    "parent_id": parent_id,
                    "doc_type": doc_type,
                    "title": title,
                    "article_number": art_num,
                    "case_name": case_name,
                    "citation": citation,
                    "year": year,
                    "bench": bench,
                    "part": part,
                    "category": category,
                    "raw_text": raw_text,
                    "full_text": full_text,
                    "explanation": explanation,
                    "historical_context": historical_context,
                    "facts": facts,
                    "ratio_decidendi": ratio,
                    "verdict": verdict,
                    "key_takeaways": takeaways,
                    "best_rank": rank,
                    "best_score": float(score),
                    "supporting_children": [child_record],
                }

        # Sort deduplicated parents by best rank
        sorted_parents = sorted(recovered_parents_map.values(), key=lambda p: p["best_rank"])

        # Format context for generator
        formatted_context = self.format_context_for_prompt(sorted_parents)

        return {
            "parents": sorted_parents,
            "parent_count": len(sorted_parents),
            "child_count": len(child_evidence),
            "child_evidence": child_evidence,
            "child_to_parent_map": child_to_parent_map,
            "provenance_records": provenance_records,
            "formatted_context": formatted_context,
        }

    def format_context_for_prompt(self, parents: List[Dict[str, Any]]) -> str:
        """
        Renders parent and child context into clean, structured prompt markdown
        with clear citation keys [Doc: <document_id>].
        """
        if not parents:
            return "No verified context documents available."

        blocks = []
        for idx, p in enumerate(parents, start=1):
            doc_id = p["document_id"]
            doc_type = p["doc_type"]
            header = f"=== SOURCE DOCUMENT {idx} [DocID: {doc_id}] ==="

            lines = [header]
            lines.append(f"Document Type: {doc_type.upper()}")
            lines.append(f"Title / Name: {p['title']}")

            if doc_type == "constitution":
                if p.get("article_number"):
                    lines.append(f"Article Number: {p['article_number']}")
                if p.get("part"):
                    lines.append(f"Part: {p['part']}")
                if p.get("category"):
                    lines.append(f"Category: {p['category']}")
                if p.get("full_text"):
                    lines.append(f"Full Statutory Text:\n> {p['full_text'].strip()}")
                if p.get("explanation"):
                    lines.append(f"Legal Explanation:\n{p['explanation'].strip()}")
                if p.get("historical_context"):
                    lines.append(f"Historical Context:\n{p['historical_context'].strip()}")
            elif doc_type == "judgment":
                if p.get("citation"):
                    lines.append(f"Citation: {p['citation']}")
                if p.get("year"):
                    lines.append(f"Year: {p['year']}")
                if p.get("bench"):
                    lines.append(f"Judicial Bench: {p['bench']}")
                if p.get("facts"):
                    lines.append(f"Facts of Case:\n{p['facts'].strip()}")
                if p.get("ratio_decidendi"):
                    lines.append(f"Ratio Decidendi:\n{p['ratio_decidendi'].strip()}")
                if p.get("verdict"):
                    lines.append(f"Verdict:\n{p['verdict'].strip()}")
                if p.get("key_takeaways"):
                    lines.append(f"Key Takeaways: {'; '.join(p['key_takeaways'])}")
            else:
                if p.get("full_text"):
                    lines.append(f"Text Content:\n{p['full_text'].strip()}")

            # Append exact supporting retrieved child passages
            children = p.get("supporting_children", [])
            if children:
                lines.append("\nExact Retrieved Child Evidence Passages:")
                for c_idx, c in enumerate(children, start=1):
                    lines.append(
                        f"  * [Evidence {idx}.{c_idx} | ChunkID: {c['chunk_id']} | Rank {c['rank']}]: \"{c['text']}\""
                    )

            blocks.append("\n".join(lines))

        return "\n\n" + "\n\n".join(blocks) + "\n"
