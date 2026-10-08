"""
Production Corpus Ingestion Pipeline with Structure-Aware Parent-Child RAG.
Parses authoritative Constitutional Articles, Amendments, and Landmark Judgments,
applies structure-aware legal chunking, logs provenance, builds ChromaDB vector store,
and creates BM25 sparse index.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi

from config import (
    CONSTITUTION_ARTICLES_PATH,
    CONSTITUTION_AMENDMENTS_PATH,
    JUDGMENTS_LANDMARKS_PATH,
    CONSTITUTION_DATA_PATH,
    JUDGMENTS_DATA_PATH,
    CHROMA_PERSIST_DIR,
    PARENT_STORE_PATH,
    CHROMA_COLLECTION_NAME,
    DEFAULT_EMBEDDING_MODEL,
    BM25_K1,
    BM25_B,
    DATASET_VERSION
)
from rag.chunking import LegalStructureChunker, estimate_tokens


def simple_tokenize(text: str) -> List[str]:
    """Basic lower-case tokenization for BM25 indexing."""
    text = text.lower()
    return re.findall(r'\b\w+\b', text)


class ProductionIngestor:
    """
    Production Hierarchical Ingestor for Expanded Legal Corpus.
    Supports both full authoritative corpus and legacy sample datasets.
    Uses structure-aware chunking preserving clauses, sections, and provenance.
    """

    def __init__(self, use_full_corpus: bool = True, batch_size: int = 64):
        self.use_full_corpus = use_full_corpus
        self.batch_size = batch_size
        self.chunker = LegalStructureChunker()
        self.parent_store: Dict[str, Dict[str, Any]] = {}
        self.child_chunks: List[Dict[str, Any]] = []
        self.bm25_index: Optional[BM25Okapi] = None
        self.stats: Dict[str, Any] = {}

    def load_raw_datasets(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Load datasets from disk.
        Returns: (articles, amendments, judgments)
        """
        articles: List[Dict[str, Any]] = []
        amendments: List[Dict[str, Any]] = []
        judgments: List[Dict[str, Any]] = []

        if self.use_full_corpus and os.path.exists(CONSTITUTION_ARTICLES_PATH):
            with open(CONSTITUTION_ARTICLES_PATH, "r", encoding="utf-8") as f:
                articles = json.load(f)
            if os.path.exists(CONSTITUTION_AMENDMENTS_PATH):
                with open(CONSTITUTION_AMENDMENTS_PATH, "r", encoding="utf-8") as f:
                    amendments = json.load(f)
            if os.path.exists(JUDGMENTS_LANDMARKS_PATH):
                with open(JUDGMENTS_LANDMARKS_PATH, "r", encoding="utf-8") as f:
                    judgments = json.load(f)
        else:
            # Fallback to legacy samples if full corpus is not available or disabled
            if os.path.exists(CONSTITUTION_DATA_PATH):
                with open(CONSTITUTION_DATA_PATH, "r", encoding="utf-8") as f:
                    articles = json.load(f)
            if os.path.exists(JUDGMENTS_DATA_PATH):
                with open(JUDGMENTS_DATA_PATH, "r", encoding="utf-8") as f:
                    judgments = json.load(f)

        return articles, amendments, judgments

    def process_parent_child_chunks(self) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Process raw documents into parent documents and structure-aware child chunks.
        """
        articles, amendments, judgments = self.load_raw_datasets()
        parent_store: Dict[str, Dict[str, Any]] = {}
        child_chunks: List[Dict[str, Any]] = []

        # 1. Process Constitutional Articles
        for item in articles:
            parent_id = f"parent_{item.get('id', item.get('document_id', 'art'))}"
            full_parent_text = (
                f"ARTICLE/TITLE: {item.get('article_number', '')} - {item.get('title', '')}\n"
                f"PART: {item.get('part', '')} | CATEGORY: {item.get('category', '')}\n"
                f"CONSTITUTIONAL TEXT: {item.get('text', '')}\n"
                f"LEGAL EXPLANATION: {item.get('explanation', '')}\n"
                f"HISTORICAL CONTEXT: {item.get('historical_context', '')}"
            )

            parent_store[parent_id] = {
                "parent_id": parent_id,
                "document_id": item.get("document_id", item.get("id")),
                "doc_type": "constitution",
                "document_type": "constitution_article",
                "article_number": item.get("article_number", ""),
                "title": item.get("title", ""),
                "part": item.get("part", ""),
                "category": item.get("category", ""),
                "full_text": full_parent_text,
                "raw_text": item.get("text", ""),
                "explanation": item.get("explanation", ""),
                "historical_context": item.get("historical_context", ""),
                "provenance": item.get("provenance", {})
            }

            art_children = self.chunker.chunk_constitutional_article(item)
            child_chunks.extend(art_children)

        # 2. Process Constitutional Amendments (if present in full corpus)
        for item in amendments:
            parent_id = f"parent_{item.get('id', item.get('document_id', 'amend'))}"
            full_parent_text = (
                f"AMENDMENT: {item.get('amendment_number', '')} ({item.get('year', '')})\n"
                f"TITLE: {item.get('title', '')}\n"
                f"PROVISIONS MODIFIED: {', '.join(item.get('provisions_modified', []))}\n"
                f"SUMMARY: {item.get('summary', '')}\n"
                f"STATEMENT OF OBJECTS AND REASONS: {item.get('statement_of_objects_and_reasons', '')}"
            )

            parent_store[parent_id] = {
                "parent_id": parent_id,
                "document_id": item.get("document_id", item.get("id")),
                "doc_type": "amendment",
                "document_type": "constitution_amendment",
                "amendment_number": item.get("amendment_number", ""),
                "title": item.get("title", ""),
                "year": item.get("year", 0),
                "provisions_modified": item.get("provisions_modified", []),
                "full_text": full_parent_text,
                "summary": item.get("summary", ""),
                "statement_of_objects_and_reasons": item.get("statement_of_objects_and_reasons", ""),
                "provenance": item.get("provenance", {})
            }

            amend_children = self.chunker.chunk_amendment(item)
            child_chunks.extend(amend_children)

        # 3. Process Supreme Court Judgments
        for item in judgments:
            parent_id = f"parent_{item.get('id', item.get('document_id', 'judg'))}"
            arts_ref = item.get("articles_referred", [])
            arts_str = ", ".join(arts_ref) if isinstance(arts_ref, list) else str(arts_ref)
            takeaways = item.get("key_takeaways", [])
            takeaways_str = " ".join(takeaways) if isinstance(takeaways, list) else str(takeaways)

            full_parent_text = (
                f"CASE NAME: {item.get('case_name', '')} ({item.get('year', '')})\n"
                f"CITATION: {item.get('citation', '')} | BENCH: {item.get('bench', '')}\n"
                f"ARTICLES REFERRED: {arts_str}\n"
                f"FACTS: {item.get('facts', '')}\n"
                f"RATIO DECIDENDI: {item.get('ratio_decidendi', '')}\n"
                f"VERDICT: {item.get('verdict', '')}\n"
                f"KEY TAKEAWAYS: {takeaways_str}"
            )

            parent_store[parent_id] = {
                "parent_id": parent_id,
                "document_id": item.get("document_id", item.get("id")),
                "doc_type": "judgment",
                "document_type": "judgment",
                "case_name": item.get("case_name", ""),
                "citation": item.get("citation", ""),
                "year": item.get("year", 0),
                "bench": item.get("bench", ""),
                "articles_referred": arts_ref,
                "acts_referred": item.get("acts_referred", []),
                "full_text": full_parent_text,
                "facts": item.get("facts", ""),
                "ratio_decidendi": item.get("ratio_decidendi", ""),
                "verdict": item.get("verdict", ""),
                "key_takeaways": takeaways,
                "provenance": item.get("provenance", {})
            }

            judg_children = self.chunker.chunk_judgment(item)
            child_chunks.extend(judg_children)

        self.parent_store = parent_store
        self.child_chunks = child_chunks

        # Calculate statistics
        char_lens = [c["char_count"] for c in child_chunks if "char_count" in c]
        token_lens = [c["estimated_tokens"] for c in child_chunks if "estimated_tokens" in c]

        self.stats = {
            "total_parents": len(parent_store),
            "total_children": len(child_chunks),
            "avg_char_length": round(sum(char_lens) / len(char_lens), 1) if char_lens else 0,
            "min_char_length": min(char_lens) if char_lens else 0,
            "max_char_length": max(char_lens) if char_lens else 0,
            "avg_token_count": round(sum(token_lens) / len(token_lens), 1) if token_lens else 0,
            "min_token_count": min(token_lens) if token_lens else 0,
            "max_token_count": max(token_lens) if token_lens else 0,
            "constitution_chunks": sum(1 for c in child_chunks if c["doc_type"] == "constitution"),
            "amendment_chunks": sum(1 for c in child_chunks if c["doc_type"] == "amendment"),
            "judgment_chunks": sum(1 for c in child_chunks if c["doc_type"] == "judgment")
        }

        return parent_store, child_chunks

    def save_parent_store(self) -> None:
        """Persist parent store to JSON."""
        with open(PARENT_STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(self.parent_store, f, indent=2, ensure_ascii=False)

    def load_parent_store(self) -> Dict[str, Dict[str, Any]]:
        """Load parent store from JSON."""
        if os.path.exists(PARENT_STORE_PATH):
            with open(PARENT_STORE_PATH, "r", encoding="utf-8") as f:
                self.parent_store = json.load(f)
        return self.parent_store

    def build_vector_store(self) -> Any:
        """
        Index child chunks into ChromaDB vector store using batched upserts.
        Ensures all metadata fields are non-null and valid for ChromaDB.
        """
        client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))

        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=DEFAULT_EMBEDDING_MODEL
        )

        collection = client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            embedding_function=embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

        if self.child_chunks:
            total = len(self.child_chunks)
            print(f"[INGESTION] Upserting {total} child passages into ChromaDB in batches of {self.batch_size}...")

            for i in range(0, total, self.batch_size):
                batch = self.child_chunks[i:i + self.batch_size]
                ids = [c["child_id"] for c in batch]
                documents = [c["text"] for c in batch]

                metadatas = []
                for c in batch:
                    # ChromaDB metadata must be primitive types (str, int, float, bool)
                    meta = {
                        "parent_id": str(c.get("parent_id", "")),
                        "doc_type": str(c.get("doc_type", "")),
                        "article_number": str(c.get("article_number", "")),
                        "case_name": str(c.get("case_name", "")),
                        "title": str(c.get("title", "")),
                        "citation": str(c.get("citation", "")),
                        "year": int(c.get("year", 0)),
                        "section": str(c.get("section", "")),
                        "source": str(c.get("source", ""))
                    }
                    metadatas.append(meta)

                collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                print(f"  -> Upserted {min(i + self.batch_size, total)} / {total} chunks")

        return collection

    def build_bm25_index(self) -> BM25Okapi:
        """Build BM25 index over child chunk texts."""
        tokenized_corpus = [simple_tokenize(c["text"]) for c in self.child_chunks]
        self.bm25_index = BM25Okapi(tokenized_corpus, k1=BM25_K1, b=BM25_B)
        return self.bm25_index

    def run_pipeline(self) -> Tuple[Dict[str, Any], Any, BM25Okapi, List[Dict[str, Any]]]:
        """Execute complete ingestion pipeline."""
        corpus_mode = "EXPANDED FULL CORPUS" if self.use_full_corpus else "SAMPLE DATASET"
        print("=" * 60)
        print(f"[INGESTION] Starting Ingestion Pipeline [{corpus_mode}]...")
        print("=" * 60)

        self.process_parent_child_chunks()
        self.save_parent_store()

        print(f"[INGESTION] Built {self.stats['total_parents']} Parents, {self.stats['total_children']} Children.")
        print(f"  - Constitutional chunks: {self.stats['constitution_chunks']}")
        print(f"  - Amendment chunks:      {self.stats['amendment_chunks']}")
        print(f"  - Judgment chunks:       {self.stats['judgment_chunks']}")
        print(f"  - Avg chunk size:        {self.stats['avg_char_length']} chars (~{self.stats['avg_token_count']} tokens)")

        print("[INGESTION] Indexing child chunks in ChromaDB...")
        collection = self.build_vector_store()

        print("[INGESTION] Building BM25 index...")
        bm25_index = self.build_bm25_index()

        print("=" * 60)
        print("[INGESTION] Pipeline finished successfully!")
        print("=" * 60)
        return self.parent_store, collection, bm25_index, self.child_chunks
