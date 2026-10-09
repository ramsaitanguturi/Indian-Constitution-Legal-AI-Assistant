"""
Hybrid Legal Named Entity Recognition (NER) Module for Indian Constitutional Law.
Extracts 10 entity categories using high-precision regex patterns, legal gazetteers
derived from corpus metadata, and span-level resolution:
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
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

from config import (
    CONSTITUTION_ARTICLES_PATH,
    CONSTITUTION_AMENDMENTS_PATH,
    JUDGMENTS_LANDMARKS_PATH,
)


class LegalNER:
    """
    Hybrid Legal NER engine combining regex rules and structured gazetteers.
    """

    # 1. Regex Patterns for Formal Legal Constructs
    ARTICLE_PATTERN = re.compile(
        r"\b(?:Articles?|Arts?\.?)\s*(\d+[A-Z]?(?:\s*\([0-9a-zA-Z]+\))*(?:\s*(?:to|-)\s*\d+[A-Z]?)?|Preamble)(?!\w)",
        re.IGNORECASE
    )

    SECTION_PATTERN = re.compile(
        r"\b(?:Sections?|Secs?\.?)\s*(\d+[A-Z]?)\b",
        re.IGNORECASE
    )

    AMENDMENT_PATTERN = re.compile(
        r"\b(\d{1,3}(?:st|nd|rd|th)?|\b(?:First|Twenty-fourth|Forty-second|Forty-fourth|Eighty-sixth|Ninety-ninth|One Hundred and Third)\b)\s+(?:Constitutional\s+)?Amendment(?:\s+Act)?(?:\s*,\s*\d{4})?\b",
        re.IGNORECASE
    )

    DATE_PATTERN = re.compile(
        r"\b(?:\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|"
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4}|"
        r"\b(?:19[4-9]\d|20[0-2]\d)\b)",
        re.IGNORECASE
    )

    PERSON_TITLE_PATTERN = re.compile(
        r"\b(?:Chief\s+Justice|Justice|Dr\.)\s+([A-Z]\.(?:\s*[A-Z]\.)*\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|[A-Z][a-z]+\s+[A-Z][a-z]+)\b"
    )

    # 2. Curated Gazetteers with Built-In Fallback Knowledge Base
    DEFAULT_COURTS = [
        "Supreme Court of India", "Supreme Court", "High Court of Delhi", "Delhi High Court",
        "High Court of Bombay", "Bombay High Court", "Allahabad High Court", "Madras High Court",
        "Calcutta High Court", "Constituent Assembly", "Privy Council"
    ]

    DEFAULT_PERSONS = [
        "Dr. B. R. Ambedkar", "B. R. Ambedkar", "Dr. B.R. Ambedkar", "B.R. Ambedkar", "Ambedkar",
        "Jawaharlal Nehru", "Nehru", "Sardar Vallabhbhai Patel", "Sardar Patel", "Nani Palkhivala", "Palkhivala",
        "Justice K.S. Puttaswamy", "Justice D.Y. Chandrachud", "Justice Chandrachud",
        "Justice P.N. Bhagwati", "Justice Bhagwati", "Justice V.R. Krishna Iyer", "Justice Krishna Iyer",
        "Justice H.R. Khanna", "Justice Khanna", "Indira Gandhi", "Maneka Gandhi",
        "A. N. Ray", "H. R. Khanna", "P. N. Bhagwati", "D. Y. Chandrachud",
        "J. S. Khehar", "V. R. Krishna Iyer", "K. S. Hegde", "S. M. Sikri",
        "R. M. Lodha", "K. Subba Rao", "Y. V. Chandrachud", "Ranjan Gogoi",
        "Kesavananda Bharati", "Shreya Singhal", "Shayara Bano", "Navtej Singh Johar",
        "Joseph Shine", "Champakam Dorairajan", "A.K. Gopalan", "Bhim Singh"
    ]

    DEFAULT_RIGHTS = [
        "right to privacy", "right to life", "personal liberty", "right to personal liberty",
        "right to equality", "equality before law", "equal protection of the laws",
        "freedom of speech and expression", "freedom of speech", "freedom of press",
        "right to education", "right to constitutional remedies", "freedom of conscience",
        "freedom of religion", "right to freedom of religion", "right to clean environment",
        "right to livelihood", "right to travel abroad", "right against exploitation",
        "protection against double jeopardy", "protection against self-incrimination",
        "protection against ex-post facto laws"
    ]

    DEFAULT_LEGAL_CONCEPTS = [
        "basic structure", "due process of law", "due process",
        "procedure established by law", "judicial review", "rule of law", "separation of powers",
        "substantive equality", "reasonable classification", "golden triangle", "manifest arbitrariness",
        "proportionality test", "proportionality", "doctrine of severability", "doctrine of eclipse",
        "doctrine of waiver", "pith and substance", "colorable legislation", "constitutional morality",
        "transformative constitutionalism", "secularism", "federalism", "cooperative federalism",
        "habeas corpus", "mandamus", "certiorari", "quo warranto", "prohibition",
        "public interest litigation", "locus standi", "creamy layer", "preventive detention",
        "sedition", "reasonable restrictions", "sovereignty", "fraternity", "amending power",
        "forced labour", "complete justice", "untouchability"
    ]

    DEFAULT_ACTS = [
        "Constitution of India", "Aadhaar Act", "Information Technology Act",
        "Representation of the People Act", "Indian Penal Code", "Code of Criminal Procedure",
        "Kerala Land Reforms Act", "Armed Forces Special Powers Act", "Unlawful Activities (Prevention) Act",
        "Right to Information Act", "National Judicial Appointments Commission Act"
    ]

    DEFAULT_CASES = [
        "Kesavananda Bharati", "Kesavananda", "Puttaswamy", "Justice K.S. Puttaswamy v. Union of India",
        "Maneka Gandhi", "Maneka Gandhi v. Union of India", "A.K. Gopalan", "A.K. Gopalan v. State of Madras",
        "Minerva Mills", "Minerva Mills v. Union of India", "S.R. Bommai", "S.R. Bommai v. Union of India",
        "Navtej Singh Johar", "Navtej Singh Johar v. Union of India", "Shreya Singhal", "Shreya Singhal v. Union of India",
        "Shayara Bano", "Shayara Bano v. Union of India", "Indra Sawhney", "Indra Sawhney v. Union of India",
        "Champakam Dorairajan", "State of Madras v. Champakam Dorairajan", "I.C. Golak Nath", "Golaknath",
        "Shankari Prasad", "Sajjan Singh", "Waman Rao", "ADM Jabalpur", "ADM Jabalpur v. Shivkant Shukla",
        "Vishaka", "Vishaka v. State of Rajasthan", "Kedar Nath Singh", "Romesh Thappar",
        "Bennett Coleman", "Subhash Kashinath Mahajan", "Joseph Shine", "Indian Young Lawyers Association",
        "Sabarimala Case", "Common Cause", "M.C. Mehta", "Bhim Singh", "E.P. Royappa", "Royappa",
        "Unni Krishnan", "Mohini Jain", "P.A. Inamdar", "T.M.A. Pai"
    ]

    def __init__(self):
        self.courts: List[str] = list(self.DEFAULT_COURTS)
        self.persons: List[str] = list(self.DEFAULT_PERSONS)
        self.rights: List[str] = list(self.DEFAULT_RIGHTS)
        self.concepts: List[str] = list(self.DEFAULT_LEGAL_CONCEPTS)
        self.acts: List[str] = list(self.DEFAULT_ACTS)
        self.cases: List[str] = list(self.DEFAULT_CASES)
        
        # Load and augment gazetteers from active corpus files
        self._load_corpus_gazetteers()
        
        # Sort multi-word gazetteers by length descending to prioritize greedy/longest matches
        self._sort_gazetteers()

    def _load_corpus_gazetteers(self):
        """Augment gazetteers dynamically using corpus files."""
        # 1. Judgments
        if Path(JUDGMENTS_LANDMARKS_PATH).exists():
            try:
                with open(JUDGMENTS_LANDMARKS_PATH, "r", encoding="utf-8") as f:
                    judgments = json.load(f)
                for j in judgments:
                    case_name = j.get("case_name")
                    if case_name:
                        self.cases.append(case_name)
                        # Extract popular shorthand (e.g., "Kesavananda Bharati" from "Kesavananda Bharati v. State...")
                        short_name = case_name.split(" v. ")[0].split(" vs. ")[0].strip()
                        if len(short_name) > 3:
                            self.cases.append(short_name)
                    for act in j.get("acts_referred", []):
                        if act:
                            self.acts.append(act)
                    for kw in j.get("keywords", []):
                        if kw and len(kw.strip()) > 2:
                            kw_clean = kw.strip().lower()
                            # Prevent case names and acts from polluting concepts
                            if not any(c.lower() == kw_clean for c in self.cases) and not any(a.lower() == kw_clean for a in self.acts):
                                self.concepts.append(kw_clean)
            except Exception:
                pass

        # 2. Amendments
        if Path(CONSTITUTION_AMENDMENTS_PATH).exists():
            try:
                with open(CONSTITUTION_AMENDMENTS_PATH, "r", encoding="utf-8") as f:
                    amends = json.load(f)
                for a in amends:
                    num = a.get("amendment_number")
                    if num:
                        self.concepts.append(num.lower())
            except Exception:
                pass

        # Deduplicate while preserving casing
        self.cases = list({c.strip(): c for c in self.cases if c and len(c.strip()) > 2}.values())
        self.acts = list({a.strip(): a for a in self.acts if a and len(a.strip()) > 2}.values())
        
        # Clean concepts to ensure no collision with cases or acts
        case_lowers = {c.lower() for c in self.cases}
        act_lowers = {a.lower() for a in self.acts}
        dedup_concepts = {}
        for c in self.concepts:
            c_clean = c.strip().lower()
            if c_clean == "basic structure doctrine":
                continue
            if len(c_clean) > 2 and c_clean not in case_lowers and c_clean not in act_lowers:
                dedup_concepts[c_clean] = c
        self.concepts = list(dedup_concepts.values())

    def _sort_gazetteers(self):
        """Sort gazetteer entries by length descending for longest-match-first matching."""
        self.cases.sort(key=len, reverse=True)
        self.persons.sort(key=len, reverse=True)
        self.courts.sort(key=len, reverse=True)
        self.rights.sort(key=len, reverse=True)
        self.concepts.sort(key=len, reverse=True)
        self.acts.sort(key=len, reverse=True)

    def extract_spans(self, text: str) -> List[Dict[str, Any]]:
        """
        Extracts non-overlapping entity spans from text across all 10 categories.
        
        Returns:
            List of dictionaries with: text, label, start, end, normalized, confidence.
        """
        if not text:
            return []

        raw_candidates: List[Dict[str, Any]] = []

        # 1. Regex: ARTICLE
        for match in self.ARTICLE_PATTERN.finditer(text):
            raw_text = match.group(0)
            art_val = match.group(1).strip()
            norm = "Preamble" if art_val.lower() == "preamble" else f"Article {art_val.upper()}"
            raw_candidates.append({
                "text": raw_text,
                "label": "ARTICLE",
                "start": match.start(),
                "end": match.end(),
                "normalized": norm,
                "confidence": 0.98
            })

        # Check explicit "Preamble" if not already captured
        for m in re.finditer(r"\bpreamble\b", text, re.IGNORECASE):
            raw_candidates.append({
                "text": m.group(0),
                "label": "ARTICLE",
                "start": m.start(),
                "end": m.end(),
                "normalized": "Preamble",
                "confidence": 0.95
            })

        # 2. Regex: SECTION
        for match in self.SECTION_PATTERN.finditer(text):
            sec_val = match.group(1).strip()
            raw_candidates.append({
                "text": match.group(0),
                "label": "SECTION",
                "start": match.start(),
                "end": match.end(),
                "normalized": f"Section {sec_val.upper()}",
                "confidence": 0.95
            })

        # 3. Regex: AMENDMENT
        for match in self.AMENDMENT_PATTERN.finditer(text):
            raw_candidates.append({
                "text": match.group(0),
                "label": "AMENDMENT",
                "start": match.start(),
                "end": match.end(),
                "normalized": match.group(0).strip(),
                "confidence": 0.95
            })

        # 4. Regex: DATE
        for match in self.DATE_PATTERN.finditer(text):
            # Exclude numbers if part of Article/Section match
            raw_candidates.append({
                "text": match.group(0),
                "label": "DATE",
                "start": match.start(),
                "end": match.end(),
                "normalized": match.group(0).strip(),
                "confidence": 0.90
            })

        # 5. Regex: PERSON with Title (Justice, Chief Justice, Dr.) -> high priority!
        for match in self.PERSON_TITLE_PATTERN.finditer(text):
            p_name = match.group(1).strip()
            raw_candidates.append({
                "text": p_name,
                "label": "PERSON",
                "start": match.start(1),
                "end": match.end(1),
                "normalized": p_name,
                "confidence": 0.98
            })

        # Helper for gazetteer search
        text_lower = text.lower()

        def _match_gazetteer(items: List[str], label: str, conf: float):
            for item in items:
                item_len = len(item)
                if item_len < 3:
                    continue
                # Use word boundary search
                pattern = r"\b" + re.escape(item.lower()) + r"\b"
                for m in re.finditer(pattern, text_lower):
                    cand_text = text[m.start():m.end()]

                    if item.lower() == "maneka gandhi":
                        prefix = text_lower[:m.start()].strip()
                        suffix = text_lower[m.end():].strip()
                        if prefix.endswith("in") or suffix.startswith("v.") or suffix.startswith("vs.") or suffix.startswith("case"):
                            cand_label = "CASE"
                        else:
                            cand_label = "PERSON"
                        if cand_label != label:
                            continue

                    raw_candidates.append({
                        "text": cand_text,
                        "label": label,
                        "start": m.start(),
                        "end": m.end(),
                        "normalized": item,
                        "confidence": conf
                    })

        # 6. Gazetteer: CASES
        _match_gazetteer(self.cases, "CASE", 0.92)

        # 7. Gazetteer: COURTS
        _match_gazetteer(self.courts, "COURT", 0.94)

        # 8. Gazetteer: PERSONS
        _match_gazetteer(self.persons, "PERSON", 0.90)

        # 9. Gazetteer: RIGHTS
        _match_gazetteer(self.rights, "RIGHT", 0.92)

        # 10. Gazetteer: LEGAL_CONCEPT
        _match_gazetteer(self.concepts, "LEGAL_CONCEPT", 0.88)

        # 11. Gazetteer: ACTS
        _match_gazetteer(self.acts, "ACT", 0.90)

        # Resolve conflicts: sort by length descending, start ascending, then label priority
        label_priority = {
            "ARTICLE": 10,
            "SECTION": 9,
            "AMENDMENT": 8,
            "CASE": 7,
            "RIGHT": 6,
            "ACT": 5,
            "PERSON": 4,
            "COURT": 3,
            "LEGAL_CONCEPT": 2,
            "DATE": 1
        }

        # If candidate is a title-matched PERSON (confidence >= 0.95), boost priority to 7.5
        def get_priority(cand: Dict[str, Any]) -> float:
            lbl = cand["label"]
            if lbl == "PERSON" and cand.get("confidence", 0) >= 0.95:
                return 7.5
            return label_priority.get(lbl, 0)

        # Sort candidates so superior matches are accepted first
        raw_candidates.sort(
            key=lambda c: (
                -(c["end"] - c["start"]),  # Longest span first
                -get_priority(c),  # Highest priority
                c["start"]
            )
        )

        selected_spans: List[Dict[str, Any]] = []
        occupied_ranges: List[Tuple[int, int]] = []

        for cand in raw_candidates:
            c_start, c_end = cand["start"], cand["end"]
            # Check overlap with already chosen spans
            overlap = False
            for o_start, o_end in occupied_ranges:
                if not (c_end <= o_start or c_start >= o_end):
                    overlap = True
                    break
            if not overlap:
                selected_spans.append(cand)
                occupied_ranges.append((c_start, c_end))

        # Sort final spans in document order (by start index)
        selected_spans.sort(key=lambda s: s["start"])
        return selected_spans

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extracts entities grouped by target 10 categories.
        
        Returns:
            Dict mapping:
            "ARTICLE", "CASE", "PERSON", "COURT", "LEGAL_CONCEPT",
            "RIGHT", "AMENDMENT", "ACT", "SECTION", "DATE"
            to lists of normalized entity strings.
        """
        all_categories = [
            "ARTICLE", "CASE", "PERSON", "COURT", "LEGAL_CONCEPT",
            "RIGHT", "AMENDMENT", "ACT", "SECTION", "DATE"
        ]
        result: Dict[str, List[str]] = {cat: [] for cat in all_categories}

        spans = self.extract_spans(text)
        for s in spans:
            label = s["label"]
            norm_val = s["normalized"]
            if norm_val not in result[label]:
                result[label].append(norm_val)

        return result

    def extract_legacy_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Backward-compatible extractor matching legacy LegalNERExtractor output:
        {"articles": [...], "cases": [...], "concepts": [...]}
        """
        structured = self.extract_entities(text)
        legacy = {
            "articles": structured.get("ARTICLE", []),
            "cases": structured.get("CASE", []),
            "concepts": []
        }

        # Combine concepts, rights, amendments for legacy callers
        for cat in ["LEGAL_CONCEPT", "RIGHT", "AMENDMENT"]:
            for item in structured.get(cat, []):
                val_lower = item.lower()
                if val_lower not in legacy["concepts"]:
                    legacy["concepts"].append(val_lower)

        return legacy


# Global singleton instance for high-performance reuse
_NER_INSTANCE: Optional[LegalNER] = None


def get_legal_ner() -> LegalNER:
    """Returns or lazily initializes the shared LegalNER instance."""
    global _NER_INSTANCE
    if _NER_INSTANCE is None:
        _NER_INSTANCE = LegalNER()
    return _NER_INSTANCE
