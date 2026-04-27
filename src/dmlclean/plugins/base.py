"""
Abstract Base Class for DMLClean plugins.

All cleaning plugins must inherit from CleanerPlugin and implement
the scan() method.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from loguru import logger


class RiskLevel(str, Enum):
    """Risk levels for cleaning targets."""

    LOW = "low"  # 🟢 Auto-clean default
    MEDIUM = "medium"  # 🟡 Confirm before clean
    HIGH = "high"  # 🔴 Manual/opt-in only
    BLOCKED = "blocked"  # ⛔ Never clean


@dataclass
class CleanCandidate:
    """
    A file or directory identified for potential cleaning.

    Attributes:
        path: Absolute path to the item.
        category: Cleaning category name.
        size_bytes: Size in bytes.
        risk_level: Assigned risk level.
        reason: Why this item was identified.
        last_accessed: Last access timestamp.
        last_modified: Last modification timestamp.
        is_directory: Whether this is a directory.
        hash_value: File hash (for duplicate detection).
        metadata: Additional metadata.
    """

    path: Path
    category: str
    size_bytes: int
    risk_level: RiskLevel
    reason: str
    last_accessed: float | None = None
    last_modified: float | None = None
    is_directory: bool = False
    hash_value: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "path": str(self.path),
            "category": self.category,
            "size_bytes": self.size_bytes,
            "risk_level": self.risk_level.value,
            "reason": self.reason,
            "last_accessed": self.last_accessed,
            "last_modified": self.last_modified,
            "is_directory": self.is_directory,
            "hash_value": self.hash_value,
            "metadata": self.metadata,
        }


class CleanerPlugin(ABC):
    """
    Abstract Base Class for all DMLClean plugins.

    Plugins are discovered via entry points (pkg_resources/importlib.metadata)
    and instantiated lazily during the scan phase.

    Example implementation:

        class BrowserCachePlugin(CleanerPlugin):
            @property
            def name(self) -> str:
                return "browser"

            @property
            def description(self) -> str:
                return "Browser cache and temporary files"

            async def scan(self, roots):
                for root in roots:
                    # Scan for browser cache files
                    yield CleanCandidate(...)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique plugin identifier.

        This name is used in configuration to enable/disable the plugin
        and in reporting to identify which plugin found each file.

        Returns:
            str: Plugin identifier (e.g., 'browser', 'dev_python').
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Human-readable description.

        Shown in help output, reports, and UI.

        Returns:
            str: Description of what this plugin cleans.
        """
        pass

    @property
    def default_enabled(self) -> bool:
        """
        Whether this plugin is enabled by default in 'fast' mode.

        Returns:
            bool: True if enabled by default.
        """
        return False

    @property
    def risk_level(self) -> RiskLevel:
        """
        Default risk level for this plugin's findings.

        Can be overridden by subclasses or individual candidates.

        Returns:
            RiskLevel: Default risk level.
        """
        return RiskLevel.MEDIUM

    @abstractmethod
    async def scan(self, roots: list[Path]) -> AsyncGenerator[CleanCandidate, None]:
        """
        Async generator that yields CleanCandidate objects.

        This is the main method that plugins must implement. It should
        scan the given root paths and yield candidates for cleaning.

        Args:
            roots: List of root paths to scan from config or --path flag.

        Yields:
            CleanCandidate: Each file/directory matching this plugin's rules.

        Example:
            async def scan(self, roots):
                for root in roots:
                    cache_dir = root / "Cache"
                    if cache_dir.exists():
                        for item in cache_dir.rglob("*"):
                            if item.is_file():
                                yield CleanCandidate(
                                    path=item,
                                    category=self.name,
                                    size_bytes=item.stat().st_size,
                                    risk_level=RiskLevel.LOW,
                                    reason="Browser cache file",
                                )
        """
        pass

    def is_protected(self, path: Path, protected_zone: Any | None = None) -> bool:
        """
        Check if a path is in the Protected Zone.

        Plugins can use this to skip protected paths during scanning.

        Args:
            path: Path to check.
            protected_zone: ProtectedZone instance (optional).

        Returns:
            bool: True if path is protected.
        """
        if protected_zone is None:
            return False

        result = protected_zone.is_protected(path)
        return bool(result.is_protected)

    def get_platform_paths(self) -> dict[str, list[str]]:
        """
        Get platform-specific paths for this plugin.

        Subclasses can override to provide OS-specific paths.

        Returns:
            dict[str, list[str]]: Mapping of platform to paths.
        """
        import sys

        if sys.platform == "win32":
            return {"windows": self.get_windows_paths()}
        elif sys.platform == "darwin":
            return {"macos": self.get_macos_paths()}
        else:
            return {"linux": self.get_linux_paths()}

    def get_windows_paths(self) -> list[str]:
        """Get Windows-specific paths."""
        return []

    def get_macos_paths(self) -> list[str]:
        """Get macOS-specific paths."""
        return []

    def get_linux_paths(self) -> list[str]:
        """Get Linux-specific paths."""
        return []

    def log_debug(self, message: str) -> None:
        """Log a debug message with plugin prefix."""
        logger.debug(f"[{self.name}] {message}")

    def log_info(self, message: str) -> None:
        """Log an info message with plugin prefix."""
        logger.info(f"[{self.name}] {message}")

    def log_warning(self, message: str) -> None:
        """Log a warning message with plugin prefix."""
        logger.warning(f"[{self.name}] {message}")

    def log_error(self, message: str) -> None:
        """Log an error message with plugin prefix."""
        logger.error(f"[{self.name}] {message}")
