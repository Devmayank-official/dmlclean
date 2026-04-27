# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Async protection service for DMLClean.

Domain service for managing protected zone configuration.
All methods are async for non-blocking I/O.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from dmlclean.domain.events import EventBus, ProtectedPathAdded, ProtectedPathRemoved
from dmlclean.exceptions import DuplicateError, NotFoundError, PermissionError, ValidationError
from dmlclean.safety.protected_zone import ProtectedZone

if TYPE_CHECKING:
    from dmlclean.safety.protected_zone import ProtectionResult
    from dmlclean.storage.database import Database
    from dmlclean.storage.protected_repo import ProtectedPathEntry, ProtectedRepository


class ProtectionService:
    """Async domain service for protected zone operations."""

    def __init__(
        self,
        db: Database,
        protected_repo: ProtectedRepository,
        protected_zone: ProtectedZone,
    ) -> None:
        self.db = db
        self.protected_repo = protected_repo
        self.protected_zone = protected_zone
        logger.debug("ProtectionService initialized")

    async def add_protection_async(
        self,
        path: str,
        description: str = "",
        is_glob: bool = False,
    ) -> ProtectedPathEntry:
        """Add a protected path (async)."""
        # Validate path
        if not path or not path.strip():
            raise ValidationError("Path cannot be empty")
        if len(path) > 500:
            raise ValidationError(f"Path too long (max 500 chars): {len(path)}")

        # Normalize path
        if not is_glob:
            try:
                path_obj = Path(path).expanduser()
                if not path_obj.is_absolute():
                    path_obj = path_obj.resolve()
                normalized_path = str(path_obj)
            except Exception as e:
                raise ValidationError(f"Invalid path format: {path} - {e}")
        else:
            normalized_path = path

        # Check for duplicates (sync for now)
        existing = self.protected_repo.get_by_path(normalized_path)
        if existing:
            raise DuplicateError(f"Path already protected: {normalized_path}")

        # Check for immutable paths
        if self._is_immutable_path(normalized_path):
            raise PermissionError(f"Cannot protect immutable system path: {normalized_path}")

        # Create entry (sync for now)
        entry_id = str(uuid.uuid4())
        entry = self.protected_repo.create(
            id=entry_id,
            path=normalized_path,
            description=description,
            is_glob=is_glob,
        )

        # Publish event
        EventBus.publish(
            ProtectedPathAdded(
                entry_id=entry_id,
                path=normalized_path,
                description=description,
                is_glob=is_glob,
            )
        )

        logger.info(f"Protected path added: {normalized_path}")
        return entry

    async def get_protection_async(self, entry_id: str) -> ProtectedPathEntry | None:
        """Get a protected path by ID (async)."""
        return self.protected_repo.get_by_id(entry_id)

    async def get_protection_by_path_async(self, path: str) -> ProtectedPathEntry | None:
        """Get a protected path by path string (async)."""
        return self.protected_repo.get_by_path(path)

    async def remove_protection_async(self, entry_id: str) -> bool:
        """Remove a protected path (async)."""
        entry = await self.get_protection_async(entry_id)
        if not entry:
            raise NotFoundError(f"Protected path not found: {entry_id}")

        success = self.protected_repo.delete(entry_id)
        if success:
            EventBus.publish(ProtectedPathRemoved(entry_id=entry_id, path=entry.path))
        return success

    async def list_protected_async(
        self,
        limit: int = 100,
        is_glob: bool | None = None,
    ) -> list[ProtectedPathEntry]:
        """List all protected paths (async)."""
        return self.protected_repo.list_all(limit=limit, is_glob=is_glob)

    def check_protection(self, path: str | Path) -> ProtectionResult:
        """Check if a path is protected (sync - uses in-memory protected zone)."""
        self._reload_protected_zone()
        path_obj = Path(path) if isinstance(path, str) else path
        return self.protected_zone.is_protected(path_obj)

    def is_protected(self, path: str | Path) -> bool:
        """Check if a path is protected (boolean only)."""
        return self.check_protection(path).is_protected

    def _reload_protected_zone(self) -> None:
        """Reload protected zone from database."""
        entries = self.protected_repo.list_all(limit=1000)
        custom_paths = [e.path for e in entries if not e.is_glob]
        custom_globs = [e.path for e in entries if e.is_glob]

        # Add DMLClean application paths to protected zone (never delete our own data!)
        app_paths = self._get_application_protected_paths()
        custom_paths.extend(app_paths)

        self.protected_zone = ProtectedZone(
            enabled=True,
            custom_paths=custom_paths,
            custom_globs=custom_globs,
            protect_git_dirs=True,
            protect_venvs=True,
        )

    def _get_application_protected_paths(self) -> list[str]:
        """
        Get DMLClean application paths that should never be deleted.

        These paths contain DMLClean's own data and must be protected:
        - Configuration files
        - Database (history, schedules)
        - Manifests (undo information)
        - Logs

        Returns:
            list[str]: List of protected application paths.
        """
        try:
            from dmlclean.storage.paths import (
                get_base_dir,
                get_config_dir,
                get_data_dir,
                get_history_dir,
                get_logs_dir,
                get_manifests_dir,
            )

            app_paths = [
                str(get_base_dir()),
                str(get_config_dir()),
                str(get_data_dir()),
                str(get_history_dir()),
                str(get_logs_dir()),
                str(get_manifests_dir()),
            ]

            # Filter to only existing paths
            return [p for p in app_paths if Path(p).exists()]

        except Exception:
            # If we can't get paths, return empty list
            # Application paths are still protected by immutable path check
            return []

    def _is_immutable_path(self, path: str) -> bool:
        """Check if path is an immutable system path."""
        import sys
        from pathlib import Path

        # Get platform-specific system paths
        if sys.platform == "win32":
            # Windows immutable paths
            immutable_paths = [
                Path(r"C:\Windows"),
                Path(r"C:\Program Files"),
                Path(r"C:\Program Files (x86)"),
                Path(r"C:\ProgramData"),
                Path(r"C:\System Volume Information"),
                Path(r"C:\Recovery"),
                Path(r"C:\PerfLogs"),
                Path(r"C:\Users\Public"),
            ]
            # Add SYSTEMDRIVE based paths
            import os

            system_drive = os.environ.get("SYSTEMDRIVE", "C:")
            immutable_paths.extend(
                [
                    Path(system_drive) / "Windows",
                    Path(system_drive) / "Program Files",
                    Path(system_drive) / "Program Files (x86)",
                ]
            )
        elif sys.platform == "darwin":
            # macOS immutable paths
            immutable_paths = [
                Path("/System"),
                Path("/Library"),
                Path("/Applications"),
                Path("/usr"),
                Path("/bin"),
                Path("/sbin"),
                Path("/mach_kernel"),
            ]
        else:
            # Linux/Unix immutable paths
            immutable_paths = [
                Path("/bin"),
                Path("/sbin"),
                Path("/usr"),
                Path("/lib"),
                Path("/lib64"),
                Path("/etc"),
                Path("/boot"),
                Path("/dev"),
                Path("/proc"),
                Path("/sys"),
                Path("/run"),
            ]

        # Normalize the input path
        try:
            input_path = Path(path).resolve()
        except Exception:
            input_path = Path(path)

        # Check if input path starts with any immutable path
        for immutable in immutable_paths:
            try:
                if immutable.exists() and input_path.is_relative_to(immutable):
                    return True
            except (ValueError, OSError):
                # is_relative_to may not exist in Python 3.8, or path issues
                try:
                    if str(input_path).startswith(str(immutable)):
                        return True
                except Exception:
                    pass

        return False

    # Sync wrappers
    def add_protection(
        self, path: str, description: str = "", is_glob: bool = False
    ) -> ProtectedPathEntry:
        import asyncio

        return asyncio.run(self.add_protection_async(path, description, is_glob))

    def get_protection(self, entry_id: str) -> ProtectedPathEntry | None:
        import asyncio

        return asyncio.run(self.get_protection_async(entry_id))

    def get_protection_by_path(self, path: str) -> ProtectedPathEntry | None:
        import asyncio

        return asyncio.run(self.get_protection_by_path_async(path))

    def remove_protection(self, entry_id: str) -> bool:
        import asyncio

        return asyncio.run(self.remove_protection_async(entry_id))

    def list_protected(
        self, limit: int = 100, is_glob: bool | None = None
    ) -> list[ProtectedPathEntry]:
        import asyncio

        return asyncio.run(self.list_protected_async(limit, is_glob))


__all__ = ["ProtectionService"]
