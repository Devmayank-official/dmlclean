"""
CLI Context and State Management for DMLClean.

Provides:
- Typer context for per-command state
- State file for persistence across CLI invocations
- Scan→Clean workflow support

Architecture:
    ```
    CLI Command → Context (ctx.obj) → State File (optional)
    ```

Example:
    ```python
    # Save scan result
    from dmlclean.cli.context import CLIContext

    ctx = CLIContext()
    ctx.save_scan_result(result)

    # Later, retrieve in clean command
    result = ctx.get_last_scan_result()
    ```
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger


@dataclass
class ScanState:
    """Scan result state for persistence."""

    timestamp: str
    mode: str
    paths: list[str]
    total_files: int
    total_size_bytes: int
    candidates: int
    by_category: dict[str, Any] = field(default_factory=dict)
    by_risk: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "mode": self.mode,
            "paths": self.paths,
            "total_files": self.total_files,
            "total_size_bytes": self.total_size_bytes,
            "candidates": self.candidates,
            "by_category": self.by_category,
            "by_risk": self.by_risk,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ScanState:
        """Create from dictionary."""
        return cls(
            timestamp=data.get("timestamp", ""),
            mode=data.get("mode", ""),
            paths=data.get("paths", []),
            total_files=data.get("total_files", 0),
            total_size_bytes=data.get("total_size_bytes", 0),
            candidates=data.get("candidates", 0),
            by_category=data.get("by_category", {}),
            by_risk=data.get("by_risk", {}),
        )


@dataclass
class CLIState:
    """CLI application state."""

    last_scan: ScanState | None = None
    last_clean_timestamp: str | None = None
    version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "last_scan": self.last_scan.to_dict() if self.last_scan else None,
            "last_clean_timestamp": self.last_clean_timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CLIState:
        """Create from dictionary."""
        last_scan = None
        if data.get("last_scan"):
            last_scan = ScanState.from_dict(data["last_scan"])

        return cls(
            version=data.get("version", "1.0"),
            last_scan=last_scan,
            last_clean_timestamp=data.get("last_clean_timestamp"),
        )


class CLIContext:
    """
    CLI context manager for state.

    Provides per-command state via Typer context and
    optional persistence to state file.

    Usage:
        ```python
        # In scan command
        @app.command()
        def scan(ctx: typer.Context):
            context = CLIContext()
            context.save_scan_result(result)

        # In clean command
        @app.command()
        def clean(ctx: typer.Context):
            context = CLIContext()
            last_scan = context.get_last_scan_result()
        ```
    """

    def __init__(self, state_dir: Path | None = None) -> None:
        """
        Initialize CLI context.

        Args:
            state_dir: Directory for state file (default: ~/.dmlclean/).
        """
        self.state_dir = state_dir or self._get_default_state_dir()
        self.state_file = self.state_dir / "state.json"
        self._state: CLIState | None = None

        # Ensure state directory exists
        self.state_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(f"CLIContext initialized: state_dir={self.state_dir}")

    def _get_default_state_dir(self) -> Path:
        """Get default state directory."""
        from dmlclean.storage.paths import get_cache_dir

        return get_cache_dir() / "state"

    def _load_state(self) -> CLIState:
        """Load state from file."""
        if self._state:
            return self._state

        if not self.state_file.exists():
            self._state = CLIState()
            return self._state

        try:
            data = json.loads(self.state_file.read_text())
            self._state = CLIState.from_dict(data)
            logger.debug(f"Loaded state from {self.state_file}")
        except Exception as e:
            logger.warning(f"Failed to load state: {e}")
            self._state = CLIState()

        return self._state

    def _save_state(self) -> None:
        """Save state to file."""
        if not self._state:
            return

        try:
            data = self._state.to_dict()
            self.state_file.write_text(json.dumps(data, indent=2))
            logger.debug(f"Saved state to {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def save_scan_result(self, result: Any) -> None:
        """
        Save scan result to state.

        Args:
            result: Scan result (dict or DTO).
        """
        state = self._load_state()

        # Convert result to state
        if hasattr(result, "to_dict"):
            data = result.to_dict()
        else:
            data = result

        state.last_scan = ScanState(
            timestamp=datetime.now().isoformat(),
            mode=data.get("mode", "fast"),
            paths=data.get("paths", []),
            total_files=data.get("total_files", 0),
            total_size_bytes=data.get("total_size_bytes", 0),
            candidates=data.get("candidates", 0),
            by_category=data.get("by_category", {}),
            by_risk=data.get("by_risk", {}),
        )

        self._state = state
        self._save_state()

    def get_last_scan_result(self) -> ScanState | None:
        """
        Get last scan result from state.

        Returns:
            ScanState | None: Last scan state if available.
        """
        state = self._load_state()

        if not state.last_scan:
            return None

        # Check if scan is stale (older than 24 hours)
        try:
            scan_time = datetime.fromisoformat(state.last_scan.timestamp)
            age_hours = (datetime.now() - scan_time).total_seconds() / 3600

            if age_hours > 24:
                logger.warning(f"Scan result is {age_hours:.1f} hours old, consider re-scanning")
        except Exception:
            pass

        return state.last_scan

    def clear_scan_result(self) -> None:
        """Clear last scan result."""
        state = self._load_state()
        state.last_scan = None
        self._state = state
        self._save_state()

    def record_clean_operation(self) -> None:
        """Record clean operation timestamp."""
        state = self._load_state()
        state.last_clean_timestamp = datetime.now().isoformat()
        self._state = state
        self._save_state()

    def get_state_summary(self) -> dict[str, Any]:
        """
        Get state summary for reporting.

        Returns:
            dict: State summary.
        """
        state = self._load_state()

        summary = {
            "has_last_scan": state.last_scan is not None,
            "last_clean_timestamp": state.last_clean_timestamp,
        }

        if state.last_scan:
            summary.update(
                {
                    "last_scan_timestamp": state.last_scan.timestamp,
                    "last_scan_mode": state.last_scan.mode,
                    "last_scan_files": state.last_scan.total_files,
                    "last_scan_size": state.last_scan.total_size_bytes,
                }
            )

        return summary


# Global context instance (for CLI usage)
_context: CLIContext | None = None


def get_context() -> CLIContext:
    """
    Get global CLI context instance.

    Returns:
        CLIContext: Global context instance.
    """
    global _context

    if _context is None:
        _context = CLIContext()

    return _context


def clear_context() -> None:
    """Clear global context."""
    global _context

    if _context:
        _context.clear_scan_result()


__all__ = [
    "CLIContext",
    "CLIState",
    "ScanState",
    "clear_context",
    "get_context",
]
