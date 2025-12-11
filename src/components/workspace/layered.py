"""
Layered Workspace Manager for the Agent Framework.

Provides a 3-layer workspace architecture while implementing the standard
IWorkspaceManager interface. This allows the agent to be configured with
either a simple WorkspaceManager or this layered version.

Layers:
- PROJECT: User's project folder (default, git integrated)
- OFFICE: Agent's private workspace for notes and custom tools
- INTERPRETER: Ephemeral sandbox for code execution
"""

import shutil
import subprocess
import tempfile
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ...interfaces.base import IWorkspaceManager


class WorkspaceLayer(Enum):
    """
    The three layers of the agent's workspace.
    
    PROJECT: User's project folder (e.g., VSCode workspace, git repo)
             - Read/Write operations (default layer)
             - Final output destination
             - Integrated with version control
    
    OFFICE: Agent's private workspace
            - Persistent storage for agent's notes, drafts, custom tools
            - Invisible to PROJECT layer
            - Enables infinite context and self-learning
            - Location: ~/.agent/office/<agent_id>/
    
    INTERPRETER: Ephemeral code execution sandbox
                 - Temporary directory
                 - Cleared on reset or session end
    """
    PROJECT = "project"
    OFFICE = "office"
    INTERPRETER = "interpreter"


class LayeredWorkspaceManager(IWorkspaceManager):
    """
    Workspace manager with 3-layer architecture.
    
    Implements IWorkspaceManager so it can be used as a drop-in replacement
    for the simple WorkspaceManager. The default layer is PROJECT.
    
    Example:
        # Simple usage (like regular WorkspaceManager)
        workspace = LayeredWorkspaceManager("/path/to/project")
        workspace.create_file("readme.md", "# Hello")
        
        # With layers
        workspace = LayeredWorkspaceManager("/path/to/project", agent_id="my_agent")
        workspace.create_file("notes.md", "# Private", layer=WorkspaceLayer.OFFICE)
        workspace.create_file("temp.py", "x = 1", layer=WorkspaceLayer.INTERPRETER)
    """
    
    # Flag for automatic context injection
    inject_context: bool = True
    
    def __init__(
        self,
        base_path: str,
        agent_id: str = "default",
        office_base: str | Path | None = None,
        inject_context: bool = True
    ):
        """
        Initialize the layered workspace.
        
        Args:
            base_path: Root of the PROJECT layer (user's project)
            agent_id: Unique identifier for the agent (for office isolation)
            office_base: Base directory for OFFICE layer (default: ~/.agent/office)
            inject_context: Whether to contribute context to system prompt
        """
        # Layer 1: PROJECT
        self._project_root = Path(base_path).resolve()
        self._project_root.mkdir(parents=True, exist_ok=True)
        
        # Layer 2: OFFICE
        if office_base:
            self._office_root = Path(office_base) / agent_id
        else:
            self._office_root = Path.home() / ".agent" / "office" / agent_id
        self._office_root.mkdir(parents=True, exist_ok=True)
        
        # Layer 3: INTERPRETER (ephemeral)
        self._temp_dir = tempfile.TemporaryDirectory(prefix="agent_interpreter_")
        self._interpreter_root = Path(self._temp_dir.name)
        
        self._agent_id = agent_id
        self.inject_context = inject_context
        
        # Audit log and storage
        self._audit_log: list[dict] = []
        self._storage_limit: int = 1024 * 1024 * 1024  # 1GB default
        self._snapshots: dict[str, dict] = {}
        
        # Default layer for IWorkspaceManager methods
        self._default_layer = WorkspaceLayer.PROJECT
    
    def __del__(self):
        """Cleanup temporary directory on destruction."""
        if hasattr(self, '_temp_dir') and self._temp_dir:
            try:
                self._temp_dir.cleanup()
            except Exception:
                pass
    
    # ==========================================================================
    # LAYER MANAGEMENT
    # ==========================================================================
    
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
    
    def set_default_layer(self, layer: WorkspaceLayer) -> None:
        """Set the default layer for IWorkspaceManager methods."""
        self._default_layer = layer
    
    @property
    def base_path(self) -> Path:
        """Compatible with WorkspaceManager - returns PROJECT root."""
        return self._project_root
    
    # ==========================================================================
    # INTERNAL HELPERS
    # ==========================================================================
    
    def _resolve_path(self, path: str, layer: WorkspaceLayer | None = None) -> Path:
        """Resolve a relative path to an absolute path within a layer."""
        if layer is None:
            layer = self._default_layer
        
        root = self.get_layer_root(layer)
        resolved = (root / path).resolve()
        
        # Security check: ensure path is within the layer root
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            raise ValueError(f"Path '{path}' escapes the {layer.value} layer")
        
        return resolved
    
    def _log_action(self, action: str, path: str, success: bool, layer: WorkspaceLayer | None = None) -> None:
        """Log an action to the audit log."""
        self._audit_log.append({
            "action": action,
            "path": path,
            "layer": (layer or self._default_layer).value,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
    
    # ==========================================================================
    # IWorkspaceManager IMPLEMENTATION (uses default layer)
    # ==========================================================================
    
    def create_file(self, path: str, content: str, layer: WorkspaceLayer | None = None) -> bool:
        """Create a file at the specified path."""
        try:
            file_path = self._resolve_path(path, layer)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')
            self._log_action("create_file", path, True, layer)
            return True
        except Exception:
            self._log_action("create_file", path, False, layer)
            return False
    
    def read_file(self, path: str, layer: WorkspaceLayer | None = None) -> str | None:
        """Read the content of a file."""
        try:
            return self._resolve_path(path, layer).read_text(encoding='utf-8')
        except Exception:
            return None
    
    def update_file(self, path: str, content: str, layer: WorkspaceLayer | None = None) -> bool:
        """Update the content of an existing file."""
        return self.create_file(path, content, layer)
    
    def delete_file(self, path: str, layer: WorkspaceLayer | None = None) -> bool:
        """Delete a file."""
        try:
            self._resolve_path(path, layer).unlink()
            self._log_action("delete_file", path, True, layer)
            return True
        except Exception:
            self._log_action("delete_file", path, False, layer)
            return False
    
    def create_directory(self, path: str, layer: WorkspaceLayer | None = None) -> bool:
        """Create a directory."""
        try:
            self._resolve_path(path, layer).mkdir(parents=True, exist_ok=True)
            self._log_action("create_dir", path, True, layer)
            return True
        except Exception:
            return False
    
    def delete_directory(self, path: str, recursive: bool = False, layer: WorkspaceLayer | None = None) -> bool:
        """Delete a directory."""
        try:
            dir_path = self._resolve_path(path, layer)
            if recursive:
                shutil.rmtree(dir_path)
            else:
                dir_path.rmdir()
            return True
        except Exception:
            return False
    
    def list_directory(self, path: str, layer: WorkspaceLayer | None = None) -> list[str]:
        """List contents of a directory."""
        try:
            return [p.name for p in self._resolve_path(path, layer).iterdir()]
        except Exception:
            return []
    
    def file_exists(self, path: str, layer: WorkspaceLayer | None = None) -> bool:
        """Check if a file exists."""
        try:
            return self._resolve_path(path, layer).exists()
        except Exception:
            return False
    
    def create_snapshot(self, name: str) -> str:
        """Create a version snapshot of the current workspace state."""
        snapshot_id = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._snapshots[snapshot_id] = {"name": name, "created": datetime.now().isoformat()}
        return snapshot_id
    
    def restore_snapshot(self, snapshot_id: str) -> bool:
        """Restore workspace to a previous snapshot."""
        return snapshot_id in self._snapshots
    
    def get_storage_usage(self) -> dict[str, Any]:
        """Get storage usage statistics."""
        total = sum(
            f.stat().st_size 
            for f in self._project_root.rglob("*") 
            if f.is_file()
        )
        return {"used_bytes": total, "limit_bytes": self._storage_limit}
    
    def set_storage_limit(self, limit_bytes: int) -> None:
        """Set the storage limit for the workspace."""
        self._storage_limit = limit_bytes
    
    def execute_command(self, command: str, timeout: float | None = None, layer: WorkspaceLayer | None = None) -> dict[str, Any]:
        """Execute a command in the workspace."""
        try:
            cwd = str(self.get_layer_root(layer or self._default_layer))
            result = subprocess.run(
                command, shell=True, cwd=cwd,
                capture_output=True, text=True, timeout=timeout or 30
            )
            return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": "Timeout", "returncode": -1}
    
    def get_audit_log(self) -> list[dict[str, Any]]:
        """Get the audit log of all workspace actions."""
        return list(self._audit_log)
    
    # ==========================================================================
    # LAYER-SPECIFIC METHODS
    # ==========================================================================
    
    def copy_between_layers(
        self,
        source_path: str,
        source_layer: WorkspaceLayer,
        dest_path: str,
        dest_layer: WorkspaceLayer
    ) -> bool:
        """
        Copy a file between layers.
        
        Useful for promoting artifacts from INTERPRETER to PROJECT/OFFICE.
        """
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
    
    # ==========================================================================
    # CONTEXT CONTRIBUTION
    # ==========================================================================
    
    def get_context_contribution(self) -> dict[str, Any]:
        """
        Get workspace context for injection into the agent's system prompt.
        
        Returns information about all three layers.
        """
        try:
            project_files = self.list_directory(".", WorkspaceLayer.PROJECT)[:20]
        except Exception:
            project_files = []
        
        try:
            office_files = self.list_directory(".", WorkspaceLayer.OFFICE)[:10]
        except Exception:
            office_files = []
        
        return {
            "workspace": {
                "type": "layered",
                "project": {
                    "base_path": str(self._project_root),
                    "files": project_files,
                },
                "office": {
                    "base_path": str(self._office_root),
                    "files": office_files,
                },
                "interpreter": {
                    "base_path": str(self._interpreter_root),
                    "status": "ready"
                },
                "storage": self.get_storage_usage()
            }
        }
