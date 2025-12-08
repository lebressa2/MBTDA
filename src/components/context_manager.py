"""
Context Manager for the Agent Framework.

Manages the agent's context dictionary which forms the system prompt.
Supports protocols and dynamic context injection.
"""

from typing import Any

from ..interfaces.base import IFormatter, IContextProvider
from ..models.data_models import Protocol


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





class ContextManager:
    """
    Manages the agent's context for system prompt generation.

    The ContextManager maintains a dictionary of context elements
    that are formatted into the agent's system prompt. It also
    manages protocols that define structured procedures.

    It acts as the "Context Renderer", pulling data from registered providers.

    Attributes:
        context: Dictionary of context key-value pairs
        protocols: Dictionary of registered Protocol objects
        formatter: IFormatter instance for formatting context
        _providers: List of registered IContextProvider components
    """

    # Class-level default formatter
    base_formatter = DictToXMLFormatter()

    def __init__(self, formatter: IFormatter | None = None):
        """
        Initialize the ContextManager.

        Args:
            formatter: Optional formatter to use (defaults to DictToXMLFormatter)
        """
        self.context: dict[str, Any] = {}
        self.protocols: dict[str, Protocol] = {}
        self.formatter = formatter or self.base_formatter
        self._providers: list[IContextProvider] = []

    # ==========================================================================
    # CONTEXT OPERATIONS
    # ==========================================================================

    def add(self, key: str, value: Any) -> None:
        """
        Add or update a context entry.

        Args:
            key: Context key
            value: Context value (can be any type)
        """
        self.context[key] = value

    def get(self, key: str) -> Any | None:
        """
        Get a context value by key.

        Args:
            key: Context key to retrieve

        Returns:
            The value if found, None otherwise
        """
        return self.context.get(key, None)

    def remove(self, key: str) -> bool:
        """
        Remove a context entry.

        Args:
            key: Context key to remove

        Returns:
            bool: True if the key was found and removed
        """
        if key in self.context:
            del self.context[key]
            return True
        return False

    def update(self, updates: dict[str, Any]) -> None:
        """
        Update multiple context entries at once.

        Args:
            updates: Dictionary of updates to apply
        """
        self.context.update(updates)

    def clear(self) -> None:
        """Clear all context entries (but not protocols)."""
        self.context.clear()

    def keys(self) -> list[str]:
        """Get all context keys."""
        return list(self.context.keys())

    # ==========================================================================
    # PROTOCOL OPERATIONS
    # ==========================================================================

    def add_protocol(self, protocol: Protocol) -> None:
        """
        Register a protocol.

        Args:
            protocol: Protocol object to register
        """
        self.protocols[protocol.protocol_name] = protocol

    def get_protocol(self, protocol_name: str) -> Protocol | None:
        """
        Get a specific protocol by name.

        Args:
            protocol_name: Name of the protocol to retrieve

        Returns:
            Protocol if found, None otherwise
        """
        return self.protocols.get(protocol_name, None)

    def get_protocols(self, query: str) -> list[Protocol]:
        """
        Search for protocols matching a query.

        Args:
            query: Search query (matches against protocol names)

        Returns:
            List of matching Protocol objects
        """
        query_lower = query.lower()
        return [
            ptc for ptc in self.protocols.values()
            if query_lower in ptc.protocol_name.lower()
        ]

    def remove_protocol(self, protocol_name: str) -> bool:
        """
        Remove a protocol by name.

        Args:
            protocol_name: Name of the protocol to remove

        Returns:
            bool: True if the protocol was found and removed
        """
        if protocol_name in self.protocols:
            del self.protocols[protocol_name]
            return True
        return False

    def list_protocols(self) -> list[str]:
        """Get a list of all registered protocol names."""
        return list(self.protocols.keys())

    # ==========================================================================
    # PROVIDER OPERATIONS
    # ==========================================================================

    def register_provider(self, provider: IContextProvider) -> None:
        """
        Register a context provider.

        Args:
            provider: Component implementing IContextProvider
        """
        if provider not in self._providers:
            self._providers.append(provider)

    # ==========================================================================
    # FORMATTING OPERATIONS
    # ==========================================================================

    def populate_system_message(self, formatter: IFormatter | None = None) -> str:
        """
        Generate the system message from the current context.

        This method acts as the "render" cycle:
        1. Collects fresh state from all registered providers
        2. Merges with static context
        3. Resolves dynamic elements (like protocols)
        4. Formats into string

        Args:
            formatter: Optional formatter to use (overrides instance formatter)

        Returns:
            str: Formatted system message
        """
        full_context = self.get_raw_context()
        fmt = formatter or self.formatter
        return fmt.format(full_context)

    def get_raw_context(self) -> dict[str, Any]:
        """
        Get the raw dictionary that forms the system prompt.
        Collects data from all providers and merges with static context.

        Returns:
            Dict[str, Any]: The raw context dictionary including protocols and provider data
        """
        # Start with static context
        full_context = dict(self.context)

        # 1. Collect from providers
        for provider in self._providers:
            if getattr(provider, 'inject_context', True):
                try:
                    contribution = provider.get_context_contribution()
                    if contribution:
                        full_context.update(contribution)
                except Exception:
                    # Fail silently on provider errors during render
                    pass

        # 2. Handle Protocol Query (Dynamic Protocols)
        # If any provider requested protocols via 'protocol_query', fetch them
        if "protocol_query" in full_context and full_context["protocol_query"]:
            query = full_context["protocol_query"]
            matching_protocols = self.get_protocols(query)
            if matching_protocols:
                # Add to a temporary list or similar
                # We need to structure how protocols are shown.
                # Currently 'active_protocols' shows running protocols.
                # We might want 'suggested_protocols' or merge them?
                # For now let's append to active_protocols data if compatible,
                # or create a new key.
                pass 
                # Actually Agent logic was:
                # self.context.add("active_protocols", [p.model_dump() for p in protocols])
                # So it treats found protocols as active/available.
                
                # We need to convert to the display format expected by formatters
                # The formatter expects a dict or list.
                # Let's put them in a list under 'relevant_protocols'
                full_context["relevant_protocols"] = [p.model_dump() for p in matching_protocols]

        # 3. Add active/running protocols (managed by ContextManager)
        if self.protocols:
            protocols_data = {}
            for name, protocol in self.protocols.items():
                current_step = protocol.get_current_step()
                protocols_data[name] = {
                    "description": protocol.description,
                    "current_step": current_step.name if current_step else "completed",
                    "progress": f"{protocol.current_step_index + 1}/{len(protocol.steps)}",
                    "current_instructions": current_step.instructions if current_step else []
                }
            # Merge with existing active_protocols if any
            if "active_protocols" in full_context:
                if isinstance(full_context["active_protocols"], dict):
                    full_context["active_protocols"].update(protocols_data)
            else:
                full_context["active_protocols"] = protocols_data

        return full_context

    def set_formatter(self, formatter: IFormatter) -> None:
        """
        Change the formatter used for generating system messages.

        Args:
            formatter: New formatter to use
        """
        self.formatter = formatter

    # ==========================================================================
    # STATE SNAPSHOT
    # ==========================================================================

    def get_snapshot(self) -> dict[str, Any]:
        """
        Get a snapshot of the current context state.

        Returns:
            Dictionary containing context and protocol states
        """
        return {
            "context": dict(self.context),
            "protocols": {
                name: protocol.model_dump()
                for name, protocol in self.protocols.items()
            }
        }

    def restore_snapshot(self, snapshot: dict[str, Any]) -> None:
        """
        Restore context from a snapshot.

        Args:
            snapshot: Previously captured snapshot dictionary
        """
        self.context = dict(snapshot.get("context", {}))
        self.protocols = {}
        for name, protocol_data in snapshot.get("protocols", {}).items():
            self.protocols[name] = Protocol(**protocol_data)
