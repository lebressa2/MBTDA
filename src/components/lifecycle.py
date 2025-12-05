"""
LifeCycle Manager for the Agent Framework.
"""

import time
from collections import deque
from typing import Any

from ..interfaces.base import ILifeCycle


class LifeCycleManager(ILifeCycle):
    """Manages token counting, rate limits, and resource usage."""

    def __init__(self):
        self._token_usage = {"input": 0, "output": 0, "total": 0}
        self._request_history: deque = deque(maxlen=1000)
        self._limits = {
            "max_tokens_per_request": 4096,
            "max_total_tokens": 100000,
            "requests_per_minute": 60,
            "max_memory_mb": 1024
        }
        self._errors: list = []

    def count_tokens(self, text: str) -> int:
        # Simple estimation: ~4 chars per token
        return len(text) // 4

    def get_token_usage(self) -> dict[str, int]:
        return dict(self._token_usage)

    def check_rate_limit(self) -> bool:
        now = time.time()
        minute_ago = now - 60
        recent = sum(1 for t, _ in self._request_history if t > minute_ago)
        return recent < self._limits["requests_per_minute"]

    def record_request(self, tokens_used: int) -> None:
        self._token_usage["total"] += tokens_used
        self._request_history.append((time.time(), tokens_used))

    def get_resource_usage(self) -> dict[str, Any]:
        try:
            import psutil
            process = psutil.Process()
            return {
                "memory_mb": process.memory_info().rss / (1024 * 1024),
                "cpu_percent": process.cpu_percent()
            }
        except ImportError:
            return {"memory_mb": 0, "cpu_percent": 0}

    def set_limits(self, **limits) -> None:
        self._limits.update(limits)

    def check_guardrails(self) -> dict[str, bool]:
        return {
            "tokens_ok": self._token_usage["total"] < self._limits["max_total_tokens"],
            "rate_ok": self.check_rate_limit(),
            "memory_ok": self.get_resource_usage().get("memory_mb", 0) < self._limits["max_memory_mb"]
        }

    def handle_api_error(self, error: Exception) -> bool:
        self._errors.append({"error": str(error), "time": time.time()})
        # Retry on rate limit errors
        if "rate" in str(error).lower():
            time.sleep(1)
            return True
        return False
