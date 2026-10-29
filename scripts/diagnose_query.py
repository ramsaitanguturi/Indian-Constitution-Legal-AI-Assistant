import sys
import os
sys.path.insert(0, os.path.abspath("."))
# Set standard output to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

import json
from rag.pipeline import get_legal_rag_pipeline

def main():
    pipeline = get_legal_rag_pipeline()
    query = "can police search house without warrant?"
    res = pipeline.run(query)

    print("=== PIPELINE TRACE ===")
    print("ORIGINAL QUERY:", res.original_query)
    print("NORMALIZED QUERY:", res.normalized_query)
    print("EXPANDED QUERY:", res.expanded_query)
    print("LANGUAGE:", res.language)
    print("ENTITIES:", res.entities)
    print("LINKED ENTITIES:", res.linked_entities)
    print("INTENT:", res.intent)
    print("ROUTING DECISION:", res.routing_decision)
    print("ABSTAINED:", res.abstained, "REASON:", res.abstention_reason)
    
    print("\n=== RETRIEVED CHUNKS (Top 5) ===")
    for idx, c in enumerate(res.retrieved_chunks[:5], 1):
        print(f"[{idx}] ID: {c.get('chunk_id')} | DocType: {c.get('doc_type')} | Title: {c.get('title')} | Score: {c.get('score')} | Rerank: {c.get('rerank_score')}")
        snippet = c.get('text', '')[:200].replace('\n', ' ')
        print(f"    Snippet: {snippet}...")

    print("\n=== PARENT CONTEXT ===")
    parents = res.parent_context.get("parents", [])
    print(f"Total Parents: {len(parents)}")
    for p in parents:
        print(f"- ID: {p.get('document_id')} | DocType: {p.get('doc_type')} | Title: {p.get('title')}")
        print(f"  Supporting children: {len(p.get('supporting_children', []))}")
        txt = p.get('full_text', '')
        print(f"  Full text len: {len(txt)} chars")

    print("\n=== GENERATED ANSWER (Length: {} chars) ===".format(len(res.generated_answer)))
    print(res.generated_answer[:1000])
    if len(res.generated_answer) > 1000:
        print("...\n[TRUNCATED]\n...")
        print(res.generated_answer[-600:])

    print("\n=== CITATIONS ===")
    for cit in res.citations:
        print(cit)

    print("\n=== CITATION VALIDATION ===")
    print(json.dumps(res.citation_validation, indent=2))

    print("\n=== CONFIDENCE ===")
    print(json.dumps(res.confidence, indent=2))

if __name__ == "__main__":
    main()
