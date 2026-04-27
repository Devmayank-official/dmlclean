"""
Undo Manager for DMLClean.

The Undo Manager enables restoration of files from trash operations
by reading deletion manifests and attempting to restore files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger

from dmlclean.safety.manifest import DeletionManifest


class UndoError(Exception):
    """Base exception for undo operations."""

    pass


class UndoUnavailableError(UndoError):
    """Raised when undo is not available for a manifest."""

    pass


class UndoPartialError(UndoError):
    """Raised when undo partially succeeded."""

    def __init__(self, message: str, restored: list[str], failed: list[str]) -> None:
        super().__init__(message)
        self.restored = restored
        self.failed = failed


class UndoManager:
    """
    Manager for undoing trash operations.

    The Undo Manager reads deletion manifests and attempts to restore
    files. Note that undo is only possible for files that were moved
    to trash (not permanently deleted) and are still in the trash.

    Attributes:
        storage_dir: Directory where manifests are stored.
    """

    def __init__(self, storage_dir: Path | None = None) -> None:
        """
        Initialize the Undo Manager.

        Args:
            storage_dir: Directory containing manifests. Uses default if None.
        """
        self.storage_dir = storage_dir or DeletionManifest.get_storage_dir()
        logger.debug(f"UndoManager initialized with storage: {self.storage_dir}")

    def list_manifests(self, limit: int = 100) -> list[dict[str, Any]]:
        """
        List available manifests for undo.

        Args:
            limit: Maximum number of manifests to return.

        Returns:
            list[dict[str, Any]]: List of manifest summaries.
        """
        if not self.storage_dir.exists():
            return []

        manifests: list[dict[str, Any]] = []

        for manifest_file in sorted(self.storage_dir.glob("manifest_*.json"), reverse=True)[:limit]:
            try:
                manifest = DeletionManifest.load(manifest_file)
                manifests.append(manifest.get_summary())
            except Exception as e:
                logger.warning(f"Failed to load manifest {manifest_file}: {e}")

        return manifests

    def get_manifest(self, manifest_id: str) -> DeletionManifest | None:
        """
        Get a manifest by ID.

        Args:
            manifest_id: Manifest ID (full UUID or first 8 chars).

        Returns:
            DeletionManifest | None: Manifest if found, None otherwise.
        """
        if not self.storage_dir.exists():
            return None

        # Try to find manifest by ID
        for manifest_file in self.storage_dir.glob("manifest_*.json"):
            try:
                manifest = DeletionManifest.load(manifest_file)
                if manifest.id.startswith(manifest_id):
                    return manifest
            except Exception as e:
                logger.warning(f"Failed to load manifest {manifest_file}: {e}")

        return None

    def get_latest_manifest(self) -> DeletionManifest | None:
        """
        Get the most recent manifest.

        Returns:
            DeletionManifest | None: Latest manifest if available.
        """
        manifests = self.list_manifests(limit=1)
        if not manifests:
            return None

        return self.get_manifest(manifests[0]["id"])

    def can_undo(self, manifest: DeletionManifest) -> tuple[bool, str]:
        """
        Check if undo is possible for a manifest.

        Args:
            manifest: Manifest to check.

        Returns:
            tuple[bool, str]: (can_undo, reason)
        """
        # Check if manifest mode supports undo
        if manifest.mode == "permanent":
            return False, "Permanent deletions cannot be undone"

        if manifest.mode == "dry-run":
            return False, "Dry-run operations don't need undo"

        if manifest.mode != "trash":
            return False, f"Undo not supported for mode: {manifest.mode}"

        # Check if any entries exist
        if not manifest.entries:
            return False, "Manifest has no entries to restore"

        # Check if files still exist in trash
        # Note: This is platform-specific and may not be reliable
        # We only check if the original paths are gone
        missing_count = 0
        for entry in manifest.entries:
            if not Path(entry.path).exists():
                missing_count += 1

        if missing_count == 0:
            return False, "Files already exist at original paths"

        if missing_count < len(manifest.entries):
            return (
                True,
                f"Partial restore possible ({missing_count}/{len(manifest.entries)} files missing)",
            )

        return True, "All files can potentially be restored"

    def undo(
        self,
        manifest: DeletionManifest,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Attempt to undo a trash operation.

        This method attempts to restore files from the trash. Note that
        send2trash doesn't provide a native restore function, so we can
        only restore files that we have tracked in our manifest and that
        still exist in the trash location.

        Args:
            manifest: Manifest to undo.
            dry_run: If True, only simulate the restore.

        Returns:
            dict[str, Any]: Result with restored and failed paths.

        Raises:
            UndoUnavailableError: If undo is not possible.
            UndoPartialError: If undo partially succeeded.
        """
        can_undo, reason = self.can_undo(manifest)
        if not can_undo:
            raise UndoUnavailableError(reason)

        logger.info(f"Starting undo operation for manifest {manifest.id}")

        restored: list[str] = []
        failed: list[str] = []
        errors: dict[str, str] = {}

        for entry in manifest.entries:
            path = Path(entry.path)

            # Skip if path already exists (already restored or never deleted)
            if path.exists():
                logger.debug(f"Skipping {path} - already exists")
                restored.append(str(path))
                continue

            # For trash mode, we can't directly restore from trash
            # because send2trash doesn't expose the trash location.
            # We can only restore if we have a backup or if the user
            # manually moves files back from trash.
            #
            # This is a limitation of the cross-platform trash API.
            # The manifest serves as an audit log for what was deleted.

            # For now, we mark this as a limitation
            failed.append(str(path))
            errors[str(path)] = (
                "Cannot restore from trash - send2trash doesn't expose trash location"
            )

            # In a future version, we could:
            # 1. Parse $Recycle.Bin on Windows
            # 2. Parse .Trash on Linux
            # 3. Parse .Trash on macOS
            # But this is complex and platform-specific.

        result = {
            "manifest_id": manifest.id,
            "restored": restored,
            "failed": failed,
            "errors": errors,
            "total_restored": len(restored),
            "total_failed": len(failed),
            "dry_run": dry_run,
        }

        if failed and restored:
            raise UndoPartialError(
                f"Partial restore: {len(restored)} restored, {len(failed)} failed",
                restored,
                failed,
            )

        logger.info(f"Undo operation completed: {len(restored)} restored, {len(failed)} failed")
        return result

    def undo_by_id(
        self,
        manifest_id: str,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Undo a specific manifest by ID.

        Args:
            manifest_id: Manifest ID (full or partial UUID).
            dry_run: If True, only simulate the restore.

        Returns:
            dict[str, Any]: Result with restored and failed paths.

        Raises:
            UndoUnavailableError: If manifest not found or undo not possible.
        """
        manifest = self.get_manifest(manifest_id)
        if manifest is None:
            raise UndoUnavailableError(f"Manifest not found: {manifest_id}")

        return self.undo(manifest, dry_run=dry_run)

    def undo_latest(self, dry_run: bool = False) -> dict[str, Any]:
        """
        Undo the most recent trash operation.

        Args:
            dry_run: If True, only simulate the restore.

        Returns:
            dict[str, Any]: Result with restored and failed paths.

        Raises:
            UndoUnavailableError: If no manifests available.
        """
        manifest = self.get_latest_manifest()
        if manifest is None:
            raise UndoUnavailableError("No manifests available for undo")

        return self.undo(manifest, dry_run=dry_run)

    def clear_history(self) -> int:
        """
        Clear all manifest history.

        Warning: This makes undo operations impossible.

        Returns:
            int: Number of manifests deleted.
        """
        if not self.storage_dir.exists():
            return 0

        count = 0
        for manifest_file in self.storage_dir.glob("manifest_*.json"):
            try:
                manifest_file.unlink()
                count += 1
            except Exception as e:
                logger.warning(f"Failed to delete manifest {manifest_file}: {e}")

        logger.info(f"Cleared {count} manifests from history")
        return count

    def export_history(self, output_path: Path) -> int:
        """
        Export all manifests to a single JSON file.

        Args:
            output_path: Path to output file.

        Returns:
            int: Number of manifests exported.
        """
        manifests = []
        for manifest_file in sorted(self.storage_dir.glob("manifest_*.json")):
            try:
                manifest = DeletionManifest.load(manifest_file)
                manifests.append(manifest.to_dict())
            except Exception as e:
                logger.warning(f"Failed to load manifest {manifest_file}: {e}")

        import json

        with output_path.open("w", encoding="utf-8") as f:
            json.dump({"manifests": manifests}, f, indent=2)

        logger.info(f"Exported {len(manifests)} manifests to {output_path}")
        return len(manifests)
