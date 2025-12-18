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

from src.interfaces.workspace import IWorkspaceManager


class SecurityError(Exception):
    """
    Raised when a security violation is detected.
    
    Examples:
    - Path traversal attempts (using '..' or absolute paths)
    - Attempts to escape layer boundaries
    - Unauthorized operations on protected layers
    """
    pass



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
    
    def __init__(
        self,
        base_path: str,
        agent_id: str = "default",
        office_base: str | Path | None = None
    ):
        """
        Initialize the layered workspace.
        
        Args:
            base_path: Root of the PROJECT layer (user's project)
            agent_id: Unique identifier for the agent (for office isolation)
            office_base: Base directory for OFFICE layer (default: ~/.agent/office)
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
    
    def _log_action(
        self, 
        action: str, 
        path: str, 
        success: bool, 
        layer: WorkspaceLayer | None = None,
        operation_type: str = "default"
    ) -> None:
        """
        Log an action to the audit log with detailed information.
        
        Args:
            action: Name of the action (e.g., 'create_file', 'promote_file')
            path: Path involved in the action
            success: Whether the action succeeded
            layer: Layer where action occurred (None = default layer)
            operation_type: Type of operation ('default', 'promotion', 'security')
        """
        effective_layer = layer or self._default_layer
        self._audit_log.append({
            "action": action,
            "path": path,
            "layer": effective_layer.value,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "operation_type": operation_type,
            "security_level": "high" if effective_layer == WorkspaceLayer.INTERPRETER else "medium"
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
    
    def enforce_layer_3_operation(self, operation_name: str, path: str) -> Path:
        """
        Enforce that dangerous operations happen in Layer 3 (INTERPRETER).
        
        Validates the path for security issues and returns the resolved path
        within the INTERPRETER layer. Use this for any operation that could
        be exploited through path traversal or escaping.
        
        Args:
            operation_name: Name of the operation (for error messages)
            path: Relative path to validate
            
        Returns:
            Path: Resolved absolute path within INTERPRETER layer
            
        Raises:
            SecurityError: If path traversal attempt is detected
            
        Example:
            safe_path = workspace.enforce_layer_3_operation("read_file", "data.json")
            # Now safe_path is guaranteed to be within INTERPRETER layer
        """
        # Check for path traversal attempts
        if path.startswith('/') or path.startswith('\\'):
            self._log_action(
                f"security_block_{operation_name}", path, False,
                WorkspaceLayer.INTERPRETER, "security"
            )
            raise SecurityError(f"Absolute path not allowed in {operation_name}: {path}")
        
        if '..' in path:
            self._log_action(
                f"security_block_{operation_name}", path, False,
                WorkspaceLayer.INTERPRETER, "security"
            )
            raise SecurityError(f"Path traversal attempt in {operation_name}: {path}")
        
        # Resolve and validate within INTERPRETER layer
        resolved = self._resolve_path(path, WorkspaceLayer.INTERPRETER)
        
        self._log_action(
            f"security_check_{operation_name}", path, True,
            WorkspaceLayer.INTERPRETER, "security"
        )
        
        return resolved
    
    def move_between_layers(
        self,
        source_path: str,
        source_layer: WorkspaceLayer,
        dest_path: str,
        dest_layer: WorkspaceLayer,
        copy_only: bool = False
    ) -> bool:
        """
        Move or copy a file between layers.
        
        Generalizes promotion/demotion/copying between any layers.
        
        Args:
            source_path: Path in source layer
            source_layer: Source layer enum
            dest_path: Path in destination layer
            dest_layer: Destination layer enum
            copy_only: If True, keep source file (copy). If False, delete source (move).
            
        Returns:
            bool: True if operation succeeded
        """
        try:
            source = self._resolve_path(source_path, source_layer)
            dest = self._resolve_path(dest_path, dest_layer)
            
            if not source.exists():
                return False
            
            # Ensure destination directory exists
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            operation = "copy" if copy_only else "move"
            
            if source.is_file():
                if copy_only:
                    shutil.copy2(source, dest)
                else:
                    shutil.move(source, dest)
            elif source.is_dir():
                if copy_only:
                    shutil.copytree(source, dest, dirs_exist_ok=True)
                else:
                    shutil.move(source, dest)
            
            self._log_action(
                f"{operation}_between_layers",
                f"{source_layer.value}:{source_path} -> {dest_layer.value}:{dest_path}",
                True,
                dest_layer,
                operation
            )
            return True
            
        except Exception as e:
            self._log_action(
                f"{'copy' if copy_only else 'move'}_failure",
                f"{source_layer.value}:{source_path} -> {dest_layer.value}:{dest_path}: {e}",
                False,
                dest_layer,
                "error"
            )
            return False

    def promote_file_to_project(self, interpreter_path: str, project_path: str) -> bool:
        """Alias for move_between_layers(copy=True) for backward compatibility."""
        return self.move_between_layers(
            interpreter_path, WorkspaceLayer.INTERPRETER,
            project_path, WorkspaceLayer.PROJECT,
            copy_only=True
        )

    def copy_between_layers(
        self,
        source_path: str,
        source_layer: WorkspaceLayer,
        dest_path: str,
        dest_layer: WorkspaceLayer
    ) -> bool:
        """Alias for move_between_layers(copy=True)."""
        return self.move_between_layers(
            source_path, source_layer,
            dest_path, dest_layer,
            copy_only=True
        )
    
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
    
    def get_snapshot(self) -> dict[str, Any]:
        """Get a snapshot of the current workspace state for context injection."""
        try:
            project_files = self.list_directory(".", WorkspaceLayer.PROJECT)[:20]
        except Exception:
            project_files = []
        
        try:
            office_files = self.list_directory(".", WorkspaceLayer.OFFICE)[:10]
        except Exception:
            office_files = []
        
        return {
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
