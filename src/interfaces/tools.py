from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional

class IToolManager(ABC):
    """
    Interface for tool management.
    """
    @abstractmethod
    def register_tool(self, context: str, tool: Any) -> None:
        """Register a tool within a specific context."""
        pass

    @abstractmethod
    def get_tools(self, contexts: List[str] | None = None) -> List[Any]:
        """Get registered tools, optionally filtered by context."""
        pass

    @abstractmethod
    def get_tool_descriptions(self, contexts: List[str] | None = None) -> str:
        """Get formatted descriptions of available tools."""
        pass

    @abstractmethod
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool by name with given arguments."""
        pass
