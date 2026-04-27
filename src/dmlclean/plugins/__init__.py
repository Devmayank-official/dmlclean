"""
Plugin system for DMLClean.

All cleaning plugins inherit from the CleanerPlugin ABC.
Plugins are discovered via entry points in pyproject.toml.

Developed by DML Labs
Lead Engineer: Github/Devmayank-official
Project URL: https://github.com/Devmayank-official/dml-clean
"""

from dmlclean.plugins.base import CleanCandidate, CleanerPlugin, RiskLevel
from dmlclean.plugins.builtin import (
    BUILTIN_PLUGINS,
    get_all_plugins,
    get_plugin_by_name,
    instantiate_all_plugins,
)

__all__ = [
    # Builtin plugin registry
    "BUILTIN_PLUGINS",
    "CleanCandidate",
    "CleanerPlugin",
    "RiskLevel",
    "get_all_plugins",
    "get_plugin_by_name",
    "instantiate_all_plugins",
]
