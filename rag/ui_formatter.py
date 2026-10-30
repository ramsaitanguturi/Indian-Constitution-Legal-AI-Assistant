"""
UI Formatter for Indian Constitution Legal AI Assistant.

Provides structured, clean extraction and formatting of Legal RAG Pipeline results:
- Direct Answer
- Relevant Legal Provisions
- Relevant Judgments (when applicable)
- Important Exceptions or Limitations (when applicable)
- Compact Legal Sources & Citations with Excerpts
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class FormattedProvision:
    title: str
    article_or_section: str
    document_id: str
    part: str = ""
    category: str = ""
    scope_and_guarantee: str = ""
    context: str = ""
    excerpt: str = ""
    full_text: str = ""


@dataclass
class FormattedJudgment:
    case_name: str
    citation: str
    year: str
    bench: str
    document_id: str
    ratio_decidendi: str = ""
    verdict: str = ""
    facts: str = ""
    key_principles: List[str] = field(default_factory=list)
    excerpt: str = ""
    full_text: str = ""


@dataclass
class FormattedLegalAnswer:
    is_abstained: bool
    abstention_reason: Optional[str]
    direct_answer: str
    provisions: List[FormattedProvision]
    judgments: List[FormattedJudgment]
    exceptions: List[str]
    citations: List[Dict[str, Any]]
    confidence_level: str
    confidence_score: float
    citations_valid: bool
    citations_checked_count: int
    strategy: str
    intent: str
    language: str
    extracted_entities: Dict[str, List[str]]
    unsupported_claims: List[str] = field(default_factory=list)
    invalid_citations: List[Dict[str, Any]] = field(default_factory=list)


def format_legal_pipeline_result(res: Any) -> FormattedLegalAnswer:
    """
    Transforms a PipelineResult into a structured, presentation-ready FormattedLegalAnswer.
    Guarantees no forced empty sections and clean separation of evidence and synthesis.
    """
    # 1. Abstention handling
    if getattr(res, "abstained", False):
        reason = getattr(res, "abstention_reason", "Out of Scope / Low Relevance")
        answer_text = getattr(res, "generated_answer", "")
        clean_ans = answer_text or (
            "The assistant could not identify verified constitutional or statutory evidence "
            "directly addressing this query. To prevent ungrounded legal assertions, "
            "generation has been safely withheld."
        )
        return FormattedLegalAnswer(
            is_abstained=True,
            abstention_reason=reason,
            direct_answer=clean_ans,
            provisions=[],
            judgments=[],
            exceptions=[],
            citations=[],
            confidence_level="VERY_LOW",
            confidence_score=0.0,
            citations_valid=True,
            citations_checked_count=0,
            strategy=res.routing_decision.get("strategy", "N/A") if hasattr(res, "routing_decision") else "N/A",
            intent=res.intent.get("intent", "N/A") if hasattr(res, "intent") else "N/A",
            language=res.language.get("language", "en").upper() if hasattr(res, "language") else "EN",
            extracted_entities=getattr(res, "entities", {}),
        )

    # 2. Extract context and parents
    parent_context = getattr(res, "parent_context", {})
    parents = parent_context.get("parents", [])
    raw_answer = getattr(res, "generated_answer", "")

    # Parse analysis section from generated answer
    an_match = re.search(r"###\s*⚖️\s*Grounded Legal Analysis(.*?)(?=###\s*📚|$)", raw_answer, re.DOTALL)
    analysis_text = an_match.group(1).strip() if an_match else raw_answer

    # Categorize parents
    const_parents = [p for p in parents if p.get("doc_type") == "constitution"]
    judgment_parents = [p for p in parents if p.get("doc_type") == "judgment"]
    statute_parents = [p for p in parents if p.get("doc_type") not in ("constitution", "judgment")]

    # Check for Executive Legal Summary (e.g., search warrant / procedural queries)
    has_exec = "Executive Legal Summary" in analysis_text

    direct_answer_paragraphs: List[str] = []
    exceptions_list: List[str] = []
    exec_sub_provisions: List[str] = []
    exec_sub_judgments: List[str] = []

    if has_exec:
        exec_match = re.search(
            r"####\s*Executive Legal Summary[^\n]*\n\n(.*?)(?=\n#####|\n####|\Z)",
            analysis_text,
            re.DOTALL,
        )
        if exec_match:
            lead_text = exec_match.group(1).strip()
            # Clean lead text
            direct_answer_paragraphs.append(lead_text)

        # Extract subsections
        sub_blocks = re.findall(
            r"(#####\s*\d+\.\s*[^\n]+)(.*?)(?=\n#####|\n####|\Z)",
            analysis_text,
            re.DOTALL,
        )
        for header, body in sub_blocks:
            clean_hdr = re.sub(r"^#####\s*\d+\.\s*", "", header).strip()
            clean_body = body.strip()
            h_lower = clean_hdr.lower()

            if any(k in h_lower for k in ["emergency", "arrest", "safeguard", "exception", "limitation"]):
                exceptions_list.append(f"**{clean_hdr}**\n\n{clean_body}")
            elif any(k in h_lower for k in ["status", "superseded", "repealed", "transition", "current law"]):
                exceptions_list.append(f"**Legislative Transition & Status**\n\n{clean_body}")
            elif any(k in h_lower for k in ["court", "judgment", "privacy", "kharak", "sharma", "puttaswamy", "doctrine"]):
                exec_sub_judgments.append(f"**{clean_hdr}**\n\n{clean_body}")
            else:
                exec_sub_provisions.append(f"**{clean_hdr}**\n\n{clean_body}")

    # Build Provisions
    provisions: List[FormattedProvision] = []
    for cp in const_parents:
        art_no = cp.get("article_number", "Article")
        title = cp.get("title", "")
        part = cp.get("part", "")
        cat = cp.get("category", "")
        expl = cp.get("explanation", "")
        hist = cp.get("historical_context", "")
        raw_text = cp.get("full_text") or cp.get("raw_text") or ""
        doc_id = cp.get("document_id") or cp.get("parent_id", "")

        # Default excerpt: First supporting child or first 200 chars of raw text
        children = cp.get("supporting_children", [])
        if children and children[0].get("text"):
            excerpt = children[0]["text"].strip()
        elif raw_text:
            excerpt = raw_text.strip()
        else:
            excerpt = expl

        # Trim excerpt cleanly
        if len(excerpt) > 280:
            excerpt = excerpt[:277] + "..."

        provisions.append(FormattedProvision(
            title=f"{art_no}: {title}" if title else art_no,
            article_or_section=art_no,
            document_id=doc_id,
            part=part,
            category=cat,
            scope_and_guarantee=expl,
            context=hist,
            excerpt=excerpt,
            full_text=raw_text,
        ))

    for sp in statute_parents:
        st_title = sp.get("title") or sp.get("document_id", "Statute")
        summary = sp.get("summary", "")
        doc_id = sp.get("document_id") or sp.get("parent_id", "")
        children = sp.get("supporting_children", [])
        excerpt = children[0]["text"].strip() if children and children[0].get("text") else summary
        if len(excerpt) > 280:
            excerpt = excerpt[:277] + "..."
        raw_text = sp.get("full_text") or sp.get("raw_text") or summary

        provisions.append(FormattedProvision(
            title=st_title,
            article_or_section="Statute",
            document_id=doc_id,
            part="",
            category="Legislation",
            scope_and_guarantee=summary,
            context=sp.get("superseded_by", ""),
            excerpt=excerpt,
            full_text=raw_text,
        ))

    # Build Judgments
    judgments: List[FormattedJudgment] = []
    for jp in judgment_parents:
        c_name = jp.get("case_name", "Landmark Case")
        cit = jp.get("citation", "")
        yr = str(jp.get("year", ""))
        bench = jp.get("bench", "")
        ratio = jp.get("ratio_decidendi", "")
        verdict = jp.get("verdict", "")
        facts = jp.get("facts", "")
        takeaways = jp.get("key_takeaways", [])
        doc_id = jp.get("document_id") or jp.get("parent_id", "")
        raw_text = jp.get("full_text") or jp.get("raw_text") or ratio

        children = jp.get("supporting_children", [])
        if ratio:
            excerpt = ratio.strip()
        elif children and children[0].get("text"):
            excerpt = children[0]["text"].strip()
        else:
            excerpt = verdict

        if len(excerpt) > 280:
            excerpt = excerpt[:277] + "..."

        judgments.append(FormattedJudgment(
            case_name=c_name,
            citation=cit,
            year=yr,
            bench=bench,
            document_id=doc_id,
            ratio_decidendi=ratio,
            verdict=verdict,
            facts=facts,
            key_principles=takeaways if isinstance(takeaways, list) else [],
            excerpt=excerpt,
            full_text=raw_text,
        ))

    # Deduce Exceptions and Limitations when applicable
    if not exceptions_list:
        # Check constitutional exceptions in parents
        for cp in const_parents:
            art_no = cp.get("article_number", "Article")
            expl = cp.get("explanation", "").lower()
            if "procedure established by law" in expl or "art. 21" in art_no.lower():
                exceptions_list.append(
                    f"**Procedural Safeguard ({art_no})**: Deprivation of personal liberty is strictly conditional "
                    f"upon 'procedure established by law', which the Supreme Court (*Maneka Gandhi*) requires to be "
                    f"just, fair, and reasonable, not arbitrary or oppressive."
                )
            elif "amend" in art_no.lower() or "368" in art_no:
                exceptions_list.append(
                    "**Basic Structure Limitation**: Parliament's constituent power to amend the Constitution under Article 368 "
                    "is subject to the unamendable Basic Structure Doctrine established in *Kesavananda Bharati*."
                )
            elif "19" in art_no:
                exceptions_list.append(
                    "**Permissible Reasonable Restrictions**: Fundamental freedoms under Article 19 are not absolute "
                    "and are conditioned by reasonable restrictions specified under clauses (2) through (6) in the interests of "
                    "sovereignty, public order, and morality."
                )

        for jp in judgment_parents:
            ratio = jp.get("ratio_decidendi", "")
            c_name = jp.get("case_name", "Precedent")
            if "proportionality" in ratio.lower() or "three-fold" in ratio.lower():
                exceptions_list.append(
                    f"**Judicial Scrutiny Test ({c_name})**: Any state interference with the right must satisfy the "
                    f"three-fold test: (1) Legality (under valid enacted law), (2) Legitimate state aim, and (3) Proportionality."
                )

    # Formulate Direct Answer
    if not direct_answer_paragraphs:
        if judgment_parents and not const_parents:
            primary_case = judgment_parents[0]
            core_rule = primary_case.get("ratio_decidendi") or primary_case.get("verdict") or ""
            direct_answer_paragraphs.append(
                f"In **{primary_case.get('case_name')}** ({primary_case.get('year')}), the Supreme Court ruled:\n\n"
                f"> *\"{core_rule.strip()}\"*"
            )
            if primary_case.get("verdict"):
                direct_answer_paragraphs.append(f"**Verdict**: {primary_case.get('verdict')}")
        elif const_parents and judgment_parents:
            art = const_parents[0].get("article_number", "The Constitution")
            case = judgment_parents[0].get("case_name", "Supreme Court precedents")
            direct_answer_paragraphs.append(
                f"Under **{art}** of the Indian Constitution, as authoritatively interpreted by the Supreme Court in **{case}**, "
                f"{judgment_parents[0].get('ratio_decidendi') or const_parents[0].get('explanation')}"
            )
        elif const_parents:
            art = const_parents[0]
            direct_answer_paragraphs.append(
                f"**{art.get('article_number')}** of the Indian Constitution provides that:\n\n"
                f"> *\"{art.get('raw_text', '').strip() or art.get('explanation', '').strip()}\"*\n\n"
                f"{art.get('explanation', '')}"
            )
        else:
            # Fallback to analysis first paragraph
            clean_lines = [p.strip() for p in analysis_text.split("\n\n") if p.strip() and not p.strip().startswith("#")]
            if clean_lines:
                direct_answer_paragraphs.append(clean_lines[0])
            else:
                direct_answer_paragraphs.append("Refer to the verified legal provisions and judicial authorities detailed below.")

    direct_ans = "\n\n".join(direct_answer_paragraphs)

    # Citation and metadata fields
    conf = getattr(res, "confidence", {})
    conf_lvl = conf.get("confidence_level", "MEDIUM")
    conf_sc = float(conf.get("confidence_score", 0.70))

    cit_val = getattr(res, "citation_validation", {})
    val_ok = bool(cit_val.get("valid", False))
    cit_cnt = int(cit_val.get("citations_checked", len(res.citations) if hasattr(res, "citations") else 0))
    inv_cits = cit_val.get("invalid_citations", [])
    unsupp = cit_val.get("unsupported_claims", [])

    strat = res.routing_decision.get("strategy", "HYBRID_SEARCH") if hasattr(res, "routing_decision") else "HYBRID_SEARCH"
    intent_name = res.intent.get("intent", "LEGAL_QUERY") if hasattr(res, "intent") else "LEGAL_QUERY"
    lang_name = res.language.get("language", "en").upper() if hasattr(res, "language") else "EN"
    ents = getattr(res, "entities", {})

    return FormattedLegalAnswer(
        is_abstained=False,
        abstention_reason=None,
        direct_answer=direct_ans,
        provisions=provisions,
        judgments=judgments,
        exceptions=exceptions_list,
        citations=getattr(res, "citations", []),
        confidence_level=conf_lvl,
        confidence_score=conf_sc,
        citations_valid=val_ok,
        citations_checked_count=cit_cnt,
        strategy=strat,
        intent=intent_name,
        language=lang_name,
        extracted_entities=ents,
        unsupported_claims=unsupp,
        invalid_citations=inv_cits,
    )

