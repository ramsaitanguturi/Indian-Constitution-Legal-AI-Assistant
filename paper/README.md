# Research Paper: Entity-Aware Hybrid Retrieval and Reranking Framework for Indian Constitutional Question Answering

This directory contains the academic research manuscript, publication-quality vector figures, BibTeX bibliography, and compilation instructions for the research study conducted on the **Indian Constitution Legal AI Assistant**.

---

## 📄 Manuscript Overview

- **Title**: *Entity-Aware Hybrid Retrieval and Reranking Framework for Indian Constitutional Question Answering*
- **Author**: Ramsai Tanguturi (Department of Computer Science \& Engineering)
- **Target Venue / Milestone**: Empirical NLP / Legal AI Research (B.Tech NLP Capstone Milestone)
- **Primary Document Files**:
  - 📕 [**Compiled Manuscript (PDF)**](main.pdf): The complete 14-page compiled academic paper with vector figures, tables, and bibliography.
  - 📝 [**LaTeX Source (`main.tex`)**](main.tex): Fully editable, modular LaTeX manuscript.
  - 📚 [**BibTeX Bibliography (`references.bib`)**](references.bib): Verified, genuine citations to peer-reviewed literature in NLP, IR, and Legal AI.
  - 🎨 [**Figures Directory (`figures/`)**](figures/): High-resolution vector diagrams (`system_architecture.pdf`, `parent_child_hierarchy.pdf`, `retrieval_comparison.pdf`) and editable TikZ sources.

---

## 🔬 Abstract Summary

Automated question answering over Indian Constitutional law presents unique domain hurdles: pronounced vocabulary mismatches between colloquial citizen queries and formal statutory text, complex hierarchical dependencies between Articles and Clauses, and catastrophic hallucination risks when large language models synthesize ungrounded legal precedents.

This paper presents the empirical evaluation, mathematical formalization, and adversarial audit of a 16-stage deterministic pipeline. The framework pairs a **Hierarchical Parent-Child Retrieval** architecture with dual-stage search: sparse lexical retrieval (BM25Okapi) and dense semantic vector retrieval (ChromaDB with 384-dimensional MiniLM embeddings) fused via **Reciprocal Rank Fusion (RRF, $k=60$)**, followed by an additive **legal entity boost ($+0.15$)** and cross-attention neural reranking (**`cross-encoder/ms-marco-MiniLM-L-6-v2`**).

Evaluated across 200 verified constitutional queries over an audited corpus of 270 parent documents (137 Articles, 18 Amendments, and 104 Supreme Court landmark judgments yielding 1,001 indexed child passages), the full neural pipeline achieves:
- **Hit@1**: **0.8400** (vs. 0.7900 BM25)
- **Recall@10**: **0.7478** (vs. 0.7003 BM25)
- **MRR**: **0.8583** (+3.12% lift over BM25)
- **NDCG@10**: **0.7787** (+5.90% lift over BM25)

The framework is augmented with a 10-class hybrid Legal Named Entity Recognizer (exact-span Macro-F1 = **0.8496**), canonical entity linking (86.67\% accuracy), an n-gram TF-IDF intent classifier (5-fold cross-validation accuracy = **0.7591** $\pm$ **0.0422**), structural citation validation, an explainable 6-signal composite confidence estimator, and an automated abstention gate ($C < 0.30$) that rejects 100\% of out-of-scope inquiries.

---

## 📊 Key Verified Experimental Findings

### 1. Information Retrieval Performance (200 Queries)

| Configuration | Hit@1 | Hit@5 | Hit@10 | Recall@10 (Orig) | Recall@10 (Canon) | MRR (Canon) | NDCG@10 (Canon) | Steady Median Latency |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Exp 1: BM25 Only** | 0.7900 | 0.8850 | 0.8950 | 0.5064 | 0.7003 | 0.8271 | 0.7197 | **3.02 ms** |
| **Exp 2: Dense Only (MiniLM)** | 0.8100 | 0.8900 | 0.8950 | 0.5250 | 0.7131 | 0.8385 | 0.7432 | 19.79 ms |
| **Exp 3: Linear Hybrid** | 0.8100 | 0.8900 | 0.8950 | 0.5150 | 0.7076 | 0.8411 | 0.7333 | 21.50 ms |
| **Exp 4: RRF ($k=60$)** | 0.8100 | 0.8900 | 0.8950 | 0.5106 | 0.7005 | 0.8396 | 0.7262 | 21.20 ms |
| **Exp 5: RRF + Entity Boost** | 0.8200 | 0.8900 | 0.8950 | 0.5352 | 0.7229 | 0.8421 | 0.7493 | 65.40 ms |
| **Exp 6: Full Pipeline (+ Cross-Encoder)** | **0.8400** | **0.9000** | **0.9050** | **0.5526** | **0.7478** | **0.8583** | **0.7787** | 891.64 ms |

### 2. Legal Named Entity Recognition (105 Annotated Queries, 211 Spans)
- **Strict Exact-Span Micro-F1**: **0.8714** | **Macro-F1**: **0.8496**
- **Perfect F1 (1.0000)**: `ARTICLE` (40/40), `AMENDMENT` (15/15), `SECTION` (11/11), `DATE` (38/38)
- **Resolved Judge Extraction**: `PERSON` F1 improved from 0.0000 to **0.8966** (13/14 resolved via `PERSON_TITLE_PATTERN`)
- **Other Categories**: `CASE` (0.8364), `ACT` (0.8000), `COURT` (0.7368), `RIGHT` (0.6667), `LEGAL_CONCEPT` (0.5600)

### 3. Intent Classification (220 Queries across 11 Classes)
- **80/20 Holdout Split**: Accuracy = **0.8485**, Macro-F1 = **0.8331** (vs. Rule Baseline Accuracy = 0.6970, Macro-F1 = 0.6290)
- **5-Fold Stratified Cross-Validation**: Mean Accuracy = **0.7591** ($\pm 0.0422$), Mean Macro-F1 = **0.7444** ($\pm 0.0417$)

---

## 🛠️ Local Compilation Instructions

To compile the LaTeX manuscript locally into PDF format:

### Prerequisites
Ensure a standard TeX distribution is installed:
- **Windows**: MiKTeX or TeX Live
- **Linux**: `texlive-latex-extra texlive-fonts-recommended texlive-science`
- **macOS**: MacTeX

### Compilation Commands

**Option 1: Standard Four-Step Pass (Recommended)**
```bash
cd paper

# Pass 1: Generate auxiliary file (.aux)
pdflatex -interaction=nonstopmode -halt-on-error main.tex

# Pass 2: Compile BibTeX bibliography (.bbl)
bibtex main

# Pass 3: Incorporate citations
pdflatex -interaction=nonstopmode -halt-on-error main.tex

# Pass 4: Finalize cross-references, table floats, and outlines
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

**Option 2: Automated Compilation via `latexmk`**
```bash
cd paper
latexmk -pdf main.tex
```

**Clean Temporary Compilation Artifacts**
```bash
# Windows PowerShell
Remove-Item *.aux, *.bbl, *.blg, *.log, *.out, *.fls, *.fdb_latexmk -ErrorAction SilentlyContinue

# Linux / macOS
rm -f *.aux *.bbl *.blg *.log *.out *.fls *.fdb_latexmk
```

---

## 📁 Directory Structure

```text
paper/
├── main.tex                  # Complete academic manuscript source
├── main.pdf                  # Compiled 14-page publication PDF
├── references.bib            # BibTeX bibliography database
├── README.md                 # Paper overview & reproduction instructions
└── figures/
    ├── system_architecture.tex      # TikZ vector source for 16-stage pipeline
    ├── system_architecture.pdf      # Compiled vector PDF graphic
    ├── parent_child_hierarchy.tex   # TikZ vector source for hierarchical RAG
    ├── parent_child_hierarchy.pdf   # Compiled vector PDF graphic
    ├── retrieval_comparison.tex     # TikZ vector source for retrieval metrics
    └── retrieval_comparison.pdf     # Compiled vector PDF graphic
```

---

## ⚖️ Academic Audit & Responsible Disclosure Notice

In accordance with rigorous academic integrity standards (documented in `docs/INDEPENDENT_AUDIT_REPORT.md` and `docs/BENCHMARK_QUALITY_REPORT.md`):
1. **Benchmark Ceiling**: 20 queries out of 200 target constitutional articles not present in the 137-article indexed subset, imposing an empirical $-10.0\%$ penalty on evaluated recall.
2. **Citation Verification**: Structural validation confirms physical document presence and retrieval set provenance; it does not constitute sentence-level Natural Language Inference (NLI) claim entailment.
3. **Academic Standing**: This software is an educational prototype and does not substitute for formal legal counsel.
