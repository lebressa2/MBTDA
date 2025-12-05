"""
Data Models for the Agent Framework.

This module contains all Pydantic models used throughout the framework,
including models for emails, tasks, protocols, and state machine components.
"""

import contextlib
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ==============================================================================
# INBOX MODELS
# ==============================================================================

class EmailMessage(BaseModel):
    """
    Represents an email message for inbox monitoring.

    Used by the IInboxClient to represent incoming emails that may
    trigger reactive agent behavior.
    """
    subject: str = Field(..., description="Email subject line")
    sender: str = Field(..., description="Email sender address")
    body_snippet: str = Field(..., description="Preview of the email body")
    is_urgent: bool = Field(default=False, description="Whether the email is marked as urgent")
    thread_id: str = Field(..., description="Unique identifier for the email thread")
    received_at: datetime = Field(default_factory=datetime.now, description="When the email was received")

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Urgent: Project Update Required",
                "sender": "manager@company.com",
                "body_snippet": "Hi, please provide an update on...",
                "is_urgent": True,
                "thread_id": "thread_12345"
            }
        }


# ==============================================================================
# TASK MODELS
# ==============================================================================

class TaskStatus(str, Enum):
    """Enumeration of possible task statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class TaskItem(BaseModel):
    """
    Represents a task item for task monitoring.

    Used by the ITaskManager to represent tasks that may
    trigger reactive agent behavior.
    """
    task_id: str = Field(..., description="Unique identifier for the task")
    title: str = Field(..., description="Task title/name")
    due_date: str | None = Field(None, description="Due date in ISO format")
    priority: int = Field(default=1, ge=1, le=5, description="Priority level (1=lowest, 5=highest)")
    status: str = Field(default=TaskStatus.PENDING.value, description="Current task status")
    description: str | None = Field(None, description="Detailed task description")
    created_at: datetime = Field(default_factory=datetime.now, description="When the task was created")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task_001",
                "title": "Review code changes",
                "due_date": "2024-12-05",
                "priority": 3,
                "status": "pending"
            }
        }


# ==============================================================================
# PROTOCOL MODELS
# ==============================================================================

class ProtocolStep(BaseModel):
    """
    Represents a single step within a protocol.

    Protocols define structured procedures the agent follows
    for specific types of tasks or situations.
    """
    name: str = Field(..., description="Step name/identifier")
    goal: str = Field(..., description="What this step aims to achieve")
    instructions: list[str] = Field(..., description="List of instructions for this step")
    notes: str | None = Field(None, description="Additional notes or considerations")
    is_complete: bool = Field(default=False, description="Whether this step has been completed")

    def mark_complete(self) -> None:
        """Mark this step as complete."""
        self.is_complete = True

    def reset(self) -> None:
        """Reset this step to incomplete."""
        self.is_complete = False


class Protocol(BaseModel):
    """
    Represents a complete protocol with multiple steps.

    Protocols provide structured guidance for the agent to follow
    when handling specific types of situations or tasks.
    """
    protocol_name: str = Field(..., description="Unique name for the protocol")
    description: str = Field(..., description="What this protocol is for")
    steps: list[ProtocolStep] = Field(..., description="Ordered list of protocol steps")
    current_step_index: int = Field(default=0, description="Index of the current step")

    def get_current_step(self) -> ProtocolStep | None:
        """Get the current step in the protocol."""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def advance_step(self) -> bool:
        """
        Advance to the next step.

        Returns:
            bool: True if advanced successfully, False if already at the end
        """
        if self.current_step_index < len(self.steps) - 1:
            self.steps[self.current_step_index].mark_complete()
            self.current_step_index += 1
            return True
        return False

    def current_step_complete(self) -> bool:
        """Check if the current step is marked as complete."""
        current = self.get_current_step()
        return current.is_complete if current else True

    def is_complete(self) -> bool:
        """Check if all steps in the protocol are complete."""
        return all(step.is_complete for step in self.steps)

    def reset(self) -> None:
        """Reset the protocol to the beginning."""
        self.current_step_index = 0
        for step in self.steps:
            step.reset()


# ==============================================================================
# STATE MACHINE MODELS
# ==============================================================================

class AgentState(str, Enum):
    """
    Enumeration of possible agent states.

    These states define the agent's current mode of operation.
    """
    IDLE = "IDLE"
    THINKING = "THINKING"
    WORKING = "WORKING"
    MONITORING = "MONITORING"
    REQUEST_RECEIVED = "REQUEST_RECEIVED"
    INTERRUPTED = "INTERRUPTED"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"


class Transition(BaseModel):
    """
    Represents a state machine transition.

    Defines how the agent moves from one state to another,
    including conditions, triggers, and callback actions.
    """
    source: str = Field(..., description="Source state name")
    target: str = Field(..., description="Target state name")
    trigger: str = Field(..., description="Event that triggers this transition")
    condition: Any | None = Field(None, description="Callable condition that must be True")
    on_exit: Any | None = Field(None, description="Callback to execute when leaving source state")
    on_enter: Any | None = Field(None, description="Callback to execute when entering target state")
    priority: int = Field(default=0, description="Priority for competing transitions")

    class Config:
        arbitrary_types_allowed = True

    def can_transition(self, agent: Any) -> bool:
        """
        Check if this transition can be taken.

        Args:
            agent: The agent instance to check conditions against

        Returns:
            bool: True if the transition can be taken
        """
        if self.condition is None:
            return True
        try:
            return self.condition(agent)
        except Exception:
            return False

    def execute_on_exit(self, agent: Any) -> None:
        """Execute the on_exit callback if defined."""
        if self.on_exit:
            with contextlib.suppress(Exception):
                self.on_exit(agent)

    def execute_on_enter(self, agent: Any) -> None:
        """Execute the on_enter callback if defined."""
        if self.on_enter:
            with contextlib.suppress(Exception):
                self.on_enter(agent)


class AgentEvent(BaseModel):
    """
    Represents an event that can trigger agent behavior.

    Events can come from the inbox, task manager, user input,
    or internal agent processes.
    """
    event_type: str = Field(..., description="Type of event (e.g., 'inbox', 'task', 'user', 'internal')")
    source: str = Field(..., description="Source of the event")
    data: dict[str, Any] = Field(default_factory=dict, description="Event payload data")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the event occurred")
    priority: int = Field(default=1, ge=1, le=5, description="Event priority")

    @classmethod
    def from_email(cls, email: EmailMessage) -> "AgentEvent":
        """Create an event from an email message."""
        return cls(
            event_type="inbox",
            source="email",
            data=email.model_dump(),
            priority=5 if email.is_urgent else 2
        )

    @classmethod
    def from_task(cls, task: TaskItem) -> "AgentEvent":
        """Create an event from a task item."""
        return cls(
            event_type="task",
            source="task_manager",
            data=task.model_dump(),
            priority=task.priority
        )

    @classmethod
    def from_user_input(cls, message: str) -> "AgentEvent":
        """Create an event from user input."""
        return cls(
            event_type="user",
            source="user_input",
            data={"message": message},
            priority=4
        )
