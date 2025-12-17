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
