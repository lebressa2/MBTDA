# Interfaces module
# Contains all abstract base classes (protocols) for the agent framework

from .base import (
    ITextClient,
    IFormatter,
    IMemoryManager,
    IToolManager,
    IWatchdog,
    ILogger,
    ILifeCycle,
    IWorkspaceManager,
    IInboxClient,
    ITaskManager,
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
