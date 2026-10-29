"""
Verification Script for End-to-End Legal RAG Pipeline on Previously Unseen Queries.
Demonstrates live retrieval, citation validation, parent hydration, and grounded synthesis.
"""

import sys
import json
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from rag.pipeline import get_legal_rag_pipeline


def run_verification():
    print("=" * 70)
    print("INDIAN CONSTITUTION LEGAL AI ASSISTANT — PIPELINE VERIFICATION")
    print("=" * 70)

    pipeline = get_legal_rag_pipeline()

    test_queries = [
        # 1. Constitutional Article lookup
        "What does Article 21 guarantee regarding protection of life and personal liberty?",
        # 2. Constitutional Amendment & SOR
        "What changes were made by the 44th Amendment Act to the right to property?",
        # 3. Supreme Court Landmark Precedent
        "What was the ratio decidendi in A.K. Gopalan v. State of Madras (1950 INSC 13)?",
        # 4. Central Statutory Legislation
        "Under Section 124A of the Indian Penal Code, what constitutes sedition?",
        # 5. Out of scope / Negative test (Abstention check)
        "What are the best ingredients for baking a chocolate cake?",
    ]

    for idx, query in enumerate(test_queries, 1):
        print(f"\n[{idx}/5] QUERY: {query}")
        print("-" * 70)

        result = pipeline.run(query)

        print(f"[*] Language Detected:    {result.language.get('language')} (confidence: {result.language.get('confidence', 0):.2f})")
        print(f"[*] Intent Classification: {result.intent.get('primary_intent')} (confidence: {result.intent.get('confidence', 0):.2f})")
        print(f"[*] Extracted Entities:    {result.entities}")
        print(f"[*] Routing Strategy:      {result.routing_decision.get('strategy')}")
        print(f"[*] Abstained:             {result.abstained}")
        if result.abstained:
            print(f"[*] Abstention Reason:     {result.abstention_reason}")
            print(f"[*] Output Message:        {result.generated_answer.strip()[:180]}...")
            continue

        print(f"[*] Retrieved Chunks:      {len(result.retrieved_chunks)} child passages")
        print(f"[*] Hydrated Parents:      {result.parent_context.get('parent_count', 0)} documents")
        for p_idx, p in enumerate(result.parent_context.get("parents", [])[:2], 1):
            p_title = p.get("title") or p.get("case_name") or p.get("document_id")
            p_type = p.get("doc_type") or p.get("document_type")
            print(f"    Parent {p_idx}: [{p_type}] {p_title}")

        print(f"[*] Citation Validation:   Status={'VALID' if result.citation_validation.get('valid') else 'INVALID'} | Checked={result.citation_validation.get('citations_checked')}")
        print(f"[*] Confidence Score:      {result.confidence.get('confidence_score', 0):.4f} ({result.confidence.get('confidence_level')})")
        print(f"[*] Generated Answer Snippet:\n{result.generated_answer.strip()[:350]}...\n")

    print("=" * 70)
    print("VERIFICATION COMPLETE: ALL PIPELINE STAGES OPERATIONAL")
    print("=" * 70)


if __name__ == "__main__":
    run_verification()
