"""
AI/ML cache cleaner plugin.

Cleans HuggingFace, PyTorch, Keras model caches.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import ClassVar

from dmlclean.plugins.base import CleanCandidate, CleanerPlugin, RiskLevel


class AIMLPlugin(CleanerPlugin):
    """Plugin for cleaning AI/ML cache files."""

    @property
    def name(self) -> str:
        return "ai_ml"

    @property
    def description(self) -> str:
        return "AI/ML cache (HuggingFace, PyTorch, Keras)"

    @property
    def default_enabled(self) -> bool:
        return False  # HIGH risk - models are large and expensive to re-download

    @property
    def risk_level(self) -> RiskLevel:
        return RiskLevel.HIGH

    # AI/ML cache patterns - all HIGH risk
    PATTERNS: ClassVar[list[tuple[str, RiskLevel, str]]] = [
        ("huggingface", RiskLevel.HIGH, "HuggingFace model cache (large files)"),
        ("huggingface/hub", RiskLevel.HIGH, "HuggingFace hub models"),
        ("torch", RiskLevel.HIGH, "PyTorch cache"),
        ("keras", RiskLevel.HIGH, "Keras cache"),
        (".keras", RiskLevel.HIGH, "Keras cache directory"),
    ]

    async def scan(self, roots: list[Path]) -> AsyncGenerator[CleanCandidate, None]:  # type: ignore[override]  # Async generator
        """Scan for AI/ML cache files."""
        import asyncio

        loop = asyncio.get_event_loop()

        def sync_scan() -> list[CleanCandidate]:
            candidates = []

            for root in roots:
                if not root.exists():
                    continue

                try:
                    for pattern, risk, reason in self.PATTERNS:
                        for item in root.rglob(f"*{pattern}*"):
                            try:
                                if not item.is_dir():
                                    continue

                                # Calculate directory size
                                total_size = 0
                                file_count = 0
                                for f in item.rglob("*"):
                                    if f.is_file():
                                        try:
                                            total_size += f.stat().st_size
                                            file_count += 1
                                        except OSError:
                                            pass

                                # Only report if significant size (>100MB)
                                if total_size > 100 * 1024 * 1024:
                                    stat = item.stat()
                                    candidates.append(
                                        CleanCandidate(
                                            path=item,
                                            category=self.name,
                                            size_bytes=total_size,
                                            risk_level=risk,
                                            reason=(
                                                f"{reason} ({file_count} files, "
                                                f"{total_size / (1024 * 1024):.1f} MB)"
                                            ),
                                            last_accessed=stat.st_atime,
                                            last_modified=stat.st_mtime,
                                            is_directory=True,
                                        )
                                    )
                            except (OSError, PermissionError):
                                pass

                except (OSError, PermissionError):
                    pass

            return candidates

        candidates = await loop.run_in_executor(None, sync_scan)
        for candidate in candidates:
            yield candidate

    def get_windows_paths(self) -> list[str]:
        """Get Windows-specific AI/ML cache paths."""
        import os

        userprofile = os.environ.get("USERPROFILE", "")
        paths = []
        if userprofile:
            paths.append(str(Path(userprofile) / ".cache" / "huggingface"))
            paths.append(str(Path(userprofile) / ".cache" / "torch"))
            paths.append(str(Path(userprofile) / ".keras"))
        return paths

    def get_macos_paths(self) -> list[str]:
        """Get macOS-specific AI/ML cache paths."""
        return [
            str(Path.home() / ".cache" / "huggingface"),
            str(Path.home() / ".cache" / "torch"),
            str(Path.home() / ".keras"),
        ]

    def get_linux_paths(self) -> list[str]:
        """Get Linux-specific AI/ML cache paths."""
        return [
            str(Path.home() / ".cache" / "huggingface"),
            str(Path.home() / ".cache" / "torch"),
            str(Path.home() / ".keras"),
        ]
