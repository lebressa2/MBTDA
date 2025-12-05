"""
Mock Inbox Client for testing and development.
"""

from typing import List, Optional
from datetime import datetime
import uuid
from ..interfaces.base import IInboxClient
from ..models.data_models import EmailMessage


class MockInboxClient(IInboxClient):
    """Mock implementation of IInboxClient for testing."""
    
    def __init__(self):
        self._emails: List[EmailMessage] = []
        self._sent_emails: List[dict] = []
        self._read_threads: set = set()
        self._archived_threads: set = set()
    
    def add_mock_email(self, subject: str, sender: str, body: str, is_urgent: bool = False) -> str:
        """Add a mock email for testing."""
        thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        email = EmailMessage(
            subject=subject,
            sender=sender,
            body_snippet=body[:100],
            is_urgent=is_urgent,
            thread_id=thread_id
        )
        self._emails.append(email)
        return thread_id
    
    def check_new_emails(self) -> List[EmailMessage]:
        unread = [e for e in self._emails if e.thread_id not in self._read_threads]
        return unread
    
    def send_email(self, to: str, subject: str, body: str, 
                   cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None) -> bool:
        self._sent_emails.append({
            "to": to, "subject": subject, "body": body,
            "cc": cc, "bcc": bcc, "sent_at": datetime.now().isoformat()
        })
        return True
    
    def mark_as_read(self, thread_id: str) -> bool:
        self._read_threads.add(thread_id)
        return True
    
    def archive(self, thread_id: str) -> bool:
        self._archived_threads.add(thread_id)
        return True
