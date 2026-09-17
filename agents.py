"""
Multi-Agent Router and LLM Engine for the Indian Constitution Legal AI Assistant.
Implements specialized prompt templates and routing for:
1. Article Agent (Constitutional text & amendments)
2. Case-Law Agent (Supreme Court judgments & precedents)
3. Explanation Agent (Simplifying legalese into plain language)
Supports Google Gemini Chat models with automatic fallback to grounded Legal Synthesis Engine when offline.
"""

import os
import sys

# Ensure UTF-8 output encoding for Windows command line environment
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from typing import Dict, List, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import GEMINI_API_KEY, DEFAULT_LLM_MODEL


# Prompt Templates for Specialized Agents
ARTICLE_AGENT_PROMPT = """You are an expert Constitutional Law Specialist specializing in the Constitution of India.
Your task is to provide an authoritative, accurate, and precise response regarding Constitutional Articles, Clauses, Parts, and Amendments.

STRICT GROUNDING CONSTRAINTS:
1. Base your answer EXCLUSIVELY on the provided CONSTITUTIONAL CONTEXT below.
2. Do NOT invent, assume, or extrapolate outside the context (Zero Hallucination).
3. Always cite the exact Article number(s), Part, and Title.
4. Explain the legal scope, key provisions, and historical context if present.

CONSTITUTIONAL CONTEXT:
{context}

USER QUERY:
{query}

CONSTITUTIONAL ANALYSIS:"""


CASE_LAW_AGENT_PROMPT = """You are a Supreme Court Legal Precedents Specialist specializing in Indian Constitutional Judgments.
Your task is to explain landmark judgments, Ratio Decidendi, facts of the case, judicial benches, and legal precedents.

STRICT GROUNDING CONSTRAINTS:
1. Base your response EXCLUSIVELY on the JUDGMENTS CONTEXT provided below.
2. Clearly highlight: Case Name, Citation, Bench details, Facts, Ratio Decidendi, and Final Verdict.
3. If comparing cases, structure the comparison clearly under distinct headings.
4. Never mention unverified precedents not present in the context.

JUDGMENTS CONTEXT:
{context}

USER QUERY:
{query}

CASE-LAW & PRECEDENT ANALYSIS:"""


EXPLANATION_AGENT_PROMPT = """You are a Legal Educator and Plain-Language Legal Assistant for citizens and law students.
Your mission is to demystify complex Indian constitutional legal jargon into simple, clear, and engaging plain English (and Hindi references where appropriate).

STRICT GROUNDING CONSTRAINTS:
1. Stay 100% faithful to the SOURCE CONTEXT provided below.
2. Avoid dense legal jargon where simple words work.
3. Use bullet points, bold key terms, and structured sections (e.g. 'What it means', 'Why it matters', 'Key Takeaway').
4. Include a brief Hindi translation of the core summary if helpful.

SOURCE CONTEXT:
{context}

USER QUERY:
{query}

PLAIN-LANGUAGE EXPLANATION:"""


class HeuristicLegalSynthesizer:
    """
    Fallback Legal Synthesis Engine.
    When OpenAI API key is unavailable or offline, generates rich, deterministic,
    fully-grounded structured legal analysis directly from the RAG Parent/Child context.
    """

    @staticmethod
    def synthesize(agent_type: str, query: str, context_docs: List[Dict[str, Any]], entities: Dict[str, List[str]]) -> str:
        if not context_docs:
            return (
                "**Context Notice**: No matching constitutional articles or landmark judgments "
                "were found in the database for your query. Please refine your search terms."
            )

        output_lines = []

        if agent_type == "article_agent":
            output_lines.append("### 📜 Constitutional Article Analysis\n")
            output_lines.append(f"**Query**: *{query}*\n")
            
            if entities.get("articles"):
                output_lines.append(f"**Identified Article References**: {', '.join(entities['articles'])}\n")

            for idx, doc in enumerate(context_docs, start=1):
                pdata = doc.get("parent_data", {})
                if pdata.get("doc_type") == "constitution":
                    output_lines.append(f"#### {idx}. {pdata.get('article_number', 'Article')} — {pdata.get('title', '')}")
                    output_lines.append(f"- **Part**: {pdata.get('part', 'N/A')}")
                    output_lines.append(f"- **Category**: {pdata.get('category', 'N/A')}")
                    output_lines.append(f"\n> **Exact Provision**:\n> *\"{pdata.get('raw_text', '')}\"*\n")
                    if pdata.get("explanation"):
                        output_lines.append(f"**Legal Scope & Judicial Interpretation**:\n{pdata.get('explanation')}\n")
                    if pdata.get("historical_context"):
                        output_lines.append(f"**Historical Context & Amendments**:\n{pdata.get('historical_context')}\n")
                    output_lines.append("---")
                else:
                    output_lines.append(f"#### {idx}. Context Match ({doc.get('doc_type', 'Legal Document')})")
                    output_lines.append(f"*{doc.get('child_text', '')}*\n")

        elif agent_type == "case_law_agent":
            output_lines.append("### ⚖️ Supreme Court Case-Law & Precedents Analysis\n")
            output_lines.append(f"**Query**: *{query}*\n")

            if entities.get("cases"):
                output_lines.append(f"**Landmark Precedents Identified**: {', '.join(entities['cases'])}\n")

            for idx, doc in enumerate(context_docs, start=1):
                pdata = doc.get("parent_data", {})
                if pdata.get("doc_type") == "judgment":
                    output_lines.append(f"#### {idx}. {pdata.get('case_name', 'Landmark Case')} ({pdata.get('year', '')})")
                    output_lines.append(f"- **Citation**: `{pdata.get('citation', 'N/A')}`")
                    output_lines.append(f"- **Judicial Bench**: {pdata.get('bench', 'N/A')}")
                    output_lines.append(f"- **Articles Referred**: {', '.join(pdata.get('articles_referred', []))}")
                    output_lines.append(f"\n**Facts of the Case**:\n{pdata.get('facts', '')}\n")
                    output_lines.append(f"**Ratio Decidendi (Principle of Law)**:\n{pdata.get('ratio_decidendi', '')}\n")
                    output_lines.append(f"**Final Verdict**:\n{pdata.get('verdict', '')}\n")
                    
                    takeaways = pdata.get("key_takeaways", [])
                    if takeaways:
                        output_lines.append("**Key Legal Takeaways**:")
                        for t in takeaways:
                            output_lines.append(f"  * {t}")
                    output_lines.append("\n---")
                else:
                    output_lines.append(f"#### {idx}. Related Provision ({pdata.get('article_number', 'Article')})")
                    output_lines.append(f"*{doc.get('child_text', '')}*\n")

        else:  # Explanation Agent
            output_lines.append("### 💡 Plain-Language Legal Summary\n")
            output_lines.append(f"**Question**: *{query}*\n")

            output_lines.append("#### 1. What You Need to Know (In Simple Terms)")
            primary_doc = context_docs[0]
            pdata = primary_doc.get("parent_data", {})

            if pdata.get("doc_type") == "constitution":
                output_lines.append(
                    f"This question relates to **{pdata.get('article_number')} ({pdata.get('title')})**. "
                    f"In simple language, this fundamental provision ensures: {pdata.get('explanation')}"
                )
            elif pdata.get("doc_type") == "judgment":
                output_lines.append(
                    f"This question relates to the landmark Supreme Court judgment **{pdata.get('case_name')}**. "
                    f"The Supreme Court established that: {pdata.get('ratio_decidendi')}"
                )
            else:
                output_lines.append(f"{primary_doc.get('child_text')}")

            output_lines.append("\n#### 2. Key Takeaways for Citizens & Students")
            for doc in context_docs:
                pdata = doc.get("parent_data", {})
                if pdata.get("doc_type") == "constitution":
                    output_lines.append(f"- **{pdata.get('article_number')}**: {pdata.get('title')} guarantees protection under {pdata.get('part')}.")
                elif pdata.get("doc_type") == "judgment":
                    output_lines.append(f"- **{pdata.get('case_name')}**: Set the legal precedent that {pdata.get('verdict')}")

            output_lines.append("\n#### 3. Summary in Everyday Words (संक्षिप्त सारांश)")
            output_lines.append(
                "यह प्रावधान या निर्णय भारतीय संविधान के तहत नागरिकों के मौलिक अधिकारों की रक्षा करता है "
                "और यह सुनिश्चित करता है कि सरकार या प्रशासन मनमाने ढंग से काम न कर सके।"
            )

        return "\n".join(output_lines)


class MultiAgentRouter:
    """
    Agentic Router that classifies incoming queries and delegates them to:
    - Article Agent
    - Case-Law Agent
    - Explanation Agent
    Powered by Google Gemini (e.g. gemini-2.5-flash / gemini-1.5-flash)
    with seamless fallback to HeuristicLegalSynthesizer when offline.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
        self.model = model or DEFAULT_LLM_MODEL
        self.llm_available = bool(self.api_key and len(self.api_key) > 5)
        self.llm = None

        if self.llm_available:
            self._init_llm()

    def _init_llm(self, api_key: Optional[str] = None):
        """Initialize or update the Google Gemini LLM instance."""
        target_key = api_key or self.api_key
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            self.llm = ChatGoogleGenerativeAI(
                model=self.model,
                google_api_key=target_key,
                temperature=0.1
            )
            self.llm_available = True
            self.api_key = target_key
        except Exception as e:
            print(f"[AGENTS] Warning: Could not initialize ChatGoogleGenerativeAI ({e}). Falling back to heuristic synthesizer.")
            self.llm = None
            self.llm_available = False

    def update_api_key(self, new_key: str):
        """Update API key at runtime if user inputs a key via UI."""
        if new_key and new_key.strip():
            self._init_llm(api_key=new_key.strip())

    def classify_query(self, query: str, entities: Dict[str, List[str]], override_mode: str = "Auto-route") -> str:
        """Classify query to select the appropriate agent."""
        if override_mode != "Auto-route":
            mode_map = {
                "Article Agent": "article_agent",
                "Case-Law Agent": "case_law_agent",
                "Explanation Agent": "explanation_agent"
            }
            return mode_map.get(override_mode, "article_agent")

        query_lower = query.lower()

        # Heuristic rules based on entities and keywords
        if entities.get("cases") or any(k in query_lower for k in ["v.", "versus", "case", "judgment", "verdict", "ratio", "bench", "precedent", "court"]):
            return "case_law_agent"

        if any(k in query_lower for k in ["explain", "simple", "meaning", "plain english", "citizen", "what does", "in easy words", "hindi"]):
            return "explanation_agent"

        if entities.get("articles") or any(k in query_lower for k in ["article", "clause", "part", "preamble", "amendment", "schedule", "constitution"]):
            return "article_agent"

        # Default fallback
        return "explanation_agent"

    def execute_agent(self, agent_type: str, query: str, context_docs: List[Dict[str, Any]], entities: Dict[str, List[str]], dynamic_api_key: Optional[str] = None) -> Dict[str, Any]:
        """Execute the chosen agent and return answer alongside metadata."""
        # Update key if dynamically passed from UI
        if dynamic_api_key and dynamic_api_key.strip() and dynamic_api_key.strip() != self.api_key:
            self.update_api_key(dynamic_api_key.strip())

        # 1. Format combined Parent context
        context_blocks = []
        for idx, doc in enumerate(context_docs, start=1):
            pdata = doc.get("parent_data", {})
            full_text = pdata.get("full_text", doc.get("child_text", ""))
            context_blocks.append(f"--- SOURCE DOCUMENT {idx} ---\n{full_text}")

        combined_context = "\n\n".join(context_blocks)

        # 2. Use Gemini LLM if available, else Heuristic Synthesizer
        used_llm = False
        if self.llm_available and self.llm:
            try:
                if agent_type == "article_agent":
                    prompt = ChatPromptTemplate.from_template(ARTICLE_AGENT_PROMPT)
                elif agent_type == "case_law_agent":
                    prompt = ChatPromptTemplate.from_template(CASE_LAW_AGENT_PROMPT)
                else:
                    prompt = ChatPromptTemplate.from_template(EXPLANATION_AGENT_PROMPT)

                chain = prompt | self.llm | StrOutputParser()
                response_text = chain.invoke({
                    "context": combined_context,
                    "query": query
                })
                used_llm = True
            except Exception as e:
                print(f"[AGENTS] Google Gemini invocation error: {e}. Using fallback synthesizer.")
                response_text = HeuristicLegalSynthesizer.synthesize(agent_type, query, context_docs, entities)
        else:
            response_text = HeuristicLegalSynthesizer.synthesize(agent_type, query, context_docs, entities)

        agent_names = {
            "article_agent": "Article Agent (Constitutional Text & Amendments)",
            "case_law_agent": "Case-Law Agent (SC Judgments & Precedents)",
            "explanation_agent": "Explanation Agent (Plain Language Simplifier)"
        }

        return {
            "agent_type": agent_type,
            "agent_name": agent_names.get(agent_type, "Legal AI Agent"),
            "response": response_text,
            "query": query,
            "entities": entities,
            "source_docs": context_docs,
            "used_llm": used_llm,
            "model_name": self.model if used_llm else "Offline Legal Synthesis Engine"
        }



if __name__ == "__main__":
    router = MultiAgentRouter()
    mock_entities = {"articles": ["Article 21"], "cases": ["Puttaswamy"], "concepts": ["privacy"]}
    mock_docs = [{
        "child_id": "child_1",
        "child_text": "Right to privacy is fundamental under Article 21.",
        "parent_data": {
            "doc_type": "judgment",
            "case_name": "Justice K.S. Puttaswamy v. Union of India",
            "citation": "(2017) 10 SCC 1",
            "year": 2017,
            "bench": "9-Judge Bench",
            "articles_referred": ["Article 21"],
            "facts": "Challenge to Aadhaar biometric scheme.",
            "ratio_decidendi": "Privacy is an intrinsic part of life and personal liberty under Article 21.",
            "verdict": "Unanimously held privacy as a fundamental right.",
            "key_takeaways": ["Paved way for data protection laws."]
        }
    }]
    res = router.execute_agent("case_law_agent", "Explain Puttaswamy case on privacy", mock_docs, mock_entities)
    print(f"\n--- {res['agent_name']} RESPONSE ---")
    print(res["response"])
