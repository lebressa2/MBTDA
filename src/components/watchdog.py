"""
Watchdog Component for the Agent Framework.
"""

import time
import threading
from typing import Optional
from ..interfaces.base import IWatchdog


class Watchdog(IWatchdog):
    """Watchdog implementation for timeout and polling control."""
    
    def __init__(self, poll_interval: float = 30.0):
        self._timer_duration: Optional[float] = None
        self._timer_start: Optional[float] = None
        self._poll_interval: float = poll_interval
        self._is_running: bool = False
        self._lock = threading.Lock()
        self._timeout_callback: Optional[callable] = None
    
    def start_timer(self, duration_seconds: float) -> None:
        with self._lock:
            self._timer_duration = duration_seconds
            self._timer_start = time.time()
            self._is_running = True
    
    def stop_timer(self) -> None:
        with self._lock:
            self._is_running = False
            self._timer_duration = None
            self._timer_start = None
    
    def is_timed_out(self) -> bool:
        with self._lock:
            if not self._is_running or self._timer_start is None:
                return False
            elapsed = time.time() - self._timer_start
            return elapsed >= self._timer_duration
    
    def get_remaining_time(self) -> Optional[float]:
        with self._lock:
            if not self._is_running or self._timer_start is None:
                return None
            elapsed = time.time() - self._timer_start
            return max(0, self._timer_duration - elapsed)
    
    def get_poll_interval(self) -> float:
        return self._poll_interval
    
    def set_poll_interval(self, interval_seconds: float) -> None:
        if interval_seconds <= 0:
            raise ValueError("Poll interval must be positive")
        self._poll_interval = interval_seconds
    
    def reset(self) -> None:
        with self._lock:
            if self._is_running and self._timer_duration is not None:
                self._timer_start = time.time()
    
    def is_running(self) -> bool:
        return self._is_running
