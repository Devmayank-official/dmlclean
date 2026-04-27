"""
Clean Request/Result DTOs.

Pydantic v2 models for clean operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class CleanRequestMode(str, Enum):
    """Clean mode options."""

    DRY_RUN = "dry-run"
    TRASH = "trash"
    PERMANENT = "permanent"


class CleanProfile(str, Enum):
    """Cleaning profile options."""

    DEVELOPER = "developer"
    DESIGNER = "designer"
    SYSTEM_ADMIN = "system-admin"
    GAMER = "gamer"
    MINIMAL = "minimal"


class CleanRequest(BaseModel):
    """
    Clean operation request.

    Attributes:
        paths: Paths to clean.
        mode: Clean mode (dry-run, trash, permanent).
        profile: Cleaning profile.
        categories: Categories to include (None = all enabled).
        min_age_days: Minimum file age to clean.
        min_size_mb: Minimum file size to clean.
        force: Skip confirmation for permanent mode.
        dry_run: If True, preview only (overrides mode).
    """

    paths: list[Path] = Field(default_factory=list)
    mode: CleanRequestMode = Field(default=CleanRequestMode.DRY_RUN)
    profile: CleanProfile = Field(default=CleanProfile.DEVELOPER)
    categories: list[str] | None = Field(default=None)
    min_age_days: int = Field(default=0, ge=0)
    min_size_mb: int = Field(default=0, ge=0)
    force: bool = Field(default=False)
    dry_run: bool = Field(default=False)

    @field_validator("paths")
    @classmethod
    def validate_paths(cls, v: list[Path]) -> list[Path]:
        """Validate paths are not empty."""
        if not v:
            raise ValueError("At least one path is required")
        return v

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: CleanRequestMode) -> CleanRequestMode:
        """Validate mode and handle dry_run override."""
        return v

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "paths": [str(p) for p in self.paths],
            "mode": self.mode.value,
            "profile": self.profile.value,
            "categories": self.categories,
            "min_age_days": self.min_age_days,
            "min_size_mb": self.min_size_mb,
            "force": self.force,
            "dry_run": self.dry_run,
        }


@dataclass
class CleanResult:
    """
    Clean operation result.

    Attributes:
        success: Whether clean succeeded.
        operation_id: Unique operation identifier.
        mode: Clean mode used.
        profile: Profile used.
        files_deleted: Number of files deleted.
        files_failed: Number of files that failed to delete.
        files_skipped: Number of files skipped (protected).
        size_bytes: Total size freed.
        duration_ms: Operation duration in milliseconds.
        errors: List of errors.
        manifest_id: Associated manifest ID (if applicable).
    """

    success: bool = True
    operation_id: str = ""
    mode: str = "dry-run"
    profile: str = "developer"
    files_deleted: int = 0
    files_failed: int = 0
    files_skipped: int = 0
    size_bytes: int = 0
    duration_ms: int = 0
    errors: list[str] = field(default_factory=list)
    manifest_id: str | None = None

    @property
    def size_human(self) -> str:
        """Get human-readable size."""
        return self._humanize_size(self.size_bytes)

    @property
    def total_processed(self) -> int:
        """Get total files processed."""
        return self.files_deleted + self.files_failed + self.files_skipped

    @property
    def success_rate(self) -> str:
        """Get success rate as percentage."""
        total = self.files_deleted + self.files_failed
        if total == 0:
            return "100.0%"
        return f"{(self.files_deleted / total * 100):.1f}%"

    @staticmethod
    def _humanize_size(size_bytes: int) -> str:
        """Convert bytes to human-readable format."""
        size: float = size_bytes
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "operation_id": self.operation_id,
            "mode": self.mode,
            "profile": self.profile,
            "files_deleted": self.files_deleted,
            "files_failed": self.files_failed,
            "files_skipped": self.files_skipped,
            "total_processed": self.total_processed,
            "size_bytes": self.size_bytes,
            "size_human": self.size_human,
            "duration_ms": self.duration_ms,
            "success_rate": self.success_rate,
            "errors": self.errors,
            "manifest_id": self.manifest_id,
        }


__all__ = [
    "CleanProfile",
    "CleanRequest",
    "CleanRequestMode",
    "CleanResult",
]
