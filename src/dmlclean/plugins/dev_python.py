"""
Python development artifacts cleaner plugin.

Cleans __pycache__, .pytest_cache, .mypy_cache, build artifacts, etc.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import ClassVar

from dmlclean.plugins.base import CleanCandidate, CleanerPlugin, RiskLevel


class PythonDevPlugin(CleanerPlugin):
    """Plugin for cleaning Python development artifacts."""

    @property
    def name(self) -> str:
        return "dev_python"

    @property
    def description(self) -> str:
        return "Python development artifacts (__pycache__, build, etc.)"

    @property
    def default_enabled(self) -> bool:
        return True

    # Patterns to clean
    PATTERNS: ClassVar[list[tuple[str, RiskLevel, str]]] = [
        ("__pycache__", RiskLevel.LOW, "Python bytecode cache"),
        (".pytest_cache", RiskLevel.LOW, "Pytest cache"),
        (".mypy_cache", RiskLevel.LOW, "MyPy cache"),
        (".ruff_cache", RiskLevel.LOW, "Ruff cache"),
        (".tox", RiskLevel.LOW, "Tox environment"),
        (".nox", RiskLevel.LOW, "Nox environment"),
        (".coverage", RiskLevel.LOW, "Coverage data"),
        ("htmlcov", RiskLevel.LOW, "HTML coverage report"),
        ("build", RiskLevel.MEDIUM, "Build artifacts"),
        ("dist", RiskLevel.MEDIUM, "Distribution artifacts"),
        ("*.egg-info", RiskLevel.LOW, "Egg info"),
        ("*.pyc", RiskLevel.LOW, "Compiled Python file"),
        ("*.pyo", RiskLevel.LOW, "Optimized Python file"),
        (".ipynb_checkpoints", RiskLevel.MEDIUM, "Jupyter checkpoint"),
    ]

    async def scan(self, roots: list[Path]) -> AsyncGenerator[CleanCandidate, None]:  # type: ignore[override]  # Async generator
        """Scan for Python development artifacts."""
        import asyncio

        loop = asyncio.get_event_loop()

        def sync_scan() -> list[CleanCandidate]:
            candidates = []

            for root in roots:
                if not root.exists():
                    continue

                try:
                    for pattern, risk, reason in self.PATTERNS:
                        if pattern.startswith("*."):
                            # File extension pattern
                            for item in root.rglob(pattern):
                                try:
                                    if item.is_file():
                                        stat = item.stat()
                                        candidates.append(
                                            CleanCandidate(
                                                path=item,
                                                category=self.name,
                                                size_bytes=stat.st_size,
                                                risk_level=risk,
                                                reason=reason,
                                                last_accessed=stat.st_atime,
                                                last_modified=stat.st_mtime,
                                            )
                                        )
                                except (OSError, PermissionError):
                                    continue
                        else:
                            # Directory pattern
                            for item in root.rglob(pattern):
                                try:
                                    if item.is_dir():
                                        # Calculate directory size
                                        total_size = sum(
                                            f.stat().st_size for f in item.rglob("*") if f.is_file()
                                        )
                                        stat = item.stat()
                                        candidates.append(
                                            CleanCandidate(
                                                path=item,
                                                category=self.name,
                                                size_bytes=total_size,
                                                risk_level=risk,
                                                reason=reason,
                                                last_accessed=stat.st_atime,
                                                last_modified=stat.st_mtime,
                                                is_directory=True,
                                            )
                                        )
                                except (OSError, PermissionError):
                                    continue
                except (OSError, PermissionError):
                    pass

            return candidates

        candidates = await loop.run_in_executor(None, sync_scan)
        for candidate in candidates:
            yield candidate
