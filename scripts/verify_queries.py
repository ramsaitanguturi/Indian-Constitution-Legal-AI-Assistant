"""
Verification script for UI Redesign testing criteria.
Tests 3 different legal queries through the Legal RAG Pipeline and UI Formatter.
"""

import sys
sys.path.insert(0, ".")

from rag.pipeline import get_legal_rag_pipeline
from rag.ui_formatter import format_legal_pipeline_result

def test_queries():
    pipeline = get_legal_rag_pipeline()
    test_suite = [
        "What did the Supreme Court rule regarding the Right to Privacy under Article 21 in the Puttaswamy judgment?",
        "What is Article 21 of the Indian Constitution?",
        "Can police search private premises without a warrant under CrPC?"
    ]

    for i, q in enumerate(test_suite, start=1):
        print(f"\n=======================================================")
        print(f"TEST QUERY {i}: {q}")
        print(f"=======================================================")
        res = pipeline.run(q)
        formatted = format_legal_pipeline_result(res)

        print(f"[OK] Pipeline Result: abstained={formatted.is_abstained}")
        print(f"[OK] Direct Answer preview:\n  {formatted.direct_answer[:180]}...")
        print(f"[OK] Provisions count: {len(formatted.provisions)}")
        for prov in formatted.provisions:
            print(f"     - Provision: {prov.title} (Doc ID: {prov.document_id})")
            print(f"       Excerpt: {prov.excerpt[:100]}...")
        print(f"[OK] Judgments count: {len(formatted.judgments)}")
        for j in formatted.judgments:
            print(f"     - Judgment: {j.case_name} ({j.year}) | Citation: {j.citation}")
            print(f"       Ratio excerpt: {j.excerpt[:100]}...")
        print(f"[OK] Exceptions count: {len(formatted.exceptions)}")
        for exc in formatted.exceptions:
            first_line = exc.splitlines()[0] if exc.splitlines() else exc
            print(f"     - Exception: {first_line[:90]}...")
        print(f"[OK] Citations count: {len(formatted.citations)}")
        print(f"[OK] Technical details: Strategy={formatted.strategy}, Intent={formatted.intent}, Conf={formatted.confidence_score:.2f} ({formatted.confidence_level}), Citations Valid={formatted.citations_valid}")

        # Assertions
        assert not formatted.is_abstained
        assert len(formatted.direct_answer) > 20
        assert len(formatted.citations) > 0

    print("\nAll 3 test queries passed verification successfully!")

if __name__ == "__main__":
    test_queries()

