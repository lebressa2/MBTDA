"""
Tool Manager for the Agent Framework.
"""

from typing import Any

from src.interfaces.tools import IToolManager


class ToolManager(IToolManager):
    """Manages tool registration and execution."""



    def __init__(self):
        self._tools: dict[str, dict[str, Any]] = {}  # tool_name -> {tool, context, description}
        self._contexts: dict[str, list[str]] = {}  # context -> [tool_names]

    def register_tool(self, context: str, tool: Any) -> None:
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
        if contexts is None:
            return [t["tool"] for t in self._tools.values()]

        tools = []
        for ctx in contexts:
            for tool_name in self._contexts.get(ctx, []):
                tools.append(self._tools[tool_name]["tool"])
        return tools

    def get_tool_descriptions(self, contexts: list[str] | None = None) -> str:
        tools = self._tools.values() if contexts is None else [
            self._tools[name] for ctx in contexts
            for name in self._contexts.get(ctx, [])
        ]

        lines = ["Available Tools:"]
        for t in tools:
            lines.append(f"- {t['tool'].name if hasattr(t['tool'], 'name') else 'Unknown'}: {t['description']}")
        return "\n".join(lines)

    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        if tool_name not in self._tools:
            raise ValueError(f"Tool '{tool_name}' not found")

        tool = self._tools[tool_name]["tool"]
        if hasattr(tool, 'invoke'):
            return tool.invoke(kwargs)
        elif callable(tool):
            return tool(**kwargs)
        raise ValueError(f"Tool '{tool_name}' is not callable")

    def execute_tool_calls(self, tool_calls: list[dict]) -> list[dict]:
        """
        Execute a list of tool calls.

        Args:
            tool_calls: List of tool call dictionaries from LLM

        Returns:
            List of tool result messages
        """
        results = []
        for call in tool_calls:
            try:
                # Extract details based on format (LangChain vs OpenAI)
                if hasattr(call, 'get'):
                    name = call.get('name')
                    args = call.get('args', {})
                    call_id = call.get('id')
                else:
                    # Object access
                    name = getattr(call, 'name', None)
                    args = getattr(call, 'args', {})
                    call_id = getattr(call, 'id', None)

                if not name:
                    continue

                # Execute
                output = self.execute_tool(name, **args)

                # Format result
                results.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": name,
                    "content": str(output)
                })
            except Exception as e:
                results.append({
                    "role": "tool",
                    "tool_call_id": call.get('id') if hasattr(call, 'get') else getattr(call, 'id', None),
                    "name": name if 'name' in locals() else "unknown",
                    "content": f"Error: {str(e)}"
                })
        return results

    def get_snapshot(self) -> dict[str, Any]:
        """Get a snapshot of available tools for context injection."""
        descriptions = {}
        for name, info in self._tools.items():
            descriptions[name] = info["description"]
        return descriptions


