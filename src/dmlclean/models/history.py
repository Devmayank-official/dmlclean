"""
History-related models for DMLClean.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HistoryEntry(BaseModel):
    """
    A cleaning history entry.

    Attributes:
        id: Unique entry identifier (UUID4).
        timestamp: Operation timestamp.
        mode: Clean mode used (dry-run, trash, permanent).
        profile: Profile used (if any).
        scan_mode: Scan mode used (fast, deep, custom).
        files_found: Number of files found during scan.
        files_deleted: Number of files actually deleted.
        size_bytes: Total size in bytes.
        duration_ms: Operation duration in milliseconds.
        categories: List of categories cleaned.
        status: Operation status (complete, partial, failed).
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Unique entry identifier (UUID4)")
    timestamp: datetime = Field(..., description="Operation timestamp")
    mode: str = Field(..., description="Clean mode (dry-run, trash, permanent)")
    profile: str | None = Field(None, description="Profile used")
    scan_mode: str = Field(..., description="Scan mode (fast, deep, custom)")
    files_found: int = Field(..., ge=0, description="Files found during scan")
    files_deleted: int = Field(..., ge=0, description="Files actually deleted")
    size_bytes: int = Field(..., ge=0, description="Total size in bytes")
    duration_ms: int = Field(..., ge=0, description="Operation duration in milliseconds")
    categories: list[str] = Field(default_factory=list, description="Categories cleaned")
    status: str = Field(..., description="Operation status (complete, partial, failed)")

    @property
    def size_human(self) -> str:
        """Get human-readable size string."""
        return self._humanize_size(self.size_bytes)

    @property
    def is_complete(self) -> bool:
        """Check if operation completed successfully."""
        return self.status == "complete"

    @staticmethod
    def _humanize_size(size_bytes: int) -> str:
        """Convert bytes to human-readable format."""
        size: float = size_bytes
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                if unit == "B":
                    return f"{int(size)} {unit}"
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"
