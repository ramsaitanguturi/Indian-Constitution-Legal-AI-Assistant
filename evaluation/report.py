"""
Compatibility wrapper exporting ReportGenerator alias for evaluation/report.py.
Maintains adherence to both IMPLEMENTATION_PLAN.md and evaluation/ spec naming.
"""

from evaluation.report_generator import ReportGenerator

__all__ = ["ReportGenerator"]
