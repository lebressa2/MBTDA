"""
Workspace Components Package.

Provides workspace management implementations:
- WorkspaceManager: Simple single-directory workspace
- LocalWorkspaceManager: Alias for WorkspaceManager
- LayeredWorkspaceManager: 3-layer workspace (PROJECT, OFFICE, INTERPRETER)
- WorkspaceLayer: Enum for the 3 layers
"""

from .base import WorkspaceManager
from .local import LocalWorkspaceManager
from .layered import LayeredWorkspaceManager, WorkspaceLayer, SecurityError

__all__ = [
    "WorkspaceManager",
    "LocalWorkspaceManager", 
    "LayeredWorkspaceManager",
    "WorkspaceLayer",
    "SecurityError"
]

