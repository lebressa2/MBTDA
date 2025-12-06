"""
Base Interfaces (Protocols) for the Agent Framework.

This module defines all abstract interfaces that components must implement.
Using Python's Protocol for structural subtyping (duck typing with type safety).
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

# ==============================================================================
# ENUMS
# ==============================================================================

class LogLevel(Enum):
    """Log levels for the ILogger interface."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ==============================================================================
# CONTEXT PROVIDER INTERFACE (Base for context-injecting components)
# ==============================================================================

class IContextProvider(ABC):
    """
    Base interface for components that contribute to the agent's context.
    
    Components implementing this interface can automatically inject their
    context into the agent's system prompt. The Agent will collect all
    contributions and merge them into the final context.
    
    Attributes:
        inject_context: Flag to enable/disable automatic context injection.
                       Defaults to True.
    
    Example:
        class MyComponent(IContextProvider):
            inject_context: bool = True
            
            def get_context_contribution(self) -> dict[str, Any]:
                return {
                    "my_component": {
                        "status": "active",
                        "data": self.get_data()
                    }
                }
    """
    
    # Flag to enable/disable context injection (default: True)
    inject_context: bool = True
    
    @abstractmethod
    def get_context_contribution(self) -> dict[str, Any]:
        """
        Get the context contribution from this component.
        
        Returns a dictionary that will be deep-merged into the agent's
        context. The structure should be designed to avoid key collisions
        with other components.
        
        Returns:
            dict[str, Any]: Context dictionary to be merged
        """
        pass


# ==============================================================================
# CORE INTERFACES
# ==============================================================================

class ITextClient(ABC):
    """
    Interface for text generation clients (LLM providers).

    Implementations can use langchain-groq, langchain-google, or any other
    LangChain-compatible provider. Works with langchain.BaseMessage.
    """

    @abstractmethod
    def invoke(self, messages: list[Any], **kwargs) -> Any:
        """
        Invoke the LLM with a list of messages.

        Args:
            messages: List of BaseMessage objects
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            BaseMessage: The LLM response
        """
        pass

    @abstractmethod
    def bind_tools(self, tools: list[Any]) -> "ITextClient":
        """
        Bind tools to the LLM for function calling.

        Args:
            tools: List of LangChain Tool objects

        Returns:
            ITextClient: A new client instance with tools bound
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the name of the underlying model."""
        pass


class IFormatter(ABC):
    """
    Interface for context formatting.

    Responsible for converting context dictionaries into formatted strings
    suitable for system prompts.
    """

    @abstractmethod
    def format(self, context: dict[str, Any]) -> str:
        """
        Format a context dictionary into a string.

        Args:
            context: Dictionary containing context data

        Returns:
            str: Formatted string representation
        """
        pass


class IMemoryManager(IContextProvider):
    """
    Interface for memory management.

    Handles short-term memory, long-term memory, and retrieval operations.
    Automatically contributes to the agent's context via IContextProvider.
    
    The 'memory' key will be injected into the system prompt containing
    recent messages and long-term memory keys.
    """

    @abstractmethod
    def add_message(self, role: str, content: str, metadata: dict | None = None) -> None:
        """Add a message to short-term memory."""
        pass

    @abstractmethod
    def get_recent_messages(self, limit: int = 10) -> list[dict[str, Any]]:
        """Retrieve recent messages from short-term memory."""
        pass

    @abstractmethod
    def store_long_term(self, key: str, value: Any, metadata: dict | None = None) -> None:
        """Store information in long-term memory."""
        pass

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Retrieve relevant memories based on a query."""
        pass

    @abstractmethod
    def clear_short_term(self) -> None:
        """Clear short-term memory."""
        pass

    # get_context_contribution() is inherited from IContextProvider and must be implemented


class IToolManager(IContextProvider):
    """
    Interface for tool management.

    Handles tool registration, execution, and retrieval.
    Tools are organized by context/category.
    
    Automatically contributes available tools to the agent's context
    via IContextProvider.
    """

    @abstractmethod
    def register_tool(self, context: str, tool: Any) -> None:
        """
        Register a tool under a specific context.

        Args:
            context: Category/context for the tool (e.g., 'retriever_funcs')
            tool: LangChain Tool object
        """
        pass

    @abstractmethod
    def get_tools(self, contexts: list[str] | None = None) -> list[Any]:
        """
        Get tools, optionally filtered by contexts.

        Args:
            contexts: List of contexts to filter by (None = all tools)

        Returns:
            List of Tool objects
        """
        pass

    @abstractmethod
    def get_tool_descriptions(self, contexts: list[str] | None = None) -> str:
        """Get formatted descriptions of available tools."""
        pass

    @abstractmethod
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool by name with given arguments."""
        pass

    # get_context_contribution() is inherited from IContextProvider and must be implemented


class IWatchdog(ABC):
    """
    Interface for watchdog/timer functionality.

    Controls timeouts and polling intervals for reactive mode.
    """

    @abstractmethod
    def start_timer(self, duration_seconds: float) -> None:
        """Start a timer for the specified duration."""
        pass

    @abstractmethod
    def stop_timer(self) -> None:
        """Stop the current timer."""
        pass

    @abstractmethod
    def is_timed_out(self) -> bool:
        """Check if the timer has expired."""
        pass

    @abstractmethod
    def get_poll_interval(self) -> float:
        """Get the polling interval for reactive mode."""
        pass

    @abstractmethod
    def set_poll_interval(self, interval_seconds: float) -> None:
        """Set the polling interval for reactive mode."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset the watchdog timer."""
        pass


class ILogger(ABC):
    """
    Interface for logging.

    Supports various output destinations (terminal, file, subprocess, etc.)
    Must be able to log thinking tokens and tool calls.
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
        """Log agent thinking tokens."""
        pass

    @abstractmethod
    def log_tool_call(self, tool_name: str, args: dict, result: Any, **kwargs) -> None:
        """Log a tool call with arguments and result."""
        pass


class ILifeCycle(ABC):
    """
    Interface for lifecycle and resource management.

    Handles token counting, rate limits, resource usage, API errors,
    message limits, and other guardrails for limited resources.
    """

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        pass

    @abstractmethod
    def get_token_usage(self) -> dict[str, int]:
        """Get current token usage statistics."""
        pass

    @abstractmethod
    def check_rate_limit(self) -> bool:
        """Check if rate limit allows another request."""
        pass

    @abstractmethod
    def record_request(self, tokens_used: int) -> None:
        """Record a request for rate limiting purposes."""
        pass

    @abstractmethod
    def get_resource_usage(self) -> dict[str, Any]:
        """Get current resource usage (memory, GPU, etc.)."""
        pass

    @abstractmethod
    def set_limits(self, **limits) -> None:
        """
        Set resource limits.

        Args:
            **limits: Limit parameters (max_tokens, requests_per_minute, etc.)
        """
        pass

    @abstractmethod
    def check_guardrails(self) -> dict[str, bool]:
        """Check all guardrails and return their status."""
        pass

    @abstractmethod
    def handle_api_error(self, error: Exception) -> bool:
        """
        Handle an API error.

        Returns:
            bool: True if the error was handled and operation can retry
        """
        pass


class IWorkspaceManager(IContextProvider):
    """
    Interface for workspace management.

    Manages the isolated environment (physical or virtual) where the agent works.
    Provides a controlled sandbox for file operations, version control,
    and computational environments.
    
    Automatically contributes workspace information to the agent's context
    via IContextProvider (e.g., base path, available files, operations).
    """

    @abstractmethod
    def create_file(self, path: str, content: str) -> bool:
        """Create a file at the specified path with given content."""
        pass

    @abstractmethod
    def read_file(self, path: str) -> str | None:
        """Read the content of a file."""
        pass

    @abstractmethod
    def update_file(self, path: str, content: str) -> bool:
        """Update the content of an existing file."""
        pass

    @abstractmethod
    def delete_file(self, path: str) -> bool:
        """Delete a file."""
        pass

    @abstractmethod
    def create_directory(self, path: str) -> bool:
        """Create a directory."""
        pass

    @abstractmethod
    def delete_directory(self, path: str, recursive: bool = False) -> bool:
        """Delete a directory."""
        pass

    @abstractmethod
    def list_directory(self, path: str) -> list[str]:
        """List contents of a directory."""
        pass

    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        pass

    @abstractmethod
    def create_snapshot(self, name: str) -> str:
        """Create a version snapshot of the current workspace state."""
        pass

    @abstractmethod
    def restore_snapshot(self, snapshot_id: str) -> bool:
        """Restore workspace to a previous snapshot."""
        pass

    @abstractmethod
    def get_storage_usage(self) -> dict[str, Any]:
        """Get storage usage statistics."""
        pass

    @abstractmethod
    def set_storage_limit(self, limit_bytes: int) -> None:
        """Set the storage limit for the workspace."""
        pass

    @abstractmethod
    def execute_command(self, command: str, timeout: float | None = None) -> dict[str, Any]:
        """Execute a command in the isolated environment."""
        pass

    @abstractmethod
    def get_audit_log(self) -> list[dict[str, Any]]:
        """Get the audit log of all workspace actions."""
        pass

    # get_context_contribution() is inherited from IContextProvider and must be implemented


# ==============================================================================
# MONITORING INTERFACES (Inbox & Tasks)
# ==============================================================================

class IInboxClient(ABC):
    """
    Interface for inbox/email operations.

    Used by the inbox_tool to provide email functionality.
    """

    @abstractmethod
    def check_new_emails(self) -> list[Any]:
        """
        Check for new emails.

        Returns:
            List[EmailMessage]: List of new email messages
        """
        pass

    @abstractmethod
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: list[str] | None = None,
        bcc: list[str] | None = None
    ) -> bool:
        """
        Send an email.

        Returns:
            bool: True if email was sent successfully
        """
        pass

    @abstractmethod
    def mark_as_read(self, thread_id: str) -> bool:
        """Mark an email thread as read."""
        pass

    @abstractmethod
    def archive(self, thread_id: str) -> bool:
        """Archive an email thread."""
        pass


class ITaskManager(ABC):
    """
    Interface for task management operations.

    Used by the task_tool to provide task functionality.
    """

    @abstractmethod
    def get_pending_tasks(self) -> list[Any]:
        """
        Get all pending tasks.

        Returns:
            List[TaskItem]: List of pending tasks
        """
        pass

    @abstractmethod
    def create_task(
        self,
        title: str,
        due_date: str | None = None,
        priority: int = 1,
        description: str | None = None
    ) -> str:
        """
        Create a new task.

        Returns:
            str: The task ID of the created task
        """
        pass

    @abstractmethod
    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        Update the status of a task.

        Args:
            task_id: The task ID
            status: New status (e.g., 'pending', 'in_progress', 'completed')

        Returns:
            bool: True if update was successful
        """
        pass

    @abstractmethod
    def get_task(self, task_id: str) -> Any | None:
        """Get a specific task by ID."""
        pass

    @abstractmethod
    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        pass

    @abstractmethod
    def get_overdue_tasks(self) -> list[Any]:
        """Get all overdue tasks."""
        pass
