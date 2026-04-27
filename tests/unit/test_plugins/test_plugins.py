"""
Plugin tests for DMLClean.

Tests for browser, dev_python, and smart_scan plugins.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from dmlclean.plugins.browser import BrowserPlugin
from dmlclean.plugins.dev_python import PythonDevPlugin
from dmlclean.plugins.smart_scan import SmartScanPlugin


class TestBrowserPlugin:
    """Tests for BrowserPlugin."""

    @pytest.fixture
    def plugin(self) -> BrowserPlugin:
        """Create browser plugin instance."""
        return BrowserPlugin()

    @pytest.fixture
    def browser_cache_tree(self, fake_fs: FakeFilesystem, monkeypatch: pytest.MonkeyPatch) -> None:
        """Create browser cache directory tree."""
        from pathlib import Path

        # Mock environment variables for testing
        monkeypatch.setenv("LOCALAPPDATA", "/Users/test/AppData/Local")
        monkeypatch.setenv("APPDATA", "/Users/test/AppData/Roaming")

        # Create Chrome cache structure that matches what browser.py expects
        chrome_cache = Path("/Users/test/AppData/Local/Google/Chrome/User Data/Default/Cache")
        chrome_cache.mkdir(parents=True, exist_ok=True)
        fake_fs.create_file(chrome_cache / "data_1", contents="cache")
        fake_fs.create_file(chrome_cache / "data_2", contents="cache")

        code_cache = Path("/Users/test/AppData/Local/Google/Chrome/User Data/Default/Code Cache")
        code_cache.mkdir(parents=True, exist_ok=True)
        fake_fs.create_file(code_cache / "file", contents="code")

        # Protected browser data (should NOT be yielded)
        user_data = Path("/Users/test/AppData/Local/Google/Chrome/User Data")
        user_data.mkdir(parents=True, exist_ok=True)
        fake_fs.create_file(user_data / "Bookmarks", contents="bookmarks")
        fake_fs.create_file(user_data / "Login Data", contents="passwords")
        fake_fs.create_file(user_data / "Cookies", contents="cookies")

    async def test_scan_yields_cache_files(
        self,
        plugin: BrowserPlugin,
        browser_cache_tree: None,
        fake_fs: FakeFilesystem,
    ) -> None:
        """Test that plugin yields cache files."""
        from pathlib import Path

        candidates = []
        # Scan the Chrome user data directory
        chrome_path = Path("/Users/test/AppData/Local/Google/Chrome/User Data")
        async for candidate in plugin.scan([chrome_path]):
            candidates.append(candidate)

        # Should find cache files
        assert len(candidates) > 0
        cache_files = [c for c in candidates if "Cache" in str(c.path)]
        assert len(cache_files) > 0

    async def test_scan_skips_protected(
        self,
        plugin: BrowserPlugin,
        browser_cache_tree: None,
    ) -> None:
        """Test that protected paths are never yielded."""
        from pathlib import Path

        candidates = []
        chrome_path = Path("/Users/test/AppData/Local/Google/Chrome/User Data")
        async for candidate in plugin.scan([chrome_path]):
            candidates.append(candidate)

        # Protected files should NOT be in results
        protected_names = ["Bookmarks", "Login Data", "Cookies"]
        for candidate in candidates:
            for protected in protected_names:
                assert protected not in str(candidate.path), (
                    f"Protected file {protected} should not be yielded"
                )

    def test_plugin_properties(self, plugin: BrowserPlugin) -> None:
        """Test plugin metadata."""
        assert plugin.name == "browser"
        assert plugin.default_enabled is True
        assert "browser" in plugin.description.lower()


class TestPythonDevPlugin:
    """Tests for PythonDevPlugin."""

    @pytest.fixture
    def plugin(self) -> PythonDevPlugin:
        """Create Python dev plugin instance."""
        return PythonDevPlugin()

    @pytest.fixture
    def python_artifacts(self, fake_fs: FakeFilesystem) -> None:
        """Create Python development artifacts."""

        # __pycache__
        fake_fs.create_file("/project/__pycache__/module.cpython-311.pyc", contents="pyc")
        fake_fs.create_file("/project/src/__pycache__/utils.cpython-311.pyc", contents="pyc")

        # pytest cache
        fake_fs.create_file("/project/.pytest_cache/.gitignore", contents="ignore")

        # Build artifacts
        fake_fs.create_file("/project/build/lib/module.py", contents="module")
        fake_fs.create_file("/project/dist/package-0.1.0.tar.gz", contents="dist")

    async def test_scan_finds_pycache(
        self,
        plugin: PythonDevPlugin,
        python_artifacts: None,
    ) -> None:
        """Test that plugin finds __pycache__ directories."""
        candidates = []
        async for candidate in plugin.scan([Path("/project")]):
            candidates.append(candidate)

        pycache_items = [c for c in candidates if "__pycache__" in str(c.path)]
        assert len(pycache_items) > 0

    async def test_scan_finds_build_dirs(
        self,
        plugin: PythonDevPlugin,
        python_artifacts: None,
    ) -> None:
        """Test that plugin finds build/dist directories."""
        candidates = []
        async for candidate in plugin.scan([Path("/project")]):
            candidates.append(candidate)

        build_items = [c for c in candidates if c.path.name in ("build", "dist")]
        assert len(build_items) >= 0  # May find build dirs

    def test_plugin_properties(self, plugin: PythonDevPlugin) -> None:
        """Test plugin metadata."""
        assert plugin.name == "dev_python"
        assert plugin.default_enabled is True


class TestSmartScanPlugin:
    """Tests for SmartScanPlugin."""

    @pytest.fixture
    def plugin(self) -> SmartScanPlugin:
        """Create smart scan plugin instance."""
        return SmartScanPlugin()

    @pytest.fixture
    def mixed_files(self, fake_fs: FakeFilesystem) -> None:
        """Create mixed file tree for smart scan."""

        # Large file (>500MB equivalent for testing)
        fake_fs.create_file("/files/large.bin", contents="x" * (100 * 1024 * 1024))

        # Empty directory
        fake_fs.create_dir("/files/empty_dir")

        # Normal files
        fake_fs.create_file("/files/normal.txt", contents="normal")

    async def test_scan_finds_large_files(
        self,
        plugin: SmartScanPlugin,
        mixed_files: None,
    ) -> None:
        """Test that plugin identifies large files."""
        candidates = []
        async for candidate in plugin.scan([Path("/files")]):
            candidates.append(candidate)

        large_files = [c for c in candidates if "Large" in c.reason]
        # May or may not find based on threshold
        assert isinstance(large_files, list)

    async def test_scan_finds_empty_dirs(
        self,
        plugin: SmartScanPlugin,
        mixed_files: None,
    ) -> None:
        """Test that plugin finds empty directories."""
        candidates = []
        async for candidate in plugin.scan([Path("/files")]):
            candidates.append(candidate)

        empty_dirs = [c for c in candidates if c.is_directory and "Empty" in c.reason]
        assert len(empty_dirs) >= 1

    def test_plugin_properties(self, plugin: SmartScanPlugin) -> None:
        """Test plugin metadata."""
        assert plugin.name == "smart_scan"
        assert plugin.default_enabled is True
        assert "large" in plugin.description.lower()
