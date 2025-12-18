from abc import ABC, abstractmethod
from typing import Any
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ILogger(ABC):
    """
    Interface for logging.
    """
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        pass

    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        pass

    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """Log an error message."""
        pass

    @abstractmethod
    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message."""
        pass

    @abstractmethod
    def log_thinking(self, thought: str, **kwargs) -> None:
        """Log agent's internal thought process."""
        pass

    @abstractmethod
    def log_tool_call(self, tool_name: str, args: dict, result: Any, **kwargs) -> None:
        """Log a tool execution."""
        pass
