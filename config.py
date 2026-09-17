"""
Configuration module for the Indian Constitution Legal AI Assistant.
Centralizes paths, embedding models, vector store settings, BM25 parameters, and RRF settings.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHROMA_PERSIST_DIR = BASE_DIR / "chroma_db"
PARENT_STORE_PATH = BASE_DIR / "parent_store.json"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Datasets
CONSTITUTION_DATA_PATH = DATA_DIR / "sample_constitution.json"
JUDGMENTS_DATA_PATH = DATA_DIR / "sample_judgments.json"

# Vector DB & Embeddings
CHROMA_COLLECTION_NAME = "indian_legal_rag"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Chunking Hyperparameters
PARENT_CHUNK_SIZE = 1200  # characters (~200 words)
PARENT_CHUNK_OVERLAP = 100
CHILD_CHUNK_SIZE = 300    # characters (~50 words)
CHILD_CHUNK_OVERLAP = 50

# BM25 Hyperparameters
BM25_K1 = 1.5
BM25_B = 0.75

# Reciprocal Rank Fusion (RRF) Hyperparameters
RRF_K = 60
DEFAULT_TOP_K = 4

# API Keys & LLM Settings (Google Gemini)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_gemini_api_key() -> str:
    """Retrieve Google Gemini API key from environment, .env, or Streamlit secrets."""
    key = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    if not key:
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                key = st.secrets.get("GEMINI_API_KEY", "") or st.secrets.get("GOOGLE_API_KEY", "")
        except Exception:
            pass
    return key


GEMINI_API_KEY = get_gemini_api_key()
GOOGLE_API_KEY = GEMINI_API_KEY  # Standard alias for Google GenAI SDKs
DEFAULT_LLM_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

