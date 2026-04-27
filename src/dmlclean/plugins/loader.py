# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Plugin loader for DMLClean.

Discovers and loads plugins via:
1. Built-in plugins (from dmlclean.plugins)
2. Entry points (installed plugin packages)
3. Manual loading (from plugins directory)

Example:
    ```python
    from dmlclean.plugins.loader import PluginLoader

    loader = PluginLoader()

    # Load all plugins
    plugins = loader.load_all()

    # Load only built-in
    builtin = loader.load_builtin()

    # Load from entry points
    external = loader.load_entry_points()
    ```
"""

from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any

from loguru import logger

from dmlclean.plugins.base import CleanerPlugin


class PluginLoader:
    """
    Plugin discovery and loading for DMLClean.

    The PluginLoader discovers and loads plugins from multiple sources:
    1. Built-in plugins (dmlclean.plugins.*)
    2. Entry points (installed plugin packages)
    3. Manual loading (from ~/.dmlclean/plugins/)

    Attributes:
        plugins_dir: Directory for manually loaded plugins.

    Example:
        ```python
        loader = PluginLoader()

        # Load all plugins
        plugins = loader.load_all()

        for plugin in plugins:
            print(f"Loaded: {plugin.name} v{plugin.version}")
        ```
    """

    BUILTIN_PACKAGE = "dmlclean.plugins"
    """Package containing built-in plugins."""

    def __init__(self) -> None:
        """
        Initialize the plugin loader.

        Sets up plugin directories and caches.
        """
        from dmlclean.storage.paths import get_cache_dir

        self.plugins_dir = get_cache_dir() / "plugins" / "installed"
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"PluginLoader initialized, plugins dir: {self.plugins_dir}")

    def load_all(self) -> list[CleanerPlugin]:
        """
        Load all plugins from all sources.

        Returns:
            list[CleanerPlugin]: List of loaded plugins.

        Raises:
            ImportError: If plugin import fails.

        Example:
            ```python
            loader = PluginLoader()
            plugins = loader.load_all()
            print(f"Loaded {len(plugins)} plugins")
            ```
        """
        plugins: list[CleanerPlugin] = []

        # Load built-in plugins
        builtin_plugins = self.load_builtin()
        plugins.extend(builtin_plugins)
        logger.debug(f"Loaded {len(builtin_plugins)} built-in plugins")

        # Load entry point plugins
        entry_plugins = self.load_entry_points()
        plugins.extend(entry_plugins)
        logger.debug(f"Loaded {len(entry_plugins)} entry point plugins")

        # Load manual plugins
        manual_plugins = self.load_manual()
        plugins.extend(manual_plugins)
        logger.debug(f"Loaded {len(manual_plugins)} manual plugins")

        logger.info(f"Total plugins loaded: {len(plugins)}")
        return plugins

    def load_builtin(self) -> list[CleanerPlugin]:
        """
        Load built-in plugins.

        Discovers plugins in the dmlclean.plugins package by
        importing all modules and finding CleanerPlugin subclasses.

        Returns:
            list[CleanerPlugin]: List of built-in plugins.

        Raises:
            ImportError: If plugin import fails.
        """
        plugins: list[CleanerPlugin] = []

        # List of built-in plugin modules
        builtin_modules = [
            "system_junk",
            "browser",
            "dev_python",
            "dev_node",
            "dev_java",
            "dev_rust_cpp",
            "ide",
            "gaming",
            "media",
            "messaging",
            "ai_ml",
            "cloud_sync",
            "package_mgr",
            "smart_scan",
        ]

        for module_name in builtin_modules:
            try:
                module = importlib.import_module(f"{self.BUILTIN_PACKAGE}.{module_name}")

                # Find plugin class in module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, CleanerPlugin)
                        and attr is not CleanerPlugin
                    ):
                        try:
                            plugin = attr()
                            plugins.append(plugin)
                            logger.debug(f"Loaded built-in plugin: {plugin.name}")
                        except Exception as e:
                            logger.warning(f"Failed to instantiate plugin {attr_name}: {e}")
                        break  # Only one plugin per module

            except ImportError as e:
                logger.warning(f"Failed to import built-in plugin {module_name}: {e}")

        return plugins

    def load_entry_points(self) -> list[CleanerPlugin]:
        """
        Load plugins from entry points.

        Discovers plugins registered via the `dmlclean.plugins`
        entry point group.

        Returns:
            list[CleanerPlugin]: List of entry point plugins.

        Raises:
            ImportError: If plugin import fails.

        Example:
            ```python
            # Plugin package registers entry point:
            # [project.entry-points."dmlclean.plugins"]
            # aws_cleanup = "dmlclean_aws_plugin:AWSPlugin"

            loader = PluginLoader()
            plugins = loader.load_entry_points()
            ```
        """
        plugins: list[CleanerPlugin] = []

        try:
            from importlib.metadata import entry_points

            # Get entry points
            eps = entry_points(group="dmlclean.plugins")

            for ep in eps:
                try:
                    plugin_class = ep.load()
                    if isinstance(plugin_class, type) and issubclass(plugin_class, CleanerPlugin):
                        plugin = plugin_class()
                        plugins.append(plugin)
                        logger.info(f"Loaded entry point plugin: {plugin.name} ({ep.name})")
                except Exception as e:
                    logger.warning(f"Failed to load entry point {ep.name}: {e}")

        except ImportError:
            logger.debug("importlib.metadata not available, skipping entry points")
        except Exception as e:
            logger.warning(f"Failed to load entry points: {e}")

        return plugins

    def load_manual(self) -> list[CleanerPlugin]:
        """
        Load plugins from manual directory.

        Discovers plugins in ~/.dmlclean/plugins/ by importing
        all .py files.

        Returns:
            list[CleanerPlugin]: List of manual plugins.

        Raises:
            ImportError: If plugin import fails.

        Example:
            ```python
            # User places plugin in ~/.dmlclean/plugins/my_plugin.py
            loader = PluginLoader()
            plugins = loader.load_manual()
            ```
        """
        plugins: list[CleanerPlugin] = []

        if not self.plugins_dir.exists():
            return plugins

        for plugin_file in self.plugins_dir.glob("*.py"):
            try:
                plugin = self._load_plugin_file(plugin_file)
                if plugin:
                    plugins.append(plugin)
            except Exception as e:
                logger.warning(f"Failed to load manual plugin {plugin_file}: {e}")

        return plugins

    def _load_plugin_file(self, plugin_file: Path) -> CleanerPlugin | None:
        """
        Load a single plugin file.

        Args:
            plugin_file: Path to plugin .py file.

        Returns:
            CleanerPlugin | None: Plugin instance if found.

        Raises:
            ImportError: If import fails.
        """
        module_name = plugin_file.stem
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)

        if spec is None or spec.loader is None:
            logger.warning(f"Cannot load plugin spec: {plugin_file}")
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find plugin class
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, CleanerPlugin)
                and attr is not CleanerPlugin
            ):
                return attr()

        logger.warning(f"No plugin class found in {plugin_file}")
        return None

    def get_plugin_by_name(self, name: str) -> CleanerPlugin | None:
        """
        Get a plugin by name.

        Args:
            name: Plugin name.

        Returns:
            CleanerPlugin | None: Plugin if found.

        Example:
            ```python
            loader = PluginLoader()
            plugin = loader.get_plugin_by_name("dev_python")
            if plugin:
                print(f"Found: {plugin.description}")
            ```
        """
        all_plugins = self.load_all()
        for plugin in all_plugins:
            if plugin.name == name:
                return plugin
        return None

    def get_enabled_plugins(
        self,
        config: dict[str, Any] | None = None,
    ) -> list[CleanerPlugin]:
        """
        Get enabled plugins based on configuration.

        Args:
            config: Optional configuration dictionary.

        Returns:
            list[CleanerPlugin]: List of enabled plugins.

        Example:
            ```python
            loader = PluginLoader()
            enabled = loader.get_enabled_plugins()
            print(f"Enabled plugins: {[p.name for p in enabled]}")
            ```
        """
        all_plugins = self.load_all()

        if config is None:
            # Return all default-enabled plugins
            return [p for p in all_plugins if p.default_enabled]

        # Filter by config
        categories_config = config.get("categories", {})
        enabled_plugins = []

        for plugin in all_plugins:
            cat_config = categories_config.get(plugin.name, {})
            enabled = cat_config.get("enabled", plugin.default_enabled)
            if enabled:
                enabled_plugins.append(plugin)

        return enabled_plugins


__all__ = ["PluginLoader"]
