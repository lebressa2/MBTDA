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
            description = "Read file. Args: path (str), layer (str, optional: 'project', 'office', 'interpreter')"
            
            def __init__(self, manager: 'RACIToolManager'):
                self._manager = manager
            
            def invoke(self, args: dict) -> dict[str, Any]:
                return self._manager._read_file(
                    args.get("path", ""), 
                    args.get("layer")
                )
        
        class WriteFileTool:
            name = "write_file"
            description = "Write file. Args: path (str), content (str), layer (str, optional: 'project', 'office')"
            
            def __init__(self, manager: 'RACIToolManager'):
                self._manager = manager
            
            def invoke(self, args: dict) -> dict[str, Any]:
                return self._manager._write_file(
                    args.get("path", ""),
                    args.get("content", ""),
                    args.get("layer")
                )
        
        class MoveFileTool:
            name = "move_file"
            description = (
                "Move/Copy files between layers. "
                "Args: source_path, source_layer, dest_path, dest_layer, copy_only (bool)"
            )
            
            def __init__(self, manager: 'RACIToolManager'):
                self._manager = manager
                
            def invoke(self, args: dict) -> dict[str, Any]:
                return self._manager._move_file(
                    args.get("source_path", ""),
                    args.get("source_layer", ""),
                    args.get("dest_path", ""),
                    args.get("dest_layer", ""),
                    args.get("copy_only", False)
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
        self._tools["move_file"] = {
            "tool": MoveFileTool(self),
            "context": "raci",
            "description": MoveFileTool.description
        }
        
        self._contexts["raci"] = ["execute_code", "read_file", "write_file", "move_file"]
    
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
        """
        Execute Python code in the interpreter layer (Layer 3).
        
        All code execution happens in the INTERPRETER layer, ensuring
        isolation from the PROJECT and OFFICE layers. The interpreter
        has access to high-level modules (search, http, data, files).
        
        Args:
            code: Python code to execute
            
        Returns:
            dict with success, output, error, artifacts, execution_time, layer
        """
        if not code:
            return {"success": False, "error": "No code provided", "layer": "INTERPRETER"}
        
        if len(code) > self._max_code_length:
            return {
                "success": False,
                "error": f"Code exceeds maximum length of {self._max_code_length} characters",
                "layer": "INTERPRETER"
            }
        
        # Execute in interpreter (always Layer 3)
        result = self._interpreter.execute(code)
        result_dict = result.to_dict()
        result_dict["layer"] = "INTERPRETER"
        return result_dict
    
    def _read_file(self, path: str, layer: str | None = None) -> dict[str, Any]:
        """Read file with optional layer specification."""
        if not path:
            return {"success": False, "error": "No path provided"}
            
        # Helper to convert string layer to enum if using layered workspace
        workspace_layer = None
        if layer and hasattr(self._workspace, 'get_layer_root'):
            from ..workspace.layered import WorkspaceLayer
            try:
                workspace_layer = WorkspaceLayer(layer.lower())
            except ValueError:
                pass  # Fallback to default behavior if invalid layer

        # If layered workspace, allow reading from specific layer
        if hasattr(self._workspace, 'read_file_from_layer') and workspace_layer:
             content = self._workspace.read_file_from_layer(path, workspace_layer)
        else:
             # Standard read (or auto-resolved in layered workspace)
             content = self._workspace.read_file(path)

        if content is None:
             return {"success": False, "error": f"File not found: {path} (layer: {layer})", "path": path}
             
        return {
            "success": True,
            "path": path,
            "content": content,
            "length": len(content),
            "layer": layer or "auto"
        }
    
    def _write_file(self, path: str, content: str, layer: str | None = None) -> dict[str, Any]:
        """Write file with optional layer specification."""
        if not path:
             return {"success": False, "error": "No path provided"}

        # Helper to convert string layer to enum
        workspace_layer = None
        if layer and hasattr(self._workspace, 'get_layer_root'):
             from ..workspace.layered import WorkspaceLayer
             try:
                 workspace_layer = WorkspaceLayer(layer.lower())
             except ValueError:
                 pass

        if hasattr(self._workspace, 'write_file_to_layer') and workspace_layer:
             success = self._workspace.write_file_to_layer(path, content, workspace_layer)
             return {
                 "success": success,
                 "path": path,
                 "bytes_written": len(content) if success else 0,
                 "layer": layer
             }
        
        # Original logic for default writing or INTERPRETER enforcement
        # If no explicit layer, check for enforcement (default behavior)
        if hasattr(self._workspace, 'enforce_layer_3_operation') and not layer:
             try:
                 safe_path = self._workspace.enforce_layer_3_operation("write_file", path)
                 safe_path.parent.mkdir(parents=True, exist_ok=True)
                 safe_path.write_text(content, encoding='utf-8')
                 return {"success": True, "path": path, "bytes_written": len(content), "layer": "INTERPRETER"}
             except Exception as e:
                 return {"success": False, "error": str(e), "layer": "INTERPRETER"}

        # Fallback
        success = self._workspace.create_file(path, content)
        return {"success": success, "path": path, "bytes_written": len(content) if success else 0}
    
    def _move_file(self, source: str, s_layer: str, dest: str, d_layer: str, copy: bool) -> dict[str, Any]:
        """Move/Copy file between layers."""
        if not hasattr(self._workspace, 'move_between_layers'):
            return {"success": False, "error": "Workspace does not support layering"}
            
        from ..workspace.layered import WorkspaceLayer
        try:
            sl = WorkspaceLayer(s_layer.lower())
            dl = WorkspaceLayer(d_layer.lower())
            
            success = self._workspace.move_between_layers(source, sl, dest, dl, copy_only=copy)
            return {"success": success, "source": f"{s_layer}:{source}", "dest": f"{d_layer}:{dest}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
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
            "tools": ["execute_code", "read_file", "write_file", "move_file"]
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
                    description="Execute Python code. Modules: weather, search, http, data, files.",
                ),
                StructuredTool.from_function(
                    func=lambda path, layer=None: self._read_file(path, layer),
                    name="read_file",
                    description="Read file. Args: path, layer (project/office/interpreter).",
                ),
                StructuredTool.from_function(
                    func=lambda path, content, layer=None: self._write_file(path, content, layer),
                    name="write_file",
                    description="Write file. Args: path, content, layer (project/office).",
                ),
                StructuredTool.from_function(
                    func=lambda source_path, source_layer, dest_path, dest_layer, copy_only=False: 
                        self._move_file(source_path, source_layer, dest_path, dest_layer, copy_only),
                    name="move_file",
                    description="Move/Copy between layers. Layers: project, office, interpreter.",
                ),
            ]
            
            return tools
        except ImportError:
            # LangChain not available
            return self.get_tools()

