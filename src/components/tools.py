"""
Tool Manager for the Agent Framework.
"""

from typing import Any

from ..interfaces.base import IToolManager


class ToolManager(IToolManager):
    """Manages tool registration and execution."""

    # Flag to enable/disable automatic context injection (default: True)
    inject_context: bool = True

    def __init__(self, inject_context: bool = True):
        self._tools: dict[str, dict[str, Any]] = {}  # tool_name -> {tool, context, description}
        self._contexts: dict[str, list[str]] = {}  # context -> [tool_names]
        self.inject_context = inject_context

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

    def get_context_contribution(self) -> dict[str, Any]:
        """
        Get tools context for injection into the agent's system prompt.
        
        Returns:
            dict with 'available_tools' key containing tool descriptions
        """
        if not self._tools:
            return {}
        
        return {
            "available_tools": self.get_tool_descriptions()
        }

