from abc import ABC, abstractmethod
from typing import Any

class ILifeCycle(ABC):
    """
    Interface for agent lifecycle management.
    """
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        pass

    @abstractmethod
    def get_token_usage(self) -> dict[str, int]:
        """Get current token usage."""
        pass

    @abstractmethod
    def check_rate_limit(self) -> bool:
        """Check if rate limits are exceeded."""
        pass

    @abstractmethod
    def record_request(self, tokens_used: int) -> None:
        """Record a request and its token usage."""
        pass

    @abstractmethod
    def get_resource_usage(self) -> dict[str, Any]:
        """Get system resource usage."""
        pass

    @abstractmethod
    def set_limits(self, **limits) -> None:
        """Set usage limits."""
        pass

    @abstractmethod
    def check_guardrails(self) -> dict[str, bool]:
        """Check if guardrails are satisfied."""
        pass

    @abstractmethod
    def handle_api_error(self, error: Exception) -> bool:
        """Handle an API error, returns True if should retry."""
        pass
