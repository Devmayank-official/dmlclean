"""
Node.js development artifacts cleaner plugin.

Cleans node_modules (opt-in, age-gated), .next, .vite, npm cache, etc.
"""

from __future__ import annotations

import os
import time
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import ClassVar

from dmlclean.plugins.base import CleanCandidate, CleanerPlugin, RiskLevel


class NodeDevPlugin(CleanerPlugin):
    """Plugin for cleaning Node.js development artifacts."""

    @property
    def name(self) -> str:
        return "dev_node"

    @property
    def description(self) -> str:
        return "Node.js development artifacts (node_modules, build output, caches)"

    @property
    def default_enabled(self) -> bool:
        return False  # Opt-in due to HIGH risk for node_modules

    # Patterns with risk levels and reasons
    PATTERNS: ClassVar[list[tuple[str, RiskLevel, str]]] = [
        # Build outputs (MEDIUM risk)
        ("node_modules", RiskLevel.HIGH, "Node.js dependencies (opt-in, age-gated)"),
        (".next", RiskLevel.LOW, "Next.js build output"),
        (".nuxt", RiskLevel.LOW, "Nuxt.js build output"),
        (".svelte-kit", RiskLevel.LOW, "SvelteKit build output"),
        (".vite", RiskLevel.LOW, "Vite cache"),
        (".turbo", RiskLevel.LOW, "Turborepo cache"),
        (".parcel-cache", RiskLevel.LOW, "Parcel cache"),
        (".eslintcache", RiskLevel.LOW, "ESLint cache"),
        ("*.tsbuildinfo", RiskLevel.LOW, "TypeScript build info"),
        ("coverage", RiskLevel.LOW, "Test coverage output"),
        ("dist", RiskLevel.MEDIUM, "Build distribution output"),
        ("build", RiskLevel.MEDIUM, "Build output directory"),
        ("out", RiskLevel.MEDIUM, "Build output directory"),
    ]

    async def scan(self, roots: list[Path]) -> AsyncGenerator[CleanCandidate, None]:  # type: ignore[override]  # Async generator
        """Scan for Node.js development artifacts."""
        import asyncio

        loop = asyncio.get_event_loop()

        def sync_scan() -> list[CleanCandidate]:
            candidates = []
            node_modules_min_age_days = 30  # Configurable age gate

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
                                except (OSError, PermissionError) as e:
                                    self.log_warning(f"Cannot access {item}: {e}")
                        else:
                            # Directory pattern
                            for item in root.rglob(pattern):
                                try:
                                    if not item.is_dir():
                                        continue

                                    # Special handling for node_modules - age gate
                                    if pattern == "node_modules":
                                        # Check if there's a package.json sibling
                                        package_json = item.parent / "package.json"
                                        if not package_json.exists():
                                            continue

                                        # Check age - only clean if older than threshold
                                        try:
                                            mtime = item.stat().st_mtime
                                            age_days = (time.time() - mtime) / (24 * 60 * 60)
                                            if age_days < node_modules_min_age_days:
                                                self.log_debug(
                                                    f"Skipping {item} - {age_days:.1f} days old "
                                                    f"(threshold: {node_modules_min_age_days} days)"
                                                )
                                                continue
                                        except OSError:
                                            continue

                                    # Calculate directory size
                                    total_size = 0
                                    file_count = 0
                                    try:
                                        for f in item.rglob("*"):
                                            if f.is_file():
                                                try:
                                                    total_size += f.stat().st_size
                                                    file_count += 1
                                                except OSError:
                                                    pass
                                    except OSError:
                                        pass

                                    stat = item.stat()
                                    candidates.append(
                                        CleanCandidate(
                                            path=item,
                                            category=self.name,
                                            size_bytes=total_size,
                                            risk_level=risk,
                                            reason=f"{reason} ({file_count} files)",
                                            last_accessed=stat.st_atime,
                                            last_modified=stat.st_mtime,
                                            is_directory=True,
                                        )
                                    )
                                except (OSError, PermissionError) as e:
                                    self.log_warning(f"Cannot access {item}: {e}")

                except (OSError, PermissionError) as e:
                    self.log_warning(f"Error scanning {root}: {e}")

            return candidates

        candidates = await loop.run_in_executor(None, sync_scan)
        for candidate in candidates:
            yield candidate

    def get_windows_paths(self) -> list[str]:
        """Get Windows-specific npm cache paths."""
        appdata = os.environ.get("APPDATA", "")
        localappdata = os.environ.get("LOCALAPPDATA", "")
        paths = []
        if appdata:
            paths.append(str(Path(appdata) / "npm-cache"))
        if localappdata:
            paths.append(str(Path(localappdata) / "npm-cache"))
        return paths

    def get_macos_paths(self) -> list[str]:
        """Get macOS-specific npm cache paths."""
        return [str(Path.home() / ".npm")]

    def get_linux_paths(self) -> list[str]:
        """Get Linux-specific npm cache paths."""
        return [str(Path.home() / ".npm")]
