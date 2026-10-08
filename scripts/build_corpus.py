"""
Corpus Build Pipeline Script.
Compiles authoritative public-domain constitutional articles, amendments,
and landmark Supreme Court judgments into schema-compliant JSON datasets
with full provenance tracking.

Output paths:
- data/constitution/articles.json
- data/constitution/amendments.json
- data/judgments/supreme_court_landmarks.json
"""

import json
import sys
from pathlib import Path

# Adjust path to import from workspace root and scripts
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import (
    CONSTITUTION_DIR,
    JUDGMENTS_DIR,
    BENCHMARK_DIR,
    ANNOTATIONS_DIR,
    CONSTITUTION_ARTICLES_PATH,
    CONSTITUTION_AMENDMENTS_PATH,
    JUDGMENTS_LANDMARKS_PATH,
)
from scripts.corpus_data_articles import get_constitutional_articles
from scripts.corpus_data_amendments import get_constitutional_amendments
from scripts.corpus_data_judgments import get_landmark_judgments


def validate_document_schema(doc: dict, doc_type: str) -> None:
    """Validate that every document contains mandatory fields and valid provenance."""
    assert "document_id" in doc, f"Missing document_id in {doc}"
    assert "document_type" in doc, f"Missing document_type in {doc}"
    assert doc["document_type"] == doc_type, f"Type mismatch: expected {doc_type}, got {doc['document_type']}"
    assert "provenance" in doc, f"Missing provenance in {doc.get('document_id')}"
    prov = doc["provenance"]
    assert "source" in prov and "retrieval_date" in prov and "version" in prov, f"Incomplete provenance in {doc.get('document_id')}"

    if doc_type == "constitution_article":
        assert "article_number" in doc, f"Missing article_number in {doc.get('document_id')}"
        assert "title" in doc and "text" in doc, f"Missing title/text in {doc.get('document_id')}"
        assert "clauses" in doc and isinstance(doc["clauses"], list), f"Missing clauses in {doc.get('document_id')}"
    elif doc_type == "constitution_amendment":
        assert "amendment_number" in doc and "year" in doc, f"Missing amendment details in {doc.get('document_id')}"
    elif doc_type == "judgment":
        assert "case_name" in doc and "year" in doc and "court" in doc, f"Missing case header in {doc.get('document_id')}"
        assert "ratio_decidendi" in doc, f"Missing ratio_decidendi in {doc.get('document_id')}"
        assert "verdict" in doc, f"Missing verdict in {doc.get('document_id')}"


def build_corpus() -> dict:
    """Build and save all corpus datasets."""
    print("=" * 60)
    print("NLP CAPSTONE CORPUS BUILDER - STAGE 1")
    print("=" * 60)

    # 1. Ensure directories exist
    for directory in [CONSTITUTION_DIR, JUDGMENTS_DIR, BENCHMARK_DIR, ANNOTATIONS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    # 2. Compile Constitutional Articles
    articles = get_constitutional_articles()
    print(f"[*] Validating {len(articles)} Constitutional Articles...")
    for art in articles:
        validate_document_schema(art, "constitution_article")

    with open(CONSTITUTION_ARTICLES_PATH, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved {len(articles)} articles to {CONSTITUTION_ARTICLES_PATH}")

    # 3. Compile Constitutional Amendments
    amendments = get_constitutional_amendments()
    print(f"[*] Validating {len(amendments)} Constitutional Amendments...")
    for amend in amendments:
        validate_document_schema(amend, "constitution_amendment")

    with open(CONSTITUTION_AMENDMENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(amendments, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved {len(amendments)} amendments to {CONSTITUTION_AMENDMENTS_PATH}")

    # 4. Compile Landmark Judgments
    judgments = get_landmark_judgments()
    print(f"[*] Validating {len(judgments)} Landmark Judgments...")
    for judg in judgments:
        validate_document_schema(judg, "judgment")

    with open(JUDGMENTS_LANDMARKS_PATH, "w", encoding="utf-8") as f:
        json.dump(judgments, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved {len(judgments)} judgments to {JUDGMENTS_LANDMARKS_PATH}")

    summary = {
        "constitutional_articles": len(articles),
        "constitutional_amendments": len(amendments),
        "landmark_judgments": len(judgments),
        "total_documents": len(articles) + len(amendments) + len(judgments)
    }

    print("-" * 60)
    print("Corpus Compilation Summary:")
    print(f"  - Constitutional Articles:  {summary['constitutional_articles']}")
    print(f"  - Landmark Amendments:      {summary['constitutional_amendments']}")
    print(f"  - SC Landmark Judgments:    {summary['landmark_judgments']}")
    print(f"  - Total Corpus Documents:   {summary['total_documents']}")
    print("=" * 60)
    return summary


if __name__ == "__main__":
    build_corpus()
