"""
Ingestion Pipeline with Parent-Child Hierarchical RAG.
Parses Constitutional Articles and Supreme Court Judgments, creates parent-child chunks,
indexes child passages in ChromaDB (dense vector store), and builds a BM25 sparse index.
"""

import json
import os
import re
from typing import Dict, List, Tuple, Any
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
    BM25_B
)


def simple_tokenize(text: str) -> List[str]:
    """Basic lower-case tokenization for BM25 indexing."""
    text = text.lower()
    return re.findall(r'\b\w+\b', text)


class ParentChildIngestor:
    """
    Hierarchical Parent-Child Ingestion Engine.
    Parent chunks retain full semantic context (Articles/Judgments),
    while child chunks (~200-300 chars) are indexed for precise vector & BM25 retrieval.
    """

    def __init__(self):
        self.parent_store: Dict[str, Dict[str, Any]] = {}
        self.child_chunks: List[Dict[str, Any]] = []
        self.bm25_index: BM25Okapi = None

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

    def _split_text_into_children(self, text: str, chunk_size: int = CHILD_CHUNK_SIZE, overlap: int = CHILD_CHUNK_OVERLAP) -> List[str]:
        """Split text into child passages with specified chunk size and overlap."""
        if not text:
            return []
        
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + chunk_size, text_len)
            # Find natural word boundary if possible
            if end < text_len:
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap if (end - overlap) > start else end

        return chunks

    def process_parent_child_chunks(self) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
        """Build parent documents and derive child passages with parent context linkages."""
        const_data, judg_data = self.load_raw_datasets()
        
        parent_store = {}
        child_chunks = []
        child_counter = 0

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

            # Derive child chunks from text and explanation
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
                child_counter += 1

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

            # Derive child chunks from facts, ratio, verdict
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
                child_counter += 1

        self.parent_store = parent_store
        self.child_chunks = child_chunks
        return parent_store, child_chunks

    def save_parent_store(self) -> None:
        """Persist parent store to JSON."""
        with open(PARENT_STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(self.parent_store, f, indent=2)

    def load_parent_store(self) -> Dict[str, Dict[str, Any]]:
        """Load parent store from JSON."""
        if os.path.exists(PARENT_STORE_PATH):
            with open(PARENT_STORE_PATH, "r", encoding="utf-8") as f:
                self.parent_store = json.load(f)
        return self.parent_store

    def build_vector_store(self) -> Any:
        """Index child chunks into ChromaDB vector store."""
        client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
        
        # Use SentenceTransformers embedding function
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=DEFAULT_EMBEDDING_MODEL
        )

        collection = client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            embedding_function=embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

        # Upsert child chunks
        if self.child_chunks:
            ids = [c["child_id"] for c in self.child_chunks]
            documents = [c["text"] for c in self.child_chunks]
            metadatas = [
                {
                    "parent_id": c["parent_id"],
                    "doc_type": c["doc_type"],
                    "article_number": c.get("article_number", ""),
                    "case_name": c.get("case_name", ""),
                    "title": c.get("title", "")
                }
                for c in self.child_chunks
            ]

            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

        return collection

    def build_bm25_index(self) -> BM25Okapi:
        """Build BM25 index over child chunk texts."""
        tokenized_corpus = [simple_tokenize(c["text"]) for c in self.child_chunks]
        self.bm25_index = BM25Okapi(tokenized_corpus, k1=BM25_K1, b=BM25_B)
        return self.bm25_index

    def run_pipeline(self) -> Tuple[Dict[str, Any], Any, BM25Okapi, List[Dict[str, Any]]]:
        """Execute complete ingestion pipeline."""
        print("[INGESTION] Processing raw datasets into Parent & Child chunks...")
        self.process_parent_child_chunks()
        self.save_parent_store()

        print(f"[INGESTION] Generated {len(self.parent_store)} Parent documents and {len(self.child_chunks)} Child chunks.")

        print("[INGESTION] Indexing child chunks in ChromaDB...")
        collection = self.build_vector_store()

        print("[INGESTION] Building BM25 index...")
        bm25_index = self.build_bm25_index()

        print("[INGESTION] Ingestion pipeline completed successfully!")
        return self.parent_store, collection, bm25_index, self.child_chunks


if __name__ == "__main__":
    ingestor = ParentChildIngestor()
    ingestor.run_pipeline()
