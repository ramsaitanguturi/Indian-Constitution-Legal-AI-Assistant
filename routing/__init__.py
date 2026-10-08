"""
Query Routing Package for Indian Constitution Legal AI Assistant.
Provides deterministic, specialized NLP query routing based on Stage 2 outputs.
"""

from routing.query_router import (
    QueryRouter,
    RoutingDecision,
    get_query_router,
)

__all__ = [
    "QueryRouter",
    "RoutingDecision",
    "get_query_router",
]
