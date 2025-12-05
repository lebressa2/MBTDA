"""
Workspace Manager for the Agent Framework.
"""

import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from ..interfaces.base import IWorkspaceManager


class WorkspaceManager(IWorkspaceManager):
    """Manages the isolated workspace environment for the agent."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._snapshots: dict[str, dict] = {}
        self._audit_log: list[dict] = []
        self._storage_limit: int = 1024 * 1024 * 1024  # 1GB default

    def _log_action(self, action: str, path: str, success: bool) -> None:
        self._audit_log.append({
            "action": action,
            "path": path,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })

    def _resolve_path(self, path: str) -> Path:
        resolved = (self.base_path / path).resolve()
        if not str(resolved).startswith(str(self.base_path)):
            raise ValueError("Path escapes workspace")
        return resolved

    def create_file(self, path: str, content: str) -> bool:
        try:
            file_path = self._resolve_path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')
            self._log_action("create_file", path, True)
            return True
        except Exception:
            self._log_action("create_file", path, False)
            return False

    def read_file(self, path: str) -> str | None:
        try:
            return self._resolve_path(path).read_text(encoding='utf-8')
        except Exception:
            return None

    def update_file(self, path: str, content: str) -> bool:
        return self.create_file(path, content)

    def delete_file(self, path: str) -> bool:
        try:
            self._resolve_path(path).unlink()
            self._log_action("delete_file", path, True)
            return True
        except Exception:
            self._log_action("delete_file", path, False)
            return False

    def create_directory(self, path: str) -> bool:
        try:
            self._resolve_path(path).mkdir(parents=True, exist_ok=True)
            self._log_action("create_dir", path, True)
            return True
        except Exception:
            return False

    def delete_directory(self, path: str, recursive: bool = False) -> bool:
        try:
            dir_path = self._resolve_path(path)
            if recursive:
                shutil.rmtree(dir_path)
            else:
                dir_path.rmdir()
            return True
        except Exception:
            return False

    def list_directory(self, path: str) -> list[str]:
        try:
            return [p.name for p in self._resolve_path(path).iterdir()]
        except Exception:
            return []

    def file_exists(self, path: str) -> bool:
        try:
            return self._resolve_path(path).exists()
        except Exception:
            return False

    def create_snapshot(self, name: str) -> str:
        snapshot_id = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._snapshots[snapshot_id] = {"name": name, "created": datetime.now().isoformat()}
        return snapshot_id

    def restore_snapshot(self, snapshot_id: str) -> bool:
        return snapshot_id in self._snapshots

    def get_storage_usage(self) -> dict[str, Any]:
        total = sum(f.stat().st_size for f in self.base_path.rglob("*") if f.is_file())
        return {"used_bytes": total, "limit_bytes": self._storage_limit}

    def set_storage_limit(self, limit_bytes: int) -> None:
        self._storage_limit = limit_bytes

    def execute_command(self, command: str, timeout: float | None = None) -> dict[str, Any]:
        try:
            result = subprocess.run(
                command, shell=True, cwd=str(self.base_path),
                capture_output=True, text=True, timeout=timeout or 30
            )
            return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": "Timeout", "returncode": -1}

    def get_audit_log(self) -> list[dict[str, Any]]:
        return list(self._audit_log)
