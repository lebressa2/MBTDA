"""
RACI Tool Manager for the Agent Framework.

Provides a code-interpreter-based tool manager implementing IToolManager.
Uses minimal tools (execute_code, read_file, write_file) instead of 
dozens of individual tool schemas.

This is an alternative to the traditional ToolManager - the user chooses
which implementation to use when configuring the agent.
"""

from typing import Any

from ...interfaces.base import IToolManager


class RACIToolManager(IToolManager):
    """
    Minimal tool manager using code interpreter approach.
    
    Implements IToolManager so it can be used as a drop-in replacement
    for the traditional ToolManager. Instead of registering many tools,
    it provides only 3 core tools that delegate to a code interpreter.
    
    Benefits:
    - Minimal context window usage (~500 tokens vs ~15000)
    - Natural composition through Python code
    - Infinite flexibility
    - Self-learning (agent can create new modules)
    
    Example:
        # Use RACI instead of traditional ToolManager
        from src.components.tools import RACIToolManager
        from src.components.interpreter import SandboxInterpreter
        from src.components.workspace import LayeredWorkspaceManager
        
        workspace = LayeredWorkspaceManager("/path/to/project")
        interpreter = SandboxInterpreter(workspace)
        tools = RACIToolManager(interpreter, workspace)
        
        # Use with Agent
        agent = Agent(
            client=client,
            tools=tools,  # Works just like ToolManager!
            workspace=workspace
        )
    """
    
    # Flag for automatic context injection
    inject_context: bool = True
    
    def __init__(
        self,
        interpreter: Any,  # SandboxInterpreter - Any to avoid circular import
        workspace: Any,  # IWorkspaceManager - Any to avoid circular import
        max_code_length: int = 10000,
        inject_context: bool = True
    ):
        """
        Initialize the RACI tool manager.
        
        Args:
            interpreter: SandboxInterpreter instance for code execution
            workspace: IWorkspaceManager instance for file operations
            max_code_length: Maximum allowed code length
            inject_context: Whether to contribute context to system prompt
        """
        self._interpreter = interpreter
        self._workspace = workspace
        self._max_code_length = max_code_length
        self.inject_context = inject_context
        
        # Internal tool registry (for compatibility)
        self._tools: dict[str, dict[str, Any]] = {}
        self._contexts: dict[str, list[str]] = {}
        
        # Register the 3 core RACI tools
        self._register_raci_tools()
    
    def _register_raci_tools(self) -> None:
        """Register the 3 core RACI tools internally."""
        # Create tool-like objects
        class ExecuteCodeTool:
            name = "execute_code"
            description = (
                "Execute Python code with access to modules: search (web), "
                "http (requests), data (json/csv), files (workspace). "
                "Use for web searches, API calls, data processing."
            )
            
            def __init__(self, manager: 'RACIToolManager'):
                self._manager = manager
            
            def invoke(self, args: dict) -> dict[str, Any]:
                return self._manager._execute_code(args.get("code", ""))
        
        class ReadFileTool:
            name = "read_file"
            description = "Read the contents of a file from the project."
            
            def __init__(self, manager: 'RACIToolManager'):
                self._manager = manager
            
            def invoke(self, args: dict) -> dict[str, Any]:
                return self._manager._read_file(args.get("path", ""))
        
        class WriteFileTool:
            name = "write_file"
            description = "Write content to a file in the project."
            
            def __init__(self, manager: 'RACIToolManager'):
                self._manager = manager
            
            def invoke(self, args: dict) -> dict[str, Any]:
                return self._manager._write_file(
                    args.get("path", ""),
                    args.get("content", "")
                )
        
        # Register tools
        self._tools["execute_code"] = {
            "tool": ExecuteCodeTool(self),
            "context": "raci",
            "description": ExecuteCodeTool.description
        }
        self._tools["read_file"] = {
            "tool": ReadFileTool(self),
            "context": "raci",
            "description": ReadFileTool.description
        }
        self._tools["write_file"] = {
            "tool": WriteFileTool(self),
            "context": "raci",
            "description": WriteFileTool.description
        }
        
        self._contexts["raci"] = ["execute_code", "read_file", "write_file"]
    
    # ==========================================================================
    # IToolManager IMPLEMENTATION
    # ==========================================================================
    
    def register_tool(self, context: str, tool: Any) -> None:
        """
        Register an additional tool.
        
        While RACI uses only 3 core tools, you can still register
        additional tools if needed.
        """
        tool_name = getattr(tool, 'name', str(tool))
        description = getattr(tool, 'description', '')
        
        self._tools[tool_name] = {
            "tool": tool,
            "context": context,
            "description": description
        }
        
        if context not in self._contexts:
            self._contexts[context] = []
        self._contexts[context].append(tool_name)
    
    def get_tools(self, contexts: list[str] | None = None) -> list[Any]:
        """Get tools, optionally filtered by contexts."""
        if contexts is None:
            return [t["tool"] for t in self._tools.values()]
        
        tools = []
        for ctx in contexts:
            for tool_name in self._contexts.get(ctx, []):
                tools.append(self._tools[tool_name]["tool"])
        return tools
    
    def get_tool_descriptions(self, contexts: list[str] | None = None) -> str:
        """Get formatted descriptions of available tools."""
        tools = self._tools.values() if contexts is None else [
            self._tools[name] for ctx in contexts
            for name in self._contexts.get(ctx, [])
        ]
        
        lines = ["Available Tools (RACI Mode):"]
        for t in tools:
            name = getattr(t['tool'], 'name', 'Unknown')
            lines.append(f"- {name}: {t['description']}")
        
        # Add interpreter modules info
        if hasattr(self._interpreter, 'get_modules_context'):
            lines.append("")
            lines.append("Interpreter Modules:")
            lines.append(self._interpreter.get_modules_context())
        
        return "\n".join(lines)
    
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool by name with given arguments."""
        if tool_name not in self._tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        tool = self._tools[tool_name]["tool"]
        if hasattr(tool, 'invoke'):
            return tool.invoke(kwargs)
        elif callable(tool):
            return tool(**kwargs)
        raise ValueError(f"Tool '{tool_name}' is not callable")
    
    # ==========================================================================
    # RACI TOOL IMPLEMENTATIONS
    # ==========================================================================
    
    def _execute_code(self, code: str) -> dict[str, Any]:
        """Execute Python code in the interpreter."""
        if not code:
            return {"success": False, "error": "No code provided"}
        
        if len(code) > self._max_code_length:
            return {
                "success": False,
                "error": f"Code exceeds maximum length of {self._max_code_length} characters"
            }
        
        result = self._interpreter.execute(code)
        return result.to_dict()
    
    def _read_file(self, path: str) -> dict[str, Any]:
        """Read a file from the workspace."""
        if not path:
            return {"success": False, "error": "No path provided"}
        
        content = self._workspace.read_file(path)
        
        if content is None:
            return {"success": False, "error": f"File not found: {path}"}
        
        return {
            "success": True,
            "path": path,
            "content": content,
            "length": len(content)
        }
    
    def _write_file(self, path: str, content: str) -> dict[str, Any]:
        """Write a file to the workspace."""
        if not path:
            return {"success": False, "error": "No path provided"}
        
        success = self._workspace.create_file(path, content)
        
        if success:
            return {
                "success": True,
                "path": path,
                "bytes_written": len(content)
            }
        else:
            return {"success": False, "error": f"Failed to write to: {path}"}
    
    # ==========================================================================
    # CONTEXT CONTRIBUTION
    # ==========================================================================
    
    def get_context_contribution(self) -> dict[str, Any]:
        """
        Get tools context for injection into the agent's system prompt.
        
        Returns RACI-specific context with module documentation.
        """
        context = {
            "available_tools": self.get_tool_descriptions(),
            "tool_mode": "raci_interpreter",
            "tools": ["execute_code", "read_file", "write_file"]
        }
        
        # Add interpreter context if available
        if hasattr(self._interpreter, 'get_context_contribution'):
            interpreter_context = self._interpreter.get_context_contribution()
            context["interpreter"] = interpreter_context.get("interpreter", {})
        
        return context
    
    # ==========================================================================
    # LANGCHAIN COMPATIBILITY
    # ==========================================================================
    
    def get_tools_for_langchain(self) -> list[Any]:
        """
        Convert tools to LangChain format.
        
        Returns tools compatible with langchain's bind_tools().
        """
        try:
            from langchain_core.tools import StructuredTool
            
            tools = [
                StructuredTool.from_function(
                    func=lambda code: self._execute_code(code),
                    name="execute_code",
                    description=(
                        "Execute Python code with modules: search, http, data, files. "
                        "Returns execution result."
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
        except ImportError:
            # LangChain not available
            return self.get_tools()
