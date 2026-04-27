"""
Scan-related models for DMLClean.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ScanStats(BaseModel):
    """
    Statistics from a scan operation.

    Attributes:
        total_files: Total number of files scanned.
        total_dirs: Total number of directories scanned.
        total_size_bytes: Total size of all scanned files.
        duration_ms: Scan duration in milliseconds.
        categories_found: Number of files per category.
    """

    model_config = ConfigDict(frozen=True)

    total_files: int = Field(..., ge=0, description="Total number of files scanned")
    total_dirs: int = Field(..., ge=0, description="Total number of directories scanned")
    total_size_bytes: int = Field(..., ge=0, description="Total size in bytes")
    duration_ms: int = Field(..., ge=0, description="Scan duration in milliseconds")
    categories_found: dict[str, int] = Field(
        default_factory=dict,
        description="Number of files per category",
    )

    @property
    def total_size_human(self) -> str:
        """Get human-readable size string."""
        return self._humanize_size(self.total_size_bytes)

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


class CleanCandidate(BaseModel):
    """
    A file or directory identified for potential cleaning.

    Attributes:
        path: Absolute path to the item.
        category: Cleaning category name.
        size_bytes: Size in bytes.
        risk_level: Assigned risk level (low, medium, high, blocked).
        reason: Why this item was identified for cleaning.
        last_accessed: Last access timestamp (Unix timestamp).
        last_modified: Last modification timestamp (Unix timestamp).
        is_directory: Whether this is a directory.
        hash_value: File hash (for duplicate detection).
        metadata: Additional metadata.
    """

    model_config = ConfigDict(frozen=True)

    path: str = Field(..., description="Absolute path to the item")
    category: str = Field(..., description="Cleaning category name")
    size_bytes: int = Field(..., ge=0, description="Size in bytes")
    risk_level: str = Field(..., description="Risk level (low, medium, high, blocked)")
    reason: str = Field(..., description="Reason for identification")
    last_accessed: float | None = Field(None, description="Last access timestamp")
    last_modified: float | None = Field(None, description="Last modification timestamp")
    is_directory: bool = Field(default=False, description="Whether this is a directory")
    hash_value: str | None = Field(None, description="File hash for duplicate detection")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @property
    def size_human(self) -> str:
        """Get human-readable size string."""
        size: float = self.size_bytes
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                if unit == "B":
                    return f"{int(size)} {unit}"
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"


class ScanResult(BaseModel):
    """
    Result of a scan operation.

    Attributes:
        scan_id: Unique scan identifier (UUID4).
        timestamp: Scan timestamp.
        mode: Scan mode (fast, deep, custom).
        profile: Profile used (if any).
        stats: Scan statistics.
        candidates: List of clean candidates identified.
    """

    model_config = ConfigDict(frozen=True)

    scan_id: str = Field(..., description="Unique scan identifier (UUID4)")
    timestamp: datetime = Field(..., description="Scan timestamp")
    mode: str = Field(..., description="Scan mode (fast, deep, custom)")
    profile: str | None = Field(None, description="Profile used")
    stats: ScanStats = Field(..., description="Scan statistics")
    candidates: list[CleanCandidate] = Field(
        default_factory=list,
        description="List of clean candidates",
    )

    @property
    def total_candidates(self) -> int:
        """Get total number of candidates."""
        return len(self.candidates)

    @property
    def total_size_bytes(self) -> int:
        """Get total size of all candidates."""
        return sum(c.size_bytes for c in self.candidates)
