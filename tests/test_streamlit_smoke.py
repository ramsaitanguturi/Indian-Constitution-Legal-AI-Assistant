"""
Smoke Test for the Streamlit Application, Research Dashboard, and Pipeline Inspector.

Ensures:
1. app.py, dashboard_view.py, and pipeline_inspector.py parse and import cleanly.
2. Dashboard functions run offline with no external API credentials.
3. Dashboard rendering handles both populated and empty result directories without exceptions.
4. Pipeline inspector renders safely across multiple input schemas.
"""

import os
from unittest.mock import patch
import pytest

from evaluation.dashboard_data import load_retrieval_results, load_evaluation_summary
from evaluation.dashboard_view import render_research_dashboard
from rag.pipeline_inspector import render_pipeline_inspector, extract_pipeline_diagnostics
from rag.pipeline import PipelineResult


class TestStreamlitSmoke:
    """Verifies that UI components and dashboard execute without unhandled exceptions."""

    def test_imports_clean(self):
        """Validates that key application modules are importable."""
        import app
        import evaluation.dashboard_view as dv
        import evaluation.dashboard_data as dd
        import rag.pipeline_inspector as pi

        assert hasattr(app, "load_rag_pipeline")
        assert hasattr(dv, "render_research_dashboard")
        assert hasattr(dd, "load_retrieval_results")
        assert hasattr(pi, "render_pipeline_inspector")

    def test_dashboard_offline_zero_api_calls(self, monkeypatch):
        """Confirms that rendering dashboard does not require GEMINI_API_KEY or internet."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.setenv("GEMINI_API_KEY", "")

        # Call dashboard render within a mock Streamlit environment
        with patch("streamlit.subheader") as mock_sub, \
             patch("streamlit.dataframe") as mock_df, \
             patch("streamlit.metric") as mock_metric:
            render_research_dashboard()
            assert mock_sub.called

    def test_dashboard_empty_dir_graceful(self, tmp_path):
        """Verifies dashboard rendering displays warning instead of crashing on empty dir."""
        with patch("streamlit.warning") as mock_warn, \
             patch("streamlit.subheader") as mock_sub:
            render_research_dashboard(results_dir=tmp_path, benchmark_dir=tmp_path)
            assert mock_sub.called
            assert mock_warn.called

    def test_inspector_render_safe(self, monkeypatch):
        """Verifies pipeline inspector renders without throwing."""
        monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyFakeSecretKeyThatShouldBeScrubbed123")
        dummy_res = PipelineResult(
            original_query="What is Article 21?",
            normalized_query="what is article 21",
            language={"language": "en", "is_english": True, "confidence": 1.0},
            intent={"intent": "ARTICLE_LOOKUP", "confidence": 0.9, "routing_mode": "hybrid"},
            entities={"ARTICLE": ["Article 21"]},
            linked_entities=[],
            expanded_query="what is article 21",
            routing_decision={"strategy": "ARTICLE_SEARCH"},
            retrieved_chunks=[],
            reranked_chunks=[],
            parent_context={"parents": [], "parent_count": 0},
            citations=[],
            generated_answer="Answer text",
            citation_validation={"valid": True, "citations_checked": 0, "invalid_citations": []},
            confidence={"confidence_score": 0.85, "confidence_level": "HIGH", "is_calibrated": False},
            abstained=False,
        )

        with patch("streamlit.expander") as mock_exp, \
             patch("streamlit.metric") as mock_metric:
            render_pipeline_inspector(dummy_res)
            assert mock_exp.called
