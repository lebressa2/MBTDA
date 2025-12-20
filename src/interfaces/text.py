from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional

class ITextClient(ABC):
    """
    Interface for text generation providers (LLMs).
    """
    @abstractmethod
    def invoke(self, messages: List[Dict[str, str]], **kwargs) -> Any:
        """Send a list of messages to the LLM and get a response."""
        pass

    @abstractmethod
    async def ainvoke(self, messages: List[Dict[str, str]], **kwargs) -> Any:
        """Async version of invoke."""
        pass
