from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Task:
    task_name: str
    course: str
    deadline: datetime
    estimated_hours: float
    priority: int = 3
    task_type: str = "作业"
    description: str = ""

    @property
    def total_minutes(self) -> int:
        return int(float(self.estimated_hours) * 60)


@dataclass
class TimeSlot:
    start: datetime
    end: datetime
    source: str = "free"
    note: str = ""

    @property
    def minutes(self) -> int:
        return max(0, int((self.end - self.start).total_seconds() // 60))


@dataclass
class PlanItem:
    start: datetime
    end: datetime
    task_name: str
    course: str
    priority: int
    task_type: str
    note: str = ""
