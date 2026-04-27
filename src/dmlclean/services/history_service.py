# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Async history service for DMLClean.

Domain service for managing cleaning history operations.
All methods are async for non-blocking I/O.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

from dmlclean.exceptions import NotFoundError

if TYPE_CHECKING:
    from dmlclean.safety.undo import UndoManager
    from dmlclean.storage.database import Database
    from dmlclean.storage.history_repo import HistoryEntry, HistoryRepository


class HistoryService:
    """
    Async domain service for cleaning history operations.

    All methods are async for non-blocking database I/O.
    """

    def __init__(
        self,
        db: Database,
        history_repo: HistoryRepository,
        undo_manager: UndoManager,
    ) -> None:
        self.db = db
        self.history_repo = history_repo
        self.undo_manager = undo_manager
        logger.debug("HistoryService initialized")

    # ========================================================================
    # ASYNC METHODS (Primary API)
    # ========================================================================

    async def list_recent_async(
        self,
        limit: int = 10,
        profile: str | None = None,
        status: str | None = None,
        mode: str | None = None,
    ) -> list[HistoryEntry]:
        """List recent cleaning operations (async)."""
        return self.history_repo.list_all(
            limit=limit,
            profile=profile,
            status=status,
            mode=mode,
        )

    async def get_entry_async(self, entry_id: str) -> HistoryEntry | None:
        """Get a specific history entry by ID (async)."""
        return self.history_repo.get_by_id(entry_id)

    async def get_entry_or_raise_async(self, entry_id: str) -> HistoryEntry:
        """Get a history entry or raise NotFoundError (async)."""
        entry = await self.get_entry_async(entry_id)
        if entry is None:
            raise NotFoundError(
                f"History entry not found: {entry_id}",
                entity_type="HistoryEntry",
                entity_id=entry_id,
            )
        return entry

    async def undo_entry_async(
        self,
        entry_id: str,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Undo a trash operation (async)."""
        entry = await self.get_entry_or_raise_async(entry_id)

        if entry.mode == "permanent":
            return {"success": False, "error": "Cannot undo permanent deletions"}
        if entry.mode == "dry-run":
            return {"success": False, "error": "Dry-run operations don't need undo"}

        manifest = self.undo_manager.get_manifest(entry_id)
        if manifest is None:
            return {"success": False, "error": f"No manifest found for entry: {entry_id}"}

        can_undo, reason = self.undo_manager.can_undo(manifest)
        if not can_undo:
            return {"success": False, "error": reason}

        result = self.undo_manager.undo(manifest, dry_run=dry_run)
        result["success"] = True

        if not dry_run and result.get("total_restored", 0) > 0:
            self.history_repo.update(
                entry_id,
                status="undone",
                error_message=f"Undone: {result['total_restored']} files restored",
            )

        return result

    async def clear_history_async(self) -> int:
        """Clear all cleaning history (async)."""
        self.undo_manager.clear_history()
        return self.history_repo.clear_all()

    async def export_history_async(self, output_path: Path) -> int:
        """Export all history to JSON (async)."""
        return self.undo_manager.export_history(output_path)

    async def get_statistics_async(self, days: int = 30) -> dict[str, Any]:
        """Get statistics for cleaning operations (async)."""
        return self.history_repo.get_summary(days=days)

    async def get_failed_operations_async(self, limit: int = 10) -> list[HistoryEntry]:
        """Get failed cleaning operations (async)."""
        return self.history_repo.get_failed(limit=limit)

    async def get_by_profile_async(
        self,
        profile: str,
        limit: int = 10,
    ) -> list[HistoryEntry]:
        """Get history entries for a specific profile (async)."""
        return self.history_repo.get_by_profile(profile, limit=limit)

    async def record_operation_async(
        self,
        id: str,
        mode: str,
        profile: str,
        scan_mode: str,
        files_found: int = 0,
        files_deleted: int = 0,
        size_bytes: int = 0,
        duration_ms: int = 0,
        categories: list[str] | None = None,
        status: str = "complete",
        error_message: str | None = None,
    ) -> HistoryEntry:
        """Record a cleaning operation in history (async)."""
        return self.history_repo.create(
            id=id,
            mode=mode,
            profile=profile,
            scan_mode=scan_mode,
            files_found=files_found,
            files_deleted=files_deleted,
            size_bytes=size_bytes,
            duration_ms=duration_ms,
            categories=categories,
            status=status,
            error_message=error_message,
        )

    # ========================================================================
    # SYNC WRAPPERS (For CLI compatibility)
    # ========================================================================

    def list_recent(
        self,
        limit: int = 10,
        profile: str | None = None,
        status: str | None = None,
        mode: str | None = None,
    ) -> list[HistoryEntry]:
        """Sync wrapper for list_recent_async."""
        import asyncio

        return asyncio.run(self.list_recent_async(limit, profile, status, mode))

    def get_entry(self, entry_id: str) -> HistoryEntry | None:
        """Sync wrapper for get_entry_async."""
        import asyncio

        return asyncio.run(self.get_entry_async(entry_id))

    def get_entry_or_raise(self, entry_id: str) -> HistoryEntry:
        """Sync wrapper for get_entry_or_raise_async."""
        import asyncio

        return asyncio.run(self.get_entry_or_raise_async(entry_id))

    def undo_entry(self, entry_id: str, dry_run: bool = False) -> dict[str, Any]:
        """Sync wrapper for undo_entry_async."""
        import asyncio

        return asyncio.run(self.undo_entry_async(entry_id, dry_run))

    def clear_history(self) -> int:
        """Sync wrapper for clear_history_async."""
        import asyncio

        return asyncio.run(self.clear_history_async())

    def export_history(self, output_path: Path) -> int:
        """Sync wrapper for export_history_async."""
        import asyncio

        return asyncio.run(self.export_history_async(output_path))

    def get_statistics(self, days: int = 30) -> dict[str, Any]:
        """Sync wrapper for get_statistics_async."""
        import asyncio

        return asyncio.run(self.get_statistics_async(days))

    def get_failed_operations(self, limit: int = 10) -> list[HistoryEntry]:
        """Sync wrapper for get_failed_operations_async."""
        import asyncio

        return asyncio.run(self.get_failed_operations_async(limit))

    def get_by_profile(self, profile: str, limit: int = 10) -> list[HistoryEntry]:
        """Sync wrapper for get_by_profile_async."""
        import asyncio

        return asyncio.run(self.get_by_profile_async(profile, limit))

    def record_operation(
        self,
        id: str,
        mode: str,
        profile: str,
        scan_mode: str,
        files_found: int = 0,
        files_deleted: int = 0,
        size_bytes: int = 0,
        duration_ms: int = 0,
        categories: list[str] | None = None,
        status: str = "complete",
        error_message: str | None = None,
    ) -> HistoryEntry:
        """Sync wrapper for record_operation_async."""
        import asyncio

        return asyncio.run(
            self.record_operation_async(
                id,
                mode,
                profile,
                scan_mode,
                files_found,
                files_deleted,
                size_bytes,
                duration_ms,
                categories,
                status,
                error_message,
            )
        )


__all__ = ["HistoryService"]
