"""
Logger Component for the Agent Framework.
"""

from datetime import datetime
from typing import Any

from ..interfaces.base import ILogger, LogLevel


class ConsoleLogger(ILogger):
    """Logger that outputs to console with rich formatting."""

    def __init__(self, name: str = "Agent", min_level: LogLevel = LogLevel.DEBUG):
        self.name = name
        self.min_level = min_level
        self._levels_order = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL]

    def _should_log(self, level: LogLevel) -> bool:
        return self._levels_order.index(level) >= self._levels_order.index(self.min_level)

    def _format_message(self, level: str, message: str) -> str:
        timestamp = datetime.now().strftime("%H:%M:%S")
        return f"[{timestamp}] [{self.name}] [{level}] {message}"

    def debug(self, message: str, **kwargs) -> None:
        if self._should_log(LogLevel.DEBUG):
            print(self._format_message("DEBUG", message))

    def info(self, message: str, **kwargs) -> None:
        if self._should_log(LogLevel.INFO):
            print(self._format_message("INFO", message))

    def warning(self, message: str, **kwargs) -> None:
        if self._should_log(LogLevel.WARNING):
            print(self._format_message("WARNING", message))

    def error(self, message: str, **kwargs) -> None:
        if self._should_log(LogLevel.ERROR):
            print(self._format_message("ERROR", message))

    def critical(self, message: str, **kwargs) -> None:
        if self._should_log(LogLevel.CRITICAL):
            print(self._format_message("CRITICAL", message))

    def log_thinking(self, thought: str, **kwargs) -> None:
        if self._should_log(LogLevel.DEBUG):
            print(f"[💭 THINKING] {thought[:200]}...")

    def log_tool_call(self, tool_name: str, args: dict, result: Any, **kwargs) -> None:
        if self._should_log(LogLevel.INFO):
            print(f"[🔧 TOOL] {tool_name} | Args: {args} | Result: {str(result)[:100]}")


class FileLogger(ILogger):
    """Logger that writes to a file."""

    def __init__(self, filepath: str, name: str = "Agent"):
        self.filepath = filepath
        self.name = name

    def _write(self, level: str, message: str) -> None:
        timestamp = datetime.now().isoformat()
        with open(self.filepath, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp} | {level} | {self.name} | {message}\n")

    def debug(self, message: str, **kwargs) -> None:
        self._write("DEBUG", message)

    def info(self, message: str, **kwargs) -> None:
        self._write("INFO", message)

    def warning(self, message: str, **kwargs) -> None:
        self._write("WARNING", message)

    def error(self, message: str, **kwargs) -> None:
        self._write("ERROR", message)

    def critical(self, message: str, **kwargs) -> None:
        self._write("CRITICAL", message)

    def log_thinking(self, thought: str, **kwargs) -> None:
        self._write("THINKING", thought)

    def log_tool_call(self, tool_name: str, args: dict, result: Any, **kwargs) -> None:
        self._write("TOOL_CALL", f"{tool_name} | {args} | {result}")


class CompositeLogger(ILogger):
    """Logger that delegates to multiple loggers."""

    def __init__(self, loggers: list[ILogger]):
        self.loggers = loggers

    def debug(self, message: str, **kwargs) -> None:
        for logger in self.loggers:
            logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        for logger in self.loggers:
            logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        for logger in self.loggers:
            logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        for logger in self.loggers:
            logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        for logger in self.loggers:
            logger.critical(message, **kwargs)

    def log_thinking(self, thought: str, **kwargs) -> None:
        for logger in self.loggers:
            logger.log_thinking(thought, **kwargs)

    def log_tool_call(self, tool_name: str, args: dict, result: Any, **kwargs) -> None:
        for logger in self.loggers:
            logger.log_tool_call(tool_name, args, result, **kwargs)
