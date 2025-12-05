"""
Mock Task Client for testing and development.
"""

from typing import List, Optional, Any, Dict
from datetime import datetime
import uuid
from ..interfaces.base import ITaskManager
from ..models.data_models import TaskItem, TaskStatus


class MockTaskClient(ITaskManager):
    """Mock implementation of ITaskManager for testing."""
    
    def __init__(self):
        self._tasks: Dict[str, TaskItem] = {}
    
    def get_pending_tasks(self) -> List[TaskItem]:
        return [t for t in self._tasks.values() if t.status == TaskStatus.PENDING.value]
    
    def create_task(self, title: str, due_date: Optional[str] = None,
                    priority: int = 1, description: Optional[str] = None) -> str:
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
    
    def get_task(self, task_id: str) -> Optional[TaskItem]:
        return self._tasks.get(task_id)
    
    def delete_task(self, task_id: str) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False
    
    def get_overdue_tasks(self) -> List[TaskItem]:
        now = datetime.now().strftime("%Y-%m-%d")
        return [
            t for t in self._tasks.values()
            if t.due_date and t.due_date < now and t.status == TaskStatus.PENDING.value
        ]

