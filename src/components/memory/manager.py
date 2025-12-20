"""
Atomic Memory Manager (Primitive Provider).

Provides context shards for history and tools for long-term storage.
"""

from collections import deque
from datetime import datetime
from typing import Any, List, Dict
from pydantic import BaseModel, Field

from src.models.data_models import Tool
from src.interfaces.memory import IMemoryManager

# ==============================================================================
# TOOL ARGUMENT SCHEMAS
# ==============================================================================

class StoreMemoryArgs(BaseModel):
    key: str = Field(..., description="Key to identify the memory")
    value: str = Field(..., description="Content to remember")

# ==============================================================================
# MEMORY MANAGER
# ==============================================================================

class InMemoryManager(IMemoryManager):
    """
    Atomic memory component. 
    Provides history as context shards and search as tools.
    """

    def __init__(self, short_term_limit: int = 50):
        self._short_term: deque = deque(maxlen=short_term_limit)
        self._long_term: Dict[str, Any] = {}

    def add_message(self, role: str, content: str, metadata: dict | None = None) -> None:
        self._short_term.append({
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        })

    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        return list(self._short_term)[-limit:]

    # --- Primitive Provider Implementation ---

    def get_context_shard(self, limit: int = 10) -> Dict[str, Any]:
        """
        Returns a context shard (knowledge primitive) containing recent history.
        """
        messages = self.get_recent_messages(limit)
        return {
            "conversation_history": [
                f"[{msg['timestamp']}] {msg['role'].upper()}: {msg['content']}"
                for msg in messages
            ]
        }

    def store_long_term(self, key: str, value: Any) -> bool:
        """Atomic operation to store data."""
        self._long_term[key] = {
            "value": value,
            "stored_at": datetime.now().isoformat()
        }
        return True

    def get_tools(self) -> List[Tool]:
        """Provides memory capabilities as Tool Shards."""
        return [
            Tool(
                name="remember",
                description="Save important information to long-term memory for later retrieval.",
                args_schema=StoreMemoryArgs,
                func=self.store_long_term
            )
        ]

    # Interface compatibility
    def clear_short_term(self) -> None:
        self._short_term.clear()

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        return [] # Placeholder