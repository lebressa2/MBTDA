"""
Atomic Tool Manager for the Agent Framework.

Manages a registry of Tool objects and handles their execution.
"""

from typing import Any, Dict, List, Optional
from src.models.data_models import Tool, ToolCall, ToolResult
from src.interfaces.tools import IToolManager

class ToolManager(IToolManager):
    """
    Registry and executor for atomic Tools.
    
    This manager is 'dumb' - it doesn't know how to create tools,
    it only knows how to store, describe, and execute them.
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register_tool(self, tool: Tool) -> None:
        """
        Register a new atomic Tool.
        
        Args:
            tool: The Tool instance to register.
        """
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        """Retrieve a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        """List all registered tools."""
        return list(self._tools.values())

    def get_tool_descriptions(self) -> str:
        """
        Get a formatted string of all tool descriptions for the system prompt.
        """
        if not self._tools:
            return "No tools available."
            
        lines = ["Available Tools:"]
        for tool in self._tools.values():
            lines.append(f"- {tool.name}: {tool.description}")
        return "\n".join(lines)

    def get_tool_schemas(self) -> List[dict]:
        """
        Get JSON schemas for all tools (for LLM tool binding).
        """
        return [tool.get_schema() for tool in self._tools.values()]

    def execute_tool(self, name: str, **kwargs) -> Any:
        """
        Execute a tool by name with validation.
        """
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found.")
        
        return tool.execute(**kwargs)

    def execute_tool_calls(self, tool_calls: List[Any]) -> List[ToolResult]:
        """
        Execute a list of tool calls from the LLM.
        
        Args:
            tool_calls: List of objects with 'name', 'args' and 'id'.
            
        Returns:
            List[ToolResult]: The results of the executions.
        """
        results = []
        for call in tool_calls:
            # Extract info (handling different LLM response formats)
            try:
                name = getattr(call, 'name', call.get('name')) if hasattr(call, 'get') or hasattr(call, 'name') else None
                args = getattr(call, 'args', call.get('args', {{}}))
                call_id = getattr(call, 'id', call.get('id', 'unknown'))
                
                if not name: continue

                output = self.execute_tool(name, **args)
                results.append(ToolResult(
                    tool_call_id=call_id,
                    name=name,
                    content=str(output)
                ))
            except Exception as e:
                results.append(ToolResult(
                    tool_call_id=getattr(call, 'id', 'unknown'),
                    name=name if 'name' in locals() else "unknown",
                    content=f"Error: {str(e)}",
                    is_error=True
                ))
        return results

    # Backward compatibility for IToolManager interface if needed
    def get_tools(self, contexts: Optional[List[str]] = None) -> List[Any]:
        return self.list_tools()