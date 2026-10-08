"""
Entity Linking Module for Indian Constitutional Law.
Resolves surface mentions, abbreviations, and informal aliases to canonical legal entity IDs
with structured metadata linked directly to corpus documents.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

from config import (
    CONSTITUTION_ARTICLES_PATH,
    CONSTITUTION_AMENDMENTS_PATH,
    JUDGMENTS_LANDMARKS_PATH,
)
from nlp.legal_ner import get_legal_ner


class EntityLinker:
    """
    Canonical Entity Linker for Articles, Cases, Amendments, and Key Legal Doctrines.
    """

    def __init__(self):
        # Maps canonical_id -> entity record
        self.entity_registry: Dict[str, Dict[str, Any]] = {}
        # Maps normalized alias string -> canonical_id
        self.alias_index: Dict[str, str] = {}
        
        # 1. Seed with known core legal concepts and rights
        self._seed_foundational_concepts()
        
        # 2. Build index dynamically from corpus files
        self._build_index_from_corpus()

    def _normalize_key(self, text: str) -> str:
        """Normalizes surface text for robust dictionary lookup."""
        if not text:
            return ""
        # Lowercase, remove punctuation, collapse whitespace
        text = text.lower().strip()
        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def _seed_foundational_concepts(self):
        """Seed foundational doctrines, rights, and landmarks."""
        foundational = [
            {
                "entity_id": "CONCEPT_BASIC_STRUCTURE",
                "canonical_name": "Basic Structure Doctrine",
                "entity_type": "LEGAL_CONCEPT",
                "aliases": [
                    "basic structure", "basic structure doctrine",
                    "essential features of the constitution", "basic structure of the constitution"
                ],
                "metadata": {
                    "originating_case": "Kesavananda Bharati v. State of Kerala (1973)",
                    "core_provision": "Article 368",
                    "description": "Judicial principle that Parliament cannot alter the essential identity and core features of the Constitution."
                }
            },
            {
                "entity_id": "RIGHT_PRIVACY",
                "canonical_name": "Right to Privacy",
                "entity_type": "RIGHT",
                "aliases": [
                    "privacy", "right to privacy", "informational privacy",
                    "personal privacy", "fundamental right to privacy"
                ],
                "metadata": {
                    "originating_case": "Justice K.S. Puttaswamy v. Union of India (2017)",
                    "core_provision": "Article 21",
                    "description": "Intrinsic part of the right to life and personal liberty under Article 21."
                }
            },
            {
                "entity_id": "RIGHT_LIFE_LIBERTY",
                "canonical_name": "Right to Life and Personal Liberty",
                "entity_type": "RIGHT",
                "aliases": [
                    "right to life", "personal liberty", "life and liberty",
                    "right to live with human dignity"
                ],
                "metadata": {
                    "core_provision": "Article 21",
                    "description": "Guarantees that no person shall be deprived of life or personal liberty except by procedure established by law."
                }
            },
            {
                "entity_id": "RIGHT_EQUALITY",
                "canonical_name": "Right to Equality",
                "entity_type": "RIGHT",
                "aliases": [
                    "equality", "right to equality", "equality before law",
                    "equal protection of the laws", "substantive equality"
                ],
                "metadata": {
                    "core_provision": "Article 14",
                    "description": "Guarantees equality before law and equal protection of laws to all persons within India."
                }
            },
            {
                "entity_id": "RIGHT_FREE_SPEECH",
                "canonical_name": "Freedom of Speech and Expression",
                "entity_type": "RIGHT",
                "aliases": [
                    "free speech", "freedom of speech", "freedom of speech and expression",
                    "freedom of the press", "speech and expression"
                ],
                "metadata": {
                    "core_provision": "Article 19(1)(a)",
                    "description": "Guarantees freedom of speech subject to reasonable restrictions under Article 19(2)."
                }
            },
            {
                "entity_id": "CONCEPT_JUDICIAL_REVIEW",
                "canonical_name": "Judicial Review",
                "entity_type": "LEGAL_CONCEPT",
                "aliases": ["judicial review", "power of judicial review"],
                "metadata": {
                    "core_provisions": ["Article 13", "Article 32", "Article 226"],
                    "description": "Power of the Supreme Court and High Courts to examine the constitutional validity of legislative acts and executive orders."
                }
            },
            {
                "entity_id": "CONCEPT_DUE_PROCESS",
                "canonical_name": "Due Process of Law",
                "entity_type": "LEGAL_CONCEPT",
                "aliases": [
                    "due process", "due process of law", "substantive due process",
                    "procedural due process", "just fair and reasonable"
                ],
                "metadata": {
                    "originating_case": "Maneka Gandhi v. Union of India (1978)",
                    "core_provision": "Article 21",
                    "description": "Requirement that laws depriving liberty must not be arbitrary, fanciful, or oppressive."
                }
            }
        ]

        for item in foundational:
            eid = item["entity_id"]
            self.entity_registry[eid] = item
            for alias in item["aliases"]:
                self.alias_index[self._normalize_key(alias)] = eid

    def _build_index_from_corpus(self):
        """Index articles, amendments, and landmark judgments from active corpus files."""
        # 1. Articles Index
        if Path(CONSTITUTION_ARTICLES_PATH).exists():
            try:
                with open(CONSTITUTION_ARTICLES_PATH, "r", encoding="utf-8") as f:
                    articles = json.load(f)
                for art in articles:
                    art_num = art.get("article_number", "").strip()
                    if not art_num:
                        continue
                    
                    if art_num.lower() == "preamble":
                        eid = "PREAMBLE"
                        aliases = ["preamble", "preamble to the constitution", "constitution preamble"]
                        canonical_name = "Preamble"
                    else:
                        num_match = re.search(r"(\d+[A-Z]?)", art_num, re.IGNORECASE)
                        clean_num = num_match.group(1).upper() if num_match else art_num.upper()
                        eid = f"ARTICLE_{clean_num}"
                        canonical_name = f"Article {clean_num}"
                        aliases = [
                            canonical_name,
                            art_num,
                            f"art {clean_num}",
                            f"art. {clean_num}",
                            f"article {clean_num}",
                            f"article {clean_num} of the constitution",
                            clean_num
                        ]
                    
                    record = {
                        "entity_id": eid,
                        "canonical_name": canonical_name,
                        "entity_type": "ARTICLE",
                        "aliases": aliases,
                        "metadata": {
                            "document_id": art.get("document_id", art.get("id", "")),
                            "title": art.get("title", ""),
                            "part": art.get("part", ""),
                            "category": art.get("category", "")
                        }
                    }
                    self.entity_registry[eid] = record
                    for al in aliases:
                        norm_al = self._normalize_key(al)
                        if norm_al:
                            self.alias_index[norm_al] = eid
            except Exception:
                pass

        # 2. Amendments Index
        if Path(CONSTITUTION_AMENDMENTS_PATH).exists():
            try:
                with open(CONSTITUTION_AMENDMENTS_PATH, "r", encoding="utf-8") as f:
                    amendments = json.load(f)
                for amend in amendments:
                    amend_str = amend.get("amendment_number", "")
                    num_match = re.search(r"(\d+)", amend_str)
                    if num_match:
                        num = num_match.group(1)
                        eid = f"AMENDMENT_{num}"
                        aliases = [
                            amend_str,
                            f"{num}th amendment",
                            f"{num} amendment",
                            f"{num}th constitutional amendment",
                            f"amendment {num}"
                        ]
                        record = {
                            "entity_id": eid,
                            "canonical_name": amend_str,
                            "entity_type": "AMENDMENT",
                            "aliases": aliases,
                            "metadata": {
                                "document_id": amend.get("document_id", amend.get("id", "")),
                                "year": amend.get("year"),
                                "title": amend.get("title", "")
                            }
                        }
                        self.entity_registry[eid] = record
                        for al in aliases:
                            norm_al = self._normalize_key(al)
                            if norm_al:
                                self.alias_index[norm_al] = eid
            except Exception:
                pass

        # 3. Judgments Index
        if Path(JUDGMENTS_LANDMARKS_PATH).exists():
            try:
                with open(JUDGMENTS_LANDMARKS_PATH, "r", encoding="utf-8") as f:
                    judgments = json.load(f)
                for j in judgments:
                    case_name = j.get("case_name", "")
                    year = j.get("year", "")
                    doc_id = j.get("document_id", j.get("id", ""))
                    lower_name = case_name.lower()
                    
                    # Meaningful landmark case IDs and aliases
                    if "puttaswamy" in lower_name and ("privacy" in doc_id or year == 2017):
                        eid = "CASE_PUTTASWAMY_2017"
                        aliases = [
                            case_name, "Justice K.S. Puttaswamy", "Puttaswamy", "Puttaswamy case",
                            "Aadhaar case", "privacy judgment", "privacy case"
                        ]
                    elif "puttaswamy" in lower_name and ("aadhaar" in doc_id or year == 2018):
                        eid = "CASE_PUTTASWAMY_AADHAAR_2018"
                        aliases = [case_name, "Puttaswamy Aadhaar case", "Aadhaar judgment"]
                    elif "kesavananda" in lower_name:
                        eid = "CASE_KESAVANANDA_1973"
                        aliases = [
                            case_name, "Kesavananda Bharati", "Kesavananda",
                            "fundamental rights case", "basic structure case"
                        ]
                    elif "maneka gandhi" in lower_name:
                        eid = "CASE_MANEKA_1978"
                        aliases = [case_name, "Maneka Gandhi", "Maneka Gandhi case", "passport case"]
                    elif "gopalan" in lower_name:
                        eid = "CASE_GOPALAN_1950"
                        aliases = [case_name, "A.K. Gopalan", "AK Gopalan", "Gopalan", "gopalan case"]
                    elif "bommai" in lower_name:
                        eid = "CASE_BOMMAI_1994"
                        aliases = [case_name, "S.R. Bommai", "SR Bommai", "bommai case", "president rule case"]
                    elif "navtej" in lower_name:
                        eid = "CASE_NAVTEJ_2018"
                        aliases = [case_name, "Navtej Singh Johar", "section 377 case", "decriminalization of homosexuality"]
                    elif "shreya singhal" in lower_name:
                        eid = "CASE_SHREYA_SINGHAL_2015"
                        aliases = [case_name, "Shreya Singhal", "section 66a case", "online free speech case"]
                    elif "shayara bano" in lower_name:
                        eid = "CASE_SHAYARA_BANO_2017"
                        aliases = [case_name, "Shayara Bano", "triple talaq case"]
                    elif "indra sawhney" in lower_name:
                        eid = "CASE_INDRA_SAWHNEY_1992"
                        aliases = [case_name, "Indra Sawhney", "mandal case", "creamy layer case", "reservation case"]
                    elif "golak nath" in lower_name:
                        eid = "CASE_GOLAK_NATH_1967"
                        aliases = [case_name, "I.C. Golak Nath", "Golaknath", "golak nath case"]
                    elif "minerva mills" in lower_name:
                        eid = "CASE_MINERVA_1980"
                        aliases = [case_name, "Minerva Mills", "minerva mills case"]
                    else:
                        lead_party = case_name.split(" v. ")[0].split(" vs. ")[0].strip()
                        clean_slug = re.sub(r"[^\w]", "_", lead_party.upper()).strip("_")
                        words = [w for w in clean_slug.split("_") if w not in ("STATE", "UNION", "OF", "INDIA", "JUSTICE", "DR") and len(w) > 1]
                        short_slug = "_".join(words[:2]) if words else clean_slug[:12]
                        eid = f"CASE_{short_slug}_{year}".upper()
                        aliases = [case_name, lead_party]

                    record = {
                        "entity_id": eid,
                        "canonical_name": case_name,
                        "entity_type": "CASE",
                        "aliases": aliases,
                        "metadata": {
                            "document_id": doc_id,
                            "citation": j.get("citation", ""),
                            "year": year,
                            "bench": j.get("bench", ""),
                            "ratio_decidendi": j.get("ratio_decidendi", "")[:180] + "..." if j.get("ratio_decidendi") else ""
                        }
                    }
                    self.entity_registry[eid] = record
                    for al in aliases:
                        norm_al = self._normalize_key(al)
                        if norm_al:
                            self.alias_index[norm_al] = eid
            except Exception:
                pass

    def link_entity(self, mention: str, entity_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Links a single mention to its canonical legal entity.
        
        Args:
            mention: Surface text (e.g. "Art 21", "Puttaswamy", "42nd Amendment").
            entity_type: Optional hint (e.g. "ARTICLE", "CASE").
            
        Returns:
            Linked entity dictionary or None if unresolved.
        """
        if not mention or not mention.strip():
            return None

        clean_norm = self._normalize_key(mention)

        # 1. Exact alias match
        if clean_norm in self.alias_index:
            eid = self.alias_index[clean_norm]
            record = self.entity_registry[eid]
            return {
                "entity_id": eid,
                "canonical_name": record["canonical_name"],
                "entity_type": record["entity_type"],
                "surface_form": mention,
                "confidence": 1.0,
                "metadata": record.get("metadata", {})
            }

        # 2. Heuristic normalization for Articles (e.g. "Art. 21(1)" -> "ARTICLE_21")
        art_match = re.search(r"\b(?:art(?:icle)?\.?)\s*(\d+[A-Z]?)\b", mention, re.IGNORECASE)
        if art_match:
            art_num = art_match.group(1).upper()
            eid = f"ARTICLE_{art_num}"
            if eid in self.entity_registry:
                record = self.entity_registry[eid]
                return {
                    "entity_id": eid,
                    "canonical_name": record["canonical_name"],
                    "entity_type": "ARTICLE",
                    "surface_form": mention,
                    "confidence": 0.95,
                    "metadata": record.get("metadata", {})
                }

        # 3. Heuristic normalization for Amendments (e.g. "42nd Amendment" -> "AMENDMENT_42")
        amend_match = re.search(r"\b(\d+)(?:st|nd|rd|th)?\s+amendment\b", mention, re.IGNORECASE)
        if amend_match:
            num = amend_match.group(1)
            eid = f"AMENDMENT_{num}"
            if eid in self.entity_registry:
                record = self.entity_registry[eid]
                return {
                    "entity_id": eid,
                    "canonical_name": record["canonical_name"],
                    "entity_type": "AMENDMENT",
                    "surface_form": mention,
                    "confidence": 0.95,
                    "metadata": record.get("metadata", {})
                }

        # 4. Fuzzy / substring match across registered aliases
        for al, eid in self.alias_index.items():
            if len(al) > 3 and (al in clean_norm or clean_norm in al):
                record = self.entity_registry[eid]
                if entity_type and record.get("entity_type") != entity_type:
                    continue
                return {
                    "entity_id": eid,
                    "canonical_name": record["canonical_name"],
                    "entity_type": record["entity_type"],
                    "surface_form": mention,
                    "confidence": 0.85,
                    "metadata": record.get("metadata", {})
                }

        return None

    def link_all(self, extracted_entities: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """
        Links all entities extracted by LegalNER.
        
        Args:
            extracted_entities: Dictionary mapping category -> list of entity strings.
            
        Returns:
            List of unique linked entity dictionaries.
        """
        linked_list: List[Dict[str, Any]] = []
        seen_ids: Set[str] = set()

        for cat, mentions in extracted_entities.items():
            for m in mentions:
                res = self.link_entity(m, entity_type=cat)
                if res and res["entity_id"] not in seen_ids:
                    seen_ids.add(res["entity_id"])
                    linked_list.append(res)

        return linked_list

    def link_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Convenience pipeline: extracts entities via LegalNER and links them.
        """
        ner = get_legal_ner()
        extracted = ner.extract_entities(query)
        return self.link_all(extracted)


# Shared global instance
_LINKER_INSTANCE: Optional[EntityLinker] = None


def get_entity_linker() -> EntityLinker:
    """Returns or lazily initializes the shared EntityLinker instance."""
    global _LINKER_INSTANCE
    if _LINKER_INSTANCE is None:
        _LINKER_INSTANCE = EntityLinker()
    return _LINKER_INSTANCE
