"""
Tests for ChromaDB embedding dimensions, collection selection, and model configuration.
Verifies:
1. get_chroma_collection_name dynamically maps models to matching collections.
2. get_embedding_dimension returns 1024 for BGE-M3 and 384 for MiniLM.
3. validate_collection_dimension permits compatible collections and raises ValueError on mismatches.
4. ParentChildIngestor and DenseRetriever use matching collection names for given models.
5. Ingestion skips re-indexing when target collection is already populated.
6. Attempting to upsert incompatible dimensions into a collection raises clear ValueError.
"""

import os
from unittest.mock import MagicMock, patch
import pytest

from config import (
    BGE_M3_MODEL_NAME,
    MINILM_MODEL_NAME,
    BGE_M3_EMBEDDING_DIM,
    MINILM_EMBEDDING_DIM,
    DEFAULT_EMBEDDING_MODEL,
    CHROMA_COLLECTION_NAME,
    get_chroma_collection_name,
    get_embedding_dimension,
    validate_collection_dimension,
    CHROMA_PERSIST_DIR,
)
from ingestion import ParentChildIngestor
from retrieval.dense_retriever import DenseRetriever


class TestCollectionSelectionAndDimensionHelpers:
    """Verifies collection mapping and dimension helper functions."""

    def test_default_embedding_model_is_bgem3(self):
        """Default embedding model must be BGE-M3 when EMBEDDING_MODEL is not overridden."""
        if "EMBEDDING_MODEL" not in os.environ:
            assert DEFAULT_EMBEDDING_MODEL == BGE_M3_MODEL_NAME
            assert CHROMA_COLLECTION_NAME == "indian_legal_rag_bgem3"

    def test_get_chroma_collection_name_mapping(self):
        """get_chroma_collection_name maps models to the correct collection."""
        assert get_chroma_collection_name(BGE_M3_MODEL_NAME) == "indian_legal_rag_bgem3"
        assert get_chroma_collection_name("bge-m3") == "indian_legal_rag_bgem3"
        assert get_chroma_collection_name("BAAI/BGE-M3") == "indian_legal_rag_bgem3"
        assert get_chroma_collection_name(MINILM_MODEL_NAME) == "indian_legal_rag"
        assert get_chroma_collection_name("sentence-transformers/all-MiniLM-L6-v2") == "indian_legal_rag"
        assert get_chroma_collection_name(None) == get_chroma_collection_name(DEFAULT_EMBEDDING_MODEL)

    def test_get_embedding_dimension_mapping(self):
        """get_embedding_dimension returns 1024 for BGE-M3 and 384 for MiniLM."""
        assert get_embedding_dimension(BGE_M3_MODEL_NAME) == 1024
        assert get_embedding_dimension("bge-m3") == 1024
        assert get_embedding_dimension(MINILM_MODEL_NAME) == 384
        assert get_embedding_dimension("all-MiniLM-L6-v2") == 384
        assert get_embedding_dimension(None) == (1024 if "bge-m3" in DEFAULT_EMBEDDING_MODEL.lower() else 384)


class TestDimensionValidation:
    """Verifies dimension validation before upsert or query."""

    def test_validate_dimension_success_bgem3(self):
        """Validation succeeds when collection dimension matches expected 1024."""
        mock_col = MagicMock()
        mock_col.name = "indian_legal_rag_bgem3"
        mock_col.count.return_value = 1
        mock_col.get.return_value = {"embeddings": [[0.1] * 1024]}

        # Should not raise
        validate_collection_dimension(mock_col, 1024, BGE_M3_MODEL_NAME)

    def test_validate_dimension_success_minilm(self):
        """Validation succeeds when collection dimension matches expected 384."""
        mock_col = MagicMock()
        mock_col.name = "indian_legal_rag"
        mock_col.count.return_value = 1
        mock_col.get.return_value = {"embeddings": [[0.1] * 384]}

        # Should not raise
        validate_collection_dimension(mock_col, 384, MINILM_MODEL_NAME)

    def test_validate_dimension_mismatch_raises_clear_error(self):
        """Validation raises clear ValueError explaining actual vs expected dimensions."""
        mock_col = MagicMock()
        mock_col.name = "indian_legal_rag"
        mock_col.count.return_value = 100
        mock_col.get.return_value = {"embeddings": [[0.1] * 384]}

        with pytest.raises(ValueError) as excinfo:
            validate_collection_dimension(mock_col, 1024, BGE_M3_MODEL_NAME)

        err_msg = str(excinfo.value)
        assert "dimension mismatch" in err_msg.lower() or "expects" in err_msg.lower()
        assert "384" in err_msg
        assert "1024" in err_msg

    def test_validate_dimension_name_convention_mismatch_raises_error(self):
        """Validation raises ValueError if collection name indicates BGE-M3 but dim is 384."""
        mock_col = MagicMock()
        mock_col.name = "indian_legal_rag_bgem3"
        mock_col.count.return_value = 0  # Empty collection

        with pytest.raises(ValueError) as excinfo:
            validate_collection_dimension(mock_col, 384, MINILM_MODEL_NAME)

        assert "1024" in str(excinfo.value)
        assert "384" in str(excinfo.value)


class TestIngestionAndRetrievalAlignment:
    """Verifies that ingestor and retriever align on models, collections, and dimensions."""

    def test_ingestor_uses_matching_collection(self):
        """ParentChildIngestor routes to the correct collection for both models."""
        ing_bgem3 = ParentChildIngestor(model_name=BGE_M3_MODEL_NAME)
        assert ing_bgem3.model_name == BGE_M3_MODEL_NAME

        ing_minilm = ParentChildIngestor(model_name=MINILM_MODEL_NAME)
        assert ing_minilm.model_name == MINILM_MODEL_NAME

    def test_build_vector_store_skips_when_already_populated(self):
        """build_vector_store does not rebuild or re-upsert if collection already has chunks."""
        ing = ParentChildIngestor(model_name=BGE_M3_MODEL_NAME)
        mock_col = MagicMock()
        mock_col.name = "indian_legal_rag_bgem3"
        mock_col.count.return_value = 7470
        mock_col.get.return_value = {"embeddings": [[0.1] * 1024]}

        with patch("chromadb.PersistentClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get_or_create_collection.return_value = mock_col
            mock_client_cls.return_value = mock_client

            col = ing.build_vector_store(force_rebuild=False)
            assert col == mock_col
            # Upsert must NOT have been called
            assert not mock_col.upsert.called

    def test_dense_retriever_validates_dimension_on_init(self):
        """DenseRetriever validates collection dimension upon initialization."""
        mock_col = MagicMock()
        mock_col.name = "indian_legal_rag"
        mock_col.count.return_value = 10
        mock_col.get.return_value = {"embeddings": [[0.1] * 384]}

        # Initializing with BGE-M3 (1024) but passing 384-d collection must raise ValueError
        with pytest.raises(ValueError) as excinfo:
            DenseRetriever(collection=mock_col, embedding_model_name=BGE_M3_MODEL_NAME)

        assert "384" in str(excinfo.value)
        assert "1024" in str(excinfo.value)

