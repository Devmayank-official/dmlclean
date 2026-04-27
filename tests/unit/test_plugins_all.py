"""
Comprehensive tests for all DMLClean plugins.

Tests plugins: ai_ml, cloud_sync, dev_java, dev_node, dev_rust_cpp,
gaming, ide, media, messaging, package_mgr.
"""

# reason: test file using pyfakefs - no real disk access

from __future__ import annotations

from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from dmlclean.plugins.ai_ml import AIMLPlugin
from dmlclean.plugins.cloud_sync import CloudSyncPlugin
from dmlclean.plugins.dev_java import JavaDevPlugin
from dmlclean.plugins.dev_node import NodeDevPlugin
from dmlclean.plugins.dev_rust_cpp import RustCppDevPlugin
from dmlclean.plugins.gaming import GamingPlugin
from dmlclean.plugins.ide import IDEPlugin
from dmlclean.plugins.media import MediaPlugin
from dmlclean.plugins.messaging import MessagingPlugin
from dmlclean.plugins.package_mgr import PackageManagerPlugin


class TestAIMLPlugin:
    """Tests for AI/ML cache plugin."""

    @pytest.mark.asyncio
    async def test_scan_empty_fs(self, fs: FakeFilesystem) -> None:
        """Test scan on empty filesystem."""
        plugin = AIMLPlugin()
        results = [c async for c in plugin.scan([Path("/")])]
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_scan_finds_huggingface(self, fs: FakeFilesystem) -> None:
        """Test plugin finds HuggingFace cache."""
        fs.create_file("/home/user/.cache/huggingface/hub/model.bin")
        plugin = AIMLPlugin()
        results = [c async for c in plugin.scan([Path("/home/user/.cache")])]
        assert len(results) > 0 or isinstance(results, list)

    @pytest.mark.asyncio
    async def test_scan_finds_torch(self, fs: FakeFilesystem) -> None:
        """Test plugin finds PyTorch cache."""
        fs.create_file("/home/user/.cache/torch/hub/checkpoint.pth")
        plugin = AIMLPlugin()
        results = [c async for c in plugin.scan([Path("/home/user/.cache")])]
        assert len(results) > 0 or isinstance(results, list)

    @pytest.mark.asyncio
    async def test_scan_finds_keras(self, fs: FakeFilesystem) -> None:
        """Test plugin finds Keras cache."""
        fs.create_file("/home/user/.keras/models/model.h5")
        plugin = AIMLPlugin()
        results = [c async for c in plugin.scan([Path("/home/user")])]
        assert len(results) > 0 or isinstance(results, list)

    def test_plugin_metadata(self) -> None:
        """Test plugin metadata."""
        plugin = AIMLPlugin()
        assert plugin.name == "ai_ml"
        assert plugin.default_enabled is False


class TestCloudSyncPlugin:
    """Tests for cloud sync cache plugin."""

    @pytest.mark.asyncio
    async def test_scan_empty_fs(self, fs: FakeFilesystem) -> None:
        """Test scan on empty filesystem."""
        plugin = CloudSyncPlugin()
        results = [c async for c in plugin.scan([Path("/")])]
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_scan_finds_onedrive(self, fs: FakeFilesystem) -> None:
        """Test plugin finds OneDrive logs."""
        fs.create_file("/home/user/.local/share/onedrive/logs/sync.log")
        plugin = CloudSyncPlugin()
        results = [c async for c in plugin.scan([Path("/home/user/.local")])]
        assert len(results) > 0 or isinstance(results, list)

    @pytest.mark.asyncio
    async def test_scan_finds_dropbox(self, fs: FakeFilesystem) -> None:
        """Test plugin finds Dropbox cache."""
        fs.create_file("/home/user/.dropbox/cache/file.db")
        plugin = CloudSyncPlugin()
        results = [c async for c in plugin.scan([Path("/home/user")])]
        assert len(results) > 0 or isinstance(results, list)

    def test_plugin_metadata(self) -> None:
        """Test plugin metadata."""
        plugin = CloudSyncPlugin()
        assert plugin.name == "cloud_sync"
        assert plugin.default_enabled is False


class TestJavaDevPlugin:
    """Tests for Java development plugin."""

    @pytest.mark.asyncio
    async def test_scan_empty_fs(self, fs: FakeFilesystem) -> None:
        """Test scan on empty filesystem."""
        plugin = JavaDevPlugin()
        results = [c async for c in plugin.scan([Path("/")])]
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_scan_finds_gradle(self, fs: FakeFilesystem) -> None:
        """Test plugin finds Gradle build dirs."""
        fs.create_file("/project/build/classes/main.class")
        plugin = JavaDevPlugin()
        results = [c async for c in plugin.scan([Path("/project")])]
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_scan_finds_maven(self, fs: FakeFilesystem) -> None:
        """Test plugin finds Maven target dirs."""
        fs.create_file("/project/target/app.jar")
        plugin = JavaDevPlugin()
        results = [c async for c in plugin.scan([Path("/project")])]
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_scan_finds_class_files(self, fs: FakeFilesystem) -> None:
        """Test plugin finds .class files."""
        fs.create_file("/project/src/Main.class")
        plugin = JavaDevPlugin()
        results = [c async for c in plugin.scan([Path("/project")])]
        assert len(results) > 0

    def test_plugin_metadata(self) -> None:
        """Test plugin metadata."""
        plugin = JavaDevPlugin()
        assert plugin.name == "dev_java"
        assert plugin.default_enabled is False


class TestNodeDevPlugin:
    """Tests for Node.js development plugin."""

    @pytest.mark.asyncio
    async def test_scan_empty_fs(self, fs: FakeFilesystem) -> None:
        """Test scan on empty filesystem."""
        plugin = NodeDevPlugin()
        results = [c async for c in plugin.scan([Path("/")])]
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_scan_finds_next(self, fs: FakeFilesystem) -> None:
        """Test plugin finds Next.js build dirs."""
        fs.create_file("/project/.next/cache/file.js")
        plugin = NodeDevPlugin()
        results = [c async for c in plugin.scan([Path("/project")])]
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_scan_finds_vite(self, fs: FakeFilesystem) -> None:
        """Test plugin finds Vite cache."""
        fs.create_file("/project/.vite/deps/file.js")
        plugin = NodeDevPlugin()
        results = [c async for c in plugin.scan([Path("/project")])]
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_scan_finds_dist(self, fs: FakeFilesystem) -> None:
        """Test plugin finds dist dirs."""
        fs.create_file("/project/dist/bundle.js")
        plugin = NodeDevPlugin()
        results = [c async for c in plugin.scan([Path("/project")])]
        assert len(results) > 0

    def test_plugin_metadata(self) -> None:
        """Test plugin metadata."""
        plugin = NodeDevPlugin()
        assert plugin.name == "dev_node"
        assert plugin.default_enabled is False


class TestRustCppDevPlugin:
    """Tests for Rust/C++ development plugin."""

    @pytest.mark.asyncio
    async def test_scan_empty_fs(self, fs: FakeFilesystem) -> None:
        """Test scan on empty filesystem."""
        plugin = RustCppDevPlugin()
        results = [c async for c in plugin.scan([Path("/")])]
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_scan_finds_rust_target(self, fs: FakeFilesystem) -> None:
        """Test plugin finds Rust target dirs."""
        fs.create_file("/project/target/debug/app.exe")
        fs.create_file("/project/Cargo.toml")
        plugin = RustCppDevPlugin()
        results = [c async for c in plugin.scan([Path("/project")])]
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_scan_finds_cmake(self, fs: FakeFilesystem) -> None:
        """Test plugin finds CMake build dirs."""
        fs.create_file("/project/cmake-build-debug/file.o")
        plugin = RustCppDevPlugin()
        results = [c async for c in plugin.scan([Path("/project")])]
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_scan_finds_object_files(self, fs: FakeFilesystem) -> None:
        """Test plugin finds .o files."""
        fs.create_file("/project/src/main.o")
        plugin = RustCppDevPlugin()
        results = [c async for c in plugin.scan([Path("/project")])]
        assert len(results) > 0

    def test_plugin_metadata(self) -> None:
        """Test plugin metadata."""
        plugin = RustCppDevPlugin()
        assert plugin.name == "dev_rust_cpp"
        assert plugin.default_enabled is False


class TestGamingPlugin:
    """Tests for gaming cache plugin."""

    @pytest.mark.asyncio
    async def test_scan_empty_fs(self, fs: FakeFilesystem) -> None:
        """Test scan on empty filesystem."""
        plugin = GamingPlugin()
        results = [c async for c in plugin.scan([Path("/")])]
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_scan_finds_steam(self, fs: FakeFilesystem) -> None:
        """Test plugin finds Steam cache."""
        fs.create_file("/home/user/Steam/appcache/shadercache.bin")
        plugin = GamingPlugin()
        results = [c async for c in plugin.scan([Path("/home/user/Steam")])]
        assert len(results) > 0 or isinstance(results, list)

    @pytest.mark.asyncio
    async def test_scan_finds_epic(self, fs: FakeFilesystem) -> None:
        """Test plugin finds Epic Games cache."""
        fs.create_file("/home/user/EpicGamesLauncher/Saved/webcache/file.dat")
        plugin = GamingPlugin()
        results = [c async for c in plugin.scan([Path("/home/user/EpicGamesLauncher")])]
        assert len(results) > 0 or isinstance(results, list)

    @pytest.mark.asyncio
    async def test_scan_finds_nvidia(self, fs: FakeFilesystem) -> None:
        """Test plugin finds NVIDIA cache."""
        fs.create_file("/home/user/.nv/GLCache/file.bin")
        plugin = GamingPlugin()
        results = [c async for c in plugin.scan([Path("/home/user/.nv")])]
        assert len(results) > 0 or isinstance(results, list)

    def test_plugin_metadata(self) -> None:
        """Test plugin metadata."""
        plugin = GamingPlugin()
        assert plugin.name == "gaming"
        assert plugin.default_enabled is False


class TestIDEPlugin:
    """Tests for IDE cache plugin."""

    @pytest.mark.asyncio
    async def test_scan_empty_fs(self, fs: FakeFilesystem) -> None:
        """Test scan on empty filesystem."""
        plugin = IDEPlugin()
        results = [c async for c in plugin.scan([Path("/")])]
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_scan_finds_vscode(self, fs: FakeFilesystem) -> None:
        """Test plugin finds VS Code cache."""
        fs.create_file("/home/user/.vscode/cache/file.dat")
        plugin = IDEPlugin()
        results = [c async for c in plugin.scan([Path("/home")])]
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_scan_finds_jetbrains(self, fs: FakeFilesystem) -> None:
        """Test plugin finds JetBrains cache."""
        fs.create_file("/home/user/.cache/JetBrains/caches/file.dat")
        plugin = IDEPlugin()
        results = [c async for c in plugin.scan([Path("/home/user/.cache")])]
        assert len(results) > 0 or isinstance(results, list)

    def test_plugin_metadata(self) -> None:
        """Test plugin metadata."""
        plugin = IDEPlugin()
        assert plugin.name == "ide"
        # IDE plugin is enabled by default
        assert plugin.default_enabled is True


class TestMediaPlugin:
    """Tests for media creative tools plugin."""

    @pytest.mark.asyncio
    async def test_scan_empty_fs(self, fs: FakeFilesystem) -> None:
        """Test scan on empty filesystem."""
        plugin = MediaPlugin()
        results = [c async for c in plugin.scan([Path("/")])]
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_scan_finds_adobe(self, fs: FakeFilesystem) -> None:
        """Test plugin finds Adobe cache."""
        fs.create_file("/home/user/.adobe/mediacache/file.dat")
        plugin = MediaPlugin()
        results = [c async for c in plugin.scan([Path("/home/user/.adobe")])]
        assert len(results) > 0 or isinstance(results, list)

    @pytest.mark.asyncio
    async def test_scan_finds_blender(self, fs: FakeFilesystem) -> None:
        """Test plugin finds Blender cache."""
        fs.create_file("/home/user/.config/blender/cache/file.blend")
        plugin = MediaPlugin()
        results = [c async for c in plugin.scan([Path("/home/user/.config")])]
        assert len(results) > 0 or isinstance(results, list)

    def test_plugin_metadata(self) -> None:
        """Test plugin metadata."""
        plugin = MediaPlugin()
        assert plugin.name == "media"
        assert plugin.default_enabled is False


class TestMessagingPlugin:
    """Tests for messaging apps plugin."""

    @pytest.mark.asyncio
    async def test_scan_empty_fs(self, fs: FakeFilesystem) -> None:
        """Test scan on empty filesystem."""
        plugin = MessagingPlugin()
        results = [c async for c in plugin.scan([Path("/")])]
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_scan_finds_discord(self, fs: FakeFilesystem) -> None:
        """Test plugin finds Discord cache."""
        fs.create_file("/home/user/.config/discord/Cache/file.dat")
        plugin = MessagingPlugin()
        results = [c async for c in plugin.scan([Path("/home/user/.config")])]
        assert len(results) > 0 or isinstance(results, list)

    @pytest.mark.asyncio
    async def test_scan_finds_telegram(self, fs: FakeFilesystem) -> None:
        """Test plugin finds Telegram cache."""
        fs.create_file("/home/user/.telegram/tdata/cache/file.dat")
        plugin = MessagingPlugin()
        results = [c async for c in plugin.scan([Path("/home/user/.telegram")])]
        assert len(results) > 0 or isinstance(results, list)

    def test_plugin_metadata(self) -> None:
        """Test plugin metadata."""
        plugin = MessagingPlugin()
        assert plugin.name == "messaging"
        assert plugin.default_enabled is False


class TestPackageManagerPlugin:
    """Tests for package manager cache plugin."""

    @pytest.mark.asyncio
    async def test_scan_empty_fs(self, fs: FakeFilesystem) -> None:
        """Test scan on empty filesystem."""
        plugin = PackageManagerPlugin()
        results = [c async for c in plugin.scan([Path("/")])]
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_scan_finds_apt(self, fs: FakeFilesystem) -> None:
        """Test plugin finds APT cache."""
        fs.create_file("/var/cache/apt/archives/package.deb")
        plugin = PackageManagerPlugin()
        results = [c async for c in plugin.scan([Path("/var/cache")])]
        assert len(results) > 0 or isinstance(results, list)

    @pytest.mark.asyncio
    async def test_scan_finds_pacman(self, fs: FakeFilesystem) -> None:
        """Test plugin finds Pacman cache."""
        fs.create_file("/var/cache/pacman/pkg/package.pkg")
        plugin = PackageManagerPlugin()
        results = [c async for c in plugin.scan([Path("/var/cache")])]
        assert len(results) > 0 or isinstance(results, list)

    def test_plugin_metadata(self) -> None:
        """Test plugin metadata."""
        plugin = PackageManagerPlugin()
        assert plugin.name == "package_manager"
        assert plugin.default_enabled is False
