# Components module
# Contains all component implementations for the agent framework

from .context_manager import (
    SYSTEM_PROMPT_TEMPLATES,
    ContextManager,
    DictToXMLFormatter,
    MarkdownFormatter,
    MetaData,
    SystemPromptTemplate,
    TemplateRegistry,
)
from .lifecycle import LifeCycleManager
from .logger import CompositeLogger, ConsoleLogger, FileLogger
from .memory import InMemoryManager
from .state_machine import StateMachine
from .tools import ToolManager
from .watchdog import Watchdog
from .workspace import WorkspaceManager

__all__ = [
    # Context Manager
    "ContextManager",
    "DictToXMLFormatter",
    "MarkdownFormatter",
    "MetaData",
    "SystemPromptTemplate",
    "SYSTEM_PROMPT_TEMPLATES",
    "TemplateRegistry",
    # State Machine
    "StateMachine",
    # Watchdog
    "Watchdog",
    # Loggers
    "ConsoleLogger",
    "FileLogger",
    "CompositeLogger",
    # Lifecycle
    "LifeCycleManager",
    # Workspace
    "WorkspaceManager",
    # Memory
    "InMemoryManager",
    # Tools
    "ToolManager",
]
