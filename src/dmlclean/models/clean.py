"""
Clean-related models for DMLClean.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CleanResult(BaseModel):
    """
    Result of a cleaning operation.

    Attributes:
        clean_id: Unique clean operation identifier (UUID4).
        timestamp: Clean operation timestamp.
        mode: Clean mode (dry-run, trash, permanent).
        profile: Profile used (if any).
        files_deleted: Number of files successfully deleted.
        size_freed_bytes: Total size freed in bytes.
        files_failed: Number of files that failed to delete.
        manifest_path: Path to deletion manifest (if applicable).
        duration_ms: Operation duration in milliseconds.
    """

    model_config = ConfigDict(frozen=True)

    clean_id: str = Field(..., description="Unique clean operation identifier (UUID4)")
    timestamp: datetime = Field(..., description="Clean operation timestamp")
    mode: str = Field(..., description="Clean mode (dry-run, trash, permanent)")
    profile: str | None = Field(None, description="Profile used")
    files_deleted: int = Field(..., ge=0, description="Number of files deleted")
    size_freed_bytes: int = Field(..., ge=0, description="Total size freed in bytes")
    files_failed: int = Field(..., ge=0, description="Number of files failed")
    manifest_path: str | None = Field(None, description="Path to deletion manifest")
    duration_ms: int = Field(..., ge=0, description="Operation duration in milliseconds")

    @property
    def size_freed_human(self) -> str:
        """Get human-readable size string."""
        return self._humanize_size(self.size_freed_bytes)

    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        total = self.files_deleted + self.files_failed
        if total == 0:
            return 100.0
        return (self.files_deleted / total) * 100

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
