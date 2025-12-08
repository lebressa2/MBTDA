"""
Clients Module.

This module exposes the client adapters for various services and LLM providers.
It uses lazy loading to avoid ImportErrors for optional dependencies.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .llm.groq_client import GroqClient
    from .llm.google_client import GoogleClient
    from .inbox.mock_client import MockInboxClient
    from .tasks.mock_client import MockTaskClient

def __getattr__(name: str) -> Any:
    """Lazy load clients."""
    if name == "GroqClient":
        try:
            from .llm.groq_client import GroqClient
            return GroqClient
        except ImportError as e:
            raise ImportError(f"Failed to import GroqClient: {e}")
            
    if name == "GoogleClient":
        try:
            from .llm.google_client import GoogleClient
            return GoogleClient
        except ImportError as e:
            raise ImportError(f"Failed to import GoogleClient: {e}")
            
    if name == "MockInboxClient":
        from .inbox.mock_client import MockInboxClient
        return MockInboxClient
        
    if name == "MockTaskClient":
        from .tasks.mock_client import MockTaskClient
        return MockTaskClient
        
    raise AttributeError(f"module {__name__} has no attribute {name}")
