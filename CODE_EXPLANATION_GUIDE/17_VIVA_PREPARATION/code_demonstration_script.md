# Live Code Demonstration Script: `17_VIVA_PREPARATION/code_demonstration_script.md`

[Back to Viva Preparation Overview](project_explanation_2_minutes.md) • [Back to Main Index](../README.md)

---

## 1. Preparation Checklist Before Demonstration

1. **Start the Streamlit Application**:
   ```bash
   streamlit run app.py
   ```
2. **Open VS Code with Ready Tabs**:
   - Tab 1: `rag/pipeline.py` (Line 109: `run`)
   - Tab 2: `retrieval/hybrid_retrieval.py` (Line 115: `retrieve`)
   - Tab 3: `retrieval/rrf.py` (Line 15: `reciprocal_rank_fusion`)
   - Tab 4: `retrieval/entity_boost.py` (Line 104: `apply_entity_boost`)
   - Tab 5: `rag/citation_validator.py` (Line 82: `validate`)
3. **Open a Split Terminal** for CLI commands.

---

## 2. Five Demonstration Scenarios

```
┌────────────────────────────────────────────────────────────────────────┐
│                   DEMONSTRATION WALKTHROUGH FLOW                       │
├────────────┬───────────────────────────────────────┬───────────────────┤
│ Scenario 1 │ Direct Constitutional Provision       │ "Article 21"      │
│ Scenario 2 │ Cross-Corpus Procedural Due Process   │ "Warrantless CrPC"│
│ Scenario 3 │ Landmark Case Law & Precedent         │ "Kesavananda"     │
│ Scenario 4 │ Adversarial / Out-of-Scope Gating     │ "UK Tax Law"      │
│ Scenario 5 │ Terminal White-Box Diagnostic Trace   │ "diagnose_query"  │
└────────────┴───────────────────────────────────────┴───────────────────┘
```

---

### Scenario 1: Exact Constitutional Provision Lookup

#### Input Query:
> *"What does Article 21 of the Indian Constitution guarantee and what are its core principles?"*

#### Actions in UI:
1. Submit query in the chat input box.
2. Point out the **Strategy Badge**: `ARTICLE_SEARCH`.
3. Point out the **Confidence Badge**: `HIGH (0.88)` (Green).
4. Expand the **Relevant Legal Provisions Card**:
   - Show that *Article 21 (Protection of life and personal liberty)* was retrieved at Rank 1.
   - Point out the verbatim quotation from the Constitution of India.
5. Expand the **Verified Citations Card**:
   - Show `[Doc: parent_const_art_021]` with source provenance.

#### What to Say to the Professor:
> *"Notice how the `QueryRouter` recognized the exact statutory mention of Article 21, applied our `ARTICLE_SEARCH` strategy, and filtered search to constitutional articles. The Statutory Entity Boost awarded +0.150 to Article 21, placing it decisively at Rank 1. Our citation validator confirmed that the cited document exists and was part of retrieved evidence."*

---

### Scenario 2: Cross-Corpus Procedural Due Process Query

#### Input Query:
> *"Can a police officer search a house without a warrant under CrPC and how does Article 21 apply?"*

#### Actions in UI:
1. Submit query.
2. Point out the **Strategy Badge**: `PROCEDURE_SEARCH`.
3. Show that the assistant produces an **Executive Legal Summary**:
   - Explains that the general rule requires a search warrant under Section 93 CrPC.
   - Explains the emergency exception under Section 165 CrPC (reasonable belief, undue delay, recorded written grounds).
   - Links the statutory search power to Article 21 procedural fairness.
4. Show that the retrieved provisions include **both** Section 165 CrPC (`act_crpc_1973`) and Article 21 (`parent_const_art_021`).

#### What to Say to the Professor:
> *"This demonstrates the cross-corpus power of our hybrid retriever. Laypersons ask about police searches without knowing statutory section numbers. Our system retrieved Section 165 of the Code of Criminal Procedure from India Code alongside Article 21 of the Constitution, synthesizing statutory exceptions and constitutional limits without hallucinating."*

---

### Scenario 3: Landmark Judicial Precedent Query

#### Input Query:
> *"What did the Supreme Court hold in Kesavananda Bharati regarding the basic structure doctrine?"*

#### Actions in UI:
1. Submit query.
2. Point out the **Strategy Badge**: `CASE_SEARCH` and Agent Persona: `case_law_agent`.
3. Show the **Relevant Judgments Card**:
   - Case Name: *Kesavananda Bharati v. State of Kerala (1973)*.
   - Citation: *(1973) 4 SCC 225*.
   - Bench: *13-Judge Constitution Bench (7:6 majority)*.
   - Ratio Decidendi: *Parliament has wide amending power under Article 368, but cannot alter the Basic Structure of the Constitution*.
   - Overruled Precedent: *Golak Nath v. State of Punjab*.

#### What to Say to the Professor:
> *"Notice that our `LegalStructureChunker` extracted the Ratio Decidendi into a dedicated child chunk. The generator quoted the exact binding ratio established by the 13-judge bench, rather than generic obiter dicta or attorney arguments."*

---

### Scenario 4: Adversarial & Out-of-Scope Safety Gating

#### Input Query:
> *"What is the corporate capital gains tax rate in London under UK Corporate Law?"*

#### Actions in UI:
1. Submit query.
2. Point out that the assistant **immediately abstains** and outputs:
   > *"Scope Notice: This inquiry falls outside the scope of Indian Constitutional Law. The assistant is specialized exclusively in the provisions of the Constitution of India, its amendments, and landmark Supreme Court judicial precedents..."*
3. Point out that the **Confidence Badge** shows `VERY_LOW (0.00)` (Red), and **no database records were queried**.

#### What to Say to the Professor:
> *"This demonstrates Gate 1 of our `AbstentionManager`. The query router analyzed the input, recognized zero Indian constitutional entities, and flagged the intent as `OUT_OF_SCOPE`. Execution halted in under 4 milliseconds at Stage 8 before calling ChromaDB or LLM endpoints, saving compute and eliminating any possibility of hallucination."*

---

### Scenario 5: Live Terminal White-Box Diagnostic Trace

Open your terminal and run:
```bash
python -m scripts.diagnose_query "Can police arrest without warrant under Article 21 and CrPC?"
```

#### What to Point Out in the Terminal Output:
1. **Step 1 & 2**: Language detected (`en`), text normalized.
2. **Step 3 & 4**: Extracted entities (`ARTICLE 21`, `CrPC`), mapped to canonical IDs `art_21`, `act_crpc_1973`.
3. **Step 5 & 6**: Intent classified as `CONSTITUTIONAL_PROCEDURE`, query expanded.
4. **Step 7 & 8**: Router selected `PROCEDURE_SEARCH`.
5. **Step 9–11**: Shows table of top 5 passages with BM25 score, Dense score, RRF score, Boost applied, and Cross-Encoder score!
6. **Step 12–15**: Shows hydrated parents, NLI claim verification (`VERIFIED_ENTAILED`), and 6-signal composite confidence (0.84).

#### What to Say to the Professor:
> *"This diagnostic CLI exposes the complete white-box pipeline. You can inspect the exact mathematical progression of scores from sparse BM25 and dense vectors to Cormack RRF, statutory boost, and cross-encoder logits for any query."*

