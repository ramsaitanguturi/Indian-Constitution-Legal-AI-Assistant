"""
Index Builder and Maintenance CLI Module.
Builds, validates, or safely rebuilds the ChromaDB vector store and BM25 sparse index
from processed legal corpus documents (Constitutional Articles, Amendments, Judgments, Statutes).

Usage:
    python -m scripts.build_index [--rebuild] [--model MODEL_NAME] [--batch-size BATCH_SIZE] [--inspect]
"""

import os
import sys
import json
import argparse
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import (
    CHROMA_PERSIST_DIR,
    PARENT_STORE_PATH,
    DEFAULT_EMBEDDING_MODEL,
    BGE_M3_MODEL_NAME,
    BGE_M3_EMBEDDING_DIM,
    MINILM_EMBEDDING_DIM,
    EMBEDDING_BATCH_SIZE,
    get_chroma_collection_name,
)
from rag.ingestion import ProductionIngestor
import chromadb


def inspect_index(model_name: str = DEFAULT_EMBEDDING_MODEL) -> Dict[str, Any]:
    """Inspect the health, chunk count, and metadata of the active ChromaDB index."""
    print("=" * 65)
    print("CHROMA DB & BM25 INDEX HEALTH AUDIT")
    print("=" * 65)

    if not CHROMA_PERSIST_DIR.exists():
        print("[-] ChromaDB persistence directory does not exist.")
        return {"status": "NOT_FOUND"}

    client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
    collection_name = get_chroma_collection_name(model_name)
    
    existing_collections = [col.name for col in client.list_collections()]
    print(f"[*] Available Collections: {existing_collections}")
    print(f"[*] Target Collection: {collection_name} (Model: {model_name})")

    parent_count = 0
    if PARENT_STORE_PATH.exists():
        with open(PARENT_STORE_PATH, "r", encoding="utf-8") as f:
            parents = json.load(f)
            parent_count = len(parents)

    info = {
        "status": "HEALTHY",
        "chroma_dir": str(CHROMA_PERSIST_DIR),
        "target_collection": collection_name,
        "model_name": model_name,
        "collections": existing_collections,
        "parent_documents_cached": parent_count,
    }

    if collection_name in existing_collections:
        col = client.get_collection(collection_name)
        count = col.count()
        info["indexed_chunks"] = count
        print(f"[+] Active Indexed Chunks: {count}")
        print(f"[+] Parent Documents in Store: {parent_count}")
    else:
        info["status"] = "COLLECTION_NOT_BUILT"
        print(f"[!] Collection '{collection_name}' has not been built yet.")

    print("=" * 65)
    return info


def build_or_rebuild_index(
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    batch_size: int = EMBEDDING_BATCH_SIZE,
    rebuild: bool = False,
) -> Dict[str, Any]:
    """Execute index construction or safe rebuild."""
    print("=" * 65)
    action = "FORCE REBUILD" if rebuild else "INCREMENTAL BUILD / VERIFY"
    print(f"INDEX BUILD PIPELINE — [{action}]")
    print(f"Embedding Model: {model_name}")
    print(f"Batch Size:      {batch_size}")
    print("=" * 65)

    collection_name = get_chroma_collection_name(model_name)

    if rebuild:
        client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
        existing_cols = [c.name for c in client.list_collections()]
        if collection_name in existing_cols:
            print(f"[*] Deleting existing collection '{collection_name}' for clean rebuild...")
            client.delete_collection(collection_name)

    ingestor = ProductionIngestor(
        use_full_corpus=True,
        batch_size=batch_size,
        model_name=model_name,
    )

    print("\n[*] Processing raw legal documents into hierarchical Parent-Child passages...")
    parent_store, child_chunks = ingestor.process_parent_child_chunks()
    ingestor.save_parent_store()

    print(f"[+] Total Parent Documents: {len(parent_store)}")
    print(f"[+] Total Child Chunks:     {len(child_chunks)}")
    print(f"    - Constitutional:        {ingestor.stats.get('constitution_chunks', 0)}")
    print(f"    - Amendments:            {ingestor.stats.get('amendment_chunks', 0)}")
    print(f"    - Judgments:             {ingestor.stats.get('judgment_chunks', 0)}")
    print(f"    - Statutes:              {ingestor.stats.get('statute_chunks', 0)}")

    print(f"\n[*] Indexing child passages into ChromaDB (Collection: {collection_name})...")
    collection = ingestor.build_vector_store()

    print("\n[*] Building and calibrating BM25 sparse index...")
    bm25 = ingestor.build_bm25_index()

    result = {
        "status": "SUCCESS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_name": model_name,
        "collection_name": collection_name,
        "parent_count": len(parent_store),
        "chunk_count": len(child_chunks),
        "stats": ingestor.stats,
    }

    print("\n" + "=" * 65)
    print("INDEX BUILD COMPLETE")
    print(f"ChromaDB Collection: {collection_name} ({collection.count()} chunks)")
    print(f"BM25 Index Size:     {len(child_chunks)} documents")
    print(f"Parent Store:        {len(parent_store)} parent records")
    print("=" * 65)

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build or inspect Indian Constitution Legal Vector Store and BM25 Index.")
    parser.add_argument("--rebuild", action="store_true", help="Force clean rebuild of vector collection.")
    parser.add_argument("--inspect", action="store_true", help="Inspect active index health without building.")
    parser.add_argument("--model", type=str, default=DEFAULT_EMBEDDING_MODEL, help="Embedding model name.")
    parser.add_argument("--batch-size", type=int, default=EMBEDDING_BATCH_SIZE, help="Embedding batch size.")
    args = parser.parse_args()

    if args.inspect:
        inspect_index(model_name=args.model)
    else:
        build_or_rebuild_index(
            model_name=args.model,
            batch_size=args.batch_size,
            rebuild=args.rebuild,
        )

