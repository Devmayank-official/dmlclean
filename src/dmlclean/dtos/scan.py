"""
Scan Request/Result DTOs.

Pydantic v2 models for scan operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ScanMode(str, Enum):
    """Scan mode options."""

    FAST = "fast"
    DEEP = "deep"
    CUSTOM = "custom"


class ScanStats(BaseModel):
    """
    Scan statistics.

    Attributes:
        total_files: Total files scanned.
        total_directories: Total directories scanned.
        total_size_bytes: Total size in bytes.
        errors: Number of errors.
        duration_seconds: Scan duration.
        files_per_second: Scan speed.
    """

    total_files: int = 0
    total_directories: int = 0
    total_size_bytes: int = 0
    errors: int = 0
    duration_seconds: float = 0.0
    files_per_second: float = 0.0

    @property
    def total_size_human(self) -> str:
        """Get human-readable size."""
        return self._humanize_size(self.total_size_bytes)

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
            "total_files": self.total_files,
            "total_directories": self.total_directories,
            "total_size_bytes": self.total_size_bytes,
            "total_size_human": self.total_size_human,
            "errors": self.errors,
            "duration_seconds": round(self.duration_seconds, 2),
            "files_per_second": round(self.files_per_second, 2),
        }


class ScanRequest(BaseModel):
    """
    Scan operation request.

    Attributes:
        paths: Paths to scan.
        mode: Scan mode (fast, deep, custom).
        categories: Categories to include (None = all enabled).
        follow_symlinks: Whether to follow symlinks.
        max_depth: Max directory depth (0 = unlimited).
        include_patterns: Glob patterns to include.
        exclude_patterns: Glob patterns to exclude.
    """

    paths: list[Path] = Field(default_factory=list)
    mode: ScanMode = Field(default=ScanMode.FAST)
    categories: list[str] | None = Field(default=None)
    follow_symlinks: bool = Field(default=False)
    max_depth: int = Field(default=0, ge=0)
    include_patterns: list[str] | None = Field(default=None)
    exclude_patterns: list[str] | None = Field(default=None)

    @field_validator("paths")
    @classmethod
    def validate_paths(cls, v: list[Path]) -> list[Path]:
        """Validate paths are not empty."""
        if not v:
            raise ValueError("At least one path is required")
        return v

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "paths": [str(p) for p in self.paths],
            "mode": self.mode.value,
            "categories": self.categories,
            "follow_symlinks": self.follow_symlinks,
            "max_depth": self.max_depth,
        }


@dataclass
class ScanResult:
    """
    Scan operation result.

    Attributes:
        success: Whether scan succeeded.
        mode: Scan mode used.
        paths_scanned: Number of paths scanned.
        total_files: Total files found.
        total_size_bytes: Total size found.
        candidates: Number of cleanable candidates.
        by_category: Breakdown by category.
        by_risk: Breakdown by risk level.
        stats: Scan statistics.
        errors: List of errors.
    """

    success: bool = True
    mode: str = "fast"
    paths_scanned: int = 0
    total_files: int = 0
    total_size_bytes: int = 0
    candidates: int = 0
    by_category: dict[str, dict[str, Any]] = field(default_factory=dict)
    by_risk: dict[str, dict[str, Any]] = field(default_factory=dict)
    stats: ScanStats | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def total_size_human(self) -> str:
        """Get human-readable size."""
        if self.stats:
            return self.stats.total_size_human
        return ScanStats._humanize_size(self.total_size_bytes)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "mode": self.mode,
            "paths_scanned": self.paths_scanned,
            "total_files": self.total_files,
            "total_size_bytes": self.total_size_bytes,
            "total_size_human": self.total_size_human,
            "candidates": self.candidates,
            "by_category": self.by_category,
            "by_risk": self.by_risk,
            "stats": self.stats.to_dict() if self.stats else None,
            "errors": self.errors,
        }


__all__ = [
    "ScanMode",
    "ScanRequest",
    "ScanResult",
    "ScanStats",
]
