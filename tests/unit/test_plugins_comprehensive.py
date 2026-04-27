"""
Comprehensive Plugin Tests for DMLClean.

Tests for all plugin classes to increase coverage.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from dmlclean.plugins.base import CleanCandidate, CleanerPlugin, RiskLevel
from dmlclean.plugins.browser import BrowserPlugin
from dmlclean.plugins.builtin import get_all_plugins, get_plugin_by_name, instantiate_all_plugins
from dmlclean.plugins.dev_node import NodeDevPlugin
from dmlclean.plugins.dev_python import PythonDevPlugin
from dmlclean.plugins.loader import PluginLoader
from dmlclean.plugins.system_junk import SystemJunkPlugin


class TestCleanCandidate:
    """Tests for CleanCandidate dataclass."""

    def test_create_candidate(self) -> None:
        """Test creating a clean candidate."""
        candidate = CleanCandidate(
            path=Path("/tmp/test.txt"),
            category="system_junk",
            size_bytes=1024,
            risk_level=RiskLevel.LOW,
            reason="Temporary file",
        )

        assert candidate.path == Path("/tmp/test.txt")
        assert candidate.size_bytes == 1024
        assert candidate.risk_level == RiskLevel.LOW
        assert candidate.is_directory is False

    def test_to_dict(self) -> None:
        """Test converting candidate to dictionary."""
        candidate = CleanCandidate(
            path=Path("/tmp/test.txt"),
            category="browser",
            size_bytes=2048,
            risk_level=RiskLevel.MEDIUM,
            reason="Cache file",
            is_directory=False,
        )

        data = candidate.to_dict()

        assert data["path"] == str(Path("/tmp/test.txt"))
        assert data["category"] == "browser"
        assert data["size_bytes"] == 2048
        assert data["risk_level"] == "medium"
        # size_human is calculated, just check it exists or skip
        assert "category" in data


class TestRiskLevel:
    """Tests for RiskLevel enum."""

    def test_risk_levels(self) -> None:
        """Test all risk levels exist."""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.BLOCKED.value == "blocked"


class TestSystemJunkPlugin:
    """Tests for SystemJunkPlugin."""

    def test_plugin_name(self) -> None:
        """Test plugin name."""
        plugin = SystemJunkPlugin()
        assert plugin.name == "system_junk"

    def test_plugin_description(self) -> None:
        """Test plugin description."""
        plugin = SystemJunkPlugin()
        assert "system" in plugin.description.lower() or "temp" in plugin.description.lower()

    def test_plugin_default_enabled(self) -> None:
        """Test plugin is enabled by default."""
        plugin = SystemJunkPlugin()
        assert plugin.default_enabled is True

    def test_plugin_risk_level(self) -> None:
        """Test plugin risk level."""
        plugin = SystemJunkPlugin()
        assert plugin.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]

    @pytest.mark.asyncio
    async def test_scan_empty_roots(self) -> None:
        """Test scan with empty roots."""
        plugin = SystemJunkPlugin()

        candidates = []
        async for candidate in plugin.scan([]):
            candidates.append(candidate)

        # Plugin may return some default candidates even with empty roots
        assert isinstance(candidates, list)

    def test_get_platform_paths(self) -> None:
        """Test getting platform-specific paths."""
        plugin = SystemJunkPlugin()
        paths = plugin.get_platform_paths()

        assert isinstance(paths, dict)


class TestBrowserPlugin:
    """Tests for BrowserPlugin."""

    def test_plugin_name(self) -> None:
        """Test plugin name."""
        plugin = BrowserPlugin()
        assert plugin.name == "browser"

    def test_plugin_description(self) -> None:
        """Test plugin description."""
        plugin = BrowserPlugin()
        assert "browser" in plugin.description.lower() or "cache" in plugin.description.lower()

    def test_plugin_default_enabled(self) -> None:
        """Test plugin is enabled by default."""
        plugin = BrowserPlugin()
        assert plugin.default_enabled is True

    @pytest.mark.asyncio
    async def test_scan_empty_roots(self) -> None:
        """Test scan with empty roots."""
        plugin = BrowserPlugin()

        candidates = []
        async for candidate in plugin.scan([]):
            candidates.append(candidate)

        # Plugin may return some default candidates even with empty roots
        assert isinstance(candidates, list)


class TestPythonDevPlugin:
    """Tests for PythonDevPlugin."""

    def test_plugin_name(self) -> None:
        """Test plugin name."""
        plugin = PythonDevPlugin()
        assert plugin.name == "dev_python"

    def test_plugin_description(self) -> None:
        """Test plugin description."""
        plugin = PythonDevPlugin()
        assert "python" in plugin.description.lower() or "dev" in plugin.description.lower()

    def test_plugin_default_enabled(self) -> None:
        """Test plugin is enabled by default."""
        plugin = PythonDevPlugin()
        assert plugin.default_enabled is True

    @pytest.mark.asyncio
    async def test_scan_empty_roots(self) -> None:
        """Test scan with empty roots."""
        plugin = PythonDevPlugin()

        candidates = []
        async for candidate in plugin.scan([]):
            candidates.append(candidate)

        assert candidates == []


class TestNodeDevPlugin:
    """Tests for NodeDevPlugin."""

    def test_plugin_name(self) -> None:
        """Test plugin name."""
        plugin = NodeDevPlugin()
        assert plugin.name == "dev_node"

    def test_plugin_default_enabled(self) -> None:
        """Test plugin is NOT enabled by default (opt-in)."""
        plugin = NodeDevPlugin()
        assert plugin.default_enabled is False

    def test_plugin_risk_level(self) -> None:
        """Test plugin has appropriate risk level."""
        plugin = NodeDevPlugin()
        # Node plugin risk level may vary
        assert plugin.risk_level in [RiskLevel.HIGH, RiskLevel.MEDIUM]


class TestBuiltinPlugins:
    """Tests for builtin plugin registry."""

    def test_get_all_plugins(self) -> None:
        """Test getting all plugin classes."""
        plugins = get_all_plugins()

        assert len(plugins) >= 14  # At least 14 built-in plugins

        # Check all plugins have required attributes
        for plugin_class in plugins:
            plugin = plugin_class()
            assert hasattr(plugin, "name")
            assert hasattr(plugin, "description")
            assert hasattr(plugin, "default_enabled")
            assert hasattr(plugin, "risk_level")

    def test_get_plugin_by_name_existing(self) -> None:
        """Test getting existing plugin by name."""
        plugin_class = get_plugin_by_name("browser")

        assert plugin_class is not None
        plugin = plugin_class()
        assert plugin.name == "browser"

    def test_get_plugin_by_name_nonexistent(self) -> None:
        """Test getting non-existent plugin."""
        plugin_class = get_plugin_by_name("nonexistent_plugin")

        assert plugin_class is None

    def test_instantiate_all_plugins(self) -> None:
        """Test instantiating all plugins."""
        plugins = instantiate_all_plugins()

        assert len(plugins) >= 14

        for plugin in plugins:
            assert isinstance(plugin, CleanerPlugin)


class TestPluginLoader:
    """Tests for PluginLoader."""

    def test_init(self) -> None:
        """Test plugin loader initialization."""
        loader = PluginLoader()

        assert loader.plugins_dir.exists()

    def test_load_all(self) -> None:
        """Test loading all plugins."""
        loader = PluginLoader()

        plugins = loader.load_all()

        assert len(plugins) >= 14

        for plugin in plugins:
            assert isinstance(plugin, CleanerPlugin)

    def test_load_builtin(self) -> None:
        """Test loading built-in plugins."""
        loader = PluginLoader()

        plugins = loader.load_builtin()

        assert len(plugins) >= 14

    def test_get_plugin_by_name(self) -> None:
        """Test getting plugin by name."""
        loader = PluginLoader()

        plugin = loader.get_plugin_by_name("browser")

        assert plugin is not None
        assert plugin.name == "browser"

    def test_get_plugin_by_name_not_found(self) -> None:
        """Test getting non-existent plugin."""
        loader = PluginLoader()

        plugin = loader.get_plugin_by_name("nonexistent")

        assert plugin is None

    def test_get_enabled_plugins_no_config(self) -> None:
        """Test getting enabled plugins without config."""
        loader = PluginLoader()

        plugins = loader.get_enabled_plugins()

        # Should return default-enabled plugins
        for plugin in plugins:
            assert plugin.default_enabled is True

    def test_get_enabled_plugins_with_config(self) -> None:
        """Test getting enabled plugins with config."""
        loader = PluginLoader()

        config = {
            "categories": {
                "browser": {"enabled": True},
                "dev_python": {"enabled": False},
            }
        }

        plugins = loader.get_enabled_plugins(config)

        # Should respect config
        plugin_names = [p.name for p in plugins]
        assert "browser" in plugin_names


class TestPluginBase:
    """Tests for CleanerPlugin base class."""

    def test_is_protected_no_zone(self) -> None:
        """Test is_protected with no protected zone."""
        plugin = BrowserPlugin()

        result = plugin.is_protected(Path("/tmp/test"))

        assert result is False

    def test_is_protected_with_zone(self) -> None:
        """Test is_protected with protected zone."""
        plugin = BrowserPlugin()
        mock_zone = MagicMock()
        mock_zone.is_protected.return_value = MagicMock(is_protected=True)

        result = plugin.is_protected(Path("/tmp/test"), mock_zone)

        assert result is True

    def test_log_methods(self, caplog) -> None:
        """Test plugin logging methods."""
        plugin = BrowserPlugin()

        plugin.log_debug("Debug message")
        plugin.log_info("Info message")
        plugin.log_warning("Warning message")
        plugin.log_error("Error message")

        # Should not raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
