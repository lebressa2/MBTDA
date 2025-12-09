"""
Knowledge Base components for the Agent Framework.

Provides implementations of IKnowledgeBase for semantic storage and retrieval.
"""

from .chroma_kb import ChromaKnowledgeBase

__all__ = [
    "ChromaKnowledgeBase",
]
