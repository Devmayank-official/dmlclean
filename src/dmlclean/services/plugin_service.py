# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Plugin service for DMLClean.

Domain service for managing plugin discovery and installation.
"""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any

import httpx
from loguru import logger

from dmlclean.storage.paths import get_cache_dir


class PluginService:
    """
    Domain service for plugin management.

    The PluginService provides high-level operations for managing
    DMLClean plugins, including:
    - Listing available plugins (from GitHub registry)
    - Installing plugins
    - Uninstalling plugins
    - Updating plugins
    - Getting plugin information

    Attributes:
        cache_dir: Directory for caching plugin registry.
        plugins_dir: Directory for installed plugins.

    Example:
        ```python
        from dmlclean.services import PluginService

        service = PluginService()

        # List available plugins
        plugins = service.list_available()

        # Install plugin
        service.install("aws-cleanup")

        # List installed plugins
        installed = service.list_installed()

        # Uninstall plugin
        service.uninstall("aws-cleanup")
        ```
    """

    PLUGIN_REGISTRY_URL = (
        "https://raw.githubusercontent.com/dmlclean/plugin-registry/main/plugins.json"
    )
    """GitHub-hosted plugin registry URL."""

    def __init__(self) -> None:
        """
        Initialize the plugin service.

        Sets up cache and plugins directories.
        """
        self.cache_dir = get_cache_dir() / "plugins"
        self.plugins_dir = get_cache_dir() / "plugins" / "installed"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("PluginService initialized")

    def list_available(
        self,
        use_cache: bool = True,
        cache_ttl_hours: int = 24,
    ) -> list[dict[str, Any]]:
        """
        List available plugins from registry.

        Args:
            use_cache: Whether to use cached registry.
            cache_ttl_hours: Cache time-to-live in hours.

        Returns:
            list[dict[str, Any]]: List of plugin metadata.

        Raises:
            httpx.HTTPError: If registry fetch fails.

        Example:
            ```python
            plugins = service.list_available()
            for plugin in plugins:
                print(f"{plugin['name']}: {plugin['description']}")
            ```
        """
        cache_file = self.cache_dir / "registry.json"

        # Check cache
        if use_cache and cache_file.exists():
            import time

            age_hours = (time.time() - cache_file.stat().st_mtime) / 3600
            if age_hours < cache_ttl_hours:
                logger.debug(f"Using cached plugin registry ({age_hours:.1f}h old)")
                return json.loads(cache_file.read_text())

        # Fetch from GitHub
        logger.debug("Fetching plugin registry from GitHub...")
        try:
            response = httpx.get(self.PLUGIN_REGISTRY_URL, timeout=5.0)
            response.raise_for_status()
            plugins = response.json().get("plugins", [])

            # Cache it
            cache_file.write_text(json.dumps(plugins, indent=2))
            logger.debug(f"Fetched {len(plugins)} plugins from registry")

            return plugins
        except httpx.HTTPError:
            # Silently use cached version or return empty
            if cache_file.exists():
                logger.debug("Using cached plugin registry")
                return json.loads(cache_file.read_text())
            logger.debug("Plugin registry unavailable, using built-in plugins only")
            return []

    def search(self, query: str) -> list[dict[str, Any]]:
        """
        Search for plugins.

        Args:
            query: Search query (matches name, description, author).

        Returns:
            list[dict[str, Any]]: Matching plugins.

        Example:
            ```python
            # Search for AWS plugins
            aws_plugins = service.search("aws")

            # Search for cloud plugins
            cloud_plugins = service.search("cloud")
            ```
        """
        plugins = self.list_available()
        query_lower = query.lower()

        return [
            p
            for p in plugins
            if query_lower in p.get("name", "").lower()
            or query_lower in p.get("description", "").lower()
            or query_lower in p.get("author", "").lower()
        ]

    def get_plugin_info(self, name: str) -> dict[str, Any] | None:
        """
        Get information about a specific plugin.

        Args:
            name: Plugin name.

        Returns:
            dict[str, Any] | None: Plugin metadata if found.

        Example:
            ```python
            info = service.get_plugin_info("aws-cleanup")
            if info:
                print(f"Version: {info['version']}")
                print(f"Author: {info['author']}")
            ```
        """
        plugins = self.list_available()
        for plugin in plugins:
            if plugin.get("name") == name:
                return plugin
        return None

    def install(
        self,
        name: str,
        version: str | None = None,
        upgrade: bool = False,
    ) -> dict[str, Any]:
        """
        Install a plugin.

        Args:
            name: Plugin name.
            version: Specific version to install (latest if None).
            upgrade: Whether to upgrade if already installed.

        Returns:
            dict[str, Any]: Installation result.

        Raises:
            ValueError: If plugin not found.
            subprocess.CalledProcessError: If installation fails.

        Example:
            ```python
            # Install latest version
            result = service.install("aws-cleanup")

            # Install specific version
            result = service.install("aws-cleanup", version="1.2.0")

            # Upgrade if installed
            result = service.install("aws-cleanup", upgrade=True)
            ```
        """
        # Check if already installed
        installed = self.list_installed()
        if name in installed:
            if not upgrade:
                return {
                    "success": False,
                    "error": f"Plugin '{name}' already installed. Use upgrade=True to upgrade.",
                }

        # Get plugin info
        plugin_info = self.get_plugin_info(name)
        if plugin_info is None:
            raise ValueError(f"Plugin '{name}' not found in registry")

        # Get download URL
        download_url = plugin_info.get("download_url")
        if not download_url:
            raise ValueError(f"Plugin '{name}' has no download URL")

        # If version specified, construct versioned URL
        if version:
            # Try to get versioned URL from releases
            download_url = download_url.replace("latest", f"tags/v{version}")

        # Install via pip
        logger.info(f"Installing plugin: {name} from {download_url}")
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    download_url,
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            logger.info(f"Plugin installed: {name}")
            return {
                "success": True,
                "name": name,
                "version": plugin_info.get("version", "unknown"),
                "output": result.stdout,
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Plugin installation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "stderr": e.stderr,
            }

    def uninstall(self, name: str) -> dict[str, Any]:
        """
        Uninstall a plugin.

        Args:
            name: Plugin name.

        Returns:
            dict[str, Any]: Uninstallation result.

        Raises:
            ValueError: If plugin not installed.

        Example:
            ```python
            result = service.uninstall("aws-cleanup")
            if result["success"]:
                print("Plugin uninstalled")
            ```
        """
        # Check if installed
        installed = self.list_installed()
        if name not in installed:
            raise ValueError(f"Plugin '{name}' not installed")

        # Uninstall via pip
        logger.info(f"Uninstalling plugin: {name}")
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "uninstall",
                    "-y",
                    name,
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            logger.info(f"Plugin uninstalled: {name}")
            return {
                "success": True,
                "name": name,
                "output": result.stdout,
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Plugin uninstallation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "stderr": e.stderr,
            }

    def list_installed(self) -> dict[str, str]:
        """
        List installed plugins.

        Returns:
            dict[str, str]: Mapping of plugin name to version.

        Example:
            ```python
            installed = service.list_installed()
            for name, version in installed.items():
                print(f"{name}: {version}")
            ```
        """
        # Use pip to list installed packages with 'dmlclean' in name
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                check=True,
            )

            packages = json.loads(result.stdout)
            plugins = {}

            for pkg in packages:
                name = pkg.get("name", "")
                if name.startswith("dmlclean-"):
                    # Extract plugin name from package name
                    plugin_name = name.replace("dmlclean-", "")
                    plugins[plugin_name] = pkg.get("version", "unknown")

            return plugins
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list installed plugins: {e}")
            return {}

    def update(self, name: str | None = None) -> dict[str, Any]:
        """
        Update plugin(s).

        Args:
            name: Plugin name (all if None).

        Returns:
            dict[str, Any]: Update results.

        Example:
            ```python
            # Update all plugins
            result = service.update()

            # Update specific plugin
            result = service.update("aws-cleanup")
            ```
        """
        if name:
            # Update specific plugin
            return self.install(name, upgrade=True)

        # Update all plugins
        installed = self.list_installed()
        results = {}

        for plugin_name in installed:
            results[plugin_name] = self.install(plugin_name, upgrade=True)

        return {
            "success": all(r.get("success", False) for r in results.values()),
            "results": results,
        }

    def get_statistics(self) -> dict[str, Any]:
        """
        Get plugin statistics.

        Returns:
            dict[str, Any]: Statistics dictionary.

        Example:
            ```python
            stats = service.get_statistics()
            print(f"Available: {stats['available']}")
            print(f"Installed: {stats['installed']}")
            ```
        """
        available = self.list_available()
        installed = self.list_installed()

        return {
            "available": len(available),
            "installed": len(installed),
            "plugin_names": [p["name"] for p in available],
            "installed_names": list(installed.keys()),
        }


__all__ = ["PluginService"]
