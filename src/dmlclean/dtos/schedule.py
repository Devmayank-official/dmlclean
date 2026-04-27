"""
Schedule Request/Result DTOs.
"""

from __future__ import annotations

from dataclasses import field
from typing import Any

from pydantic import BaseModel


class ScheduleRequest(BaseModel):
    """Schedule creation request."""

    name: str
    cron_expression: str
    profile: str = "developer"
    clean_mode: str = "dry-run"
    categories: list[str] | None = None
    enabled: bool = True


class ScheduleEntry(BaseModel):
    """Schedule entry."""

    id: str
    name: str
    cron_expression: str
    profile: str
    clean_mode: str
    enabled: bool
    next_run: str | None = None


class ScheduleListResult(BaseModel):
    """Schedule list result."""

    schedules: list[ScheduleEntry] = field(default_factory=list)
    total: int = 0
    enabled_count: int = 0
    disabled_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "schedules": [s.model_dump() for s in self.schedules],
            "total": self.total,
            "enabled_count": self.enabled_count,
            "disabled_count": self.disabled_count,
        }


__all__ = ["ScheduleEntry", "ScheduleListResult", "ScheduleRequest"]
