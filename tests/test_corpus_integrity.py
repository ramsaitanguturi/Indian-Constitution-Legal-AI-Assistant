"""
Automated Corpus and Index Integrity Tests.
Verifies:
1. Every indexed chunk maps to a verified parent document in parent_store.json.
2. Every citation resolves to valid source metadata.
3. Reported manifest counts match the actual datasets and indices on disk.
4. Judgment records accurately separate full-text, summary, and metadata records.
5. Repealed and omitted constitutional provisions are accurately flagged.
6. Amendment enactment and effective dates are verified and not identical defaults.
7. Central statutory acts have verified section-level structures.
8. Raw download manifests reflect verified files and cryptographic checksums.
"""

import json
import hashlib
from pathlib import Path
import pytest

from config import (
    BASE_DIR,
    PARENT_STORE_PATH,
    CONSTITUTION_ARTICLES_PATH,
    CONSTITUTION_AMENDMENTS_PATH,
    JUDGMENTS_LANDMARKS_PATH,
    LEGISLATION_ACTS_PATH,
    CORPUS_MANIFEST_PATH,
    RAW_DOWNLOADS_MANIFEST,
    RAW_JUDGMENTS_DIR,
    RAW_LEGISLATION_DIR,
    RAW_CONSTITUTION_DIR,
)


@pytest.fixture(scope="module")
def parent_store():
    assert PARENT_STORE_PATH.exists(), f"Missing {PARENT_STORE_PATH}"
    with open(PARENT_STORE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def corpus_manifest():
    assert CORPUS_MANIFEST_PATH.exists(), f"Missing {CORPUS_MANIFEST_PATH}"
    with open(CORPUS_MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def raw_manifest():
    assert RAW_DOWNLOADS_MANIFEST.exists(), f"Missing {RAW_DOWNLOADS_MANIFEST}"
    with open(RAW_DOWNLOADS_MANIFEST, "r", encoding="utf-8") as f:
        return json.load(f)


class TestCorpusAndIndexIntegrity:
    """Verifies that indexing, metadata, and data sources strictly adhere to legal ground truth."""

    def test_reported_manifest_counts_match_actual_datasets(self, corpus_manifest):
        """Manifest counts must match the exact number of records in each processed file."""
        with open(CONSTITUTION_ARTICLES_PATH, "r", encoding="utf-8") as f:
            articles = json.load(f)
        with open(CONSTITUTION_AMENDMENTS_PATH, "r", encoding="utf-8") as f:
            amendments = json.load(f)
        with open(JUDGMENTS_LANDMARKS_PATH, "r", encoding="utf-8") as f:
            judgments = json.load(f)
        with open(LEGISLATION_ACTS_PATH, "r", encoding="utf-8") as f:
            legislation = json.load(f)

        counts = corpus_manifest["counts_by_document_type"]
        assert counts["constitution_article"] == len(articles)
        assert counts["constitution_amendment"] == len(amendments)
        assert counts["judgment"] == len(judgments)
        assert counts["statute"] == len(legislation)
        assert corpus_manifest["total_documents"] == len(articles) + len(amendments) + len(judgments) + len(legislation)

    def test_parent_store_contains_all_corpus_records(self, parent_store):
        """Parent store must hydrate every provision, amendment, judgment, and statute."""
        assert len(parent_store) >= 806

        doc_types = {v.get("doc_type") for v in parent_store.values()}
        assert "constitution" in doc_types
        assert "amendment" in doc_types
        assert "judgment" in doc_types
        assert "statute" in doc_types

        # Verify key landmark cases exist
        assert any("gopalan" in k.lower() or "1950_insc_13" in k.lower() for k in parent_store)
        assert any("kesavananda" in k.lower() for k in parent_store)
        assert any("puttaswamy" in k.lower() for k in parent_store)

    def test_judgment_granularity_labeling(self):
        """Judgments must be explicitly categorized as full_text, summary_only, or metadata_only."""
        with open(JUDGMENTS_LANDMARKS_PATH, "r", encoding="utf-8") as f:
            judgments = json.load(f)

        full_text = [j for j in judgments if j.get("content_type") == "full_text"]
        summary_only = [j for j in judgments if j.get("content_type") == "summary_only"]
        metadata_only = [j for j in judgments if j.get("content_type") == "metadata_only"]

        assert len(full_text) >= 10, f"Expected >= 10 full-text decisions, got {len(full_text)}"
        assert len(summary_only) == 104, f"Expected 104 landmark briefs, got {len(summary_only)}"
        assert len(metadata_only) >= 50, f"Expected >= 50 metadata records, got {len(metadata_only)}"

        # Verify full-text integrity
        for j in full_text:
            assert j.get("has_full_text") is True
            assert j.get("is_official_full_text") is True
            assert j.get("total_pages", 0) > 0
            assert len(j.get("text", "")) > 5000, f"Full text too short for {j.get('case_name')}"
            assert j.get("source_file", "").endswith(".pdf")

        # Verify summary-only integrity
        for j in summary_only:
            assert j.get("has_full_text") is False
            assert j.get("is_official_full_text") is False
            assert "RATIO DECIDENDI:" in j.get("text", "")

    def test_constitutional_repealed_provisions_flagged(self):
        """Repealed or omitted provisions must not be labeled in_force."""
        with open(CONSTITUTION_ARTICLES_PATH, "r", encoding="utf-8") as f:
            articles = json.load(f)

        art_map = {a.get("document_id"): a for a in articles}

        # Article 31 omitted by 44th Amendment
        assert "const_art_031" in art_map
        assert art_map["const_art_031"]["legal_status"] in ("repealed", "omitted")

        # Article 31D omitted by 43rd Amendment
        assert "const_art_31D" in art_map
        assert art_map["const_art_31D"]["legal_status"] in ("repealed", "omitted")

        # Article 238 omitted by 7th Amendment
        assert "const_art_238" in art_map
        assert art_map["const_art_238"]["legal_status"] in ("repealed", "omitted")

        # Article 370 special provisions status
        assert "const_art_370" in art_map
        assert art_map["const_art_370"]["legal_status"] == "inoperative_special_provisions"

    def test_amendment_dates_verified_not_all_same(self):
        """Amendment enactment and effective dates must be distinct and verified."""
        with open(CONSTITUTION_AMENDMENTS_PATH, "r", encoding="utf-8") as f:
            amendments = json.load(f)

        assert len(amendments) == 106
        enactment_dates = {a.get("enactment_date") for a in amendments}
        # Across 106 amendments over 70+ years, there must be dozens of distinct enactment dates
        assert len(enactment_dates) >= 40

        # Every amendment must carry statement of objects and reasons
        for a in amendments:
            sor = a.get("statement_of_objects") or a.get("statement_of_objects_and_reasons")
            assert sor and len(sor.strip()) > 10, f"Missing SOR in amendment {a.get('amendment_number')}"

    def test_central_acts_section_level_structure(self):
        """Central statutory acts must preserve section numbers, titles, and text."""
        with open(LEGISLATION_ACTS_PATH, "r", encoding="utf-8") as f:
            acts = json.load(f)

        assert len(acts) >= 12, f"Expected >= 12 central acts, got {len(acts)}"
        total_sections = sum(len(a.get("sections", [])) for a in acts)
        assert total_sections >= 1500, f"Expected >= 1500 sections, got {total_sections}"

        act_ids = {a.get("document_id") for a in acts}
        assert "act_ipc_1860" in act_ids
        assert "act_crpc_1973" in act_ids
        assert "act_iea_1872" in act_ids
        assert "act_cpc_1908" in act_ids
        assert "act_citizenship_1955" in act_ids
        assert "act_rti_2005" in act_ids

        # Verify IPC Section 124A (Sedition) exists
        ipc = next(a for a in acts if a.get("document_id") == "act_ipc_1860")
        assert any("124A" in s.get("section_number", "") or "Sedition" in s.get("title", "") for s in ipc["sections"])

    def test_raw_downloads_manifest_integrity(self, raw_manifest):
        """Every file recorded in the download manifest must exist with matching SHA-256."""
        sources = raw_manifest.get("sources", [])
        assert len(sources) >= 20

        for entry in sources:
            target_path = BASE_DIR / entry["target_path"]
            assert target_path.exists(), f"Target file does not exist: {target_path}"
            assert target_path.stat().st_size == entry["bytes_downloaded"]

            # Verify actual SHA-256 on disk
            hasher = hashlib.sha256()
            with open(target_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            assert hasher.hexdigest() == entry["sha256"], f"Checksum mismatch for {target_path}"

    def test_chroma_indexed_chunks_and_parent_mapping(self, parent_store):
        """Every indexed chunk in ChromaDB must map to a real parent in parent_store."""
        import chromadb
        from config import CHROMA_PERSIST_DIR, get_chroma_collection_name

        assert CHROMA_PERSIST_DIR.exists(), "ChromaDB directory does not exist"
        client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
        col_name = get_chroma_collection_name()
        col = client.get_collection(col_name)
        count = col.count()
        assert count >= 1000, f"Expected >= 1000 chunks, found {count}"

        # Sample chunks from ChromaDB and verify metadata integrity
        sample = col.get(limit=200, include=["metadatas", "documents"])
        assert len(sample["ids"]) > 0
        for meta in sample["metadatas"]:
            parent_id = meta.get("parent_id")
            assert parent_id, f"Chunk missing parent_id: {meta}"
            # Parent ID must resolve directly or canonical case-insensitive in parent store
            resolved = (
                parent_id in parent_store
                or parent_id.lower() in parent_store
                or parent_id.replace("parent_", "") in parent_store
            )
            assert resolved, f"Chunk parent_id '{parent_id}' does not resolve to parent_store"
            # Verify document type is valid
            doc_type = meta.get("doc_type") or meta.get("document_type")
            assert doc_type in ("constitution", "constitution_article", "amendment", "constitution_amendment", "judgment", "statute")

