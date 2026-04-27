"""
User-facing message constants for DMLClean.

All user-visible messages are centralized here for consistency
and easy localization in the future.
"""

# Operation headers
MSG_DRY_RUN_HEADER: str = "DRY RUN - no files will be deleted"
"""Header shown during dry-run mode operations."""

# Protected zone messages
MSG_PROTECTED_BLOCKED: str = "⛔ Operation blocked: path is in Protected Zone"
"""Shown when a cleaning operation attempts to touch a protected path."""

MSG_IMMUTABLE_BLOCKED: str = "⛔ Cannot remove immutable protection: {path}"
"""Shown when user tries to remove an immutable protected path."""

MSG_SELF_STORAGE_PROTECTED: str = (
    "DMLClean's own data directory is permanently protected and cannot be cleaned or removed."
)
"""Informational message about DMLClean's self-protection."""

# Confirmation messages
MSG_CONFIRM_PERMANENT: str = 'Type "DELETE" to confirm permanent deletion'
"""Prompt shown before permanent deletion of high-risk targets."""

# Empty state messages
MSG_NOTHING_TO_CLEAN: str = "✓ Nothing to clean - system is already clean"
"""Shown when scan finds no cleanable files."""

MSG_UNDO_EMPTY: str = "No operations to undo"
"""Shown when history is empty or no trash operations exist."""

# Exit code descriptions
EXIT_CODE_DESCRIPTIONS: dict[int, str] = {
    0: "Success / nothing found",
    1: "Runtime error",
    2: "Found but not cleaned (dry-run)",
    3: "Partial clean (some failures)",
    4: "Protected zone violation blocked",
    5: "User cancelled confirmation",
}
"""Human-readable descriptions for exit codes."""
