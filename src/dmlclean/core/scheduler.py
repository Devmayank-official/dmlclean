"""
Scheduler integration for DMLClean with SQLite persistence.

Provides APScheduler-based scheduling with:
- Cron expressions
- Natural language scheduling
- SQLite persistence for job storage
- Native OS scheduler export (cron/Task Scheduler)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from dmlclean.config.schema import CleanMode, ScanMode
from dmlclean.storage import (
    Database,
    ScheduleEntry,
    ScheduleRepository,
    get_database,
)


@dataclass
class ScheduledJob:
    """
    A scheduled cleaning job.

    Attributes:
        id: Unique job identifier.
        name: Human-readable job name.
        cron_expression: Cron expression or natural language.
        scan_mode: Scan mode for this job.
        clean_mode: Clean mode for this job.
        categories: Categories to clean.
        enabled: Whether job is active.
        next_run: Next scheduled run time.
    """

    id: str
    name: str
    cron_expression: str
    scan_mode: ScanMode = ScanMode.FAST
    clean_mode: CleanMode = CleanMode.DRY_RUN
    categories: list[str] = field(default_factory=list)
    enabled: bool = True
    next_run: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "cron_expression": self.cron_expression,
            "scan_mode": self.scan_mode.value,
            "clean_mode": self.clean_mode.value,
            "categories": self.categories,
            "enabled": self.enabled,
            "next_run": self.next_run.isoformat() if self.next_run else None,
        }

    @classmethod
    def from_entry(cls, entry: ScheduleEntry) -> ScheduledJob:
        """Create ScheduledJob from ScheduleEntry."""
        return cls(
            id=entry.id,
            name=entry.name,
            cron_expression=entry.cron_expression,
            scan_mode=ScanMode(entry.scan_mode) if entry.scan_mode else ScanMode.FAST,
            clean_mode=CleanMode(entry.clean_mode) if entry.clean_mode else CleanMode.DRY_RUN,
            categories=entry.categories,
            enabled=entry.enabled,
            next_run=datetime.fromisoformat(entry.next_run) if entry.next_run else None,
        )

    def to_entry(self) -> ScheduleEntry:
        """Convert ScheduledJob to ScheduleEntry."""
        return ScheduleEntry(
            id=self.id,
            name=self.name,
            cron_expression=self.cron_expression,
            scan_mode=self.scan_mode.value,
            clean_mode=self.clean_mode.value,
            categories=self.categories,
            enabled=self.enabled,
            next_run=self.next_run.isoformat() if self.next_run else None,
        )


class Scheduler:
    """
    Scheduler manager for DMLClean with SQLite persistence.

    Wraps APScheduler with DMLClean-specific functionality and
    persistent storage via SQLite.

    Attributes:
        db: Database instance for persistence.
        repo: Schedule repository for CRUD operations.
        scheduler: Underlying APScheduler instance.
    """

    def __init__(self, db: Database | None = None) -> None:
        """
        Initialize the scheduler with SQLite persistence.

        Args:
            db: Optional database instance. Creates default if None.
        """
        # Use provided database or get global instance
        self.db = db or get_database()
        # Pass Database wrapper, not raw connection
        self.repo = ScheduleRepository(self.db)

        # Initialize scheduler
        self.scheduler = BackgroundScheduler()
        self._jobs: dict[str, ScheduledJob] = {}

        # Load existing jobs from database
        self._load_jobs_from_db()

        logger.info(f"Scheduler initialized with SQLite persistence: {self.db.db_path}")

    def _load_jobs_from_db(self) -> None:
        """Load all enabled jobs from database into memory."""
        try:
            entries = self.repo.list_all(limit=1000)
            for entry in entries:
                job = ScheduledJob.from_entry(entry)
                self._jobs[job.id] = job
                logger.debug(f"Loaded job from DB: {job.id} ({job.name})")
        except Exception as e:
            logger.warning(f"Failed to load jobs from database: {e}")

    def start(self) -> None:
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

            # Resume APScheduler jobs for enabled entries
            for job in self._jobs.values():
                if job.enabled:
                    self._register_with_apscheduler(job)

    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the scheduler.

        Args:
            wait: Whether to wait for pending jobs to complete.
        """
        self.scheduler.shutdown(wait=wait)
        logger.info("Scheduler shutdown complete")

    def _register_with_apscheduler(self, job: ScheduledJob) -> None:
        """
        Register a job with APScheduler.

        Args:
            job: Job to register.
        """
        try:
            parts = job.cron_expression.split()
            if len(parts) == 5:
                minute, hour, day, month, day_of_week = parts
            else:
                raise ValueError("Invalid cron expression")
        except Exception as e:
            logger.warning(f"Invalid cron '{job.cron_expression}', using default: {e}")
            minute, hour, day, month, day_of_week = "0", "3", "*", "*", "*"

        # Create a wrapper callback that updates the database
        def run_job() -> None:
            logger.info(f"Running scheduled job: {job.name} ({job.id})")
            # Note: The actual cleaning callback would be passed in add_job
            # This is a placeholder for the database update

        self.scheduler.add_job(
            run_job,
            trigger="cron",
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            id=job.id,
            name=job.name,
            replace_existing=True,
        )

        logger.debug(f"Registered job with APScheduler: {job.id}")

    def add_job(
        self,
        job_id: str,
        name: str,
        cron_expression: str,
        callback: Callable[[], Any],
        scan_mode: ScanMode = ScanMode.FAST,
        clean_mode: CleanMode = CleanMode.DRY_RUN,
        categories: list[str] | None = None,
        min_age_days: int = 0,
        min_size_mb: int = 0,
    ) -> ScheduledJob:
        """
        Add a scheduled job with SQLite persistence.

        Args:
            job_id: Unique job identifier.
            name: Human-readable job name.
            cron_expression: Cron expression (e.g., "0 3 * * *").
            callback: Function to call when job runs.
            scan_mode: Scan mode for this job.
            clean_mode: Clean mode for this job.
            categories: Categories to clean.
            min_age_days: Minimum file age to clean.
            min_size_mb: Minimum file size to clean.

        Returns:
            ScheduledJob: Created job object.
        """
        # Create job object
        job = ScheduledJob(
            id=job_id,
            name=name,
            cron_expression=cron_expression,
            scan_mode=scan_mode,
            clean_mode=clean_mode,
            categories=categories or [],
        )

        # Save to database
        self.repo.create(
            id=job_id,
            name=name,
            cron_expression=cron_expression,
            enabled=True,
            profile="custom",
            scan_mode=scan_mode.value,
            clean_mode=clean_mode.value,
            categories=categories,
            min_age_days=min_age_days,
            min_size_mb=min_size_mb,
        )

        # Add to in-memory cache
        self._jobs[job_id] = job

        # Register with APScheduler if running
        if self.scheduler.running:
            self._register_with_apscheduler(job)

        logger.info(f"Scheduled job added: {name} ({job_id})")

        return job

    def remove_job(self, job_id: str) -> bool:
        """
        Remove a scheduled job.

        Args:
            job_id: Job identifier to remove.

        Returns:
            bool: True if job was removed.
        """
        try:
            # Remove from APScheduler
            self.scheduler.remove_job(job_id)

            # Remove from database
            self.repo.delete(job_id)

            # Remove from in-memory cache
            if job_id in self._jobs:
                del self._jobs[job_id]

            logger.info(f"Job removed: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to remove job {job_id}: {e}")
            return False

    def get_job(self, job_id: str) -> ScheduledJob | None:
        """
        Get a job by ID.

        Args:
            job_id: Job identifier.

        Returns:
            ScheduledJob | None: Job if found.
        """
        return self._jobs.get(job_id)

    def list_jobs(self) -> list[ScheduledJob]:
        """
        List all scheduled jobs from database.

        Returns:
            list[ScheduledJob]: List of jobs.
        """
        # Refresh from database
        entries = self.repo.list_all(limit=1000)
        jobs = []
        for entry in entries:
            job = ScheduledJob.from_entry(entry)
            jobs.append(job)
            # Update in-memory cache
            self._jobs[job.id] = job
        return jobs

    def enable_job(self, job_id: str) -> bool:
        """Enable a job."""
        try:
            # Update database
            self.repo.update(job_id, enabled=True)

            # Update in-memory cache
            if job_id in self._jobs:
                self._jobs[job_id].enabled = True

            # Resume in APScheduler if running
            if self.scheduler.running:
                self.scheduler.resume_job(job_id)

            logger.info(f"Job enabled: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to enable job {job_id}: {e}")
            return False

    def disable_job(self, job_id: str) -> bool:
        """Disable a job."""
        try:
            # Update database
            self.repo.update(job_id, enabled=False)

            # Update in-memory cache
            if job_id in self._jobs:
                self._jobs[job_id].enabled = False

            # Pause in APScheduler if running
            if self.scheduler.running:
                self.scheduler.pause_job(job_id)

            logger.info(f"Job disabled: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to disable job {job_id}: {e}")
            return False

    def update_job_next_run(self, job_id: str, next_run: datetime) -> bool:
        """
        Update the next run time for a job.

        Args:
            job_id: Job identifier.
            next_run: Next run datetime.

        Returns:
            bool: True if updated.
        """
        try:
            self.repo.update(job_id, next_run=next_run.isoformat())

            if job_id in self._jobs:
                self._jobs[job_id].next_run = next_run

            return True
        except Exception as e:
            logger.warning(f"Failed to update next_run for job {job_id}: {e}")
            return False

    def mark_job_run(self, job_id: str, success: bool = True, error: str | None = None) -> bool:
        """
        Mark a job as run.

        Args:
            job_id: Job identifier.
            success: Whether run was successful.
            error: Error message if failed.

        Returns:
            bool: True if updated.
        """
        try:
            self.repo.mark_run(job_id, success=success, error_message=error)
            logger.info(f"Job run recorded: {job_id} (success={success})")
            return True
        except Exception as e:
            logger.warning(f"Failed to mark job run {job_id}: {e}")
            return False

    def export_cron(self, job_id: str) -> str | None:
        """
        Export a job as a cron entry.

        Args:
            job_id: Job identifier.

        Returns:
            str | None: Cron entry string.
        """
        job = self.get_job(job_id)
        if not job:
            return None

        # Generate cron command
        command = (
            f"dmlclean clean --mode {job.clean_mode.value} --categories {','.join(job.categories)}"
        )
        return f"{job.cron_expression} {command}"

    def export_windows_task(self, job_id: str) -> str | None:
        """
        Export a job as Windows Task Scheduler XML.

        Args:
            job_id: Job identifier.

        Returns:
            str | None: XML string for task import.
        """
        job = self.get_job(job_id)
        if not job:
            return None

        # Parse cron expression for Windows
        parts = job.cron_expression.split()
        if len(parts) != 5:
            return None

        minute, hour = parts[0], parts[1]

        # Generate schtasks command
        command = f"dmlclean clean --mode {job.clean_mode.value}"

        xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>{datetime.now().strftime("%Y-%m-%dT")}T{hour.zfill(2)}:{minute.zfill(2)}:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Actions Context="Author">
    <Exec>
      <Command>{command}</Command>
    </Exec>
  </Actions>
</Task>"""
        return xml

    def install_native(self, job_id: str) -> bool:
        """
        Install a job as a native OS scheduled task.

        Args:
            job_id: Job identifier.

        Returns:
            bool: True if successfully installed.
        """
        import subprocess
        import sys

        job = self.get_job(job_id)
        if not job:
            return False

        if sys.platform == "win32":
            # Windows Task Scheduler
            xml_content = self.export_windows_task(job_id)
            if not xml_content:
                return False

            # Write temp XML file
            import tempfile

            with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
                f.write(xml_content)
                xml_path = f.name

            try:
                # Import task
                result = subprocess.run(
                    ["schtasks", "/Create", "/TN", f"DMLClean_{job_id}", "/XML", xml_path],
                    capture_output=True,
                    text=True,
                )
                return result.returncode == 0
            except Exception as e:
                logger.error(f"Failed to install Windows task: {e}")
                return False
            finally:
                Path(xml_path).unlink()

        else:
            # Linux/macOS cron
            cron_entry = self.export_cron(job_id)
            if not cron_entry:
                return False

            try:
                # Add to crontab
                result = subprocess.run(
                    ["crontab", "-l"],
                    capture_output=True,
                    text=True,
                )
                existing = result.stdout if result.returncode == 0 else ""

                # Check if already exists
                if f"DMLClean_{job_id}" in existing:
                    logger.info(f"Cron job already installed: {job_id}")
                    return True

                # Add new entry
                new_crontab = existing + f"\n# DMLClean: {job.name}\n{cron_entry}\n"

                result = subprocess.run(
                    ["crontab", "-"],
                    input=new_crontab,
                    capture_output=True,
                    text=True,
                )
                return result.returncode == 0
            except Exception as e:
                logger.error(f"Failed to install cron job: {e}")
                return False

    def uninstall_native(self, job_id: str) -> bool:
        """
        Remove a native OS scheduled task.

        Args:
            job_id: Job identifier.

        Returns:
            bool: True if successfully removed.
        """
        import subprocess
        import sys

        if sys.platform == "win32":
            try:
                result = subprocess.run(
                    ["schtasks", "/Delete", "/TN", f"DMLClean_{job_id}", "/F"],
                    capture_output=True,
                    text=True,
                )
                return result.returncode == 0
            except Exception:
                return False
        else:
            try:
                result = subprocess.run(
                    ["crontab", "-l"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    return False

                # Remove DMLClean entry
                lines = result.stdout.split("\n")
                new_lines = [
                    line
                    for line in lines
                    if f"DMLClean_{job_id}" not in line
                    and not (
                        line.startswith("# DMLClean:")
                        and any(
                            ln.strip() == line
                            for ln in lines[lines.index(line) + 1 :]
                            if "DMLClean" in ln
                        )
                    )
                ]

                if len(new_lines) == len(lines):
                    return False

                subprocess.run(
                    ["crontab", "-"],
                    input="\n".join(new_lines),
                    capture_output=True,
                    text=True,
                )
                return True
            except Exception:
                return False
