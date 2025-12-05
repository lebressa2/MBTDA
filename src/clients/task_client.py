"""
Mock Task Client for testing and development.
"""

import uuid
from datetime import datetime

from ..interfaces.base import ITaskManager
from ..models.data_models import TaskItem, TaskStatus


class MockTaskClient(ITaskManager):
    """Mock implementation of ITaskManager for testing."""

    def __init__(self):
        self._tasks: dict[str, TaskItem] = {}

    def get_pending_tasks(self) -> list[TaskItem]:
        return [t for t in self._tasks.values() if t.status == TaskStatus.PENDING.value]

    def create_task(self, title: str, due_date: str | None = None,
                    priority: int = 1, description: str | None = None) -> str:
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        self._tasks[task_id] = TaskItem(
            task_id=task_id,
            title=title,
            due_date=due_date,
            priority=priority,
            description=description
        )
        return task_id

    def update_task_status(self, task_id: str, status: str) -> bool:
        if task_id in self._tasks:
            self._tasks[task_id].status = status
            return True
        return False

    def get_task(self, task_id: str) -> TaskItem | None:
        return self._tasks.get(task_id)

    def delete_task(self, task_id: str) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def get_overdue_tasks(self) -> list[TaskItem]:
        now = datetime.now().strftime("%Y-%m-%d")
        return [
            t for t in self._tasks.values()
            if t.due_date and t.due_date < now and t.status == TaskStatus.PENDING.value
        ]

