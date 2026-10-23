"""Circuit Breaker and Adaptive Bulkhead Fallback.
100% Python Standard Library.
"""

import time
from typing import Dict, Any, Optional, Callable
from collections import deque


class CircuitBreakerState:
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerBulkhead:
    """Combines a 3-state circuit breaker with concurrency bulkhead isolation to prevent
    cascading system failures and execute graceful fallbacks."""

    def __init__(
        self,
        failure_rate_threshold: float = 0.50,
        recovery_timeout_seconds: float = 10.0,
        half_open_trial_limit: int = 3,
        sliding_window_size: int = 10,
        max_concurrent_calls: int = 5,
    ):
        self.failure_rate_threshold = failure_rate_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.half_open_trial_limit = half_open_trial_limit
        self.sliding_window_size = sliding_window_size
        self.max_concurrent_calls = max_concurrent_calls

        self.state = CircuitBreakerState.CLOSED
        self.opened_at: Optional[float] = None
        self.window: deque = deque(maxlen=sliding_window_size)
        self.consecutive_successes_in_half_open = 0
        self.active_concurrent_calls = 0

    def can_execute(self, now: Optional[float] = None) -> Dict[str, Any]:
        """Evaluates whether an execution call is permitted, blocked by open circuit, or rejected by bulkhead."""
        current_time = now if now is not None else time.time()

        # Check circuit breaker state transition: OPEN -> HALF_OPEN
        if self.state == CircuitBreakerState.OPEN:
            if self.opened_at and (current_time - self.opened_at) >= self.recovery_timeout_seconds:
                self.state = CircuitBreakerState.HALF_OPEN
                self.consecutive_successes_in_half_open = 0

        # If OPEN, fast fail
        if self.state == CircuitBreakerState.OPEN:
            remaining_cooldown = max(0.0, round(self.recovery_timeout_seconds - (current_time - (self.opened_at or 0)), 2))
            return {
                "allowed": False,
                "state": self.state,
                "reason": "CIRCUIT_OPEN",
                "remaining_cooldown_seconds": remaining_cooldown,
                "active_calls": self.active_concurrent_calls,
            }

        # Bulkhead concurrency check
        if self.active_concurrent_calls >= self.max_concurrent_calls:
            return {
                "allowed": False,
                "state": self.state,
                "reason": "BULKHEAD_FULL",
                "remaining_cooldown_seconds": 0.0,
                "active_calls": self.active_concurrent_calls,
                "max_concurrency": self.max_concurrent_calls,
            }

        self.active_concurrent_calls += 1
        return {
            "allowed": True,
            "state": self.state,
            "reason": "PERMITTED",
            "active_calls": self.active_concurrent_calls,
        }

    def record_success(self):
        """Records a successful execution."""
        self.active_concurrent_calls = max(0, self.active_concurrent_calls - 1)
        self.window.append(1)  # 1 = success

        if self.state == CircuitBreakerState.HALF_OPEN:
            self.consecutive_successes_in_half_open += 1
            if self.consecutive_successes_in_half_open >= self.half_open_trial_limit:
                # Successfully recovered -> reset to CLOSED
                self.state = CircuitBreakerState.CLOSED
                self.opened_at = None
                self.window.clear()

    def record_failure(self, now: Optional[float] = None):
        """Records a failed execution."""
        current_time = now if now is not None else time.time()
        self.active_concurrent_calls = max(0, self.active_concurrent_calls - 1)
        self.window.append(0)  # 0 = failure

        if self.state == CircuitBreakerState.HALF_OPEN:
            # Immediate trip back to OPEN upon trial failure
            self.state = CircuitBreakerState.OPEN
            self.opened_at = current_time
            return

        if self.state == CircuitBreakerState.CLOSED and len(self.window) >= self.sliding_window_size:
            failures = self.window.count(0)
            rate = failures / len(self.window)
            if rate >= self.failure_rate_threshold:
                self.state = CircuitBreakerState.OPEN
                self.opened_at = current_time

    def get_status(self) -> Dict[str, Any]:
        """Returns the current diagnostic state of the circuit breaker and bulkhead."""
        total_in_window = len(self.window)
        fail_count = self.window.count(0)
        failure_rate = round(fail_count / total_in_window, 3) if total_in_window > 0 else 0.0

        return {
            "state": self.state,
            "active_concurrent_calls": self.active_concurrent_calls,
            "max_concurrent_calls": self.max_concurrent_calls,
            "recent_failure_rate": failure_rate,
            "window_sample_size": total_in_window,
            "is_available": self.state != CircuitBreakerState.OPEN and self.active_concurrent_calls < self.max_concurrent_calls,
        }
