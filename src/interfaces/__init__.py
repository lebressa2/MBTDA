# Interfaces module
# Contains all abstract base classes (protocols) for the agent framework

from .base import (
    IFormatter,
    IInboxClient,
    ILifeCycle,
    ILogger,
    IMemoryManager,
    ITaskManager,
    ITextClient,
    IToolManager,
    IWatchdog,
    IWorkspaceManager,
)

__all__ = [
    "ITextClient",
    "IFormatter",
    "IMemoryManager",
    "IToolManager",
    "IWatchdog",
    "ILogger",
    "ILifeCycle",
    "IWorkspaceManager",
    "IInboxClient",
    "ITaskManager",
]
