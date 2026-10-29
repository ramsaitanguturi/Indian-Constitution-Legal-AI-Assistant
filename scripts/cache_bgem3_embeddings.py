"""
Incremental BGE-M3 Neural Embedding Cache Builder.
Pre-computes and caches BAAI/bge-m3 1024-d embeddings into SQLite cache,
then cleanly builds the ChromaDB 'indian_legal_rag_bgem3' vector store.
Fully resumable and incremental.
"""

import os
import sys
import time
import json
import sqlite3
import hashlib
from pathlib import Path
from typing import List, Dict, Any

os.environ.setdefault("HF_HUB_OFFLINE", "1")

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import torch
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb

from config import (
    CHROMA_PERSIST_DIR,
    BGE_M3_MODEL_NAME,
    BGE_M3_EMBEDDING_DIM,
    PARENT_STORE_PATH,
)
from rag.ingestion import ProductionIngestor
from retrieval.embeddings import EMBEDDING_DB_PATH, get_embedding_function


def run_cache_and_build(batch_size: int = 64):
    print("=" * 70)
    print("BGE-M3 VECTOR EMBEDDING & INDEX COMPILATION PIPELINE")
    print(f"Model: {BGE_M3_MODEL_NAME} (1024-d)")
    print(f"Threads: {torch.get_num_threads()}")
    print("=" * 70)

    # 1. Process Chunks
    print("\n[*] Stage 1: Loading verified corpus child chunks...")
    ingestor = ProductionIngestor(use_full_corpus=True, model_name=BGE_M3_MODEL_NAME)
    parent_store, child_chunks = ingestor.process_parent_child_chunks()
    total_chunks = len(child_chunks)
    print(f"[+] Loaded {total_chunks} child chunks across {len(parent_store)} parent records.")

    # 2. Check Existing SQLite Cache
    print("\n[*] Stage 2: Auditing persistent SQLite embedding cache...")
    with sqlite3.connect(str(EMBEDDING_DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT content_hash FROM embedding_cache WHERE model_name = ?",
            [BGE_M3_MODEL_NAME]
        )
        cached_hashes = {row[0] for row in cursor.fetchall()}

    print(f"[+] Found {len(cached_hashes)} pre-computed BGE-M3 vectors in cache.")

    # Identify missing chunks
    missing_items = []
    chunk_hashes = []
    for c in child_chunks:
        text = c["text"]
        chash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        chunk_hashes.append(chash)
        if chash not in cached_hashes:
            missing_items.append((chash, text))

    print(f"[*] Missing from cache: {len(missing_items)} / {total_chunks} chunks.")

    # 3. Compute Embeddings if needed
    if missing_items:
        print(f"\n[*] Stage 3: Computing BGE-M3 embeddings for {len(missing_items)} passages...")
        print("[*] Loading SentenceTransformer model...")
        model = SentenceTransformer(BGE_M3_MODEL_NAME, device="cpu", local_files_only=True)
        if hasattr(model, "max_seq_length") and model.max_seq_length > 512:
            model.max_seq_length = 512

        start_time = time.time()
        num_missing = len(missing_items)

        for i in range(0, num_missing, batch_size):
            batch = missing_items[i:i + batch_size]
            b_hashes = [item[0] for item in batch]
            b_texts = [item[1] for item in batch]

            t_b0 = time.time()
            vectors = model.encode(
                b_texts,
                batch_size=len(batch),
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
            b_dur = time.time() - t_b0

            # Store in SQLite
            with sqlite3.connect(str(EMBEDDING_DB_PATH)) as conn:
                params = [
                    (chash, BGE_M3_MODEL_NAME, 1024, vec.astype(np.float32).tobytes())
                    for chash, vec in zip(b_hashes, vectors)
                ]
                conn.executemany(
                    "INSERT OR REPLACE INTO embedding_cache (content_hash, model_name, dim, vector) VALUES (?, ?, ?, ?)",
                    params,
                )
                conn.commit()

            done_count = min(i + batch_size, num_missing)
            elapsed = time.time() - start_time
            rate = done_count / elapsed if elapsed > 0 else 0
            eta = (num_missing - done_count) / rate if rate > 0 else 0
            print(
                f"  -> Encoded {done_count}/{num_missing} ({done_count/num_missing*100:.1f}%) "
                f"| Batch: {b_dur:.2f}s | Rate: {rate:.1f} chunks/s | ETA: {eta/60:.1f} min",
                flush=True
            )

        print(f"[+] Neural encoding finished in {(time.time() - start_time)/60:.2f} minutes.")

    # 4. Upsert into ChromaDB
    print("\n[*] Stage 4: Indexing into ChromaDB collection 'indian_legal_rag_bgem3'...")
    client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
    collection_name = "indian_legal_rag_bgem3"

    existing_cols = [c.name for c in client.list_collections()]
    if collection_name in existing_cols:
        print(f"[*] Deleting existing collection '{collection_name}' for clean rebuild...")
        client.delete_collection(collection_name)

    embedding_fn = get_embedding_function(model_name=BGE_M3_MODEL_NAME, batch_size=batch_size)
    collection = client.create_collection(
        name=collection_name,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )

    # Upsert in fast cached batches of 128
    upsert_batch_size = 128
    for i in range(0, total_chunks, upsert_batch_size):
        batch = child_chunks[i:i + upsert_batch_size]
        ids = [c["child_id"] for c in batch]
        documents = [c["text"] for c in batch]
        metadatas = []
        for c in batch:
            metadatas.append({
                "parent_id": str(c.get("parent_id", "")),
                "doc_type": str(c.get("doc_type", "")),
                "article_number": str(c.get("article_number", "")),
                "case_name": str(c.get("case_name", "")),
                "title": str(c.get("title", "")),
                "citation": str(c.get("citation", "")),
                "year": int(c.get("year", 0)),
                "section": str(c.get("section", "")),
                "source": str(c.get("source", ""))
            })

        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        print(f"  -> ChromaDB Upserted {min(i + upsert_batch_size, total_chunks)} / {total_chunks} chunks", flush=True)

    print("\n" + "=" * 70)
    print("BGE-M3 INDEX BUILD COMPLETE")
    print(f"Collection: {collection_name}")
    print(f"Chunks:     {collection.count()}")
    print("=" * 70)


if __name__ == "__main__":
    run_cache_and_build(batch_size=64)

