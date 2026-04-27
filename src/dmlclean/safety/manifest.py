"""
Deletion Manifest for DMLClean.

The Deletion Manifest is a pre-operation log of all files that will be
deleted. It serves as an audit trail and enables undo operations.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from loguru import logger


@dataclass
class ManifestEntry:
    """
    A single entry in the deletion manifest.

    Attributes:
        path: Absolute path to the file or directory.
        size_bytes: Size in bytes.
        hash_value: xxhash fingerprint (if computed).
        deleted_at: ISO 8601 timestamp of deletion.
        mode: Clean mode used (dry-run, trash, permanent).
        category: Cleaning category that identified this file.
        risk_level: Risk level assigned (low, medium, high).
        is_directory: Whether this is a directory.
        metadata: Additional metadata (mtime, atime, etc.).
    """

    path: str
    size_bytes: int
    hash_value: str | None = None
    deleted_at: str = ""
    mode: str = "dry-run"
    category: str = ""
    risk_level: str = "low"
    is_directory: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Set deleted_at timestamp if not provided."""
        if not self.deleted_at:
            self.deleted_at = datetime.now(UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.

        Returns:
            dict[str, Any]: Dictionary representation.
        """
        return {
            "path": self.path,
            "size_bytes": self.size_bytes,
            "hash_value": self.hash_value,
            "deleted_at": self.deleted_at,
            "mode": self.mode,
            "category": self.category,
            "risk_level": self.risk_level,
            "is_directory": self.is_directory,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ManifestEntry:
        """
        Create a ManifestEntry from a dictionary.

        Args:
            data: Dictionary with entry data.

        Returns:
            ManifestEntry: Created instance.
        """
        return cls(
            path=data["path"],
            size_bytes=data["size_bytes"],
            hash_value=data.get("hash_value"),
            deleted_at=data.get("deleted_at", ""),
            mode=data.get("mode", "dry-run"),
            category=data.get("category", ""),
            risk_level=data.get("risk_level", "low"),
            is_directory=data.get("is_directory", False),
            metadata=data.get("metadata", {}),
        )


@dataclass
class DeletionManifest:
    """
    Complete deletion manifest for a cleaning operation.

    Attributes:
        id: Unique manifest identifier (UUID).
        created_at: ISO 8601 timestamp of creation.
        operation_id: Related operation identifier.
        mode: Clean mode (dry-run, trash, permanent).
        profile: Profile used for cleaning.
        entries: List of manifest entries.
        total_size_bytes: Total size of all files.
        total_files: Total number of files.
        total_directories: Total number of directories.
        categories: Summary of files per category.
        notes: Optional notes about this operation.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    operation_id: str = ""
    mode: str = "dry-run"
    profile: str = "default"
    entries: list[ManifestEntry] = field(default_factory=list)
    total_size_bytes: int = 0
    total_files: int = 0
    total_directories: int = 0
    categories: dict[str, int] = field(default_factory=dict)
    notes: str = ""

    def add_entry(self, entry: ManifestEntry) -> None:
        """
        Add an entry to the manifest.

        Args:
            entry: Manifest entry to add.
        """
        self.entries.append(entry)

        # Update totals
        if entry.is_directory:
            self.total_directories += 1
        else:
            self.total_files += 1

        self.total_size_bytes += entry.size_bytes

        # Update category counts
        if entry.category:
            self.categories[entry.category] = self.categories.get(entry.category, 0) + 1

    def add_entries(self, entries: list[ManifestEntry]) -> None:
        """
        Add multiple entries to the manifest.

        Args:
            entries: List of manifest entries.
        """
        for entry in entries:
            self.add_entry(entry)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.

        Returns:
            dict[str, Any]: Dictionary representation.
        """
        return {
            "id": self.id,
            "created_at": self.created_at,
            "operation_id": self.operation_id,
            "mode": self.mode,
            "profile": self.profile,
            "entries": [e.to_dict() for e in self.entries],
            "total_size_bytes": self.total_size_bytes,
            "total_files": self.total_files,
            "total_directories": self.total_directories,
            "categories": self.categories,
            "notes": self.notes,
            "summary": {
                "total_size_human": self._humanize_size(self.total_size_bytes),
                "total_items": self.total_files + self.total_directories,
            },
        }

    @staticmethod
    def _humanize_size(size_bytes: int) -> str:
        """
        Convert bytes to human-readable format.

        Args:
            size_bytes: Size in bytes.

        Returns:
            str: Human-readable size (e.g., "1.5 GB").
        """
        size: float = size_bytes
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeletionManifest:
        """
        Create a DeletionManifest from a dictionary.

        Args:
            data: Dictionary with manifest data.

        Returns:
            DeletionManifest: Created instance.
        """
        manifest = cls(
            id=data.get("id", ""),
            created_at=data.get("created_at", ""),
            operation_id=data.get("operation_id", ""),
            mode=data.get("mode", "dry-run"),
            profile=data.get("profile", "default"),
            total_size_bytes=data.get("total_size_bytes", 0),
            total_files=data.get("total_files", 0),
            total_directories=data.get("total_directories", 0),
            categories=data.get("categories", {}),
            notes=data.get("notes", ""),
        )
        manifest.entries = [ManifestEntry.from_dict(e) for e in data.get("entries", [])]
        return manifest

    def to_json(self, indent: int = 2) -> str:
        """
        Serialize to JSON string.

        Args:
            indent: JSON indentation level.

        Returns:
            str: JSON string.
        """
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> DeletionManifest:
        """
        Create a DeletionManifest from a JSON string.

        Args:
            json_str: JSON string.

        Returns:
            DeletionManifest: Created instance.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def save(self, storage_dir: Path | None = None) -> Path:
        """
        Save the manifest to a JSON file.

        Args:
            storage_dir: Directory to save manifest. Uses default if None.

        Returns:
            Path: Path to saved manifest file.
        """
        if storage_dir is None:
            storage_dir = self.get_storage_dir()

        # Create directory if needed
        storage_dir.mkdir(parents=True, exist_ok=True)

        # Save to file with timestamp in name
        timestamp = datetime.fromisoformat(self.created_at).strftime("%Y%m%d_%H%M%S")
        filename = f"manifest_{timestamp}_{self.id[:8]}.json"
        file_path = storage_dir / filename

        with file_path.open("w", encoding="utf-8") as f:
            f.write(self.to_json())

        logger.info(f"Deletion manifest saved to: {file_path}")
        return file_path

    @classmethod
    def load(cls, manifest_path: Path) -> DeletionManifest:
        """
        Load a manifest from a JSON file.

        Args:
            manifest_path: Path to manifest file.

        Returns:
            DeletionManifest: Loaded manifest.
        """
        with manifest_path.open("r", encoding="utf-8") as f:
            json_str = f.read()
        return cls.from_json(json_str)

    @staticmethod
    def get_storage_dir() -> Path:
        """
        Get the default manifest storage directory.

        Returns:
            Path: Storage directory path.
        """
        from dmlclean.storage.paths import get_manifests_dir

        return get_manifests_dir()

    def get_summary(self) -> dict[str, Any]:
        """
        Get a summary of this manifest.

        Returns:
            dict[str, Any]: Summary dictionary.
        """
        return {
            "id": self.id,
            "created_at": self.created_at,
            "mode": self.mode,
            "profile": self.profile,
            "total_files": self.total_files,
            "total_directories": self.total_directories,
            "total_size_bytes": self.total_size_bytes,
            "total_size_human": self._humanize_size(self.total_size_bytes),
            "categories": self.categories,
        }
