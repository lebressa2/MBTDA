from abc import ABC, abstractmethod
from typing import Any, List, Optional

class ITaskManager(ABC):
    """
    Interface for task management.
    """
    @abstractmethod
    def get_pending_tasks(self) -> List[Any]:
        """Get all pending tasks."""
        pass

    @abstractmethod
    def create_task(self, title: str, due_date: Optional[str] = None,
                    priority: int = 1, description: Optional[str] = None) -> str:
        """Create a new task."""
        pass

    @abstractmethod
    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update the status of a task."""
        pass

    @abstractmethod
    def get_task(self, task_id: str) -> Optional[Any]:
        """Get a specific task by ID."""
        pass

    @abstractmethod
    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        pass

    @abstractmethod
    def get_overdue_tasks(self) -> List[Any]:
        """Get all overdue tasks."""
        pass
