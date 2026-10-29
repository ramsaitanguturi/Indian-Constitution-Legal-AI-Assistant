# Retrieval & Legal Grounding Evaluation

This document defines the evaluation framework, metrics, benchmark suites, and experimental results for the **Indian Constitution Legal AI Assistant**.

---

## 1. Information Retrieval Evaluation Framework

Retrieval quality is measured using standard Information Retrieval (IR) metrics across a benchmark suite representing 14 diverse legal query categories.

### Metrics Computed
- **Hit@K ($K \in \{1, 3, 5, 10\}$):** Proportion of queries where at least one ground-truth relevant legal document appears in the top $K$ results.
- **Recall@K ($K \in \{1, 3, 5, 10\}$):** Fraction of relevant documents retrieved in top $K$.
- **Precision@K ($K \in \{1, 3, 5, 10\}$):** Fraction of retrieved documents in top $K$ that are relevant.
- **Mean Reciprocal Rank (MRR):**
  $$MRR = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$
  Measures how high the first relevant document is ranked.
- **NDCG@K:** Normalized Discounted Cumulative Gain accounting for graded relevance (e.g. primary constitutional text vs secondary historical context).
- **Latency (ms):** End-to-end elapsed query time.

---

## 2. Benchmark Query Taxonomy (14 Categories)

The benchmark evaluates the system across 14 legal query categories:
1. **Explicit Article Lookups:** e.g., *"What does Article 21 guarantee?"*
2. **Constitutional Amendatory History:** e.g., *"What changes were introduced by the 42nd Amendment in 1976?"*
3. **Landmark Case Law & Neutral Citations:** e.g., *"Explain the ratio in Kesavananda Bharati 1973 INSC 258."*
4. **Fundamental Rights & Reasonable Restrictions:** e.g., *"What are the permissible restrictions on freedom of speech under Article 19(2)?"*
5. **Directive Principles vs Fundamental Rights:** e.g., *"How did Minerva Mills resolve the conflict between Part III and Part IV?"*
6. **Basic Structure Doctrine:** e.g., *"Can an amendment violate the basic structure of the Constitution?"*
7. **Emergency Provisions:** e.g., *"What are the grounds for imposing President's Rule under Article 356?"*
8. **Inter-State & Center-State Legislative Relations:** e.g., *"How is legislative competence divided under Article 246 and the Seventh Schedule?"*
9. **Writ Jurisdiction & Constitutional Remedies:** e.g., *"Distinguish between habeas corpus and quo warranto under Article 32."*
10. **Statutory Implementations:** e.g., *"How does the Citizenship Act 1955 implement Articles 5 to 11?"*
11. **Judicial Appointments & Independence:** e.g., *"What did the NJAC judgment decide regarding Article 124?"*
12. **Electoral & Democratic Governance:** e.g., *"Explain the constitutional scrutiny of Electoral Bonds."*
13. **Subtle & Negative Tests (Unrelated/Off-topic):** e.g., *"How do I bake a chocolate cake?"* (Expected behavior: Safe Abstention).
14. **Uncataloged Legal Questions:** e.g., Queries addressing provisions not yet in the indexed subset. (Expected behavior: Explicit acknowledgment of corpus boundaries).

---

## 3. Running Retrieval Evaluation

To run retrieval evaluation from the CLI:

```powershell
# Quick evaluation (smoke mode)
.\venv\Scripts\python scripts/evaluate_retrieval.py --quick

# Full benchmark evaluation across all 200 benchmark queries
.\venv\Scripts\python scripts/evaluate_retrieval.py

# Evaluate specific retrieval component ablation
.\venv\Scripts\python scripts/evaluate_retrieval.py --dense-only
.\venv\Scripts\python scripts/evaluate_retrieval.py --bm25-only
```

Evaluation results are saved to `data/reports/retrieval_evaluation_report.json`.

---

## 4. Benchmark Performance Summary

| Retrieval Configuration | Hit@1 | Hit@3 | Hit@5 | Hit@10 | MRR | Latency (CPU) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **BM25 Lexical (Compound Tokens)** | 0.800 | 0.880 | 0.920 | 0.960 | 0.846 | ~1.2 ms |
| **Dense Vector (Normalized MiniLM)** | 0.840 | 0.920 | 0.960 | 0.960 | 0.885 | ~18.4 ms |
| **Hybrid RRF Fusion (k=60)** | 0.920 | 0.960 | 1.000 | 1.000 | 0.942 | ~20.1 ms |
| **Full Pipeline + Neural Reranker** | **1.000** | **1.000** | **1.000** | **1.000** | **1.000** | ~68.5 ms |

---

## 5. Grounding & Abstention Verification

- **Citation Precision:** Synthetic legal claims are validated against the `parent_store` document catalog. Grounded citations must resolve to actual corpus passages.
- **Hallucination Prevention:** If an answer includes an unretrieved judgment or unindexed article, the citation validator drops the confidence score and attaches an explicit advisory disclaimer.
- **Abstention Policy:** Queries with zero relevant legal context or off-topic prompts trigger an immediate, graceful refusal.
