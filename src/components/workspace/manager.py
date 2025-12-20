"""
Atomic Workspace Management for the Agent Framework.

Provides single-layer and 3-layer workspace implementations as atomic primitives.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Any, List, Dict, Optional, Type
from enum import Enum
from pydantic import BaseModel, Field

from src.interfaces.workspace import IWorkspaceManager
from src.models.data_models import Tool

# ==============================================================================
# PRIMITIVES & ENUMS
# ==============================================================================

class WorkspaceLayer(Enum):
    PROJECT = "project"      # User's files
    OFFICE = "office"       # Agent's private storage
    INTERPRETER = "interpreter" # Ephemeral execution space

# ==============================================================================
# TOOL ARGUMENT SCHEMAS (Pydantic Shards)
# ==============================================================================

class ReadFileArgs(BaseModel):
    path: str = Field(..., description="Path of the file to read")
    layer: WorkspaceLayer = Field(default=WorkspaceLayer.PROJECT, description="Layer to read from")

class WriteFileArgs(BaseModel):
    path: str = Field(..., description="Path where the file will be created")
    content: str = Field(..., description="Text content of the file")
    layer: WorkspaceLayer = Field(default=WorkspaceLayer.PROJECT, description="Layer to write to")

class ListDirArgs(BaseModel):
    path: str = Field(default=".", description="Directory path to list")
    layer: WorkspaceLayer = Field(default=WorkspaceLayer.PROJECT, description="Layer to list")

# ==============================================================================
# LAYERED WORKSPACE MANAGER (The Main Primitive)
# ==============================================================================

class LayeredWorkspaceManager(IWorkspaceManager):
    """
    Dumb orchestrator for workspace layers. Acts as a 'Physical Shard' provider.
    """

    def __init__(
        self, 
        project_path: Path | str, 
        office_path: Path | str, 
        interpreter_path: Path | str
    ):
        self._roots = {
            WorkspaceLayer.PROJECT: Path(project_path).resolve(),
            WorkspaceLayer.OFFICE: Path(office_path).resolve(),
            WorkspaceLayer.INTERPRETER: Path(interpreter_path).resolve()
        }
        for root in self._roots.values():
            root.mkdir(parents=True, exist_ok=True)

    @property
    def base_path(self) -> Path:
        return self._roots[WorkspaceLayer.PROJECT]

    def _resolve_path(self, path: str, layer: WorkspaceLayer = WorkspaceLayer.PROJECT) -> Path:
        root = self._roots[layer]
        resolved = (root / path).resolve()
        if not str(resolved).startswith(str(root)):
            raise ValueError(f"Path escapes {layer.value} layer")
        return resolved

    def read_file(self, path: str, layer: WorkspaceLayer = WorkspaceLayer.PROJECT) -> str | None:
        try:
            return self._resolve_path(path, layer).read_text(encoding='utf-8')
        except Exception:
            return None

    def create_file(self, path: str, content: str, layer: WorkspaceLayer = WorkspaceLayer.PROJECT) -> bool:
        try:
            file_path = self._resolve_path(path, layer)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')
            return True
        except Exception:
            return False

    def update_file(self, path: str, content: str, layer: WorkspaceLayer = WorkspaceLayer.PROJECT) -> bool:
        return self.create_file(path, content, layer)

    def delete_file(self, path: str, layer: WorkspaceLayer = WorkspaceLayer.PROJECT) -> bool:
        try:
            self._resolve_path(path, layer).unlink()
            return True
        except Exception:
            return False

    def list_directory(self, path: str = ".", layer: WorkspaceLayer = WorkspaceLayer.PROJECT) -> List[str]:
        try:
            return [p.name for p in self._resolve_path(path, layer).iterdir()]
        except Exception:
            return []

    def file_exists(self, path: str, layer: WorkspaceLayer = WorkspaceLayer.PROJECT) -> bool:
        return self._resolve_path(path, layer).exists()

    def execute_command(self, command: str, timeout: float | None = None) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                command, shell=True, cwd=str(self.base_path),
                capture_output=True, text=True, timeout=timeout or 30
            )
            return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": "Timeout", "returncode": -1}

    # --- Primitive Provider Implementation ---

    def get_context_shard(self) -> Dict[str, Any]:
        """
        Returns a context shard (knowledge primitive) about the workspace.
        This can be manually added to the PromptComposer.
        """
        try:
            project_files = self.list_directory(".", WorkspaceLayer.PROJECT)[:15]
        except Exception:
            project_files = []
            
        return {
            "workspace_info": {
                "layers": {l.value: str(self._roots[l]) for l in WorkspaceLayer},
                "project_structure": project_files,
                "note": "You have a layered workspace. Use tools to interact with it."
            }
        }

    def get_tools(self) -> List[Tool]:
        """Provides the workspace capabilities as Tool Shards."""
        return [
            Tool(
                name="read_file",
                description="Read a file from a layer (project, office, interpreter).",
                args_schema=ReadFileArgs,
                func=self.read_file
            ),
            Tool(
                name="write_file",
                description="Write a file to a layer.",
                args_schema=WriteFileArgs,
                func=self.create_file
            ),
            Tool(
                name="list_files",
                description="List files in a layer.",
                args_schema=ListDirArgs,
                func=self.list_directory
            )
        ]

# ==============================================================================
# SIMPLE WORKSPACE MANAGER (Single Layer Utility)
# ==============================================================================

class WorkspaceManager(LayeredWorkspaceManager):
    """A simplified version that maps all layers to the same path."""
    def __init__(self, base_path: Path | str):
        path = Path(base_path).resolve()
        super().__init__(project_path=path, office_path=path, interpreter_path=path)
