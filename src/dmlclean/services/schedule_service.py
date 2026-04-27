# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Async schedule service for DMLClean.

Domain service for managing scheduled cleaning operations.
All methods are async for non-blocking I/O.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from loguru import logger

from dmlclean.domain.events import EventBus, ScheduleCreated
from dmlclean.exceptions import NotFoundError

if TYPE_CHECKING:
    from dmlclean.core.scheduler import Scheduler
    from dmlclean.storage.database import Database
    from dmlclean.storage.schedule_repo import ScheduleEntry, ScheduleRepository


class ScheduleService:
    """Async domain service for scheduled cleaning operations."""

    def __init__(
        self,
        db: Database,
        schedule_repo: ScheduleRepository,
        scheduler: Scheduler,
    ) -> None:
        self.db = db
        self.schedule_repo = schedule_repo
        self.scheduler = scheduler
        logger.debug("ScheduleService initialized")

    async def create_schedule_async(
        self,
        name: str,
        cron_expression: str,
        profile: str = "developer",
        scan_mode: str = "fast",
        clean_mode: str = "dry-run",
        categories: list[str] | None = None,
        min_age_days: int = 0,
        min_size_mb: int = 0,
        human_readable: str | None = None,
        enabled: bool = True,
    ) -> ScheduleEntry:
        """Create a new scheduled cleaning job (async)."""
        job_id = str(uuid.uuid4())

        entry = await self.schedule_repo.create_async(
            id=job_id,
            name=name,
            cron_expression=cron_expression,
            human_readable=human_readable,
            enabled=enabled,
            profile=profile,
            scan_mode=scan_mode,
            clean_mode=clean_mode,
            categories=categories,
            min_age_days=min_age_days,
            min_size_mb=min_size_mb,
        )

        EventBus.publish(
            ScheduleCreated(
                job_id=job_id,
                name=name,
                cron_expression=cron_expression,
                profile=profile,
                clean_mode=clean_mode,
                enabled=enabled,
            )
        )

        if enabled:
            self.scheduler.start()
            self.scheduler.add_job(
                job_id=job_id,
                name=name,
                cron_expression=cron_expression,
                callback=lambda: None,
                scan_mode=scan_mode,
                clean_mode=clean_mode,
                categories=categories,
                min_age_days=min_age_days,
                min_size_mb=min_size_mb,
            )

        logger.info(f"Schedule created: {job_id} ({name})")
        return entry

    async def get_schedule_async(self, job_id: str) -> ScheduleEntry | None:
        """Get a schedule by ID (async)."""
        return await self.schedule_repo.get_by_id_async(job_id)

    async def list_schedules_async(
        self,
        enabled: bool | None = None,
        limit: int = 100,
    ) -> list[ScheduleEntry]:
        """List all schedules (async)."""
        return await self.schedule_repo.list_all_async(limit=limit, enabled=enabled)

    async def remove_schedule_async(self, job_id: str) -> bool:
        """Remove a schedule (async)."""
        self.scheduler.remove_job(job_id)
        return await self.schedule_repo.delete_async(job_id)

    async def enable_schedule_async(self, job_id: str) -> bool:
        """Enable a schedule (async)."""
        entry = await self.get_schedule_async(job_id)
        if not entry:
            raise NotFoundError(f"Schedule not found: {job_id}")

        success = await self.schedule_repo.update_async(job_id, enabled=True)
        if success:
            self.scheduler.start()
            self.scheduler.enable_job(job_id)
        return success

    async def disable_schedule_async(self, job_id: str) -> bool:
        """Disable a schedule (async)."""
        entry = await self.get_schedule_async(job_id)
        if not entry:
            raise NotFoundError(f"Schedule not found: {job_id}")

        success = await self.schedule_repo.update_async(job_id, enabled=False)
        if success:
            self.scheduler.disable_job(job_id)
        return success

    # Sync wrappers
    def create_schedule(self, **kwargs: Any) -> ScheduleEntry:
        import asyncio

        return asyncio.run(self.create_schedule_async(**kwargs))

    def get_schedule(self, job_id: str) -> ScheduleEntry | None:
        import asyncio

        return asyncio.run(self.get_schedule_async(job_id))

    def list_schedules(self, enabled: bool | None = None, limit: int = 100) -> list[ScheduleEntry]:
        import asyncio

        return asyncio.run(self.list_schedules_async(enabled, limit))

    def remove_schedule(self, job_id: str) -> bool:
        import asyncio

        return asyncio.run(self.remove_schedule_async(job_id))

    def enable_schedule(self, job_id: str) -> bool:
        import asyncio

        return asyncio.run(self.enable_schedule_async(job_id))

    def disable_schedule(self, job_id: str) -> bool:
        import asyncio

        return asyncio.run(self.disable_schedule_async(job_id))


__all__ = ["ScheduleService"]
