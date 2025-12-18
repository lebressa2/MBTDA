from abc import ABC, abstractmethod
from typing import Any, List, Optional

class IInboxClient(ABC):
    """
    Interface for inbox management (email, messaging).
    """
    @abstractmethod
    def check_new_emails(self) -> List[Any]:
        """Check for new incoming messages."""
        pass

    @abstractmethod
    def send_email(self, to: str, subject: str, body: str,
                   cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None) -> bool:
        """Send a message."""
        pass

    @abstractmethod
    def mark_as_read(self, thread_id: str) -> bool:
        """Mark a message thread as read."""
        pass

    @abstractmethod
    def archive(self, thread_id: str) -> bool:
        """Archive a message thread."""
        pass
