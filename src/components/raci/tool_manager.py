"""
RACI Tool Manager Implementation.

Provides a minimal tool interface for the RACI architecture.
Instead of dozens of tool schemas, uses only 2-3 core tools:
1. execute_code: Run Python in the interpreter
2. read_file: Read from PROJECT layer
3. write_file: Write to PROJECT layer

All other functionality is accessed through interpreter modules.
"""

from typing import Any

from ...interfaces.base import IContextProvider
from ...interfaces.raci import IRACIToolManager, WorkspaceLayer
from .interpreter import SandboxInterpreter
from .workspace import LayeredWorkspace


class RACIToolManager(IRACIToolManager, IContextProvider):
    """
    Minimal tool manager for RACI architecture.
    
    This replaces traditional tool-calling with a code-first approach.
    The agent writes Python code that runs in a sandbox interpreter
    with access to pre-configured modules.
    
    Benefits:
    - Minimal context window usage (~500 tokens vs ~15000)
    - Natural composition through code
    - Infinite flexibility
    - Self-learning (agent can create new modules)
    
    Tools Provided:
    1. execute_code: Execute Python with access to modules
    2. read_file: Read a file from the project
    3. write_file: Write a file to the project
    
    Example:
        # Create RACI components
        workspace = LayeredWorkspace(project_root="/path/to/project")
        interpreter = SandboxInterpreter(workspace)
        tools = RACIToolManager(interpreter, workspace)
        
        # Get tools for LLM binding
        tool_schemas = tools.get_tools()
        
        # Execute a tool call
        result = tools.execute_tool("execute_code", code='''
            from search import web
            print(web("Python tutorials"))
        ''')
    """
    
    # IContextProvider flag
    inject_context: bool = True
    
    def __init__(
        self,
        interpreter: SandboxInterpreter,
        workspace: LayeredWorkspace,
        max_code_length: int = 10000,
        require_confirmation_for_write: bool = False
    ):
        """
        Initialize the RACI tool manager.
        
        Args:
            interpreter: SandboxInterpreter instance
            workspace: LayeredWorkspace instance
            max_code_length: Maximum allowed code length
            require_confirmation_for_write: Whether to require user confirmation for writes
        """
        self._interpreter = interpreter
        self._workspace = workspace
        self._max_code_length = max_code_length
        self._require_confirmation = require_confirmation_for_write
        
        # Pending write operations (for confirmation flow)
        self._pending_writes: dict[str, tuple[str, str]] = {}
    
    def get_tools(self) -> list[dict[str, Any]]:
        """
        Get the minimal tool schemas.
        
        Returns only 3 tools instead of the typical 20-50 tools.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "execute_code",
                    "description": (
                        "Execute Python code in the interpreter sandbox. "
                        "Available modules: search (web search), http (requests), "
                        "data (json/csv), files (workspace read/write). "
                        "Use this for web searches, API calls, data processing, etc."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python code to execute. Can use: from search import web; from http import get, post; from data import parse_json, to_json; from files import read, write"
                            }
                        },
                        "required": ["code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read the contents of a file from the project.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path to the file"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write content to a file in the project.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path for the file"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write to the file"
                            }
                        },
                        "required": ["path", "content"]
                    }
                }
            }
        ]
    
    def execute_tool(self, name: str, **kwargs) -> Any:
        """Execute a tool by name."""
        if name == "execute_code":
            return self._execute_code(**kwargs)
        elif name == "read_file":
            return self._read_file(**kwargs)
        elif name == "write_file":
            return self._write_file(**kwargs)
        else:
            return {"error": f"Unknown tool: {name}"}
    
    def _execute_code(self, code: str) -> dict[str, Any]:
        """Execute Python code in the interpreter."""
        if len(code) > self._max_code_length:
            return {
                "success": False,
                "error": f"Code exceeds maximum length of {self._max_code_length} characters"
            }
        
        result = self._interpreter.execute(code)
        return result.to_dict()
    
    def _read_file(self, path: str) -> dict[str, Any]:
        """Read a file from the project."""
        content = self._workspace.read(path, WorkspaceLayer.PROJECT)
        
        if content is None:
            return {
                "success": False,
                "error": f"File not found: {path}"
            }
        
        return {
            "success": True,
            "path": path,
            "content": content,
            "length": len(content)
        }
    
    def _write_file(self, path: str, content: str) -> dict[str, Any]:
        """Write a file to the project."""
        if self._require_confirmation:
            # Store for later confirmation
            import uuid
            write_id = str(uuid.uuid4())[:8]
            self._pending_writes[write_id] = (path, content)
            return {
                "success": False,
                "pending": True,
                "write_id": write_id,
                "message": f"Write to '{path}' requires confirmation. ID: {write_id}"
            }
        
        success = self._workspace.write(path, content, WorkspaceLayer.PROJECT)
        
        if success:
            return {
                "success": True,
                "path": path,
                "bytes_written": len(content)
            }
        else:
            return {
                "success": False,
                "error": f"Failed to write to: {path}"
            }
    
    def confirm_write(self, write_id: str) -> dict[str, Any]:
        """Confirm a pending write operation."""
        if write_id not in self._pending_writes:
            return {
                "success": False,
                "error": f"No pending write with ID: {write_id}"
            }
        
        path, content = self._pending_writes.pop(write_id)
        success = self._workspace.write(path, content, WorkspaceLayer.PROJECT)
        
        if success:
            return {
                "success": True,
                "path": path,
                "bytes_written": len(content)
            }
        else:
            return {
                "success": False,
                "error": f"Failed to write to: {path}"
            }
    
    def cancel_write(self, write_id: str) -> bool:
        """Cancel a pending write operation."""
        if write_id in self._pending_writes:
            del self._pending_writes[write_id]
            return True
        return False
    
    def get_context_contribution(self) -> dict[str, Any]:
        """
        Get context for the system prompt.
        
        Instead of tool schemas, returns module documentation
        and usage examples optimized for minimal token usage.
        """
        modules_context = self._interpreter.get_modules_context()
        
        return {
            "raci": {
                "mode": "code_interpreter",
                "description": "Execute Python code to perform actions. Use modules instead of individual tools.",
                "modules_documentation": modules_context,
                "tools": ["execute_code", "read_file", "write_file"],
                "workspace_layers": {
                    "project": "User's project folder (read/write)",
                    "office": "Your private workspace for notes (via files module)",
                    "interpreter": "Temporary execution space"
                }
            }
        }
    
    def get_tools_for_langchain(self) -> list[Any]:
        """
        Convert tools to LangChain format.
        
        Returns tools compatible with langchain's bind_tools().
        """
        from langchain_core.tools import StructuredTool
        
        tools = [
            StructuredTool.from_function(
                func=lambda code: self._execute_code(code),
                name="execute_code",
                description=(
                    "Execute Python code with access to: search (web), http (requests), "
                    "data (json/csv), files (workspace). Returns execution result."
                ),
            ),
            StructuredTool.from_function(
                func=lambda path: self._read_file(path),
                name="read_file",
                description="Read a file from the project.",
            ),
            StructuredTool.from_function(
                func=lambda path, content: self._write_file(path, content),
                name="write_file",
                description="Write content to a file in the project.",
            ),
        ]
        
        return tools
