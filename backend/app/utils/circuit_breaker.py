from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout_seconds: int = 90
    failure_count: int = 0
    opened_at: datetime | None = None
    _name: str = field(default="source", repr=False)

    def can_execute(self) -> bool:
        if self.opened_at is None:
            return True
        elapsed = datetime.now(timezone.utc) - self.opened_at
        return elapsed >= timedelta(seconds=self.recovery_timeout_seconds)

    def record_success(self) -> None:
        self.failure_count = 0
        self.opened_at = None

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.opened_at = datetime.now(timezone.utc)

    @property
    def state(self) -> str:
        if self.opened_at is None:
            return "closed"
        if self.can_execute():
            return "half-open"
        return "open"
