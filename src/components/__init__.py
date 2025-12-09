# Components module
# Contains all component implementations for the agent framework
# Re-exports from sub-packages for backward compatibility and ease of use

from .context import (
    SYSTEM_PROMPT_TEMPLATES,
    ContextManager,
    DictToXMLFormatter,
    MarkdownFormatter,
    MetaData,
    SystemPromptTemplate,
    TemplateRegistry,
)
from .lifecycle import LifeCycleManager
from .logging import CompositeLogger, ConsoleLogger, FileLogger
from .memory import InMemoryManager
from .state import StateMachine
from .tools import ToolManager
from .monitoring import Watchdog
from .workspace import WorkspaceManager, LocalWorkspaceManager
from .knowledge import ChromaKnowledgeBase

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
    "LocalWorkspaceManager",
    # Memory
    "InMemoryManager",
    # Tools
    "ToolManager",
    # Knowledge Base
    "ChromaKnowledgeBase",
]
