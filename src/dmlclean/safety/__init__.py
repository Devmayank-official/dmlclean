"""
Safety mechanisms for DMLClean.

This package provides:
- Protected Zone: Path protection rules to prevent accidental deletion
- Deletion Manifest: Pre-operation logging of all files to be deleted
- Undo Manager: Restore files from trash operations
"""

from dmlclean.safety.manifest import DeletionManifest, ManifestEntry
from dmlclean.safety.protected_zone import ProtectedZone, ProtectionRule
from dmlclean.safety.undo import UndoManager

__all__ = [
    "DeletionManifest",
    "ManifestEntry",
    "ProtectedZone",
    "ProtectionRule",
    "UndoManager",
]
