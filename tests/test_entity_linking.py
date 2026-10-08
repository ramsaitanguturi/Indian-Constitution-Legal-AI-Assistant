"""
Unit tests for Entity Linking module.
Verifies normalization of surface mentions, abbreviations, and informal aliases
to canonical entity IDs and enriched corpus metadata.
"""

import pytest
from nlp.entity_linking import EntityLinker, get_entity_linker


@pytest.fixture(scope="module")
def linker_instance():
    return get_entity_linker()


class TestArticleLinking:
    """Verifies linking of constitutional articles across different surface variants."""

    @pytest.mark.parametrize("surface_form", [
        "Article 21",
        "Art 21",
        "Art. 21",
        "art. 21",
        "article 21 of the constitution"
    ])
    def test_link_article_21_variants(self, linker_instance, surface_form):
        res = linker_instance.link_entity(surface_form, entity_type="ARTICLE")
        assert res is not None
        assert res["entity_id"] == "ARTICLE_21"
        assert res["canonical_name"] == "Article 21"
        assert res["entity_type"] == "ARTICLE"
        assert "metadata" in res
        assert "title" in res["metadata"]

    def test_link_article_14_and_32(self, linker_instance):
        res_14 = linker_instance.link_entity("Art. 14")
        assert res_14 is not None
        assert res_14["entity_id"] == "ARTICLE_14"

        res_32 = linker_instance.link_entity("Article 32")
        assert res_32 is not None
        assert res_32["entity_id"] == "ARTICLE_32"

    def test_link_preamble(self, linker_instance):
        res = linker_instance.link_entity("Preamble to the Constitution")
        assert res is not None
        assert res["entity_id"] == "PREAMBLE"
        assert res["canonical_name"] == "Preamble"


class TestJudgmentsLinking:
    """Verifies linking of landmark cases from informal aliases to canonical IDs."""

    @pytest.mark.parametrize("alias", [
        "Puttaswamy",
        "Justice K.S. Puttaswamy",
        "Puttaswamy case",
        "Aadhaar case",
        "privacy judgment"
    ])
    def test_link_puttaswamy_variants(self, linker_instance, alias):
        res = linker_instance.link_entity(alias)
        assert res is not None
        assert "PUTTASWAMY" in res["entity_id"]
        assert res["entity_type"] == "CASE"
        assert res["metadata"]["year"] == 2017

    @pytest.mark.parametrize("alias", [
        "Kesavananda Bharati",
        "Kesavananda",
        "basic structure case"
    ])
    def test_link_kesavananda_variants(self, linker_instance, alias):
        res = linker_instance.link_entity(alias)
        assert res is not None
        assert "KESAVANANDA" in res["entity_id"]
        assert res["metadata"]["year"] == 1973

    def test_link_maneka_gandhi(self, linker_instance):
        res = linker_instance.link_entity("Maneka Gandhi")
        assert res is not None
        assert "MANEKA" in res["entity_id"]
        assert res["metadata"]["year"] == 1978

    def test_link_ak_gopalan(self, linker_instance):
        res = linker_instance.link_entity("A.K. Gopalan")
        assert res is not None
        assert "GOPALAN" in res["entity_id"]


class TestAmendmentsAndConceptsLinking:
    """Verifies linking of constitutional amendments and legal doctrines."""

    def test_link_42nd_amendment(self, linker_instance):
        res = linker_instance.link_entity("42nd Amendment")
        assert res is not None
        assert res["entity_id"] == "AMENDMENT_42"
        assert res["entity_type"] == "AMENDMENT"

    def test_link_44th_amendment(self, linker_instance):
        res = linker_instance.link_entity("44th Constitutional Amendment")
        assert res is not None
        assert res["entity_id"] == "AMENDMENT_44"

    def test_link_basic_structure_concept(self, linker_instance):
        res = linker_instance.link_entity("basic structure doctrine")
        assert res is not None
        assert res["entity_id"] == "CONCEPT_BASIC_STRUCTURE"
        assert res["entity_type"] == "LEGAL_CONCEPT"

    def test_link_right_to_privacy(self, linker_instance):
        res = linker_instance.link_entity("right to privacy")
        assert res is not None
        assert res["entity_id"] == "RIGHT_PRIVACY"
        assert res["entity_type"] == "RIGHT"


class TestEntityLinkerQueryPipeline:
    """Verifies end-to-end entity linking from raw queries and unresolvable entities."""

    def test_link_query_end_to_end(self, linker_instance):
        query = "What did Puttaswamy decide about privacy under Article 21?"
        linked = linker_instance.link_query(query)
        assert len(linked) >= 2
        linked_ids = {item["entity_id"] for item in linked}
        assert "ARTICLE_21" in linked_ids
        assert any("PUTTASWAMY" in lid for lid in linked_ids)

    def test_unresolvable_entity(self, linker_instance):
        res = linker_instance.link_entity("completely unknown fictitious entity 12345")
        assert res is None

    def test_empty_string(self, linker_instance):
        assert linker_instance.link_entity("") is None
        assert linker_instance.link_all({}) == []
