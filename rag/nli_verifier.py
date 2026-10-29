"""
Natural Language Inference (NLI) Claim-Level Verification Module.

Decomposes generated legal answers into atomic factual claims, evaluates each
claim against retrieved evidence for:
1. ENTAILMENT (logically and factually supported by retrieved evidence)
2. CONTRADICTION (asserts facts inverted, negated, or contradicted by statutory text)
3. NEUTRAL / INSUFFICIENT_EVIDENCE (claim lacks sufficient grounding in retrieved text)

Operates deterministically without requiring paid external APIs or large downloads,
while supporting optional neural NLI cross-encoders when available.
"""

import re
from typing import Dict, List, Any, Optional, Tuple, Set


# Polarity and modal conflict markers in legal language
POSITIVE_MODALS = {
    "shall", "must", "mandates", "requires", "guarantees", "entitled", "permits",
    "allows", "confers", "empowered", "valid", "constitutional", "upheld", "lawful"
}

NEGATIVE_MODALS = {
    "prohibits", "forbids", "shall not", "cannot", "unconstitutional", "void",
    "struck down", "invalid", "barred", "overruled", "unlawful", "no person shall"
}

CONTRADICTION_PAIRS = [
    (
        r"\b(?:permits?|permitted|allows?|allowed|can|may)\b",
        r"\b(?:prohibits?|prohibited|forbids?|forbidden|cannot|shall not|no person shall|abolished|illegal)\b"
    ),
    (
        r"\b(?:constitutional|valid|upheld|lawful)\b",
        r"\b(?:unconstitutional|invalid|void|struck down|unlawful|null and void)\b"
    ),
    (
        r"\b(?:unanimous|unanimously)\b",
        r"\b(?:dissent|split|majority\s+(?:of\s+)?(?:4:3|5:4|6:5|7:6))\b"
    ),
    (
        r"\b(?:absolute|unrestricted)\b",
        r"\b(?:reasonable\s+restrictions?|subject\s+to|not\s+absolute)\b"
    ),
]


LEGAL_GENERIC_STOPWORDS = {
    "shall", "article", "articles", "right", "rights", "state", "states",
    "constitution", "constitutional", "under", "which", "their", "clause",
    "part", "with", "from", "that", "this", "have", "been", "person",
    "persons", "laws", "court", "courts", "india", "indian", "also", "into",
    "such", "than", "other", "some", "only", "then", "more", "most", "each",
    "were", "when", "what", "where", "case", "cases", "holding", "order",
    "acts", "held", "title", "text", "category", "provision", "provisions",
    "within", "about", "there", "these", "those",
    # Generic procedural terms that occur universally across legal statutes
    "police", "officer", "section", "sections", "power", "powers", "code",
    "procedure", "criminal", "general", "matter", "matters", "public",
    "proceedings", "offence", "offences", "action", "rules"
}


class NLIVerifier:
    """
    Claim-level Natural Language Inference and Evidence Grounding Verifier.
    Evaluates individual propositions against retrieved evidence context.
    """

    def __init__(
        self,
        entailment_threshold: float = 0.60,
        contradiction_threshold: float = 0.50,
        use_neural_model: bool = False,
        model_name: Optional[str] = None
    ):
        self.entailment_threshold = entailment_threshold
        self.contradiction_threshold = contradiction_threshold
        self.use_neural_model = use_neural_model
        self.model_name = model_name or "cross-encoder/nli-deberta-v3-small"
        self._model = None

        if self.use_neural_model:
            self._init_neural_model()

    def _init_neural_model(self) -> None:
        """Attempts to load a local CrossEncoder for NLI if available in cache."""
        try:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self.model_name, num_labels=3)
        except Exception:
            self._model = None
            self.use_neural_model = False

    @staticmethod
    def split_into_claims(answer_text: str) -> List[str]:
        """
        Decomposes generated answer into atomic factual sentences,
        stripping markdown artifacts, section headers, and citation tags.
        """
        if not answer_text or not answer_text.strip():
            return []

        # Remove citation tags like [Doc: parent_const_art_021]
        cleaned = re.sub(r"\[Doc:\s*[^\]]+\]", "", answer_text)

        # Remove markdown headers and emphasis
        cleaned = re.sub(r"^#{1,6}\s+.*$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"^\d+\.\s+\*\*[^*]+\*\*:\s*$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", cleaned)

        # Protect common legal abbreviations with periods from sentence splitting
        cleaned = re.sub(r"\b([vV])\.\s+(?=[A-Z])", r"\1_DOT_ ", cleaned)
        cleaned = re.sub(r"\b([nN]o)\.\s+(?=[0-9A-Z])", r"\1_DOT_ ", cleaned)
        cleaned = re.sub(r"\b([aA]rt)\.\s+(?=[0-9A-Z])", r"\1_DOT_ ", cleaned)
        cleaned = re.sub(r"\b([sS]ec)\.\s+(?=[0-9A-Z])", r"\1_DOT_ ", cleaned)

        # Split on sentence boundaries (avoiding splits on initials like 'B. R. Ambedkar' or 'Art. 21')
        raw_sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", cleaned)

        claims = []
        for s in raw_sentences:
            s_clean = s.replace("_DOT_", ".").strip()
            # Remove leading bullet points or numbers
            s_clean = re.sub(r"^[-*•\d\.\)]+\s*", "", s_clean).strip()

            # Filter out boilerplate phrases or headers
            if len(s_clean) < 15:
                continue
            if s_clean.lower().startswith(("here is", "in summary", "the following", "context notice")):
                continue
            if s_clean.endswith(":"):
                continue

            claims.append(s_clean)

        return claims

    def _detect_polarity_contradiction(self, claim: str, evidence: str) -> Tuple[bool, float, str]:
        """
        Checks whether claim directly contradicts evidence through polarity inversion
        or diametrical antonym clashes on the same legal subject.
        Excludes generic legal stop-words so that unrelated statutory clauses
        are not conflated.
        """
        claim_lower = claim.lower()
        evidence_lower = evidence.lower()

        for pos_pat, neg_pat in CONTRADICTION_PAIRS:
            # Case 1: Claim asserts positive, evidence asserts negative
            # Polarity clash requires claim to assert positive without negative,
            # and evidence to assert negative without affirming the positive on that proposition.
            if re.search(pos_pat, claim_lower) and not re.search(neg_pat, claim_lower):
                if re.search(neg_pat, evidence_lower) and not re.search(pos_pat, evidence_lower):
                    claim_tokens = set(re.findall(r"\b[a-zA-Z]{4,}\b", claim_lower)) - LEGAL_GENERIC_STOPWORDS
                    ev_tokens = set(re.findall(r"\b[a-zA-Z]{4,}\b", evidence_lower)) - LEGAL_GENERIC_STOPWORDS
                    overlap = claim_tokens.intersection(ev_tokens)
                    if len(overlap) >= 2:
                        return True, 0.90, f"Polarity conflict: claim asserts permission/validity whereas evidence asserts prohibition/invalidation (overlap: {overlap})"

            # Case 2: Claim asserts negative, evidence asserts positive
            if re.search(neg_pat, claim_lower) and not re.search(pos_pat, claim_lower):
                if re.search(pos_pat, evidence_lower) and not re.search(neg_pat, evidence_lower):
                    claim_tokens = set(re.findall(r"\b[a-zA-Z]{4,}\b", claim_lower)) - LEGAL_GENERIC_STOPWORDS
                    ev_tokens = set(re.findall(r"\b[a-zA-Z]{4,}\b", evidence_lower)) - LEGAL_GENERIC_STOPWORDS
                    overlap = claim_tokens.intersection(ev_tokens)
                    if len(overlap) >= 2:
                        return True, 0.85, f"Polarity conflict: claim asserts prohibition whereas evidence establishes affirmative constitutional protection (overlap: {overlap})"

        return False, 0.0, ""

    def evaluate_claim(self, claim: str, evidence_passages: List[str]) -> Dict[str, Any]:
        """
        Evaluates a single atomic claim against the retrieved evidence corpus.

        Returns:
            Dict containing verdict ('ENTAILMENT', 'CONTRADICTION', 'NEUTRAL'),
            confidence score (0.0 - 1.0), and matching evidence snippet.
        """
        if not evidence_passages:
            return {
                "claim": claim,
                "verdict": "NEUTRAL",
                "confidence": 0.0,
                "matching_evidence": "",
                "reason": "No retrieved evidence provided."
            }

        # If neural model is enabled and loaded, execute cross-encoder scoring
        if self.use_neural_model and self._model:
            try:
                pairs = [[claim, p] for p in evidence_passages]
                scores = self._model.predict(pairs)
                # Typical NLI output: [contradiction, neutral, entailment]
                best_idx = 0
                best_score = -1.0
                best_verdict = "NEUTRAL"
                for idx, score_vec in enumerate(scores):
                    c_prob, n_prob, e_prob = score_vec
                    if e_prob > best_score and e_prob > self.entailment_threshold:
                        best_score = float(e_prob)
                        best_verdict = "ENTAILMENT"
                        best_idx = idx
                    elif c_prob > best_score and c_prob > self.contradiction_threshold:
                        best_score = float(c_prob)
                        best_verdict = "CONTRADICTION"
                        best_idx = idx

                return {
                    "claim": claim,
                    "verdict": best_verdict,
                    "confidence": round(best_score if best_score > 0 else 0.5, 4),
                    "matching_evidence": evidence_passages[best_idx][:200],
                    "method": "neural_cross_encoder"
                }
            except Exception:
                pass

        # Deterministic Proposition Polarity & Overlap Analyzer
        claim_words = set(re.findall(r"\b[a-zA-Z0-9]{3,}\b", claim.lower()))
        best_overlap_ratio = 0.0
        best_ev_passage = ""
        is_contradicted = False
        contradiction_reason = ""

        # First pass: identify the most relevant evidence passage
        for ev in evidence_passages:
            ev_lower = ev.lower()
            ev_words = set(re.findall(r"\b[a-zA-Z0-9]{3,}\b", ev_lower))

            if not claim_words:
                continue

            shared = claim_words.intersection(ev_words)
            ratio = len(shared) / len(claim_words)

            if ratio > best_overlap_ratio:
                best_overlap_ratio = ratio
                best_ev_passage = ev

        # Second pass: check for polarity contradiction ONLY on passages with substantial overlap
        if best_overlap_ratio >= 0.30 and best_ev_passage:
            contra, contra_conf, reason = self._detect_polarity_contradiction(claim, best_ev_passage)
            if contra:
                is_contradicted = True
                contradiction_reason = reason

        if is_contradicted:
            return {
                "claim": claim,
                "verdict": "CONTRADICTION",
                "confidence": 0.88,
                "matching_evidence": best_ev_passage[:200],
                "reason": contradiction_reason,
                "method": "proposition_polarity_analysis"
            }

        if best_overlap_ratio >= self.entailment_threshold:
            return {
                "claim": claim,
                "verdict": "ENTAILMENT",
                "confidence": round(min(1.0, best_overlap_ratio), 4),
                "matching_evidence": best_ev_passage[:200],
                "reason": f"Sufficient propositional overlap ({best_overlap_ratio:.1%}) with verified statutory evidence.",
                "method": "proposition_polarity_analysis"
            }

        return {
            "claim": claim,
            "verdict": "NEUTRAL",
            "confidence": round(best_overlap_ratio, 4),
            "matching_evidence": best_ev_passage[:200] if best_ev_passage else "",
            "reason": f"Insufficient evidence: proposition overlap ({best_overlap_ratio:.1%}) below threshold.",
            "method": "proposition_polarity_analysis"
        }

    def verify_answer(
        self,
        answer_text: str,
        recovered_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Decomposes answer into claims and verifies every claim against recovered parent & child evidence.

        Args:
            answer_text: Complete text of generated RAG response.
            recovered_context: Context dictionary from ParentChildRecovery.recover().

        Returns:
            Structured verification report with atomic claims breakdown.
        """
        claims = self.split_into_claims(answer_text)

        # Extract evidence text units
        passages: List[str] = []
        parents = recovered_context.get("parents", [])
        for p in parents:
            if p.get("raw_text"):
                passages.append(p["raw_text"])
            if p.get("text"):
                passages.append(p["text"])
            if p.get("explanation"):
                passages.append(p["explanation"])
            if p.get("ratio_decidendi"):
                passages.append(p["ratio_decidendi"])
            for ch in p.get("supporting_children", []):
                if isinstance(ch, dict) and ch.get("text"):
                    passages.append(ch["text"])

        child_evidence = recovered_context.get("child_evidence", [])
        for ch in child_evidence:
            if isinstance(ch, dict) and ch.get("text"):
                passages.append(ch["text"])

        # If answer is empty or an explicit grounded abstention notice
        ans_lower = answer_text.lower().strip()
        is_explicit_abstention = (
            "insufficient evidence:" in ans_lower
            or "notice of insufficient evidence" in ans_lower
            or "safely withheld" in ans_lower
            or "out of scope" in ans_lower
            or ans_lower.startswith("**notice")
            or ans_lower.startswith("**scope notice")
        )
        if not claims or (is_explicit_abstention and len(claims) <= 2):
            return {
                "nli_status": "VERIFIED_ABSTENTION",
                "total_claims": 0,
                "entailed_claims": 0,
                "contradicted_claims": 0,
                "neutral_claims": 0,
                "entailment_ratio": 1.0,
                "has_contradictions": False,
                "claims_breakdown": [],
                "summary": "System produced a valid grounded abstention or null claim set."
            }

        claim_results = []
        entailed_count = 0
        contradicted_count = 0
        neutral_count = 0

        for claim in claims:
            res = self.evaluate_claim(claim, passages)
            claim_results.append(res)
            if res["verdict"] == "ENTAILMENT":
                entailed_count += 1
            elif res["verdict"] == "CONTRADICTION":
                contradicted_count += 1
            else:
                neutral_count += 1

        total = len(claims)
        entailment_ratio = round(entailed_count / total, 4) if total > 0 else 0.0
        has_contradictions = contradicted_count > 0

        if has_contradictions:
            nli_status = "CONTRADICTED"
        elif entailment_ratio >= 0.60:
            nli_status = "VERIFIED_ENTAILED"
        else:
            nli_status = "PARTIALLY_GROUNDED"

        return {
            "nli_status": nli_status,
            "total_claims": total,
            "entailed_claims": entailed_count,
            "contradicted_claims": contradicted_count,
            "neutral_claims": neutral_count,
            "entailment_ratio": entailment_ratio,
            "has_contradictions": has_contradictions,
            "claims_breakdown": claim_results,
            "summary": f"{entailed_count}/{total} claims entailed, {contradicted_count} contradicted, {neutral_count} ungrounded."
        }


_GLOBAL_NLI_VERIFIER: Optional[NLIVerifier] = None


def get_nli_verifier() -> NLIVerifier:
    """Singleton factory for NLIVerifier."""
    global _GLOBAL_NLI_VERIFIER
    if _GLOBAL_NLI_VERIFIER is None:
        _GLOBAL_NLI_VERIFIER = NLIVerifier()
    return _GLOBAL_NLI_VERIFIER
