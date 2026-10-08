"""
Controlled Legal Query Expansion Module for Indian Constitutional Law.
Deterministically maps conversational concepts and informal queries to formal constitutional
provisions, landmark doctrines, and statutory terms using a verified synonym graph.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

from config import SYNONYM_GRAPH_PATH, MAX_EXPANSION_TERMS
from nlp.preprocessing import normalize_legal_text
from nlp.legal_ner import get_legal_ner


class QueryExpander:
    """
    Controlled, deterministic legal query expansion engine.
    """

    def __init__(self, synonym_path: Optional[Path] = None):
        self.synonym_path = synonym_path or SYNONYM_GRAPH_PATH
        self.synonym_graph: Dict[str, List[str]] = {}
        self._load_synonym_graph()

    def _load_synonym_graph(self):
        """Loads synonym graph from JSON configuration file."""
        if Path(self.synonym_path).exists():
            try:
                with open(self.synonym_path, "r", encoding="utf-8") as f:
                    self.synonym_graph = json.load(f)
            except Exception:
                self.synonym_graph = {}

    def expand(
        self,
        query: str,
        max_terms: int = MAX_EXPANSION_TERMS,
        enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Expands user query with formal constitutional terminology.
        
        Args:
            query: Raw user query string.
            max_terms: Maximum number of expansion terms to append (prevents semantic drift).
            enabled: Master toggle to enable/disable expansion.
            
        Returns:
            {
                "original_query": str,
                "expanded_query": str,
                "expanded_terms": List[str],
                "expansion_sources": Dict[str, str],
                "was_expanded": bool
            }
        """
        if not query or not query.strip() or not enabled:
            return {
                "original_query": query,
                "expanded_query": query,
                "expanded_terms": [],
                "expansion_sources": {},
                "was_expanded": False
            }

        q_clean = normalize_legal_text(query, expand_abbreviations=True)
        q_lower = q_clean.lower()
        
        expanded_terms: List[str] = []
        expansion_sources: Dict[str, str] = {}
        seen_terms: Set[str] = set()

        # Iterate over synonym triggers (longest trigger phrases first)
        sorted_triggers = sorted(self.synonym_graph.keys(), key=len, reverse=True)

        for trigger in sorted_triggers:
            if len(expanded_terms) >= max_terms:
                break
                
            # Match whole-word boundary
            pattern = r"\b" + re.escape(trigger.lower()) + r"\b"
            if re.search(pattern, q_lower):
                target_terms = self.synonym_graph[trigger]
                for term in target_terms:
                    term_clean = term.strip()
                    term_lower = term_clean.lower()
                    
                    # Avoid adding term if already present in original query or already selected
                    if term_lower in q_lower or term_lower in seen_terms:
                        continue
                        
                    expanded_terms.append(term_clean)
                    seen_terms.add(term_lower)
                    expansion_sources[term_clean] = f"Triggered by concept '{trigger}'"
                    
                    if len(expanded_terms) >= max_terms:
                        break

        if expanded_terms:
            # Construct composite expanded query: "Original Query (term1 term2)"
            expanded_query_str = f"{q_clean} {' '.join(expanded_terms)}"
            return {
                "original_query": query,
                "expanded_query": expanded_query_str,
                "expanded_terms": expanded_terms,
                "expansion_sources": expansion_sources,
                "was_expanded": True
            }

        return {
            "original_query": query,
            "expanded_query": q_clean,
            "expanded_terms": [],
            "expansion_sources": {},
            "was_expanded": False
        }


# Global shared instance
_EXPANDER_INSTANCE: Optional[QueryExpander] = None


def get_query_expander() -> QueryExpander:
    """Returns or lazily initializes the shared QueryExpander."""
    global _EXPANDER_INSTANCE
    if _EXPANDER_INSTANCE is None:
        _EXPANDER_INSTANCE = QueryExpander()
    return _EXPANDER_INSTANCE
