"""
Language Detection Module for Legal Queries.
Detects whether an incoming user query is in English, an Indic language (e.g. Hindi in Devanagari script),
or Unknown/Unintelligible, to guide appropriate routing and user notices.
"""

import re
import unicodedata
from typing import Dict, Any


# Common English grammatical and functional words
ENGLISH_INDICATORS = {
    "the", "is", "what", "which", "how", "why", "who", "whom", "can", "does",
    "explain", "under", "article", "constitution", "court", "judgment", "rights",
    "fundamental", "liberty", "law", "supreme", "bench", "decide", "decision",
    "ruling", "between", "versus", "against", "state", "union", "india", "case",
    "privacy", "speech", "equality", "amendment", "act", "section", "citizen"
}

# Common transliterated Hindi/Hinglish indicators
HINGLISH_INDICATORS = {
    "kya", "kyon", "kaise", "samvidhan", "adhikar", "kanoon", "hoga", "hota",
    "hai", "hain", "ke", "ki", "ka", "mein", "par", "se", "aur", "nahi"
}


def detect_script(text: str) -> str:
    """
    Detects the dominant script in the query based on Unicode character blocks.
    """
    if not text:
        return "none"
        
    devanagari_chars = len(re.findall(r"[\u0900-\u097F]", text))
    bengali_chars = len(re.findall(r"[\u0980-\u09FF]", text))
    tamil_chars = len(re.findall(r"[\u0B80-\u0BFF]", text))
    telugu_chars = len(re.findall(r"[\u0C00-\u0C7F]", text))
    latin_chars = len(re.findall(r"[a-zA-Z]", text))
    
    total_letters = devanagari_chars + bengali_chars + tamil_chars + telugu_chars + latin_chars
    if total_letters == 0:
        return "symbols_or_numbers"
        
    if devanagari_chars / total_letters > 0.3:
        return "devanagari"
    if bengali_chars / total_letters > 0.3:
        return "bengali"
    if tamil_chars / total_letters > 0.3:
        return "tamil"
    if telugu_chars / total_letters > 0.3:
        return "telugu"
    if latin_chars / total_letters >= 0.7:
        return "latin"
        
    return "mixed"


def detect_language(text: str) -> Dict[str, Any]:
    """
    Identifies the language of the query and returns confidence metrics.
    
    Returns:
        {
            "language": "en" | "hi" | "hinglish" | "unknown",
            "is_english": bool,
            "confidence": float,
            "script": str,
            "reason": str
        }
    """
    if not text or not text.strip():
        return {
            "language": "unknown",
            "is_english": False,
            "confidence": 0.0,
            "script": "none",
            "reason": "Empty input"
        }
        
    cleaned = text.strip()
    script = detect_script(cleaned)
    
    # 1. Non-Latin scripts
    if script == "devanagari":
        return {
            "language": "hi",
            "is_english": False,
            "confidence": 0.95,
            "script": "devanagari",
            "reason": "Devanagari script detected"
        }
    elif script in ("bengali", "tamil", "telugu"):
        return {
            "language": script[:2],
            "is_english": False,
            "confidence": 0.95,
            "script": script,
            "reason": f"Indic {script} script detected"
        }
        
    # 2. Latin script analysis
    tokens = [t.lower() for t in re.findall(r"\b[a-zA-Z]+\b", cleaned)]
    if not tokens:
        return {
            "language": "unknown",
            "is_english": False,
            "confidence": 0.2,
            "script": script,
            "reason": "No alphabetic tokens found"
        }
        
    token_set = set(tokens)
    en_matches = len(token_set & ENGLISH_INDICATORS)
    hinglish_matches = len(token_set & HINGLISH_INDICATORS)
    
    if hinglish_matches >= 2 and hinglish_matches > en_matches:
        return {
            "language": "hinglish",
            "is_english": False,
            "confidence": 0.75,
            "script": "latin",
            "reason": "Transliterated Hindi / Hinglish keywords detected"
        }
        
    # High confidence English
    if en_matches >= 1 or len(tokens) >= 3:
        confidence = min(0.98, 0.6 + (en_matches * 0.1) + (len(tokens) * 0.02))
        return {
            "language": "en",
            "is_english": True,
            "confidence": round(confidence, 2),
            "script": "latin",
            "reason": "English grammatical patterns and Latin script"
        }
        
    # Default for single Latin word
    return {
        "language": "en",
        "is_english": True,
        "confidence": 0.55,
        "script": "latin",
        "reason": "Latin word assumed English"
    }
