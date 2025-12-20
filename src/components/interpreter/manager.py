"""
Atomic Code Interpreter for the Agent Framework.

Provides code execution capabilities as Tool and Context Shards.
"""

import io
import sys
import time
import traceback
import types
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from typing import Any, List, Dict, Optional
from pydantic import BaseModel, Field

from src.interfaces.workspace import IWorkspaceManager
from src.interfaces.raci import ExecutionResult, ModuleInfo
from src.models.data_models import Tool

# ==============================================================================
# TOOL ARGUMENT SCHEMAS
# ==============================================================================

class ExecuteCodeArgs(BaseModel):
    code: str = Field(..., description="The Python code to execute in the sandbox.")

# ==============================================================================
# INTERPRETER MANAGER
# ==============================================================================

class SandboxInterpreter:
    """
    Atomic Python interpreter. 
    Provides logic execution as Tool Shards and documentation as Context Shards.
    """

    def __init__(
        self,
        workspace: IWorkspaceManager,
        timeout_default: float = 30.0
    ):
        self._workspace = workspace
        self._timeout_default = timeout_default
        self._namespace: Dict[str, Any] = {}
        self._builtin_modules: List[ModuleInfo] = []
        self._init_builtin_modules()

    def _init_builtin_modules(self) -> None:
        """Initialize the documentation for built-in modules."""
        self._builtin_modules = [
            ModuleInfo(
                name="files",
                description="Workspace file operations",
                functions={
                    "read(path)": "Read file content",
                    "write(path, content)": "Write file content",
                    "list_dir(path='.')": "List directory contents"
                },
                examples=['from files import read; print(read("data.txt"))']
            ),
            ModuleInfo(
                name="data",
                description="JSON/CSV utilities",
                functions={"parse_json(text)": "String to dict", "to_json(obj)": "Dict to string"},
                examples=['import data; obj = data.parse_json(\'{\"a\":1}\' )']
            )
        ]

    def _build_execution_namespace(self) -> Dict[str, Any]:
        """Build the isolated namespace with internal modules."""
        # Simple internal modules implementation
        def class_to_module(name, methods):
            mod = types.ModuleType(name)
            for k, v in methods.items(): setattr(mod, k, v)
            return mod

        files_mod = class_to_module("files", {
            "read": self._workspace.read_file,
            "write": self._workspace.create_file,
            "list_dir": self._workspace.list_directory
        })

        import json
        data_mod = class_to_module("data", {
            "parse_json": json.loads,
            "to_json": json.dumps
        })

        return {
            "__builtins__": __builtins__,
            "files": files_mod,
            "data": data_mod,
            **self._namespace
        }

    def execute(self, code: str) -> ExecutionResult:
        """Atomic execution logic."""
        start_time = time.time()
        stdout_capture = io.StringIO()
        namespace = self._build_execution_namespace()
        
        try:
            with redirect_stdout(stdout_capture):
                exec(code, namespace)
            
            # Update persistent state (excluding modules)
            for k, v in namespace.items():
                if k not in ["__builtins__", "files", "data"]:
                    self._namespace[k] = v
                    
            return ExecutionResult(
                success=True,
                output=stdout_capture.getvalue(),
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output=stdout_capture.getvalue(),
                error=f"{type(e).__name__}: {e}",
                execution_time=time.time() - start_time
            )

    # --- Primitive Provider Implementation ---

    def get_context_shard(self) -> Dict[str, Any]:
        """
        Returns a context shard (knowledge primitive) about available modules.
        """
        modules_doc = {}
        for mod in self._builtin_modules:
            modules_doc[mod.name] = {
                "description": mod.description,
                "functions": mod.functions
            }
            
        return {
            "code_interpreter": {
                "status": "active",
                "available_modules": modules_doc,
                "note": "Use the execute_code tool to run Python. Variables persist between calls."
            }
        }

    def get_tools(self) -> List[Tool]:
        """Provides the execution capability as a Tool Shard."""
        return [
            Tool(
                name="execute_code",
                description="Run Python code to perform calculations, data processing, or file operations.",
                args_schema=ExecuteCodeArgs,
                func=self.execute
            )
        ]

    def reset(self) -> None:
        """Reset interpreter state."""
        self._namespace.clear()
