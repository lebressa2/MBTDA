# Interfaces module
# Contains all abstract base classes (protocols) for the agent framework

from .text import ITextClient
from .memory import IMemoryManager
from .tools import IToolManager
from .workspace import IWorkspaceManager
from .knowledge import IKnowledgeBase, IEmbedderProvider
from .logging import ILogger, LogLevel
from .context import IFormatter
from .monitoring import IWatchdog
from .lifecycle import ILifeCycle
from .tasks import ITaskManager
from .inbox import IInboxClient

__all__ = [
    "ITextClient",
    "IMemoryManager",
    "IToolManager",
    "IWorkspaceManager",
    "IKnowledgeBase",
    "IEmbedderProvider",
    "ILogger",
    "LogLevel",
    "IFormatter",
    "IWatchdog",
    "ILifeCycle",
    "ITaskManager",
    "IInboxClient",
]
