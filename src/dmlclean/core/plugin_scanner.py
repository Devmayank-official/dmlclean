"""
Plugin-Integrated Scanner for DMLClean.

This module provides the plugin-based scanning architecture:
- Plugins discover and categorize files
- Scanner aggregates results from all enabled plugins
- Unified CleanCandidate model across all plugins
- Lazy loading with container-managed caching

Architecture:
    ```
    CLI → Service → PluginScanner → [Plugin1, Plugin2, ...] → ScanResult
    ```

Example:
    ```python
    # Container-managed plugin scanner
    container = Container.create()
    scanner = container.scanner  # PluginScanner with lazy-loaded plugins

    # Scan
    result = await scanner.scan([Path("/tmp")])
    ```
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger

from dmlclean.core.analyzer import CleanCandidate
from dmlclean.core.scanner import FileSystemScanner, ScanResult, ScanStats
from dmlclean.plugins.base import CleanerPlugin


@dataclass
class PluginScanConfig:
    """
    Configuration for plugin-based scanning.

    Attributes:
        enabled_categories: List of category names to scan.
        use_plugins: Whether to use plugins (default: True).
        fallback_to_regex: Use regex analyzer if plugins fail.
        parallel_execution: Run plugins in parallel.
        timeout_per_plugin: Timeout per plugin in seconds.
    """

    enabled_categories: list[str] | None = None
    use_plugins: bool = True
    fallback_to_regex: bool = False
    parallel_execution: bool = True
    timeout_per_plugin: float = 30.0


class PluginScanner:
    """
    Plugin-integrated file system scanner.

    The PluginScanner orchestrates plugin-based scanning:
    1. Loads enabled plugins (lazy, container-managed)
    2. Invokes each plugin's scan() method
    3. Aggregates CleanCandidate results
    4. Returns unified ScanResult

    This is the primary scanner for DMLClean v2.0+.

    Attributes:
        config: Plugin scan configuration.
        plugin_loader: PluginLoader instance.
        plugins_cache: Cached plugin instances.

    Example:
        ```python
        from dmlclean.container import Container

        container = Container.create()
        scanner = PluginScanner(
            plugin_loader=container.plugin_service,
            config=PluginScanConfig(
                enabled_categories=["browser", "dev_python"],
                parallel_execution=True,
            )
        )

        result = await scanner.scan([Path("/tmp")])
        ```
    """

    def __init__(
        self,
        plugin_loader: Any | None = None,
        config: PluginScanConfig | None = None,
        fallback_scanner: FileSystemScanner | None = None,
    ) -> None:
        """
        Initialize plugin scanner.

        Args:
            plugin_loader: PluginLoader or PluginService instance.
            config: Plugin scan configuration.
            fallback_scanner: Fallback scanner if plugins fail.
        """
        self.plugin_loader = plugin_loader
        self.config = config or PluginScanConfig()
        self.fallback_scanner = fallback_scanner or FileSystemScanner()

        self._plugins_cache: list[CleanerPlugin] = []
        self._plugins_loaded = False

        logger.debug(f"PluginScanner initialized: config={self.config}")

    def _load_plugins(self) -> list[CleanerPlugin]:
        """
        Load enabled plugins (lazy loading).

        Returns:
            list[CleanerPlugin]: List of enabled plugin instances.
        """
        if self._plugins_loaded:
            return self._plugins_cache

        if not self.config.use_plugins:
            logger.debug("Plugins disabled, using fallback scanner")
            return []

        try:
            # Load plugins from loader
            if hasattr(self.plugin_loader, "list_available"):
                # PluginService
                all_plugins = self.plugin_loader.list_available()
                plugin_instances = []
                for plugin_info in all_plugins:
                    try:
                        # Instantiate plugin
                        plugin_name = plugin_info.get("name", "")
                        if self.config.enabled_categories:
                            if plugin_name in self.config.enabled_categories:
                                plugin = self._instantiate_plugin(plugin_name)
                                if plugin:
                                    plugin_instances.append(plugin)
                        else:
                            # Load default-enabled plugins
                            plugin = self._instantiate_plugin(plugin_name)
                            if plugin and plugin.default_enabled:
                                plugin_instances.append(plugin)
                    except Exception:
                        pass  # Skip individual plugin errors
                self._plugins_cache = plugin_instances
            elif hasattr(self.plugin_loader, "load_all"):
                # PluginLoader
                all_plugins = self.plugin_loader.load_all()
                if self.config.enabled_categories:
                    self._plugins_cache = [
                        p for p in all_plugins if p.name in self.config.enabled_categories
                    ]
                else:
                    self._plugins_cache = [p for p in all_plugins if p.default_enabled]
            else:
                logger.warning("Unknown plugin loader type, skipping plugins")
                self._plugins_cache = []

            logger.info(f"Loaded {len(self._plugins_cache)} enabled plugins")
            self._plugins_loaded = True
            return self._plugins_cache

        except Exception as e:
            logger.error(f"Failed to load plugins: {e}")
            self._plugins_cache = []
            self._plugins_loaded = True
            return []

    def _instantiate_plugin(self, plugin_name: str) -> CleanerPlugin | None:
        """
        Instantiate a plugin by name.

        Args:
            plugin_name: Name of plugin to instantiate.

        Returns:
            CleanerPlugin | None: Plugin instance if successful.
        """
        try:
            # Try to import from builtin plugins
            from dmlclean.plugins.builtin import get_plugin_by_name

            plugin_class = get_plugin_by_name(plugin_name)
            if plugin_class:
                return plugin_class()
        except Exception as e:
            logger.debug(f"Failed to instantiate plugin {plugin_name}: {e}")

        return None

    async def scan(
        self,
        roots: list[Path],
        progress_callback: Callable[[int, Path], None] | None = None,
    ) -> ScanResult:
        """
        Scan using plugins (primary) with fallback to regex scanner.

        Args:
            roots: Root paths to scan.
            progress_callback: Optional progress callback.

        Returns:
            ScanResult: Aggregated scan result.
        """
        start_time = time.time()

        # Load plugins
        plugins = self._load_plugins()

        if not plugins:
            # No plugins, use fallback
            logger.debug("No plugins available, using fallback scanner")
            return await self.fallback_scanner.scan(roots, progress_callback)

        # Scan with plugins
        all_candidates: list[CleanCandidate] = []
        all_errors: list[tuple[Path, str]] = []
        total_files = 0
        total_dirs = 0
        total_size = 0

        if self.config.parallel_execution:
            # Parallel plugin execution
            tasks = []
            for plugin in plugins:
                task = self._scan_with_plugin(plugin, roots, progress_callback)
                tasks.append(task)

            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Plugin scan failed: {result}")
                        all_errors.append((Path(), str(result)))
                    else:
                        # Merge results
                        candidates, errors, files, dirs, size = result
                        all_candidates.extend(candidates)
                        all_errors.extend(errors)
                        total_files += files
                        total_dirs += dirs
                        total_size += size

            except Exception as e:
                logger.error(f"Parallel plugin scan failed: {e}")
                # Fallback to regex scanner
                if self.config.fallback_to_regex:
                    return await self.fallback_scanner.scan(roots, progress_callback)
                raise
        else:
            # Sequential plugin execution
            for plugin in plugins:
                try:
                    candidates, errors, files, dirs, size = await self._scan_with_plugin(
                        plugin, roots, progress_callback
                    )
                    all_candidates.extend(candidates)
                    all_errors.extend(errors)
                    total_files += files
                    total_dirs += dirs
                    total_size += size
                except Exception as e:
                    logger.error(f"Plugin {plugin.name} failed: {e}")
                    all_errors.append((Path(), str(e)))

        # Build result
        duration = time.time() - start_time
        stats = ScanStats(
            total_files=total_files,
            total_directories=total_dirs,
            total_size_bytes=total_size,
            errors=len(all_errors),
            duration_seconds=duration,
            files_per_second=total_files / duration if duration > 0 else 0,
        )

        # Convert candidates to paths for backward compatibility
        paths = [c.path for c in all_candidates if not c.is_directory]
        directories = [c.path for c in all_candidates if c.is_directory]

        result = ScanResult(
            paths=paths,
            directories=directories,
            stats=stats,
            errors=all_errors,
        )

        # Attach candidates for downstream use
        result.candidates = all_candidates  # type: ignore[attr-defined]

        logger.info(
            f"Plugin scan complete: {len(all_candidates)} candidates, "
            f"{total_files} files, {humanize_size(total_size)}"
        )

        return result

    async def _scan_with_plugin(
        self,
        plugin: CleanerPlugin,
        roots: list[Path],
        progress_callback: Callable[[int, Path], None] | None = None,
    ) -> tuple[list[CleanCandidate], list[tuple[Path, str]], int, int, int]:
        """
        Scan with a single plugin.

        Args:
            plugin: Plugin instance.
            roots: Root paths to scan.
            progress_callback: Progress callback.

        Returns:
            tuple: (candidates, errors, file_count, dir_count, total_size)
        """
        candidates: list[CleanCandidate] = []
        errors: list[tuple[Path, str]] = []
        file_count = 0
        dir_count = 0
        total_size = 0

        try:
            # Timeout protection
            async def do_scan() -> list[CleanCandidate]:
                plugin_candidates = []
                async for candidate in plugin.scan(roots):
                    plugin_candidates.append(candidate)
                    if progress_callback:
                        progress_callback(len(plugin_candidates), candidate.path)
                return plugin_candidates

            plugin_candidates = await asyncio.wait_for(
                do_scan(),
                timeout=self.config.timeout_per_plugin,
            )

            # Aggregate
            for candidate in plugin_candidates:
                candidates.append(candidate)
                if candidate.is_directory:
                    dir_count += 1
                else:
                    file_count += 1
                    total_size += candidate.size_bytes

            logger.debug(f"Plugin {plugin.name}: {len(candidates)} candidates")

        except TimeoutError:
            error_msg = f"Plugin {plugin.name} timed out after {self.config.timeout_per_plugin}s"
            logger.error(error_msg)
            errors.append((Path(), error_msg))
        except Exception as e:
            error_msg = f"Plugin {plugin.name} failed: {e}"
            logger.error(error_msg)
            errors.append((Path(), error_msg))

        return candidates, errors, file_count, dir_count, total_size

    def scan_sync(
        self,
        roots: list[Path],
        progress_callback: Callable[[int, Path], None] | None = None,
    ) -> ScanResult:
        """
        Synchronous wrapper for plugin scan.

        Args:
            roots: Root paths to scan.
            progress_callback: Progress callback.

        Returns:
            ScanResult: Scan result.
        """
        return asyncio.run(self.scan(roots, progress_callback))


def humanize_size(size_bytes: int) -> str:
    """Convert bytes to human-readable format."""
    size: float = size_bytes
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


__all__ = [
    "PluginScanConfig",
    "PluginScanner",
]
