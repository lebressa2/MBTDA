"""
Memory Manager for the Agent Framework.
"""

from collections import deque
from datetime import datetime
from typing import Any

from ..interfaces.base import IMemoryManager


class InMemoryManager(IMemoryManager):
    """In-memory implementation of memory management."""

    def __init__(self, short_term_limit: int = 50):
        self._short_term: deque = deque(maxlen=short_term_limit)
        self._long_term: dict[str, Any] = {}

    def add_message(self, role: str, content: str, metadata: dict | None = None) -> None:
        self._short_term.append({
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        })

    def get_recent_messages(self, limit: int = 10) -> list[dict[str, Any]]:
        return list(self._short_term)[-limit:]

    def store_long_term(self, key: str, value: Any, metadata: dict | None = None) -> None:
        self._long_term[key] = {
            "value": value,
            "metadata": metadata or {},
            "stored_at": datetime.now().isoformat()
        }

    def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        # Simple keyword matching
        query_lower = query.lower()
        results = []
        for key, data in self._long_term.items():
            if query_lower in key.lower() or query_lower in str(data.get("value", "")).lower():
                results.append({"key": key, **data})
        return results[:top_k]

    def clear_short_term(self) -> None:
        self._short_term.clear()

    def get_memory_context(self) -> dict[str, Any]:
        return {
            "recent_messages": self.get_recent_messages(5),
            "long_term_keys": list(self._long_term.keys())[:10]
        }
