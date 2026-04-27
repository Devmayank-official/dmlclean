"""
Schedule-related models for DMLClean.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ScheduleJob(BaseModel):
    """
    A scheduled cleaning job.

    Attributes:
        id: Unique job identifier (UUID4).
        name: Human-readable job name.
        cron_expression: Cron expression (e.g., "0 3 * * *").
        human_readable: Natural language description (e.g., "Every day at 3 AM").
        enabled: Whether job is active.
        profile: Profile to use.
        scan_mode: Scan mode (fast, deep, custom).
        clean_mode: Clean mode (dry-run, trash, permanent).
        last_run: Last run timestamp (if any).
        next_run: Next scheduled run timestamp (if any).
        run_count: Total number of successful runs.
        created_at: Job creation timestamp.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Unique job identifier (UUID4)")
    name: str = Field(..., description="Human-readable job name")
    cron_expression: str = Field(..., description="Cron expression")
    human_readable: str | None = Field(None, description="Natural language description")
    enabled: bool = Field(default=True, description="Whether job is active")
    profile: str = Field(default="developer", description="Profile to use")
    scan_mode: str = Field(default="fast", description="Scan mode")
    clean_mode: str = Field(default="dry-run", description="Clean mode")
    last_run: datetime | None = Field(None, description="Last run timestamp")
    next_run: datetime | None = Field(None, description="Next scheduled run timestamp")
    run_count: int = Field(default=0, ge=0, description="Total successful runs")
    created_at: datetime = Field(..., description="Job creation timestamp")

    @property
    def is_active(self) -> bool:
        """Check if job is enabled and has a future next_run."""
        if not self.enabled:
            return False
        if self.next_run is None:
            return False
        return self.next_run > datetime.now()

    @property
    def is_overdue(self) -> bool:
        """Check if job is overdue (past next_run and still enabled)."""
        if not self.enabled:
            return False
        if self.next_run is None:
            return False
        return self.next_run < datetime.now()
