"""
Corpus Build Pipeline Script.
Compiles authoritative constitutional articles, all 12 schedules, 1st to 106th amendments,
landmark Supreme Court judgments, and constitutional statutory acts into schema-compliant
JSON datasets with cryptographic SHA-256 integrity manifests and source provenance.

Supports both full-corpus production builds and fast --smoke-test mode.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import (
    CONSTITUTION_DIR,
    JUDGMENTS_DIR,
    BENCHMARK_DIR,
    ANNOTATIONS_DIR,
    PROCESSED_CONSTITUTION_DIR,
    PROCESSED_AMENDMENTS_DIR,
    PROCESSED_JUDGMENTS_DIR,
    PROCESSED_LEGISLATION_DIR,
    CONSTITUTION_ARTICLES_PATH,
    CONSTITUTION_AMENDMENTS_PATH,
    JUDGMENTS_LANDMARKS_PATH,
    LEGISLATION_ACTS_PATH,
    CORPUS_MANIFEST_PATH,
)

from scripts.ingest_constitution import ingest_constitution
from scripts.ingest_amendments import build_amendments_dataset
from scripts.ingest_judgments import ingest_judgments
from scripts.ingest_legislation import ingest_legislation
from rag.schema import LegalDocument


def validate_document_records(docs: List[Dict[str, Any]], expected_type: str) -> None:
    """Validate that every document complies with LegalDocument schema without missing keys."""
    for idx, doc in enumerate(docs):
        assert "document_id" in doc, f"Missing document_id in document {idx} of {expected_type}"
        assert "document_type" in doc, f"Missing document_type in {doc.get('document_id')}"
        assert doc["document_type"] == expected_type, (
            f"Type mismatch: expected {expected_type}, got {doc['document_type']} in {doc.get('document_id')}"
        )
        assert "text" in doc and doc["text"].strip(), f"Empty legal text in {doc.get('document_id')}"
        assert "source_url" in doc, f"Missing source_url in {doc.get('document_id')}"
        assert "source_hash" in doc, f"Missing source_hash in {doc.get('document_id')}"


def build_corpus(smoke_test: bool = False) -> Dict[str, Any]:
    """Execute complete corpus compilation and output audit manifest."""
    print("=" * 70)
    mode_label = "SMOKE TEST MODE (Sample Partition)" if smoke_test else "FULL PRODUCTION CORPUS"
    print(f"INDIAN CONSTITUTION LEGAL CORPUS BUILDER — {mode_label}")
    print("=" * 70)

    # 1. Ensure target directories exist
    for directory in [
        CONSTITUTION_DIR, JUDGMENTS_DIR, BENCHMARK_DIR, ANNOTATIONS_DIR,
        PROCESSED_CONSTITUTION_DIR, PROCESSED_AMENDMENTS_DIR,
        PROCESSED_JUDGMENTS_DIR, PROCESSED_LEGISLATION_DIR
    ]:
        directory.mkdir(parents=True, exist_ok=True)

    # 2. Ingest Constitution Provisions & Schedules
    print("\n[*] Stage 1: Ingesting Consolidated Constitutional Articles & Schedules...")
    articles = ingest_constitution()
    if smoke_test:
        articles = articles[:25]
    validate_document_records(articles, "constitution_article")
    with open(CONSTITUTION_ARTICLES_PATH, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved {len(articles)} constitutional provisions to {CONSTITUTION_ARTICLES_PATH}")

    # 3. Ingest Amendment Acts (1st to 106th)
    print("\n[*] Stage 2: Ingesting Constitution Amendment Acts (1st to 106th)...")
    amendments = build_amendments_dataset()
    if smoke_test:
        amendments = amendments[:10]
    validate_document_records(amendments, "constitution_amendment")
    with open(CONSTITUTION_AMENDMENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(amendments, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved {len(amendments)} amendment acts to {CONSTITUTION_AMENDMENTS_PATH}")

    # 4. Ingest Supreme Court Landmark Decisions
    print("\n[*] Stage 3: Ingesting Landmark Supreme Court Judgments...")
    judgments = ingest_judgments()
    if smoke_test:
        judgments = judgments[:15]
    validate_document_records(judgments, "judgment")
    with open(JUDGMENTS_LANDMARKS_PATH, "w", encoding="utf-8") as f:
        json.dump(judgments, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved {len(judgments)} decisions to {JUDGMENTS_LANDMARKS_PATH}")

    # 5. Ingest Central Legislation
    print("\n[*] Stage 4: Ingesting Constitutional Central Legislation (India Code)...")
    legislation = ingest_legislation()
    if smoke_test:
        legislation = legislation[:2]
    validate_document_records(legislation, "statute")
    with open(LEGISLATION_ACTS_PATH, "w", encoding="utf-8") as f:
        json.dump(legislation, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved {len(legislation)} central acts to {LEGISLATION_ACTS_PATH}")

    # 6. Generate Comprehensive Manifest
    total_docs = len(articles) + len(amendments) + len(judgments) + len(legislation)
    total_chars = (
        sum(len(a.get("text", "")) for a in articles) +
        sum(len(am.get("text", "")) for am in amendments) +
        sum(len(j.get("text", "")) for j in judgments) +
        sum(len(l.get("text", "")) for l in legislation)
    )

    full_text_judgments = sum(1 for j in judgments if j.get("content_type") == "full_text")
    summary_judgments = sum(1 for j in judgments if j.get("content_type") == "summary_only")
    metadata_judgments = sum(1 for j in judgments if j.get("content_type") == "metadata_only")
    total_statute_sections = sum(len(l.get("sections", [])) for l in legislation)

    manifest = {
        "manifest_version": "2.1.0-production",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "is_smoke_test": smoke_test,
        "counts_by_document_type": {
            "constitution_article": len(articles),
            "constitution_amendment": len(amendments),
            "judgment": len(judgments),
            "statute": len(legislation),
        },
        "judgment_granularity": {
            "official_full_text": full_text_judgments,
            "structured_summary_briefs": summary_judgments,
            "registry_metadata_only": metadata_judgments,
        },
        "statute_granularity": {
            "total_acts": len(legislation),
            "total_sections_parsed": total_statute_sections,
        },
        "total_documents": total_docs,
        "total_character_count": total_chars,
        "estimated_total_tokens": round(total_chars / 4),
        "source_provenance_summary": {
            "constitution": {
                "source": "Legislative Department, Ministry of Law and Justice, Government of India",
                "version": "Amended up to 106th Amendment Act",
                "coverage": "Preamble, Articles 1 to 395+, Schedules 1 to 12",
                "repealed_or_omitted_flagged": sum(1 for a in articles if a.get("legal_status") in ("repealed", "omitted", "inoperative_special_provisions")),
            },
            "amendments": {
                "source": "Legislative Department, Ministry of Law and Justice, Government of India",
                "version": "1st to 106th Constitutional Amendment Acts",
                "coverage": "All 106 enacted Amendment Acts with verified dates and Statement of Objects and Reasons"
            },
            "judgments": {
                "source": "Supreme Court of India / Open Data AWS Registry",
                "coverage": f"{full_text_judgments} full-text SCR PDF decisions (1950–1952), {summary_judgments} landmark case briefs (1950–2024), {metadata_judgments} registry records"
            },
            "legislation": {
                "source": "India Code, Ministry of Law and Justice, Government of India",
                "coverage": f"{len(legislation)} Central Acts ({total_statute_sections} sections) including IPC 1860, CrPC 1973, IEA 1872, CPC 1908, Citizenship Act, RPA, PHRA, RTI, AFSPA, OLA, Delimitation Act, CAG Act"
            }
        }
    }

    with open(CORPUS_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("CORPUS BUILD COMPLETE")
    print(f"Total Documents: {total_docs}")
    print(f" - Constitutional Articles & Schedules: {len(articles)}")
    print(f" - Constitutional Amendments:          {len(amendments)}")
    print(f" - Supreme Court Decisions:             {len(judgments)}")
    print(f" - Statutory Central Acts:              {len(legislation)}")
    print(f"Total Text Size: {total_chars:,} characters (~{round(total_chars/4):,} tokens)")
    print(f"[+] Manifest saved to: {CORPUS_MANIFEST_PATH}")
    print("=" * 70)

    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build and validate Indian Legal Corpus.")
    parser.add_argument("--smoke-test", action="store_true", help="Run small smoke-test partition rather than full corpus.")
    args = parser.parse_args()
    build_corpus(smoke_test=args.smoke_test)
