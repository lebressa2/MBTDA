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

from ..interfaces.base import IFormatter
from ..models.data_models import Protocol

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


# ==============================================================================
# SYSTEM PROMPT TEMPLATES (DICTIONARY-BASED)
# ==============================================================================

class SystemPromptTemplate(str, Enum):
    """
    Pre-defined system prompt template identifiers.

    Templates are DICTIONARIES that define the base context structure.
    They work in harmony with context.add() - templates provide the base,
    context.add() can add or override any field.
    """

    # Minimal template - just identity
    MINIMAL = "minimal"

    # General purpose assistant
    GENERAL_ASSISTANT = "general_assistant"

    # Task-oriented agent with protocols
    TASK_AGENT = "task_agent"

    # Reactive/monitoring agent
    REACTIVE_AGENT = "reactive_agent"


# Template content dictionary - each template is a DICT structure
SYSTEM_PROMPT_TEMPLATES: dict[str, dict[str, Any]] = {
    "minimal": {
        "identity": {
            "name": "{meta.agent_name}",
            "role": "{meta.agent_role}",
        }
    },

    "general_assistant": {
        "identity": {
            "name": "{meta.agent_name}",
            "role": "{meta.agent_role}",
            "description": "An AI assistant designed to help users accomplish their goals efficiently. Has access to tools and can execute actions to complete tasks."
        },
        "session": {
            "datetime": "{meta.current_datetime}",
            "session_id": "{meta.session_id}",
            "user": "{meta.user_name}"
        },
        "states_explanation": {
            "description": "You operate in different states that guide your behavior.",
            "states": {
                "IDLE": "Awaiting new instructions. Be ready to receive and understand requests.",
                "REQUEST_RECEIVED": "A new request has arrived. Acknowledge and begin processing.",
                "THINKING": "Analyze the request, plan your approach, and decide on actions.",
                "WORKING": "Execute tools and actions to accomplish the task.",
                "MONITORING": "(Reactive mode) Observing for events like new emails or tasks.",
                "INTERRUPTED": "Operation was interrupted. Assess the situation and recover."
            },
            "note": "Your current state indicates what mode of operation you should be in."
        },
        "protocols_explanation": {
            "description": "Protocols are structured procedures you follow for specific types of tasks.",
            "structure": {
                "steps": "Ordered sequence of actions to complete",
                "goals": "What each step aims to achieve",
                "instructions": "Specific guidance for each step"
            },
            "behavior": "When a protocol is active, follow its steps sequentially. Mark steps as complete before moving to the next."
        },
        "guidelines": [
            "Always consider the current state when responding",
            "If a protocol is active, follow its current step's instructions",
            "Use available tools when they can help accomplish the task",
            "Be clear and helpful in your responses",
            "If you're unsure, ask clarifying questions"
        ]
    },

    "task_agent": {
        "identity": {
            "name": "{meta.agent_name}",
            "role": "Task Execution Agent",
            "description": "Specializes in completing tasks methodically by following protocols and using tools. Excels at structured problem-solving and step-by-step execution."
        },
        "session": {
            "datetime": "{meta.current_datetime}",
            "session_id": "{meta.session_id}"
        },
        "operating_modes": {
            "IDLE": "Ready and waiting for a new task assignment",
            "REQUEST_RECEIVED": "New task received - acknowledge and prepare to process",
            "THINKING": "Planning phase - analyze requirements, break down the task",
            "WORKING": "Execution phase - use tools and perform actions",
            "INTERRUPTED": "Handle interruption gracefully, save state if needed"
        },
        "protocol_system": {
            "description": "Protocols define HOW to complete specific types of tasks",
            "workflow": [
                "Protocol Activation: When a relevant protocol exists, it will be loaded into your context",
                "Step Progression: Complete each step before moving to the next",
                "Instructions: Each step has specific instructions - follow them carefully",
                "Completion: Mark a protocol complete when all steps are done"
            ],
            "structure": {
                "protocol_name": "Unique identifier",
                "description": "What the protocol accomplishes",
                "steps": "List of ProtocolStep objects with name, goal, and instructions",
                "current_step_index": "Which step you're currently on"
            }
        },
        "tool_usage": [
            "Identify the appropriate tool for the action",
            "Prepare the correct arguments",
            "Execute the tool call",
            "Process the result and continue"
        ],
        "execution_principles": [
            "Be methodical and thorough",
            "Document your reasoning",
            "Verify results before reporting completion",
            "Handle errors gracefully"
        ]
    },

    "reactive_agent": {
        "identity": {
            "name": "{meta.agent_name}",
            "role": "Reactive Monitoring Agent",
            "purpose": "Continuously observe event sources (inbox, tasks, etc.) and respond to events as they occur. Operates mainly in MONITORING state, transitioning to THINKING/WORKING when events require action."
        },
        "session": {
            "datetime": "{meta.current_datetime}",
            "session_id": "{meta.session_id}",
            "monitoring_active": True
        },
        "state_machine": {
            "MONITORING": {
                "type": "Primary State",
                "description": "Actively observing event sources",
                "behavior": "Waiting for new emails, tasks, or other triggers. Low resource consumption, high alertness."
            },
            "REQUEST_RECEIVED": {
                "type": "Trigger State",
                "description": "An event has been detected",
                "behavior": "Transition here when processing begins."
            },
            "THINKING": {
                "type": "Analysis State",
                "description": "Evaluate the event/request",
                "behavior": "Determine appropriate response. Plan any necessary actions."
            },
            "WORKING": {
                "type": "Action State",
                "description": "Execute tools and actions",
                "behavior": "Process the event. Generate responses."
            },
            "IDLE": {
                "type": "Standby State",
                "description": "Not monitoring",
                "behavior": "Waiting for explicit activation."
            }
        },
        "event_handling": {
            "workflow": [
                "Identify event type (inbox, task, user, internal)",
                "Assess priority (1-5, higher = more urgent)",
                "Determine required actions",
                "Execute response",
                "Return to monitoring"
            ],
            "event_types": {
                "inbox": "New email received - check sender, subject, urgency",
                "task": "Task update - check priority, due date, status",
                "user": "Direct user input - highest priority, respond immediately",
                "internal": "System events - handle based on type"
            }
        },
        "priorities": [
            "Urgent emails (is_urgent=True) → Immediate attention",
            "High-priority tasks (priority >= 4) → Process soon",
            "Regular events → Handle in order",
            "System events → Process as appropriate"
        ]
    }
}


class TemplateRegistry:
    """
    Registry for system prompt templates.

    Allows users to register custom templates as dictionaries.
    Templates define the base context structure that works in
    harmony with context.add() operations.

    Example:
        # Register a custom template
        TemplateRegistry.register("my_agent", {
            "identity": {"name": "{meta.agent_name}", "role": "Custom Role"},
            "custom_section": {"key": "value"}
        })

        # Use it
        context = ContextManager(template="my_agent")
    """

    _custom_templates: dict[str, dict[str, Any]] = {}

    @classmethod
    def register(cls, name: str, template: dict[str, Any]) -> None:
        """
        Register a custom template.

        Args:
            name: Unique template name
            template: Dictionary defining the template structure

        Example:
            TemplateRegistry.register("code_assistant", {
                "identity": {
                    "name": "{meta.agent_name}",
                    "role": "Code Assistant",
                    "expertise": ["Python", "JavaScript", "SQL"]
                },
                "behavior": {
                    "style": "concise",
                    "format_preference": "markdown"
                }
            })
        """
        cls._custom_templates[name] = template

    @classmethod
    def get(cls, name: str) -> dict[str, Any] | None:
        """
        Get a template by name.

        Checks custom templates first, then built-in templates.

        Args:
            name: Template name

        Returns:
            Template dictionary or None if not found
        """
        # Check custom templates first
        if name in cls._custom_templates:
            return _deep_copy_dict(cls._custom_templates[name])

        # Check built-in templates
        if name in SYSTEM_PROMPT_TEMPLATES:
            return _deep_copy_dict(SYSTEM_PROMPT_TEMPLATES[name])

        return None

    @classmethod
    def list_templates(cls) -> list[str]:
        """Get list of all available template names."""
        builtin = list(SYSTEM_PROMPT_TEMPLATES.keys())
        custom = list(cls._custom_templates.keys())
        return builtin + custom

    @classmethod
    def unregister(cls, name: str) -> bool:
        """
        Remove a custom template.

        Args:
            name: Template name to remove

        Returns:
            True if removed, False if not found
        """
        if name in cls._custom_templates:
            del cls._custom_templates[name]
            return True
        return False


def _deep_copy_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Deep copy a dictionary."""
    result = {}
    for key, value in d.items():
        if isinstance(value, dict):
            result[key] = _deep_copy_dict(value)
        elif isinstance(value, list):
            result[key] = [_deep_copy_dict(item) if isinstance(item, dict) else item for item in value]
        else:
            result[key] = value
    return result


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
        meta: MetaData | None = None
    ):
        """
        Initialize the ContextManager.

        Args:
            formatter: Optional formatter to use (defaults to DictToXMLFormatter)
            template: Template name (string) to load from registry, or a custom
                     template dictionary. Templates define the base context structure.
            meta: Optional MetaData instance for dynamic variables

        Example:
            # Using a built-in template by name
            ctx = ContextManager(template="general_assistant")

            # Using a custom template dictionary
            ctx = ContextManager(template={
                "identity": {"name": "{meta.agent_name}", "role": "Custom"},
                "behavior": {"style": "concise"}
            })
        """
        self.context: dict[str, Any] = {}
        self.protocols: dict[str, Protocol] = {}
        self.formatter = formatter or self.base_formatter
        self.meta = meta or MetaData()

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
    # FORMATTING OPERATIONS
    # ==========================================================================

    def _build_full_context(self) -> dict[str, Any]:
        """
        Build the complete context by merging template + dynamic context + protocols.

        Returns:
            Complete merged context dictionary with interpolated values
        """
        # Start with template as base
        full_context = _deep_copy_dict(self._template) if self._template else {}

        # Deep merge dynamic context (overrides template)
        if self.context:
            full_context = _deep_merge_dicts(full_context, self.context)

        # Add active protocols
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
            full_context["active_protocols"] = protocols_data

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

    # ==========================================================================
    # STATE SNAPSHOT
    # ==========================================================================

    def get_snapshot(self) -> dict[str, Any]:
        """
        Get a snapshot of the current context state.

        Returns:
            Dictionary containing template, context, protocols, and meta
        """
        return {
            "template": _deep_copy_dict(self._template),
            "context": dict(self.context),
            "protocols": {
                name: protocol.model_dump()
                for name, protocol in self.protocols.items()
            },
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

        self.protocols = {}
        for name, protocol_data in snapshot.get("protocols", {}).items():
            self.protocols[name] = Protocol(**protocol_data)

        if "meta" in snapshot:
            self.meta = MetaData(**snapshot["meta"])
