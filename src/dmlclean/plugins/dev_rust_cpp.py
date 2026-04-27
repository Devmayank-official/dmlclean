"""
Rust/C++ build artifacts cleaner plugin.

Cleans target directories, object files, and build outputs.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import ClassVar

from dmlclean.plugins.base import CleanCandidate, CleanerPlugin, RiskLevel


class RustCppDevPlugin(CleanerPlugin):
    """Plugin for cleaning Rust/C++ build artifacts."""

    @property
    def name(self) -> str:
        return "dev_rust_cpp"

    @property
    def description(self) -> str:
        return "Rust/C++ build artifacts (target/, *.o, *.obj, cmake-build)"

    @property
    def default_enabled(self) -> bool:
        return False  # Opt-in for development environments

    # Patterns with risk levels and reasons
    PATTERNS: ClassVar[list[tuple[str, RiskLevel, str]]] = [
        ("target", RiskLevel.MEDIUM, "Rust/CMake build output"),
        ("cmake-build-*", RiskLevel.MEDIUM, "CLion CMake build directory"),
        ("*.o", RiskLevel.LOW, "Object file"),
        ("*.obj", RiskLevel.LOW, "Object file"),
        ("*.pdb", RiskLevel.LOW, "Debug symbols"),
        ("*.ilk", RiskLevel.LOW, "Linker file"),
        ("*.a", RiskLevel.LOW, "Static library"),
        ("*.lib", RiskLevel.LOW, "Static library"),
        ("*.so", RiskLevel.LOW, "Shared library"),
        ("*.dll", RiskLevel.LOW, "Dynamic library"),
        ("*.dylib", RiskLevel.LOW, "Dynamic library"),
        ("*.exe", RiskLevel.LOW, "Executable (build output)"),
        ("Debug", RiskLevel.MEDIUM, "Debug build output"),
        ("Release", RiskLevel.MEDIUM, "Release build output"),
        ("x64", RiskLevel.MEDIUM, "x64 build output"),
        ("x86", RiskLevel.MEDIUM, "x86 build output"),
    ]

    async def scan(self, roots: list[Path]) -> AsyncGenerator[CleanCandidate, None]:  # type: ignore[override]  # Async generator
        """Scan for Rust/C++ build artifacts."""
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
                            for item in root.rglob(pattern):
                                try:
                                    if item.is_file():
                                        # Check for Cargo.toml sibling for target dirs
                                        if pattern == "target":
                                            cargo_toml = item.parent / "Cargo.toml"
                                            if not cargo_toml.exists():
                                                continue

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
                                    pass
                        else:
                            if "*" in pattern:
                                # Glob pattern
                                for item in root.glob(pattern):
                                    try:
                                        if item.is_dir():
                                            total_size = sum(
                                                f.stat().st_size
                                                for f in item.rglob("*")
                                                if f.is_file()
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
                                        pass
                            else:
                                # Exact directory name
                                for item in root.rglob(pattern):
                                    try:
                                        if not item.is_dir():
                                            continue

                                        # For target/, check for Cargo.toml or CMakeLists.txt
                                        if pattern == "target":
                                            cargo_toml = item.parent / "Cargo.toml"
                                            cmake_lists = item.parent / "CMakeLists.txt"
                                            if not (cargo_toml.exists() or cmake_lists.exists()):
                                                continue

                                        total_size = 0
                                        file_count = 0
                                        for f in item.rglob("*"):
                                            if f.is_file():
                                                try:
                                                    total_size += f.stat().st_size
                                                    file_count += 1
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
                                    except (OSError, PermissionError):
                                        pass

                except (OSError, PermissionError):
                    pass

            return candidates

        candidates = await loop.run_in_executor(None, sync_scan)
        for candidate in candidates:
            yield candidate
