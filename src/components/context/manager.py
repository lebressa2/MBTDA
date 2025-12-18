"""
Context Manager for the Agent Framework.

Manages the agent's context dictionary which forms the system prompt.
Supports protocols, dynamic context injection, and template factories.
"""

import re
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from src.interfaces.context import IFormatter
from .templates import (
    SYSTEM_PROMPT_TEMPLATES,
    SystemPromptTemplate,
    TemplateRegistry,
    _deep_copy_dict
)

# ==============================================================================
# METADATA MODEL FOR DYNAMIC VARIABLES
# ==============================================================================

class MetaData(BaseModel):
    """
    Model for dynamic metadata that can be referenced in system prompts.

    This model provides common fields that are automatically updated
    and can be interpolated in the system prompt using {meta.field} syntax.

    Example:
        context.meta.agent_name = "Assistant"
        context.add("greeting", "Hello, I am {meta.agent_name}")
        # Result: "Hello, I am Assistant"
    """
    # Agent identity
    agent_name: str = Field(default="Agent", description="Name of the agent")
    agent_role: str = Field(default="AI Assistant", description="Role or persona")
    agent_version: str = Field(default="1.0.0", description="Agent version")

    # Session data
    session_id: str | None = Field(default=None, description="Current session ID")
    user_name: str | None = Field(default=None, description="Name of the current user")

    # Dynamic time fields (auto-updated on access)
    _cached_time: datetime | None = None

    @property
    def current_time(self) -> str:
        """Current time in ISO format (auto-updated)."""
        return datetime.now().isoformat()

    @property
    def current_date(self) -> str:
        """Current date in YYYY-MM-DD format."""
        return datetime.now().strftime("%Y-%m-%d")

    @property
    def current_datetime(self) -> str:
        """Current date and time formatted for display."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Custom fields dictionary for extensibility
    custom: dict[str, Any] = Field(default_factory=dict, description="Custom metadata fields")

    class Config:
        arbitrary_types_allowed = True

    def get_field(self, field_name: str) -> Any:
        """
        Get a field value by name, supporting dot notation for nested access.

        Args:
            field_name: Field name (e.g., "agent_name" or "custom.my_field")

        Returns:
            Field value or None if not found
        """
        if "." in field_name:
            parts = field_name.split(".", 1)
            if parts[0] == "custom" and parts[1] in self.custom:
                return self.custom[parts[1]]
            return None

        # Check for property (like current_time)
        if hasattr(self.__class__, field_name):
            attr = getattr(self.__class__, field_name)
            if isinstance(attr, property):
                return attr.fget(self)

        # Check for regular field
        if hasattr(self, field_name):
            return getattr(self, field_name)

        return None




def _deep_merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Deep merge two dictionaries.

    Override values take precedence. Nested dicts are merged recursively.
    """
    result = _deep_copy_dict(base)

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


from .formatters import DictToXMLFormatter, MarkdownFormatter


class ContextManager:
    """
    Manages the agent's context for system prompt generation.

    The ContextManager maintains a dictionary of context elements
    that are formatted into the agent's system prompt. It supports:

    - **Templates (Dictionaries)**: Pre-defined context structures that define
      the base context. Templates are DICTS, not strings.
    - **Dynamic Context (context.add)**: Add or override any field. Works in
      harmony with templates - templates provide base, add() extends/overrides.
    - **Dynamic Variables**: MetaData model with auto-updating fields
      that can be referenced using {meta.field} syntax in string values.
    - **Protocols**: Structured procedures for specific task types

    Key Design:
        - Templates are dictionaries that define base context structure
        - context.add(key, value) adds/overrides fields in the context
        - Template + context.add() are MERGED (deep merge) when generating output
        - Values can be ANY type (strings, dicts, lists, objects with __str__)
        - String values support {meta.field} interpolation

    Attributes:
        _template: Base template dictionary (from TemplateRegistry or custom)
        context: Dynamic context entries added via add()
        protocols: Dictionary of registered Protocol objects
        formatter: IFormatter instance for formatting context
        meta: MetaData instance for dynamic variables

    Example:
        # Using a template (dictionary-based)
        context = ContextManager(template="general_assistant")
        context.meta.agent_name = "MyAgent"

        # Add/override context - works in harmony with template
        context.add("custom_field", "my value")
        context.add("identity", {"name": "Override"})  # Overrides template's identity

        # Any parseable value works
        context.add("timestamp", datetime.now())  # Will be str() when formatted
        context.add("config", some_pydantic_model)  # Uses __str__ or model_dump
    """

    # Class-level default formatter
    base_formatter = DictToXMLFormatter()

    # Pattern for matching {meta.field} variables
    _META_PATTERN = re.compile(r'\{meta\.([a-zA-Z_][a-zA-Z0-9_.]*)\}')

    def __init__(
        self,
        formatter: IFormatter | None = None,
        template: str | dict[str, Any] | None = None,
        meta: MetaData | None = None,
        initial_context: dict[str, Any] | None = None
    ):
        """
        Initialize the ContextManager.

        Args:
            formatter: Optional formatter to use (defaults to DictToXMLFormatter)
            template: Template name (string) to load from registry, or a custom
                     template dictionary. Templates define the base context structure.
            meta: Optional MetaData instance for dynamic variables
            initial_context: Dictionary of context items to add immediately
        """
        self.formatter = formatter or self.base_formatter
        self.meta = meta or MetaData()
        
        # Load template
        self._template: dict[str, Any] = {}
        if isinstance(template, str):
            loaded = TemplateRegistry.get(template)
            if loaded:
                self._template = _deep_copy_dict(loaded)
        elif isinstance(template, dict):
            self._template = _deep_copy_dict(template)
            
        # Initialize dynamic context
        self.context: dict[str, Any] = {}

        # Add initial context if provided
        if initial_context:
            for key, value in initial_context.items():
                self.add(key, value)

        # Set up template (dictionary-based)
        if template is None:
            self._template: dict[str, Any] = {}
        elif isinstance(template, str):
            # Load from registry
            loaded = TemplateRegistry.get(template)
            self._template = loaded if loaded else {}
        elif isinstance(template, dict):
            # Direct dictionary template
            self._template = _deep_copy_dict(template)
        else:
            self._template = {}

    # ==========================================================================
    # FACTORY METHODS
    # ==========================================================================

    @classmethod
    def create_minimal(
        cls,
        agent_name: str = "Agent",
        agent_role: str = "AI Assistant"
    ) -> "ContextManager":
        """
        Create a minimal ContextManager with just identity.

        Args:
            agent_name: Name of the agent
            agent_role: Role/persona of the agent

        Returns:
            ContextManager configured with minimal template
        """
        meta = MetaData(agent_name=agent_name, agent_role=agent_role)
        return cls(template="minimal", meta=meta)

    @classmethod
    def create_general_assistant(
        cls,
        agent_name: str = "Assistant",
        agent_role: str = "AI Assistant",
        user_name: str | None = None,
        session_id: str | None = None
    ) -> "ContextManager":
        """
        Create a general-purpose assistant ContextManager.

        Includes detailed explanations of states and protocols
        suitable for most use cases.

        Args:
            agent_name: Name of the agent
            agent_role: Role/persona of the agent
            user_name: Optional name of the user
            session_id: Optional session identifier

        Returns:
            ContextManager configured with general assistant template
        """
        meta = MetaData(
            agent_name=agent_name,
            agent_role=agent_role,
            user_name=user_name,
            session_id=session_id
        )
        return cls(template="general_assistant", meta=meta)

    @classmethod
    def create_task_agent(
        cls,
        agent_name: str = "TaskAgent",
        session_id: str | None = None
    ) -> "ContextManager":
        """
        Create a task-oriented agent ContextManager.

        Optimized for structured task execution with protocols.

        Args:
            agent_name: Name of the agent
            session_id: Optional session identifier

        Returns:
            ContextManager configured with task agent template
        """
        meta = MetaData(
            agent_name=agent_name,
            agent_role="Task Execution Agent",
            session_id=session_id
        )
        return cls(template="task_agent", meta=meta)

    @classmethod
    def create_reactive_agent(
        cls,
        agent_name: str = "Monitor",
        session_id: str | None = None
    ) -> "ContextManager":
        """
        Create a reactive/monitoring agent ContextManager.

        Optimized for event-driven operation with inbox and task monitoring.

        Args:
            agent_name: Name of the agent
            session_id: Optional session identifier

        Returns:
            ContextManager configured with reactive agent template
        """
        meta = MetaData(
            agent_name=agent_name,
            agent_role="Reactive Monitoring Agent",
            session_id=session_id
        )
        return cls(template="reactive_agent", meta=meta)

    @classmethod
    def create_from_template(
        cls,
        template: dict[str, Any],
        agent_name: str = "Agent",
        agent_role: str = "AI Assistant",
        **meta_kwargs: Any
    ) -> "ContextManager":
        """
        Create a ContextManager with a custom template dictionary.

        Args:
            template: Custom template dictionary
            agent_name: Name of the agent
            agent_role: Role/persona of the agent
            **meta_kwargs: Additional MetaData fields (e.g., user_name, session_id)

        Returns:
            ContextManager configured with custom template

        Example:
            context = ContextManager.create_from_template(
                template={
                    "identity": {"name": "{meta.agent_name}"},
                    "custom_section": {"key": "value"}
                },
                agent_name="CustomBot",
                user_name="Alice"
            )
        """
        meta = MetaData(agent_name=agent_name, agent_role=agent_role)

        # Apply additional meta kwargs
        for key, value in meta_kwargs.items():
            if hasattr(meta, key):
                setattr(meta, key, value)
            else:
                meta.custom[key] = value

        return cls(template=template, meta=meta)

    # ==========================================================================
    # TEMPLATE OPERATIONS
    # ==========================================================================

    def set_template(self, template: str | dict[str, Any]) -> None:
        """
        Set or change the base template.

        Args:
            template: Template name (string) or template dictionary
        """
        if isinstance(template, str):
            loaded = TemplateRegistry.get(template)
            self._template = loaded if loaded else {}
        elif isinstance(template, dict):
            self._template = _deep_copy_dict(template)
        else:
            self._template = {}

    def get_template(self) -> dict[str, Any]:
        """Get a copy of the current template dictionary."""
        return _deep_copy_dict(self._template)

    # ==========================================================================
    # DYNAMIC VARIABLE INTERPOLATION
    # ==========================================================================

    def _interpolate_meta_variables(self, text: str) -> str:
        """
        Replace {meta.field} placeholders with actual values from MetaData.

        Args:
            text: String containing {meta.field} placeholders

        Returns:
            String with placeholders replaced by actual values
        """
        def replace_match(match: re.Match) -> str:
            field_name = match.group(1)
            value = self.meta.get_field(field_name)
            return str(value) if value is not None else match.group(0)

        return self._META_PATTERN.sub(replace_match, text)

    def _interpolate_value(self, value: Any) -> Any:
        """
        Recursively interpolate meta variables in values.

        Handles strings, dicts, lists, and any object with __str__.
        For non-string, non-container types, converts to string for interpolation
        if needed.

        Args:
            value: Value to interpolate

        Returns:
            Interpolated value
        """
        if isinstance(value, str):
            return self._interpolate_meta_variables(value)
        elif isinstance(value, dict):
            return {k: self._interpolate_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._interpolate_value(item) for item in value]
        elif hasattr(value, 'model_dump'):
            # Pydantic models - dump to dict and interpolate
            return self._interpolate_value(value.model_dump())
        else:
            # Any other type - keep as is (will be str() when formatted)
            return value

    # ==========================================================================
    # CONTEXT OPERATIONS
    # ==========================================================================

    def add(self, key: str, value: Any) -> None:
        """
        Add or update a context entry.

        This works in HARMONY with templates:
        - If a template defines the key, your value OVERRIDES it
        - If the template doesn't have the key, your value is ADDED
        - Deep merge applies to nested dictionaries

        Values can be ANY type:
        - Strings: Support {meta.field} interpolation
        - Dicts: Merged deeply with template/existing context
        - Lists: Replaced entirely
        - Objects: Must have __str__ or model_dump() for serialization
        - f-strings: work naturally: add("time", f"{datetime.now()}")

        Args:
            key: Context key (use dot notation for nested: "identity.name")
            value: Any value - strings, dicts, lists, objects with __str__

        Example:
            # Simple values
            context.add("greeting", "Hello {meta.user_name}!")
            context.add("timestamp", datetime.now())  # Any __str__ object

            # Override template section
            context.add("identity", {"custom_field": "value"})

            # f-strings work naturally
            context.add("info", f"Generated at {time.time()}")
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
        """Clear all dynamic context entries (but not template or protocols)."""
        self.context.clear()

    def keys(self) -> list[str]:
        """Get all dynamic context keys."""
        return list(self.context.keys())



    # ==========================================================================
    # FORMATTING OPERATIONS
    # ==========================================================================

    def _build_full_context(self) -> dict[str, Any]:
        """
        Build the complete context by merging template + dynamic context.

        Returns:
            Complete merged context dictionary with interpolated values
        """
        # Start with template as base
        full_context = _deep_copy_dict(self._template) if self._template else {}

        # Deep merge dynamic context (this includes contributions from components above)
        if self.context:
            full_context = _deep_merge_dicts(full_context, self.context)

        # Interpolate all meta variables
        return self._interpolate_value(full_context)

    def populate_system_message(self, formatter: IFormatter | None = None) -> str:
        """
        Generate the system message from template + context + protocols.

        This method:
        1. Starts with the template dictionary as base
        2. Deep merges dynamic context (context.add() values)
        3. Adds protocol information
        4. Interpolates all {meta.field} variables
        5. Formats using the configured formatter

        Args:
            formatter: Optional formatter to use (overrides instance formatter)

        Returns:
            str: Formatted system message
        """
        fmt = formatter or self.formatter
        full_context = self._build_full_context()
        return fmt.format(full_context) if full_context else ""

    def get_raw_context(self) -> dict[str, Any]:
        """
        Get the complete merged context dictionary.

        This is the MERGED result of template + context.add() + protocols,
        with all {meta.field} variables interpolated.

        Returns:
            Dict[str, Any]: Complete context dictionary
        """
        return self._build_full_context()

    def set_formatter(self, formatter: IFormatter) -> None:
        """
        Change the formatter used for generating system messages.

        Args:
            formatter: New formatter to use
        """
        self.formatter = formatter

    def build_system_prompt(self) -> str:
        """
        Build the complete system prompt from context.

        This is the main method for generating the agent's system prompt.
        It collects contributions from registered components and formats
        everything into a single string.

        Returns:
            str: The formatted system prompt ready for LLM consumption
        """
        # Generate the formatted system message
        return self.populate_system_message()


    # ==========================================================================
    # STATE SNAPSHOT
    # ==========================================================================

    def get_snapshot(self) -> dict[str, Any]:
        """
        Get a snapshot of the current context state.

        Returns:
            Dictionary containing template, context, and meta
        """
        return {
            "template": _deep_copy_dict(self._template),
            "context": dict(self.context),
            "meta": self.meta.model_dump()
        }

    def restore_snapshot(self, snapshot: dict[str, Any]) -> None:
        """
        Restore context from a snapshot.

        Args:
            snapshot: Previously captured snapshot dictionary
        """
        if "template" in snapshot:
            self._template = _deep_copy_dict(snapshot["template"])

        self.context = dict(snapshot.get("context", {}))

        if "meta" in snapshot:
            self.meta = MetaData(**snapshot["meta"])
