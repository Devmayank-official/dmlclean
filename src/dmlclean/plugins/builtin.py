# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Built-in plugin registry for DMLClean.

This module provides the entry point for all built-in cleaning plugins.
Plugins are registered via the `dmlclean.plugins` entry point group in pyproject.toml.

Developed by DML Labs
Lead Engineer: Github/Devmayank-official
Project URL: https://github.com/Devmayank-official/dml-clean
"""

from dmlclean.plugins.ai_ml import AIMLPlugin
from dmlclean.plugins.base import CleanerPlugin
from dmlclean.plugins.browser import BrowserPlugin
from dmlclean.plugins.cloud_sync import CloudSyncPlugin
from dmlclean.plugins.dev_java import JavaDevPlugin
from dmlclean.plugins.dev_node import NodeDevPlugin
from dmlclean.plugins.dev_python import PythonDevPlugin
from dmlclean.plugins.dev_rust_cpp import RustCppDevPlugin
from dmlclean.plugins.gaming import GamingPlugin
from dmlclean.plugins.ide import IDEPlugin
from dmlclean.plugins.media import MediaPlugin
from dmlclean.plugins.messaging import MessagingPlugin
from dmlclean.plugins.package_mgr import PackageManagerPlugin
from dmlclean.plugins.smart_scan import SmartScanPlugin
from dmlclean.plugins.system_junk import SystemJunkPlugin

# Export all built-in plugin classes for direct import
__all__ = [
    "AIMLPlugin",
    "BrowserPlugin",
    "CloudSyncPlugin",
    "GamingPlugin",
    "IDEPlugin",
    "JavaDevPlugin",
    "MediaPlugin",
    "MessagingPlugin",
    "NodeDevPlugin",
    "PackageManagerPlugin",
    "PythonDevPlugin",
    "RustCppDevPlugin",
    "SmartScanPlugin",
    "SystemJunkPlugin",
]

# List of all plugin classes for iteration/discovery
BUILTIN_PLUGINS = [
    SystemJunkPlugin,
    BrowserPlugin,
    PythonDevPlugin,
    NodeDevPlugin,
    JavaDevPlugin,
    RustCppDevPlugin,
    IDEPlugin,
    GamingPlugin,
    MediaPlugin,
    MessagingPlugin,
    AIMLPlugin,
    CloudSyncPlugin,
    PackageManagerPlugin,
    SmartScanPlugin,
]


def get_all_plugins() -> list[type[CleanerPlugin]]:
    """
    Get all built-in plugin classes.

    Returns:
        list[type[CleanerPlugin]]: List of plugin classes.
    """
    return BUILTIN_PLUGINS.copy()


def get_plugin_by_name(name: str) -> type[CleanerPlugin] | None:
    """
    Get a plugin class by name.

    Args:
        name: Plugin name (e.g., 'browser', 'dev_python').

    Returns:
        type[CleanerPlugin] | None: Plugin class if found.
    """
    name_lower = name.lower().replace("-", "_")
    for plugin in BUILTIN_PLUGINS:
        if plugin().name.lower() == name_lower:
            return plugin
    return None


def instantiate_all_plugins() -> list[CleanerPlugin]:
    """
    Instantiate all built-in plugins.

    Returns:
        list[CleanerPlugin]: List of plugin instances.
    """
    return [plugin() for plugin in BUILTIN_PLUGINS]
