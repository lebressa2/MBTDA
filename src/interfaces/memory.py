from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional

class IMemoryManager(ABC):
    """
    Interface for memory management.
    """
    @abstractmethod
    def add_message(self, role: str, content: str, metadata: Dict | None = None) -> None:
        """Add a message to short-term memory."""
        pass

    @abstractmethod
    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent messages from short-term memory."""
        pass

    @abstractmethod
    def store_long_term(self, key: str, value: Any, metadata: Dict | None = None) -> None:
        """Store information in long-term memory."""
        pass

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant memories based on a query."""
        pass
