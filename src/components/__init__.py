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
from .tools import ToolManager, RACIToolManager
from .monitoring import Watchdog
from .workspace import WorkspaceManager, LocalWorkspaceManager, LayeredWorkspaceManager, WorkspaceLayer
try:
    from .knowledge import ChromaKnowledgeBase
except ImportError:
    ChromaKnowledgeBase = None
from .interpreter import SandboxInterpreter

__all__ = [
    # Context Manager
    "ContextManager",
    "DictToXMLFormatter",
    "MarkdownFormatter",
    "MetaData",
    "SystemPromptTemplate",
    "SYSTEM_PROMPT_TEMPLATES",
    "TemplateRegistry",
    # Watchdog
    "Watchdog",
    # Loggers
    "ConsoleLogger",
    "FileLogger",
    "CompositeLogger",
    # Lifecycle
    "LifeCycleManager",
    # Workspace (choose one)
    "WorkspaceManager",          # Simple single-directory
    "LocalWorkspaceManager",     # Alias
    "LayeredWorkspaceManager",   # 3-layer (PROJECT, OFFICE, INTERPRETER)
    "WorkspaceLayer",            # Enum for layers
    # Memory
    "InMemoryManager",
    # Tools (choose one)
    "ToolManager",               # Traditional with tool schemas
    "RACIToolManager",           # Code interpreter approach
    # Knowledge Base
    "ChromaKnowledgeBase",
    # Interpreter (for RACI mode)
    "SandboxInterpreter",
]


