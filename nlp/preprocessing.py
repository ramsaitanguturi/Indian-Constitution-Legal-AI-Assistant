"""
NLP Preprocessing Module for Indian Constitutional Legal Text.
Handles text normalization, unicode cleaning, case folding, legal abbreviation expansion,
and structure-preserving tokenization.
"""

import re
import unicodedata
from typing import List, Dict, Tuple, Optional


# Standard legal abbreviations mapped to full canonical terms
LEGAL_ABBREVIATIONS: Dict[str, str] = {
    # Judicial & Institutional
    r"\bS\.?C\.?I\.?\b": "Supreme Court of India",
    r"\bS\.?C\.?\b": "Supreme Court",
    r"\bH\.?C\.?\b": "High Court",
    r"\bC\.?J\.?I\.?\b": "Chief Justice of India",
    r"\bJ\.\b": "Justice",
    r"\bJJ\.\b": "Justices",
    r"\bU\.?O\.?I\.?\b": "Union of India",
    r"\bG\.?O\.?I\.?\b": "Government of India",
    r"\bC\.?O\.?I\.?\b": "Constitution of India",
    r"\bP\.?I\.?L\.?\b": "Public Interest Litigation",
    
    # Constitutional & Statutory Provisions - Check dotted form first
    r"\bArts?\.(?!\w)": "Article",
    r"\bArts?\b": "Article",
    r"\bSecs?\.(?!\w)": "Section",
    r"\bSecs?\b": "Section",
    r"\bCls?\.(?!\w)": "Clause",
    r"\bCls?\b": "Clause",
    r"\bSchs?\.(?!\w)": "Schedule",
    r"\bSchs?\b": "Schedule",
    r"\bu/a\b": "under Article",
    r"\bU/A\b": "under Article",
    r"\bu/s\b": "under Section",
    r"\bU/S\b": "under Section",
    r"\br/w\b": "read with",
    r"\bR/W\b": "read with",
    
    # Law Reports & Citations
    r"\bA\.?I\.?R\.?\b": "All India Reporter",
    r"\bS\.?C\.?C\.?\b": "Supreme Court Cases",
    r"\bS\.?C\.?R\.?\b": "Supreme Court Reports",
    
    # Common Legal Terms (versus / vs / vs. -> v.)
    r"\b(?:vs\.?|versus)\b": "v.",
}

# Compile regex patterns for efficient replacement
_COMPILED_ABBREVIATIONS = [
    (re.compile(pattern, re.IGNORECASE), replacement)
    for pattern, replacement in LEGAL_ABBREVIATIONS.items()
]


def clean_unicode_and_quotes(text: str) -> str:
    """
    Normalize unicode representation (NFKC) and replace typographic/curly
    quotes, em-dashes, and non-breaking spaces with standard ASCII equivalents.
    """
    if not text:
        return ""
    
    # NFKC normalizes compatibility characters
    text = unicodedata.normalize("NFKC", text)
    
    # Map curved quotes, apostrophes, dashes, bullets
    charmap = {
        "\u2018": "'",  # Left single quotation mark
        "\u2019": "'",  # Right single quotation mark
        "\u201a": "'",  # Single low-9 quotation mark
        "\u201c": '"',  # Left double quotation mark
        "\u201d": '"',  # Right double quotation mark
        "\u201e": '"',  # Double low-9 quotation mark
        "\u2013": "-",  # En dash
        "\u2014": "-",  # Em dash
        "\u2026": "...",  # Horizontal ellipsis
        "\u00a0": " ",  # Non-breaking space
        "\u200b": "",   # Zero-width space
        "\ufeff": "",   # Byte order mark
    }
    for orig, repl in charmap.items():
        text = text.replace(orig, repl)
        
    return text


def expand_legal_abbreviations(text: str) -> str:
    """
    Expands common legal abbreviations (e.g. 'Art. 21' -> 'Article 21',
    'SC' -> 'Supreme Court', 'CJI' -> 'Chief Justice of India').
    """
    if not text:
        return ""
        
    result = text
    for regex, replacement in _COMPILED_ABBREVIATIONS:
        result = regex.sub(replacement, result)
        
    return result


def normalize_legal_text(
    text: str,
    expand_abbreviations: bool = True,
    lowercase: bool = False
) -> str:
    """
    Comprehensive text normalization pipeline for legal queries and passages.
    
    Args:
        text: Raw input query or legal text.
        expand_abbreviations: Whether to expand standard legal acronyms.
        lowercase: Whether to fold text to lowercase.
        
    Returns:
        Cleaned, normalized string.
    """
    if not text:
        return ""
        
    # 1. Clean unicode, curly quotes, dashes
    cleaned = clean_unicode_and_quotes(text)
    
    # 2. Expand abbreviations if requested
    if expand_abbreviations:
        cleaned = expand_legal_abbreviations(cleaned)
        
    # 3. Collapse multiple whitespaces and tabs
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n\s*\n", "\n\n", cleaned)
    cleaned = cleaned.strip()
    
    # 4. Optional lowercasing
    if lowercase:
        cleaned = cleaned.lower()
        
    return cleaned


def tokenize_query(text: str) -> List[str]:
    """
    Tokenizes a legal query preserving compound structures such as:
    - 'Article 19(1)(a)'
    - 'Section 66A'
    - 'v.'
    - '103rd'
    """
    if not text:
        return []
        
    # Regex splits words while keeping alphanumeric with parenthetical clause numbers intact
    tokens = re.findall(r"\b\w+(?:\([^)]+\))+|\b\w+\b|[^\w\s]", text)
    return [t for t in tokens if t.strip()]


def extract_keywords(text: str, stop_words: Optional[set] = None) -> List[str]:
    """
    Extracts lowercase alphabetic keywords, removing common English stopwords
    while retaining legal terms.
    """
    if not text:
        return []
        
    default_stops = {
        "a", "an", "the", "and", "or", "but", "if", "then", "else", "when",
        "at", "by", "for", "with", "about", "against", "between", "into",
        "through", "during", "before", "after", "above", "below", "to", "from",
        "up", "down", "in", "out", "on", "off", "over", "under", "again",
        "further", "then", "once", "here", "there", "all", "any", "both",
        "each", "few", "more", "most", "other", "some", "such", "no", "nor",
        "not", "only", "own", "same", "so", "than", "too", "very", "s", "t",
        "can", "will", "just", "don", "should", "now", "is", "am", "are", "was",
        "were", "be", "been", "being", "have", "has", "had", "having", "do",
        "does", "did", "doing", "what", "which", "who", "whom", "this", "that",
        "these", "those", "how", "why", "where"
    }
    stops = stop_words if stop_words is not None else default_stops
    
    words = re.findall(r"\b[a-zA-Z0-9]+(?:\([a-zA-Z0-9]+\))*\b", text.lower())
    return [w for w in words if w not in stops and len(w) > 1]
