"""
Manifest-related models for DMLClean.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ManifestEntry(BaseModel):
    """
    A single entry in a deletion manifest.

    Attributes:
        path: Absolute path to the file or directory.
        size_bytes: Size in bytes.
        xxhash: xxhash fingerprint of the file.
        deleted_at: Deletion timestamp.
        mode: Clean mode used (dry-run, trash, permanent).
        category: Cleaning category that identified this file.
        risk_level: Risk level assigned (low, medium, high, blocked).
    """

    model_config = ConfigDict(frozen=True)

    path: str = Field(..., description="Absolute path to the file")
    size_bytes: int = Field(..., ge=0, description="Size in bytes")
    xxhash: str = Field(..., description="xxhash fingerprint")
    deleted_at: datetime = Field(..., description="Deletion timestamp")
    mode: str = Field(..., description="Clean mode used")
    category: str = Field(..., description="Cleaning category")
    risk_level: str = Field(..., description="Risk level")

    @property
    def size_human(self) -> str:
        """Get human-readable size string."""
        return self._humanize_size(self.size_bytes)

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


class ManifestRecord(BaseModel):
    """
    A complete deletion manifest record.

    Attributes:
        manifest_id: Unique manifest identifier (UUID4).
        created_at: Manifest creation timestamp.
        mode: Clean mode used.
        total_files: Total number of files in manifest.
        total_size_bytes: Total size of all files.
        entries: List of manifest entries.
    """

    model_config = ConfigDict(frozen=True)

    manifest_id: str = Field(..., description="Unique manifest identifier")
    created_at: datetime = Field(..., description="Manifest creation timestamp")
    mode: str = Field(..., description="Clean mode used")
    total_files: int = Field(..., ge=0, description="Total number of files")
    total_size_bytes: int = Field(..., ge=0, description="Total size in bytes")
    entries: list[ManifestEntry] = Field(
        default_factory=list,
        description="List of manifest entries",
    )

    @property
    def total_size_human(self) -> str:
        """Get human-readable size string."""
        return self._humanize_size(self.total_size_bytes)

    @property
    def is_empty(self) -> bool:
        """Check if manifest has no entries."""
        return self.total_files == 0

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
