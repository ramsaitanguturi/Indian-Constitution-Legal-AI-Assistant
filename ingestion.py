"""
Ingestion Pipeline with Parent-Child Hierarchical RAG.
Maintains backward-compatible facade routing through the modular rag/ package.
Parses Constitutional Articles and Supreme Court Judgments, creates parent-child chunks,
indexes child passages in ChromaDB (dense vector store), and builds a BM25 sparse index.
"""

import json
import os
import re
from typing import Dict, List, Tuple, Any, Optional
import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi

from config import (
    CONSTITUTION_DATA_PATH,
    JUDGMENTS_DATA_PATH,
    CHROMA_PERSIST_DIR,
    PARENT_STORE_PATH,
    CHROMA_COLLECTION_NAME,
    DEFAULT_EMBEDDING_MODEL,
    CHILD_CHUNK_SIZE,
    CHILD_CHUNK_OVERLAP,
    BM25_K1,
    BM25_B,
    get_chroma_collection_name,
    get_embedding_dimension,
    validate_collection_dimension,
)
from rag.chunking import LegalStructureChunker, estimate_tokens
from rag.ingestion import ProductionIngestor, simple_tokenize


class ParentChildIngestor:
    """
    Hierarchical Parent-Child Ingestion Engine.
    Parent chunks retain full semantic context (Articles/Judgments),
    while child chunks are indexed for precise vector & BM25 retrieval.
    Provides backward compatibility for baseline evaluation while enabling
    routing to ProductionIngestor for the expanded corpus.
    """

    def __init__(
        self,
        use_full_corpus: bool = False,
        batch_size: int = 64,
        model_name: Optional[str] = None,
    ):
        self.use_full_corpus = use_full_corpus
        self.batch_size = batch_size
        self.model_name = model_name or DEFAULT_EMBEDDING_MODEL
        self.chunker = LegalStructureChunker()
        self.parent_store: Dict[str, Dict[str, Any]] = {}
        self.child_chunks: List[Dict[str, Any]] = []
        self.bm25_index: Optional[BM25Okapi] = None
        self.collection: Optional[Any] = None
        self._production_ingestor = ProductionIngestor(
            use_full_corpus=use_full_corpus,
            batch_size=batch_size,
            model_name=self.model_name,
        )

    def load_raw_datasets(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Load JSON datasets for Constitution Articles and Supreme Court Judgments."""
        constitution_data = []
        judgments_data = []

        if os.path.exists(CONSTITUTION_DATA_PATH):
            with open(CONSTITUTION_DATA_PATH, "r", encoding="utf-8") as f:
                constitution_data = json.load(f)

        if os.path.exists(JUDGMENTS_DATA_PATH):
            with open(JUDGMENTS_DATA_PATH, "r", encoding="utf-8") as f:
                judgments_data = json.load(f)

        return constitution_data, judgments_data

    def _split_text_into_children(
        self,
        text: str,
        chunk_size: int = CHILD_CHUNK_SIZE,
        overlap: int = CHILD_CHUNK_OVERLAP
    ) -> List[str]:
        """Split text into child passages using legacy sliding window algorithm."""
        return self.chunker.chunk_legacy_sliding_window(text, chunk_size=chunk_size, overlap=overlap)

    def process_parent_child_chunks(self) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
        """Build parent documents and derive child passages."""
        if self.use_full_corpus:
            self.parent_store, self.child_chunks = self._production_ingestor.process_parent_child_chunks()
            return self.parent_store, self.child_chunks

        # Legacy baseline dataset processing (for backwards-compatible unit tests)
        const_data, judg_data = self.load_raw_datasets()
        parent_store = {}
        child_chunks = []

        # 1. Process Constitution Articles
        for item in const_data:
            parent_id = f"parent_{item['id']}"
            full_parent_text = (
                f"ARTICLE/TITLE: {item['article_number']} - {item['title']}\n"
                f"PART: {item['part']} | CATEGORY: {item['category']}\n"
                f"CONSTITUTIONAL TEXT: {item['text']}\n"
                f"LEGAL EXPLANATION: {item.get('explanation', '')}\n"
                f"HISTORICAL CONTEXT: {item.get('historical_context', '')}"
            )

            parent_store[parent_id] = {
                "parent_id": parent_id,
                "doc_type": "constitution",
                "article_number": item["article_number"],
                "title": item["title"],
                "part": item["part"],
                "category": item["category"],
                "full_text": full_parent_text,
                "raw_text": item["text"],
                "explanation": item.get("explanation", ""),
                "historical_context": item.get("historical_context", "")
            }

            combined_text_for_children = f"{item['title']}. {item['text']} {item.get('explanation', '')}"
            passages = self._split_text_into_children(combined_text_for_children)

            for p_idx, passage in enumerate(passages):
                child_id = f"child_const_{item['id']}_{p_idx}"
                child_chunks.append({
                    "child_id": child_id,
                    "parent_id": parent_id,
                    "text": passage,
                    "doc_type": "constitution",
                    "article_number": item["article_number"],
                    "title": item["title"],
                    "category": item["category"]
                })

        # 2. Process Supreme Court Judgments
        for item in judg_data:
            parent_id = f"parent_{item['id']}"
            takeaways_str = " ".join(item.get("key_takeaways", []))
            full_parent_text = (
                f"CASE NAME: {item['case_name']} ({item['year']})\n"
                f"CITATION: {item['citation']} | BENCH: {item['bench']}\n"
                f"ARTICLES REFERRED: {', '.join(item.get('articles_referred', []))}\n"
                f"FACTS: {item['facts']}\n"
                f"RATIO DECIDENDI: {item['ratio_decidendi']}\n"
                f"VERDICT: {item['verdict']}\n"
                f"KEY TAKEAWAYS: {takeaways_str}"
            )

            parent_store[parent_id] = {
                "parent_id": parent_id,
                "doc_type": "judgment",
                "case_name": item["case_name"],
                "citation": item["citation"],
                "year": item["year"],
                "bench": item["bench"],
                "articles_referred": item.get("articles_referred", []),
                "full_text": full_parent_text,
                "facts": item["facts"],
                "ratio_decidendi": item["ratio_decidendi"],
                "verdict": item["verdict"],
                "key_takeaways": item.get("key_takeaways", [])
            }

            judg_combined = f"{item['case_name']}. FACTS: {item['facts']} RATIO: {item['ratio_decidendi']} VERDICT: {item['verdict']}"
            passages = self._split_text_into_children(judg_combined)

            for p_idx, passage in enumerate(passages):
                child_id = f"child_judg_{item['id']}_{p_idx}"
                child_chunks.append({
                    "child_id": child_id,
                    "parent_id": parent_id,
                    "text": passage,
                    "doc_type": "judgment",
                    "case_name": item["case_name"],
                    "year": item["year"],
                    "articles_referred": ", ".join(item.get("articles_referred", []))
                })

        self.parent_store = parent_store
        self.child_chunks = child_chunks
        return parent_store, child_chunks

    def save_parent_store(self) -> None:
        """Persist parent store to JSON, preserving full corpus records if existing store is larger."""
        if os.path.exists(PARENT_STORE_PATH):
            try:
                with open(PARENT_STORE_PATH, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                if len(existing) > len(self.parent_store):
                    existing.update(self.parent_store)
                    self.parent_store = existing
            except Exception:
                pass

        with open(PARENT_STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(self.parent_store, f, indent=2, ensure_ascii=False)

    def load_parent_store(self) -> Dict[str, Dict[str, Any]]:
        """Load parent store from JSON."""
        if os.path.exists(PARENT_STORE_PATH):
            with open(PARENT_STORE_PATH, "r", encoding="utf-8") as f:
                self.parent_store = json.load(f)
        return self.parent_store

    def build_vector_store(self, force_rebuild: bool = False) -> Any:
        """Index child chunks into ChromaDB vector store."""
        if self.use_full_corpus:
            self.collection = self._production_ingestor.build_vector_store(force_rebuild=force_rebuild)
            return self.collection

        client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
        col_name = get_chroma_collection_name(self.model_name)
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.model_name
        )

        collection = client.get_or_create_collection(
            name=col_name,
            embedding_function=embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

        # Validate dimension before upserting
        expected_dim = get_embedding_dimension(self.model_name)
        validate_collection_dimension(collection, expected_dim, self.model_name)

        # Prevent unnecessarily rebuilding or re-ingesting an already populated collection
        if not force_rebuild and collection.count() > 0:
            print(f"[INGESTION] Collection '{col_name}' already populated with {collection.count()} chunks. Skipping re-indexing.")
            self.collection = collection
            return collection

        if self.child_chunks:
            ids = [c["child_id"] for c in self.child_chunks]
            documents = [c["text"] for c in self.child_chunks]
            metadatas = [
                {
                    "parent_id": str(c.get("parent_id", "")),
                    "doc_type": str(c.get("doc_type", "")),
                    "article_number": str(c.get("article_number", "")),
                    "case_name": str(c.get("case_name", "")),
                    "title": str(c.get("title", ""))
                }
                for c in self.child_chunks
            ]

            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

        self.collection = collection
        return collection

    def build_bm25_index(self) -> BM25Okapi:
        """Build BM25 index over child chunk texts."""
        tokenized_corpus = [simple_tokenize(c["text"]) for c in self.child_chunks]
        self.bm25_index = BM25Okapi(tokenized_corpus, k1=BM25_K1, b=BM25_B)
        return self.bm25_index

    def run_pipeline(self, force_rebuild: bool = False) -> Tuple[Dict[str, Any], Any, BM25Okapi, List[Dict[str, Any]]]:
        """Execute complete ingestion pipeline."""
        print("[INGESTION] Processing raw datasets into Parent & Child chunks...")
        self.process_parent_child_chunks()
        self.save_parent_store()

        print(f"[INGESTION] Generated {len(self.parent_store)} Parent documents and {len(self.child_chunks)} Child chunks.")

        print("[INGESTION] Indexing child chunks in ChromaDB...")
        collection = self.build_vector_store(force_rebuild=force_rebuild)

        print("[INGESTION] Building BM25 index...")
        bm25_index = self.build_bm25_index()

        print("[INGESTION] Ingestion pipeline completed successfully!")
        return self.parent_store, collection, bm25_index, self.child_chunks


if __name__ == "__main__":
    ingestor = ParentChildIngestor()
    ingestor.run_pipeline()
