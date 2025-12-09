"""
Local Workspace Manager.

Implementation of a workspace manager that creates a specific directory structure
for the agent: <root>/<agent_name>/workspace/
"""

from pathlib import Path
from .base import WorkspaceManager

class LocalWorkspaceManager(WorkspaceManager):
    """
    Local workspace manager that organizes files by agent name.
    
    Structure: base_path/agent_name/workspace/
    """
    
    def __init__(self, agent_name: str, base_path: str, inject_context: bool = True):
        """
        Initialize the local workspace manager.
        
        Args:
            agent_name: Name of the agent (used for directory naming)
            base_path: Root path where agent directories will be created
            inject_context: Whether to inject workspace context into the agent
        """
        # Construct the specific path for this agent
        # agent_name/workspace/
        root_path = Path(base_path).resolve()
        agent_workspace = root_path / agent_name / "workspace"
        
        # Initialize the parent class with the constructed path
        # The parent (WorkspaceManager) will creating the directory if it doesn't exist
        super().__init__(base_path=str(agent_workspace), inject_context=inject_context)
