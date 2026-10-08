"""
RAG (Retrieval-Augmented Generation) package for Indian Constitution Legal AI Assistant.
Contains structure-aware chunking, parent-child context management, ingestion,
and grounded generation.
"""

from .chunking import LegalStructureChunker, estimate_tokens
from .ingestion import ProductionIngestor, simple_tokenize

__all__ = [
    "LegalStructureChunker",
    "estimate_tokens",
    "ProductionIngestor",
    "simple_tokenize",
]
