"""
Canonical Data Schema and Validation for the Indian Legal Corpus.
Standardizes metadata fields, types, and document validation across
Constitutional Articles, Amendments, Judgments, and Statutory Legislation.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProvenanceMetadata(BaseModel):
    """Source provenance and document verification metadata."""
    source_url: str = Field(description="Official authoritative or public dataset URL")
    source_name: str = Field(description="Name of the official issuing body or public repository")
    source_file: Optional[str] = Field(default=None, description="Original filename or path in raw archive")
    source_hash: str = Field(description="SHA-256 cryptographic checksum of original raw content")
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="ISO timestamp of acquisition")
    version_date: Optional[str] = Field(default=None, description="Official publication or amendment consolidation date")
    legal_status: str = Field(default="in_force", description="in_force, amended, repealed, superseded, pending")
    license: str = Field(default="Government Open Data License - India (GODL) / Fair Dealing", description="Licensing terms")
    processing_status: str = Field(default="processed", description="raw, processed, failed, indexed")


class ClauseRecord(BaseModel):
    """Individual constitutional clause or statutory sub-section."""
    clause_id: str
    clause_number: str
    text: str


class LegalDocument(BaseModel):
    """
    Standard schema for all documents in the Indian Constitution & Legal Corpus.
    Fields that are unavailable remain null or omitted; no synthetic metadata is fabricated.
    """
    document_id: str = Field(description="Stable deterministic document identifier")
    document_type: str = Field(description="constitution_article, constitution_amendment, judgment, statute")
    title: str = Field(description="Official title of the document or case")
    
    # Judicial Metadata (optional, for judgments)
    court: Optional[str] = None
    case_name: Optional[str] = None
    citation: Optional[str] = None
    neutral_citation: Optional[str] = None
    document_date: Optional[str] = None
    bench: Optional[str] = None
    judges: Optional[List[str]] = None
    
    # Statutory / Constitutional Metadata (optional)
    enactment_date: Optional[str] = None
    effective_date: Optional[str] = None
    jurisdiction: str = "India (Federal/Constitutional)"
    part: Optional[str] = None
    article: Optional[str] = None
    article_number: Optional[str] = None
    clause: Optional[str] = None
    section: Optional[str] = None
    schedule: Optional[str] = None
    amendment_number: Optional[str] = None
    year: Optional[int] = None
    
    # Document Content & Structure
    text: str = Field(description="Authoritative legal text")
    clauses: Optional[List[Dict[str, Any]]] = None
    sections: Optional[List[Dict[str, Any]]] = None
    explanation: Optional[str] = None
    historical_context: Optional[str] = None
    
    # Judgment Specific Sections (optional)
    facts: Optional[str] = None
    questions_of_law: Optional[List[str]] = None
    arguments: Optional[str] = None
    holdings: Optional[str] = None
    ratio_decidendi: Optional[str] = None
    verdict: Optional[str] = None
    key_takeaways: Optional[List[str]] = None
    articles_referred: Optional[List[str]] = None
    acts_referred: Optional[List[str]] = None
    precedents_referred: Optional[List[str]] = None
    
    # Technical & Provenance
    source_url: str
    source_name: str
    source_file: Optional[str] = None
    source_hash: str
    retrieved_at: str
    version_date: Optional[str] = None
    legal_status: str = "in_force"
    language: str = "en"
    page_number: Optional[int] = None
    parent_document_id: Optional[str] = None
    license: str = "Government Open Data License - India (GODL)"
    processing_status: str = "processed"
    provenance: Optional[Dict[str, Any]] = None

    def compute_hash(self) -> str:
        """Calculate SHA-256 checksum of normalized text."""
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()

    def to_parent_dict(self) -> Dict[str, Any]:
        """Convert to parent_store format for backward compatibility with RAG synthesizer."""
        d = self.model_dump(exclude_none=True)
        # Ensure legacy keys exist
        d["id"] = self.document_id
        d["parent_id"] = f"parent_{self.document_id}"
        d["doc_type"] = "constitution" if "constitution" in self.document_type else ("judgment" if self.document_type == "judgment" else "statute")
        d["category"] = d.get("category", self.part or self.document_type)
        return d


def compute_sha256(content: bytes) -> str:
    """Compute SHA-256 hash of byte content."""
    return hashlib.sha256(content).hexdigest()

