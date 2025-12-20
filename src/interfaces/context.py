from abc import ABC, abstractmethod
from typing import Any

class IFormatter(ABC):
    """
    Interface for context formatters.
    """
    @abstractmethod
    def format(self, context: dict[str, Any]) -> str:
        """Format the context dictionary into a string."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the formatter."""
        pass
