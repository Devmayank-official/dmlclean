"""
Trend-related models for DMLClean.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DiskTrendPoint(BaseModel):
    """
    A single disk usage trend data point.

    Attributes:
        timestamp: Measurement timestamp.
        total_bytes: Total disk size in bytes.
        free_bytes: Free space in bytes.
        used_bytes: Used space in bytes.
    """

    model_config = ConfigDict(frozen=True)

    timestamp: datetime = Field(..., description="Measurement timestamp")
    total_bytes: int = Field(..., ge=0, description="Total disk size in bytes")
    free_bytes: int = Field(..., ge=0, description="Free space in bytes")
    used_bytes: int = Field(..., ge=0, description="Used space in bytes")

    @property
    def percent_used(self) -> float:
        """Get percentage of disk used."""
        if self.total_bytes == 0:
            return 0.0
        return (self.used_bytes / self.total_bytes) * 100

    @property
    def percent_free(self) -> float:
        """Get percentage of disk free."""
        if self.total_bytes == 0:
            return 0.0
        return (self.free_bytes / self.total_bytes) * 100

    @property
    def total_human(self) -> str:
        """Get human-readable total size."""
        return self._humanize_size(self.total_bytes)

    @property
    def free_human(self) -> str:
        """Get human-readable free space."""
        return self._humanize_size(self.free_bytes)

    @property
    def used_human(self) -> str:
        """Get human-readable used space."""
        return self._humanize_size(self.used_bytes)

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


class TrendSummary(BaseModel):
    """
    Summary of disk usage trends.

    Attributes:
        points: List of trend data points.
        growth_bytes_per_day: Average growth rate in bytes per day.
        projected_full_days: Days until disk is full (None if shrinking).
    """

    model_config = ConfigDict(frozen=True)

    points: list[DiskTrendPoint] = Field(
        default_factory=list,
        description="List of trend data points",
    )
    growth_bytes_per_day: float = Field(
        default=0.0,
        description="Average growth rate in bytes per day",
    )
    projected_full_days: int | None = Field(
        None,
        description="Days until disk is full (None if shrinking)",
    )

    @property
    def point_count(self) -> int:
        """Get number of data points."""
        return len(self.points)

    @property
    def is_growing(self) -> bool:
        """Check if disk usage is growing."""
        return self.growth_bytes_per_day > 0

    @property
    def is_shrinking(self) -> bool:
        """Check if disk usage is shrinking."""
        return self.growth_bytes_per_day < 0

    @property
    def latest_point(self) -> DiskTrendPoint | None:
        """Get the most recent trend point."""
        if not self.points:
            return None
        return max(self.points, key=lambda p: p.timestamp)

    @property
    def growth_human(self) -> str:
        """Get human-readable growth rate."""
        return self._humanize_size(abs(int(self.growth_bytes_per_day))) + "/day"

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
