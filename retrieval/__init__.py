"""
Retrieval and Reranking Subsystem for Indian Constitution Legal AI Assistant.
Provides independent, modular, and evaluable retrieval components:
- BM25Retriever: Standalone BM25 lexical keyword search
- DenseRetriever: Standalone ChromaDB semantic vector search
- fuse: Reciprocal Rank Fusion (RRF) rank combiner
- apply_entity_boost: Legal entity-aware ranking boost
- CrossEncoderReranker: Neural cross-encoder reranker
- HybridRetriever: Configurable orchestrator with ablation switches
"""

from retrieval.bm25_retriever import BM25Retriever, simple_tokenize
from retrieval.dense_retriever import DenseRetriever
from retrieval.rrf import fuse
from retrieval.entity_boost import apply_entity_boost
from retrieval.reranker import CrossEncoderReranker
from retrieval.hybrid_retriever import HybridRetriever

__all__ = [
    "BM25Retriever",
    "DenseRetriever",
    "fuse",
    "apply_entity_boost",
    "CrossEncoderReranker",
    "HybridRetriever",
    "simple_tokenize",
]
