"""
Priority 5 End-to-End Query Verification Test Script.
Executes the 7 mandatory queries against the live Legal RAG Pipeline:
1. Article 21 lookup.
2. Basic Structure Doctrine query.
3. Multiple judgments query.
4. Exact case citation retrieval.
5. Statutory section lookup.
6. Unseen question.
7. Unsupported question that triggers abstention.

Verifies that all citations resolve to actual source documents in parent_store.json.
"""

import sys
import json
from pathlib import Path

# UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from rag.pipeline import get_legal_rag_pipeline, PipelineResult
from config import PARENT_STORE_PATH


def run_priority5_tests():
    print("=" * 75)
    print("PRIORITY 5: LIVE END-TO-END QUERY RETRIEVAL & GROUNDING VERIFICATION")
    print("=" * 75)

    with open(PARENT_STORE_PATH, "r", encoding="utf-8") as f:
        parent_store = json.load(f)

    pipeline = get_legal_rag_pipeline()

    test_cases = [
        {
            "id": "TC_01_ARTICLE_21",
            "name": "Article 21 Constitutional Lookup",
            "query": "What does Article 21 of the Constitution of India guarantee?",
            "expect_abstain": False,
            "target_keywords": ["life", "liberty", "procedure established by law"],
        },
        {
            "id": "TC_02_BASIC_STRUCTURE",
            "name": "Basic Structure Doctrine",
            "query": "What is the Basic Structure Doctrine and which landmark judgment established it?",
            "expect_abstain": False,
            "target_keywords": ["Kesavananda", "basic structure", "368"],
        },
        {
            "id": "TC_03_MULTIPLE_JUDGMENTS",
            "name": "Multiple Judgments Synthesis (Gopalan to Maneka Gandhi)",
            "query": "How did the interpretation of personal liberty evolve from A.K. Gopalan to Maneka Gandhi?",
            "expect_abstain": False,
            "target_keywords": ["Gopalan", "Maneka", "due process"],
        },
        {
            "id": "TC_04_EXACT_CITATION",
            "name": "Exact Case Citation Retrieval",
            "query": "What was decided by the Supreme Court in 1950 INSC 13 ([1950] 1 S.C.R. 88)?",
            "expect_abstain": False,
            "target_keywords": ["Gopalan", "Madras", "1950"],
        },
        {
            "id": "TC_05_STATUTORY_SECTION",
            "name": "Statutory Section Lookup (IPC Section 124A)",
            "query": "What does Section 124A of the Indian Penal Code define regarding sedition?",
            "expect_abstain": False,
            "target_keywords": ["sedition", "disaffection", "124A"],
        },
        {
            "id": "TC_06_UNSEEN_QUESTION",
            "name": "Unseen Question (Article 22 Preventive Detention Safeguards)",
            "query": "Under what circumstances can preventive detention be ordered under Article 22 and what procedural safeguards are mandated?",
            "expect_abstain": False,
            "target_keywords": ["detention", "grounds", "Advisory Board"],
        },
        {
            "id": "TC_07_ABSTENTION_CHECK",
            "name": "Unsupported Question (Automated Safe Abstention Gate)",
            "query": "What is the best recipe and baking temperature for a traditional chocolate cake?",
            "expect_abstain": True,
            "target_keywords": ["out of scope", "cannot answer", "non-legal", "abstain"],
        },
    ]

    results_summary = []

    for idx, tc in enumerate(test_cases, 1):
        print(f"\n[{idx}/7] TEST CASE: {tc['name']}")
        print(f"QUERY: \"{tc['query']}\"")
        print("-" * 75)

        res: PipelineResult = pipeline.run(tc["query"])

        abstained = res.abstained
        print(f"  * Abstained:             {abstained} (Expected: {tc['expect_abstain']})")
        print(f"  * Intent Classified:     {res.intent.get('primary_intent')} (conf: {res.intent.get('confidence', 0):.2f})")
        print(f"  * Routing Strategy:      {res.routing_decision.get('strategy')}")
        print(f"  * Entities Extracted:    {res.entities}")

        # Check abstention match
        abstention_ok = (abstained == tc["expect_abstain"])

        citation_ok = True
        parents_verified = 0

        if not abstained:
            chunks_retrieved = len(res.retrieved_chunks)
            parents_hydrated = res.parent_context.get("parent_count", 0)
            print(f"  * Chunks Retrieved:      {chunks_retrieved}")
            print(f"  * Parents Hydrated:      {parents_hydrated}")

            # Verify citations resolve to actual documents in parent_store
            for p in res.parent_context.get("parents", []):
                pid = p.get("parent_id")
                doc_id = p.get("document_id") or p.get("id")
                # Must resolve directly or case-insensitive in parent_store
                resolves = (
                    pid in parent_store
                    or (pid and pid.lower() in parent_store)
                    or f"parent_{doc_id}" in parent_store
                    or doc_id in parent_store
                )
                if resolves:
                    parents_verified += 1
                else:
                    print(f"  [-] UNRESOLVED PARENT CITATION: pid={pid}, doc_id={doc_id}")
                    citation_ok = False

            print(f"  * Citations Verified:    {parents_verified}/{parents_hydrated} resolved to parent_store.json")
            print(f"  * Confidence Score:      {res.confidence.get('confidence_score', 0):.4f} ({res.confidence.get('confidence_level')})")
            print(f"  * Citation Validator:    {res.citation_validation.get('valid')} (checked: {res.citation_validation.get('citations_checked')})")
            print(f"  * Answer Excerpt:\n    \"{res.generated_answer.strip()[:240]}...\"")
        else:
            print(f"  * Abstention Reason:     {res.abstention_reason}")
            print(f"  * Abstention Output:\n    \"{res.generated_answer.strip()[:240]}...\"")

        test_passed = abstention_ok and (citation_ok if not abstained else True)
        status_label = "PASSED" if test_passed else "FAILED"
        print(f"  >>> STATUS: [{status_label}]")

        results_summary.append({
            "test_id": tc["id"],
            "name": tc["name"],
            "query": tc["query"],
            "abstained": abstained,
            "expected_abstain": tc["expect_abstain"],
            "parents_hydrated": res.parent_context.get("parent_count", 0) if not abstained else 0,
            "parents_verified": parents_verified,
            "citations_valid": res.citation_validation.get("valid", False) if not abstained else True,
            "status": status_label,
        })

    print("\n" + "=" * 75)
    print("END-TO-END VERIFICATION SUMMARY:")
    all_passed = all(r["status"] == "PASSED" for r in results_summary)
    for r in results_summary:
        print(f"  [{r['status']}] {r['name']}: Abstained={r['abstained']} | Verified={r['parents_verified']}")
    print(f"\nOVERALL RESULT: {'ALL 7 TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 75)

    return results_summary


if __name__ == "__main__":
    run_priority5_tests()

