from typing import Any
from ....interfaces.base import IFormatter

class MarkdownFormatter(IFormatter):
    """
    Formats a dictionary into Markdown structured text.

    Alternative formatter for agents that prefer Markdown prompts.
    """

    def format(self, context: dict[str, Any]) -> str:
        """
        Format a context dictionary into Markdown string.

        Args:
            context: Dictionary containing context data

        Returns:
            str: Markdown-formatted string representation
        """
        return self._format_dict(context, level=1)

    def _format_dict(self, data: dict[str, Any], level: int) -> str:
        """Recursively format a dictionary."""
        lines = []
        header_prefix = "#" * min(level, 6)

        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"\n{header_prefix} {key.replace('_', ' ').title()}\n")
                lines.append(self._format_dict(value, level + 1))
            elif isinstance(value, list):
                lines.append(f"\n{header_prefix} {key.replace('_', ' ').title()}\n")
                lines.append(self._format_list(value, level + 1))
            else:
                lines.append(f"**{key.replace('_', ' ').title()}:** {value}")

        return "\n".join(lines)

    def _format_list(self, data: list[Any], level: int) -> str:
        """Format a list of items."""
        lines = []

        for item in data:
            if isinstance(item, dict):
                for key, value in item.items():
                    lines.append(f"- **{key}:** {value}")
            else:
                lines.append(f"- {item}")

        return "\n".join(lines)
