from typing import Any
from ....interfaces.base import IFormatter

class DictToXMLFormatter(IFormatter):
    """
    Formats a dictionary into XML-like structured text.

    This formatter converts nested dictionaries into a readable
    XML-style format for system prompts.
    """

    def __init__(self, indent: str = "  "):
        """
        Initialize the formatter.

        Args:
            indent: String to use for indentation
        """
        self.indent = indent

    def format(self, context: dict[str, Any]) -> str:
        """
        Format a context dictionary into XML-like string.

        Args:
            context: Dictionary containing context data

        Returns:
            str: XML-formatted string representation
        """
        return self._format_dict(context, level=0)

    def _format_dict(self, data: dict[str, Any], level: int) -> str:
        """Recursively format a dictionary."""
        lines = []
        prefix = self.indent * level

        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}<{key}>")
                lines.append(self._format_dict(value, level + 1))
                lines.append(f"{prefix}</{key}>")
            elif isinstance(value, list):
                lines.append(f"{prefix}<{key}>")
                lines.append(self._format_list(value, level + 1, key))
                lines.append(f"{prefix}</{key}>")
            else:
                lines.append(f"{prefix}<{key}>{self._escape_xml(str(value))}</{key}>")

        return "\n".join(lines)

    def _format_list(self, data: list[Any], level: int, parent_key: str) -> str:
        """Format a list of items."""
        lines = []
        prefix = self.indent * level
        item_tag = self._get_singular(parent_key)

        for item in data:
            if isinstance(item, dict):
                lines.append(f"{prefix}<{item_tag}>")
                lines.append(self._format_dict(item, level + 1))
                lines.append(f"{prefix}</{item_tag}>")
            else:
                lines.append(f"{prefix}<{item_tag}>{self._escape_xml(str(item))}</{item_tag}>")

        return "\n".join(lines)

    def _get_singular(self, plural: str) -> str:
        """Get a singular form of a plural word (simple heuristic)."""
        if plural.endswith("ies"):
            return plural[:-3] + "y"
        elif plural.endswith("s"):
            return plural[:-1]
        return plural + "_item"

    def _escape_xml(self, text: str) -> str:
        """Escape special XML characters."""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))
