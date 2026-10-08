"""
NLP Query Understanding Package for Indian Constitution Legal AI Assistant.
Provides text preprocessing, language detection, hybrid Legal NER,
canonical entity linking, intent classification, and controlled query expansion.
"""

from nlp.preprocessing import (
    clean_unicode_and_quotes,
    expand_legal_abbreviations,
    normalize_legal_text,
    tokenize_query,
    extract_keywords,
)

from nlp.language_detection import (
    detect_language,
    detect_script,
)

from nlp.legal_ner import (
    LegalNER,
    get_legal_ner,
)

from nlp.entity_linking import (
    EntityLinker,
    get_entity_linker,
)

from nlp.intent_classifier import (
    RuleBasedIntentClassifier,
    MLIntentClassifier,
    HybridIntentClassifier,
    get_intent_classifier,
)

from nlp.query_expansion import (
    QueryExpander,
    get_query_expander,
)

__all__ = [
    "clean_unicode_and_quotes",
    "expand_legal_abbreviations",
    "normalize_legal_text",
    "tokenize_query",
    "extract_keywords",
    "detect_language",
    "detect_script",
    "LegalNER",
    "get_legal_ner",
    "EntityLinker",
    "get_entity_linker",
    "RuleBasedIntentClassifier",
    "MLIntentClassifier",
    "HybridIntentClassifier",
    "get_intent_classifier",
    "QueryExpander",
    "get_query_expander",
]
