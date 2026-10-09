"""
Compatibility wrapper exporting QAEvaluator alias for RAGEvaluator.
Maintains adherence to both IMPLEMENTATION_PLAN.md and evaluation/ spec naming.
"""

from evaluation.rag_eval import RAGEvaluator

# Alias for backwards compatibility with plan
QAEvaluator = RAGEvaluator

__all__ = ["QAEvaluator", "RAGEvaluator"]
