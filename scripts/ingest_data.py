"""
Ingestion Pipeline CLI Runner.
Executes structure-aware chunking, parent document storage, ChromaDB vector indexing,
and BM25 sparse indexing over the Indian Constitutional legal corpus.

Usage:
    python scripts/ingest_data.py --corpus full
    python scripts/ingest_data.py --corpus sample
"""

import argparse
import sys
import time
from pathlib import Path

# Adjust path to import from workspace root
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from rag.ingestion import ProductionIngestor


def main():
    parser = argparse.ArgumentParser(description="Ingest legal corpus into Parent Store, ChromaDB, and BM25 index.")
    parser.add_argument(
        "--corpus",
        choices=["full", "sample"],
        default="full",
        help="Select corpus mode: 'full' for expanded authoritative corpus, 'sample' for legacy 14-doc sample."
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Batch size for ChromaDB vector embeddings upsert (default: 64)."
    )

    args = parser.parse_args()
    use_full = (args.corpus == "full")

    print(f"[*] Starting ingestion runner with corpus='{args.corpus}', batch_size={args.batch_size}...")
    start_time = time.time()

    ingestor = ProductionIngestor(use_full_corpus=use_full, batch_size=args.batch_size)
    parent_store, collection, bm25_index, child_chunks = ingestor.run_pipeline()

    elapsed = round(time.time() - start_time, 2)
    print(f"[+] Ingestion completed in {elapsed} seconds.")
    print(f"[+] Indexed {len(child_chunks)} child passages across {len(parent_store)} parent documents.")
    print(f"[+] ChromaDB collection '{collection.name}' now contains {collection.count()} vectors.")


if __name__ == "__main__":
    main()
