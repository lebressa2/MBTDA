"""
Layered Workspace Implementation.

Provides the 3-layer workspace architecture:
- PROJECT: User's project folder (git integrated)
- OFFICE: Agent's private workspace for notes and tools
- INTERPRETER: Ephemeral sandbox for code execution
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from ...interfaces.raci import ILayeredWorkspace, WorkspaceLayer


class LayeredWorkspace(ILayeredWorkspace):
    """
    Implementation of the 3-layer workspace architecture.
    
    Layer 1 (PROJECT): User's project folder
        - Typically the VSCode workspace or current working directory
        - Integrated with git for version control
        - Read/Write operations may require user confirmation
    
    Layer 2 (OFFICE): Agent's private workspace
        - Located at ~/.agent/office/<agent_id>/
        - Persists across sessions
        - Used for notes, drafts, custom modules, knowledge base
        - Invisible to the user's project
    
    Layer 3 (INTERPRETER): Ephemeral execution sandbox
        - Temporary directory created per session
        - Cleared on reset or session end
        - Used for code execution artifacts
    
    Example:
        workspace = LayeredWorkspace(
            project_root="/path/to/project",
            agent_id="my_agent"
        )
        
        # Read from project
        content = workspace.read("src/main.py", WorkspaceLayer.PROJECT)
        
        # Write to office
        workspace.write("notes/todo.md", "# Tasks", WorkspaceLayer.OFFICE)
        
        # Copy artifact to project
        workspace.copy_between_layers(
            "output.csv", WorkspaceLayer.INTERPRETER,
            "data/output.csv", WorkspaceLayer.PROJECT
        )
    """
    
    def __init__(
        self,
        project_root: str | Path | None = None,
        agent_id: str = "default",
        office_base: str | Path | None = None,
        interpreter_dir: str | Path | None = None
    ):
        """
        Initialize the layered workspace.
        
        Args:
            project_root: Root of the project layer (default: cwd)
            agent_id: Unique identifier for the agent (for office isolation)
            office_base: Base directory for office layer (default: ~/.agent/office)
            interpreter_dir: Directory for interpreter (default: temp dir)
        """
        # Layer 1: PROJECT
        self._project_root = Path(project_root) if project_root else Path.cwd()
        
        # Layer 2: OFFICE
        if office_base:
            self._office_root = Path(office_base) / agent_id
        else:
            self._office_root = Path.home() / ".agent" / "office" / agent_id
        self._office_root.mkdir(parents=True, exist_ok=True)
        
        # Layer 3: INTERPRETER (ephemeral)
        if interpreter_dir:
            self._interpreter_root = Path(interpreter_dir)
            self._interpreter_root.mkdir(parents=True, exist_ok=True)
            self._temp_dir = None
        else:
            self._temp_dir = tempfile.TemporaryDirectory(prefix="raci_")
            self._interpreter_root = Path(self._temp_dir.name)
        
        self._agent_id = agent_id
    
    def __del__(self):
        """Cleanup temporary directory on destruction."""
        if self._temp_dir:
            try:
                self._temp_dir.cleanup()
            except Exception:
                pass
    
    def get_layer_root(self, layer: WorkspaceLayer) -> Path:
        """Get the root path for a workspace layer."""
        if layer == WorkspaceLayer.PROJECT:
            return self._project_root
        elif layer == WorkspaceLayer.OFFICE:
            return self._office_root
        elif layer == WorkspaceLayer.INTERPRETER:
            return self._interpreter_root
        else:
            raise ValueError(f"Unknown layer: {layer}")
    
    def _resolve_path(self, path: str, layer: WorkspaceLayer) -> Path:
        """Resolve a relative path to an absolute path within a layer."""
        root = self.get_layer_root(layer)
        resolved = (root / path).resolve()
        
        # Security check: ensure path is within the layer root
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            raise ValueError(f"Path '{path}' escapes the {layer.value} layer")
        
        return resolved
    
    def read(
        self, 
        path: str, 
        layer: WorkspaceLayer = WorkspaceLayer.PROJECT
    ) -> str | None:
        """Read a file from the specified layer."""
        try:
            file_path = self._resolve_path(path, layer)
            if file_path.exists() and file_path.is_file():
                return file_path.read_text(encoding="utf-8")
            return None
        except Exception:
            return None
    
    def write(
        self, 
        path: str, 
        content: str,
        layer: WorkspaceLayer = WorkspaceLayer.PROJECT
    ) -> bool:
        """Write a file to the specified layer."""
        try:
            file_path = self._resolve_path(path, layer)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return True
        except Exception:
            return False
    
    def delete(
        self, 
        path: str, 
        layer: WorkspaceLayer = WorkspaceLayer.PROJECT
    ) -> bool:
        """Delete a file from the specified layer."""
        try:
            file_path = self._resolve_path(path, layer)
            if file_path.exists():
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
                return True
            return False
        except Exception:
            return False
    
    def list_dir(
        self, 
        path: str = ".",
        layer: WorkspaceLayer = WorkspaceLayer.PROJECT,
        recursive: bool = False
    ) -> list[str]:
        """List directory contents."""
        try:
            dir_path = self._resolve_path(path, layer)
            if not dir_path.exists() or not dir_path.is_dir():
                return []
            
            root = self.get_layer_root(layer)
            
            if recursive:
                return [
                    str(p.relative_to(root))
                    for p in dir_path.rglob("*")
                    if p.is_file()
                ]
            else:
                return [
                    str(p.relative_to(root))
                    for p in dir_path.iterdir()
                ]
        except Exception:
            return []
    
    def exists(
        self, 
        path: str, 
        layer: WorkspaceLayer = WorkspaceLayer.PROJECT
    ) -> bool:
        """Check if a path exists in the specified layer."""
        try:
            file_path = self._resolve_path(path, layer)
            return file_path.exists()
        except Exception:
            return False
    
    def copy_between_layers(
        self,
        source_path: str,
        source_layer: WorkspaceLayer,
        dest_path: str,
        dest_layer: WorkspaceLayer
    ) -> bool:
        """Copy a file between layers."""
        try:
            source = self._resolve_path(source_path, source_layer)
            dest = self._resolve_path(dest_path, dest_layer)
            
            if not source.exists():
                return False
            
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            if source.is_file():
                shutil.copy2(source, dest)
            elif source.is_dir():
                shutil.copytree(source, dest, dirs_exist_ok=True)
            
            return True
        except Exception:
            return False
    
    def get_layer_info(self, layer: WorkspaceLayer) -> dict[str, Any]:
        """Get information about a layer."""
        root = self.get_layer_root(layer)
        
        total_size = 0
        file_count = 0
        
        if root.exists():
            for path in root.rglob("*"):
                if path.is_file():
                    file_count += 1
                    try:
                        total_size += path.stat().st_size
                    except OSError:
                        pass
        
        return {
            "layer": layer.value,
            "root_path": str(root),
            "exists": root.exists(),
            "total_size_bytes": total_size,
            "file_count": file_count
        }
    
    def clear_interpreter(self) -> None:
        """Clear all files in the interpreter layer."""
        try:
            for item in self._interpreter_root.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
        except Exception:
            pass
    
    def get_context_contribution(self) -> dict[str, Any]:
        """Get context contribution for the agent's system prompt."""
        project_files = self.list_dir(".", WorkspaceLayer.PROJECT)[:20]  # Limit
        office_files = self.list_dir(".", WorkspaceLayer.OFFICE)[:10]
        
        return {
            "workspace": {
                "project": {
                    "root": str(self._project_root),
                    "files_preview": project_files
                },
                "office": {
                    "root": str(self._office_root),
                    "files": office_files
                },
                "interpreter": {
                    "root": str(self._interpreter_root),
                    "status": "ready"
                }
            }
        }
