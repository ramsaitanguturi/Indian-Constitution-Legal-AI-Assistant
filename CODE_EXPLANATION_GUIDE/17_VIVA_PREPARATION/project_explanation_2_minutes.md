# 2-Minute Project Elevator Pitch: `17_VIVA_PREPARATION/project_explanation_2_minutes.md`

[Back to Viva Preparation Overview](code_demonstration_script.md) • [Back to Main Index](../README.md)

---

## 1. Context & When to Use

Use this script when the external examiner or professor opens the viva with:
> *"Give me a brief 2-minute overview of your project. What did you build, why did you build it, and what are your main results?"*

**Timing Target**: Exactly 120 seconds (approx. 260–280 spoken words). Speak calmly, confidently, and clearly.

---

## 2. The Spoken Presentation Script

> "Good morning, respected professors and external examiners.
> 
> My project is titled **'Indian Constitution Legal AI Assistant'** — an **Entity-Aware Hybrid Retrieval and Reranking Framework for Indian Constitutional Question Answering**.
> 
> General-purpose AI chatbots fail in legal domains because they suffer from **vocabulary mismatch**, **statutory anchor confusion**, and **hallucination of non-existent laws**. In constitutional law, citing a fabricated article or inverting a judicial holding is unacceptable.
> 
> To solve this, I designed and implemented a **4-tier architecture**:
> 
> 1. **First, an NLP Understanding Pipeline** that performs language detection, custom legal text preprocessing, extracts 10 legal entity categories—such as Articles, Landmark Cases, and Amendments—and links them to canonical IDs.
> 2. **Second, a Deterministic Query Router** that selects optimal retrieval strategies without costly LLM calls.
> 3. **Third, a Two-Stage Hybrid Retrieval Engine**. In stage one, we combine sparse BM25 with dense 1024-dimensional BGE-M3 vector search using **Cormack Reciprocal Rank Fusion ($k=60$)**, followed by our novel **Statutory Entity Boost (+0.15)**. In stage two, a **Transformer Cross-Encoder** reranks the top 30 candidates down to the top 5 with full cross-attention.
> 4. **Fourth, an Asymmetric Grounded Generation and Safety Subsystem**. We search small 300-character child passages, but hydrate the complete 1,200-character parent document from `parent_store.json`. We enforce zero-temperature generation, structural citation validation, sentence-level Natural Language Inference to catch polarity contradictions, and a 5-stage abstention gate that safely withholds generation if confidence drops below 0.30.
> 
> We evaluated our system on a benchmark of 100 expert-annotated constitutional queries across our 886-document corpus. Our full hybrid pipeline achieved an **NDCG@10 of 0.7787** — a **41.9% improvement over the BM25 baseline** and a **35.7% improvement over dense vector search**, with **100% structural citation validity** and zero data leakage.
> 
> I am excited to demonstrate the code and the live Streamlit application. Thank you."

---

## 3. Key Numbers & Acronyms to Memorize

- **Corpus Size**: 886 documents (477 Articles & Schedules, 106 Amendments, 286 Judgments, 17 Central Acts).
- **Indexed Chunks**: 7,470 child passages (~300 chars).
- **Primary Retrieval Metric**: **NDCG@10 = 0.7787** (+41.9% gain over BM25 = 0.5484).
- **MRR**: **0.7420** (+51.1% gain over BM25 = 0.4912).
- **Core Algorithms**: Cormack RRF ($k=60$), BGE-M3 (1024-d), Cross-Encoder (`ms-marco-MiniLM-L-6-v2`), NLI Polarity Checking.

