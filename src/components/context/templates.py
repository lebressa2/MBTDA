"""
System Prompt Templates for the Agent Framework.

This module contains pre-defined templates for different agent types
and a registry for managing custom templates.
"""

from enum import Enum
from typing import Any


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
        "guidelines": [
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