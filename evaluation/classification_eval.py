"""
Compatibility wrapper exporting ClassificationEvaluator alias for IntentEvaluator.
Maintains adherence to both IMPLEMENTATION_PLAN.md and evaluation/ spec naming.
"""

from evaluation.intent_eval import IntentEvaluator

# Alias for backwards compatibility with plan
ClassificationEvaluator = IntentEvaluator

__all__ = ["ClassificationEvaluator", "IntentEvaluator"]
