from abc import ABC, abstractmethod

class IWatchdog(ABC):
    """
    Interface for watchdog monitoring.
    """
    @abstractmethod
    def start_timer(self, duration_seconds: float) -> None:
        """Start a timeout timer."""
        pass

    @abstractmethod
    def stop_timer(self) -> None:
        """Stop the timeout timer."""
        pass

    @abstractmethod
    def is_timed_out(self) -> bool:
        """Check if the timer has timed out."""
        pass

    @abstractmethod
    def get_remaining_time(self) -> float | None:
        """Get remaining time until timeout."""
        pass

    @abstractmethod
    def get_poll_interval(self) -> float:
        """Get the current poll interval."""
        pass

    @abstractmethod
    def set_poll_interval(self, interval_seconds: float) -> None:
        """Set the poll interval."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset the timer."""
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """Check if the watchdog is running."""
        pass
