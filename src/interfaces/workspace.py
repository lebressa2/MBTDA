from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional
from pathlib import Path
from src.models.data_models import Tool

class IWorkspaceManager(ABC):
    """
    Interface for workspace management.
    """
    @property
    @abstractmethod
    def base_path(self) -> Path:
        """Get the base path of the workspace."""
        pass

    @abstractmethod
    def create_file(self, path: str, content: str) -> bool:
        """Create a file in the workspace."""
        pass

    @abstractmethod
    def read_file(self, path: str) -> str | None:
        """Read a file from the workspace."""
        pass

    @abstractmethod
    def update_file(self, path: str, content: str) -> bool:
        """Update an existing file."""
        pass

    @abstractmethod
    def delete_file(self, path: str) -> bool:
        """Delete a file from the workspace."""
        pass

    @abstractmethod
    def create_directory(self, path: str) -> bool:
        """Create a directory in the workspace."""
        pass

    @abstractmethod
    def delete_directory(self, path: str, recursive: bool = False) -> bool:
        """Delete a directory."""
        pass

    @abstractmethod
    def list_directory(self, path: str) -> List[str]:
        """List contents of a directory."""
        pass

    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        pass

    @abstractmethod
    def execute_command(self, command: str, timeout: float | None = None) -> Dict[str, Any]:
        """Execute a command in the isolated environment."""
        pass

    @abstractmethod
    def get_tools(self) -> List[Tool]:
        """Get the list of atomic tools provided by this workspace."""
        pass