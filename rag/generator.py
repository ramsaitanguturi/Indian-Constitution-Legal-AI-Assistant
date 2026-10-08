"""
Grounded Legal Generator for Indian Constitution RAG Assistant.
Generates structured legal answers derived STRICTLY from verified retrieved evidence.
Distinguishes verbatim evidence from explanatory synthesis, preserves provenance,
provides structured citations, and safely handles insufficient evidence.
"""

import os
import re
from typing import Dict, List, Any, Optional

from config import GEMINI_API_KEY, DEFAULT_LLM_MODEL


GROUNDED_RAG_PROMPT = """You are a senior Constitutional Law Scholar and Legal Grounding Engine specializing in the Constitution of India.
Your mission is to formulate an authoritative, precise legal answer derived STRICTLY and EXCLUSIVELY from the verified SOURCE DOCUMENTS provided below.

GROUNDING & INTEGRITY CONSTRAINTS:
1. Answer ONLY using the facts, provisions, definitions, and legal ratios contained in the provided evidence.
2. ZERO EXTERNAL HALLUCINATION: Under NO circumstances should you cite Articles, Amendments, or Judgments that are NOT present in the provided source documents.
3. Every legal claim MUST include an explicit bracketed citation key matching the source document ID, e.g. [Doc: <doc_id>].
4. Clearly distinguish direct statutory/judicial evidence from explanatory legal analysis.
5. If the provided documents are insufficient to answer the query, state explicitly: "INSUFFICIENT EVIDENCE: The provided constitutional sources do not contain sufficient evidence to answer this query."

STRUCTURE YOUR RESPONSE INTO THREE DISTINCT SECTIONS:
### 📜 Direct Legal Evidence
(Quote or present verbatim the exact constitutional clauses or judicial ratio decidendi from the sources, with citation keys)

### ⚖️ Grounded Legal Analysis
(Provide structured, objective synthesis explaining the legal implications, scope, and principles strictly based on the evidence)

### 📚 Verified Citations
(List the exact documents cited using [Doc: <doc_id>] and their formal titles)

VERIFIED SOURCE DOCUMENTS:
{context}

USER QUERY:
{query}

GROUNDED RESPONSE:"""


class GroundedGenerator:
    """
    Grounded Generator with dual-mode execution:
    1. Online Google Gemini Chat with strict grounding constraints when API key is provided.
    2. Deterministic Grounded Legal Synthesis Engine when offline or API key is absent.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        enable_online: bool = False,
    ):
        self.api_key = api_key or GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
        self.model_name = model_name or DEFAULT_LLM_MODEL
        self.enable_online = enable_online or bool(api_key and len(api_key) > 5)
        self.llm_available = bool(self.enable_online and self.api_key and len(self.api_key) > 5)
        self.llm = None

        if self.llm_available:
            self._init_llm()

    def _init_llm(self, api_key: Optional[str] = None):
        """Initialize or update the Google Gemini LLM instance."""
        target_key = api_key or self.api_key
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            # Use valid model name or fallback
            target_model = self.model_name if "gemini" in self.model_name.lower() else "gemini-1.5-flash"
            self.llm = ChatGoogleGenerativeAI(
                model=target_model,
                google_api_key=target_key,
                temperature=0.0,  # Zero temperature for maximal grounding determinism
                timeout=10,  # Prevent test / network hangs
            )
            self.llm_available = True
            self.api_key = target_key
        except Exception:
            self.llm = None
            self.llm_available = False

    def update_api_key(self, new_key: str):
        """Update API key at runtime if user inputs a key via UI."""
        if new_key and new_key.strip():
            self.enable_online = True
            self._init_llm(api_key=new_key.strip())

    def generate(
        self,
        query: str,
        recovered_context: Dict[str, Any],
        routing_decision: Optional[Any] = None,
        dynamic_api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes grounded generation from recovered parent/child context.

        Args:
            query: User's legal question.
            recovered_context: Output dictionary from ParentChildRecovery.recover().
            routing_decision: Optional RoutingDecision providing strategy context.
            dynamic_api_key: Optional runtime Gemini API key.

        Returns:
            Dictionary containing:
            - answer: Formatted markdown answer
            - citations: Structured list of citations
            - used_llm: Boolean flag
            - model_name: Generation engine identifier
            - has_insufficient_evidence: Boolean flag
            - distinguished_sections: Dictionary mapping evidence, analysis, citations
        """
        if dynamic_api_key and dynamic_api_key.strip() and dynamic_api_key.strip() != self.api_key:
            self.update_api_key(dynamic_api_key.strip())

        parents = recovered_context.get("parents", [])
        if not parents:
            return {
                "answer": (
                    "**Notice of Insufficient Evidence**: No verified constitutional provisions "
                    "or landmark Supreme Court judgments were found in the database to answer this inquiry. "
                    "To avoid ungrounded legal assertions, generation has been safely withheld."
                ),
                "citations": [],
                "used_llm": False,
                "model_name": "GroundedGenerator (Deterministic Safety)",
                "has_insufficient_evidence": True,
                "distinguished_sections": {
                    "evidence": "",
                    "analysis": "Insufficient verified evidence retrieved.",
                    "citations": "",
                },
            }

        # Build structured citations catalog directly from recovered evidence
        structured_citations = self._build_structured_citations(parents)

        # Attempt online LLM generation if available
        if self.llm_available and self.llm is not None:
            try:
                from langchain_core.prompts import ChatPromptTemplate
                from langchain_core.output_parsers import StrOutputParser

                prompt_tmpl = ChatPromptTemplate.from_template(GROUNDED_RAG_PROMPT)
                chain = prompt_tmpl | self.llm | StrOutputParser()
                prompt_context = recovered_context.get("formatted_context", "")

                response_text = chain.invoke({
                    "context": prompt_context,
                    "query": query,
                })

                # Parse sections from generated output
                sections = self._parse_distinguished_sections(response_text)

                # Check if model declared insufficient evidence
                has_insufficient = "INSUFFICIENT EVIDENCE" in response_text.upper()

                return {
                    "answer": response_text,
                    "citations": structured_citations,
                    "used_llm": True,
                    "model_name": self.model_name,
                    "has_insufficient_evidence": has_insufficient,
                    "distinguished_sections": sections,
                }
            except Exception as e:
                # Graceful fallback to deterministic offline synthesizer
                pass

        # Offline / Fallback Deterministic Grounded Legal Synthesis
        offline_result = self._synthesize_grounded_offline(query, parents, routing_decision)
        offline_result["citations"] = structured_citations
        return offline_result

    def _build_structured_citations(self, parents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Constructs an authoritative list of structured citation objects from parent docs."""
        citations = []
        for p in parents:
            doc_id = p["document_id"]
            doc_type = p["doc_type"]
            title = p.get("title", doc_id)
            supporting_chunks = [c["chunk_id"] for c in p.get("supporting_children", [])]
            primary_evidence = p["supporting_children"][0]["text"] if p.get("supporting_children") else ""

            citation_entry = {
                "citation_key": f"[Doc: {doc_id}]",
                "document_id": doc_id,
                "doc_type": doc_type,
                "source_title": title,
                "article_number": p.get("article_number"),
                "case_name": p.get("case_name"),
                "citation": p.get("citation"),
                "year": p.get("year"),
                "bench": p.get("bench"),
                "part": p.get("part"),
                "category": p.get("category"),
                "supporting_chunk_ids": supporting_chunks,
                "evidence_snippet": primary_evidence[:200] + ("..." if len(primary_evidence) > 200 else ""),
            }
            citations.append(citation_entry)
        return citations

    def _parse_distinguished_sections(self, text: str) -> Dict[str, str]:
        """Separates response text into Evidence, Analysis, and Citations sections."""
        evidence = ""
        analysis = ""
        citations = ""

        ev_match = re.search(r"###\s*📜\s*Direct Legal Evidence(.*?)(?=###\s*⚖️|###\s*📚|$)", text, re.DOTALL)
        an_match = re.search(r"###\s*⚖️\s*Grounded Legal Analysis(.*?)(?=###\s*📚|$)", text, re.DOTALL)
        cit_match = re.search(r"###\s*📚\s*Verified Citations(.*?)$", text, re.DOTALL)

        if ev_match:
            evidence = ev_match.group(1).strip()
        if an_match:
            analysis = an_match.group(1).strip()
        if cit_match:
            citations = cit_match.group(1).strip()

        # Fallback if headings differ
        if not evidence and not analysis:
            analysis = text

        return {
            "evidence": evidence,
            "analysis": analysis,
            "citations": citations,
        }

    def _synthesize_grounded_offline(
        self,
        query: str,
        parents: List[Dict[str, Any]],
        routing_decision: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Deterministic, fully-grounded offline synthesis engine.
        Constructs rich, strictly-grounded legal explanation directly from recovered records.
        """
        evidence_lines = []
        analysis_lines = []
        citations_lines = []

        for idx, p in enumerate(parents, start=1):
            doc_id = p["document_id"]
            doc_type = p["doc_type"]
            cit_key = f"[Doc: {doc_id}]"

            if doc_type == "constitution":
                art = p.get("article_number", "Article")
                title = p.get("title", "")
                part = p.get("part", "Part III")
                raw_text = p.get("full_text", "")
                explanation = p.get("explanation", "")
                historical = p.get("historical_context", "")

                evidence_lines.append(f"**{idx}. {art} — {title}** {cit_key}")
                evidence_lines.append(f"> *\"{raw_text.strip()}\"*")

                analysis_lines.append(f"#### {idx}. Analysis of {art} ({title})")
                analysis_lines.append(f"- **Constitutional Placement**: {part} ({p.get('category', 'Fundamental Rights')}).")
                if explanation:
                    analysis_lines.append(f"- **Scope & Interpretation**: {explanation}")
                if historical:
                    analysis_lines.append(f"- **Context & Amendments**: {historical}")

                citations_lines.append(f"- {cit_key}: **{art}** — {title} ({part})")

            elif doc_type == "judgment":
                case_name = p.get("case_name", "Landmark Case")
                cit = p.get("citation", "N/A")
                bench = p.get("bench", "Supreme Court")
                year = p.get("year", "")
                facts = p.get("facts", "")
                ratio = p.get("ratio_decidendi", "")
                verdict = p.get("verdict", "")
                takeaways = p.get("key_takeaways", [])

                evidence_lines.append(f"**{idx}. {case_name} ({year})** {cit_key}")
                evidence_lines.append(f"- **Formal Citation**: `{cit}` | **Bench**: {bench}")
                if ratio:
                    evidence_lines.append(f"- **Ratio Decidendi**: > *\"{ratio.strip()}\"*")

                analysis_lines.append(f"#### {idx}. Legal Doctrine in {case_name}")
                if facts:
                    analysis_lines.append(f"- **Background Facts**: {facts}")
                if verdict:
                    analysis_lines.append(f"- **Verdict & Holding**: {verdict}")
                if takeaways:
                    analysis_lines.append("- **Core Principles Established**:")
                    for t in takeaways:
                        analysis_lines.append(f"  * {t}")

                citations_lines.append(f"- {cit_key}: **{case_name}** `{cit}` ({year})")

            else:
                raw_text = p.get("full_text", "")
                evidence_lines.append(f"**{idx}. {p.get('title', doc_id)}** {cit_key}")
                evidence_lines.append(f"> *\"{raw_text.strip()}\"*")
                analysis_lines.append(f"#### {idx}. Context from {p.get('title', doc_id)}")
                analysis_lines.append(raw_text)
                citations_lines.append(f"- {cit_key}: {p.get('title', doc_id)}")

        evidence_section = "\n\n".join(evidence_lines)
        analysis_section = "\n\n".join(analysis_lines)
        citations_section = "\n".join(citations_lines)

        full_answer = (
            f"### 📜 Direct Legal Evidence\n\n{evidence_section}\n\n"
            f"### ⚖️ Grounded Legal Analysis\n\n{analysis_section}\n\n"
            f"### 📚 Verified Citations\n\n{citations_section}"
        )

        return {
            "answer": full_answer,
            "citations": [],  # Will be populated by caller
            "used_llm": False,
            "model_name": "GroundedLegalSynthesizer (Offline Grounded Engine)",
            "has_insufficient_evidence": False,
            "distinguished_sections": {
                "evidence": evidence_section,
                "analysis": analysis_section,
                "citations": citations_section,
            },
        }
