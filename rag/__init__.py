"""
RAG (Retrieval-Augmented Generation) package for Indian Constitution Legal AI Assistant.
Contains structure-aware chunking, parent-child context management, ingestion,
and grounded generation.
"""

from .chunking import LegalStructureChunker, estimate_tokens
from .ingestion import ProductionIngestor, simple_tokenize
from .parent_child import ParentChildRecovery
from .generator import GroundedGenerator
from .citation_validator import CitationValidator
from .confidence import ConfidenceEstimator
from .abstention import AbstentionManager
from .pipeline import LegalRAGPipeline, PipelineResult, get_legal_rag_pipeline

__all__ = [
    "LegalStructureChunker",
    "estimate_tokens",
    "ProductionIngestor",
    "simple_tokenize",
    "ParentChildRecovery",
    "GroundedGenerator",
    "CitationValidator",
    "ConfidenceEstimator",
    "AbstentionManager",
    "LegalRAGPipeline",
    "PipelineResult",
    "get_legal_rag_pipeline",
]
