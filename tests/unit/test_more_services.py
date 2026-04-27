# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for ScheduleService, PluginService, and CleaningService."""

from __future__ import annotations

from dmlclean.services.cleaning_service import CleaningService
from dmlclean.services.plugin_service import PluginService
from dmlclean.services.schedule_service import ScheduleService
from dmlclean.storage.database import Database

# ============== ScheduleService Tests ==============


class TestScheduleService:
    """Tests for ScheduleService"""

    def test_create_schedule(self, db: Database) -> None:
        """Test creating schedule."""
        service = ScheduleService(db)
        entry = service.create_schedule(
            name="Daily Cleanup",
            cron_expression="0 3 * * *",
            profile="developer",
        )
        assert entry.name == "Daily Cleanup"
        assert entry.cron_expression == "0 3 * * *"

    def test_get_schedule(self, db: Database) -> None:
        """Test getting schedule by ID."""
        service = ScheduleService(db)
        entry = service.create_schedule(name="Test", cron_expression="0 3 * * *")
        retrieved = service.get_schedule(entry.id)
        assert retrieved is not None
        assert retrieved.id == entry.id

    def test_list_schedules(self, db: Database) -> None:
        """Test listing schedules."""
        service = ScheduleService(db)
        service.create_schedule(name="Schedule1", cron_expression="0 3 * * *")
        service.create_schedule(name="Schedule2", cron_expression="0 4 * * *")
        entries = service.list_schedules()
        assert len(entries) == 2

    def test_enable_schedule(self, db: Database) -> None:
        """Test enabling schedule."""
        service = ScheduleService(db)
        entry = service.create_schedule(name="Test", cron_expression="0 3 * * *", enabled=False)
        result = service.enable_schedule(entry.id)
        assert result is True

    def test_disable_schedule(self, db: Database) -> None:
        """Test disabling schedule."""
        service = ScheduleService(db)
        entry = service.create_schedule(name="Test", cron_expression="0 3 * * *", enabled=True)
        result = service.disable_schedule(entry.id)
        assert result is True

    def test_remove_schedule(self, db: Database) -> None:
        """Test removing schedule."""
        service = ScheduleService(db)
        entry = service.create_schedule(name="Test", cron_expression="0 3 * * *")
        result = service.remove_schedule(entry.id)
        assert result is True

    def test_get_schedule_statistics(self, db: Database) -> None:
        """Test getting statistics."""
        service = ScheduleService(db)
        service.create_schedule(name="Schedule1", cron_expression="0 3 * * *")
        service.create_schedule(name="Schedule2", cron_expression="0 4 * * *", enabled=False)
        stats = service.get_schedule_statistics()
        assert stats["total"] == 2
        assert stats["enabled"] == 1
        assert stats["disabled"] == 1


# ============== PluginService Tests ==============


class TestPluginService:
    """Tests for PluginService"""

    def test_init(self) -> None:
        """Test PluginService initialization."""
        service = PluginService()
        assert service.plugins_dir.exists()

    def test_list_available_mocked(self, httpx_mock) -> None:
        """Test listing available plugins (mocked)."""
        from dmlclean.services.plugin_service import PluginService

        # Mock the HTTP response
        httpx_mock.add_response(
            url="https://raw.githubusercontent.com/dmlclean/plugin-registry/main/plugins.json",
            json={
                "plugins": [
                    {"name": "aws-cleanup", "version": "1.0.0", "description": "AWS cleanup"}
                ]
            },
        )

        service = PluginService()
        plugins = service.list_available(use_cache=False)

        assert isinstance(plugins, list)
        assert len(plugins) > 0

    def test_search_mocked(self, httpx_mock) -> None:
        """Test searching plugins (mocked)."""
        # Mock the HTTP response
        httpx_mock.add_response(
            url="https://raw.githubusercontent.com/dmlclean/plugin-registry/main/plugins.json",
            json={
                "plugins": [
                    {
                        "name": "aws-cleanup",
                        "version": "1.0.0",
                        "description": "AWS cleanup",
                        "author": "DML Labs",
                    }
                ]
            },
        )

        service = PluginService()
        results = service.search("aws")
        # May be empty, but shouldn't crash
        assert isinstance(results, list)

    def test_list_installed(self) -> None:
        """Test listing installed plugins."""
        service = PluginService()
        installed = service.list_installed()
        # Returns dict of installed plugins
        assert isinstance(installed, dict)

    def test_get_statistics_mocked(self, httpx_mock) -> None:
        """Test getting plugin statistics (mocked)."""
        # Mock the HTTP response
        httpx_mock.add_response(
            url="https://raw.githubusercontent.com/dmlclean/plugin-registry/main/plugins.json",
            json={"plugins": []},
        )

        service = PluginService()
        stats = service.get_statistics()
        assert "available" in stats
        assert "installed" in stats


# ============== CleaningService Tests ==============


class TestCleaningService:
    """Tests for CleaningService"""

    def test_init(self, db: Database) -> None:
        """Test CleaningService initialization."""
        service = CleaningService(db)
        assert service.db == db
        assert service.history_service is not None

    def test_execute_scan(self, db: Database, fs: FakeFilesystem) -> None:
        """Test executing scan."""
        # Create test files
        fs.create_dir("/tmp/test_scan")
        fs.create_file("/tmp/test_scan/file1.tmp", contents="test" * 100)
        fs.create_file("/tmp/test_scan/file2.log", contents="test" * 100)

        service = CleaningService(db)
        from pathlib import Path

        result = service.execute_scan(paths=[Path("/tmp/test_scan")], mode="fast")

        assert result["success"] is True
        assert result["paths_scanned"] == 1
        assert result["total_files"] >= 2

    def test_execute_clean_dry_run(self, db: Database, fs: FakeFilesystem) -> None:
        """Test executing clean in dry-run mode."""
        # Create test files
        fs.create_dir("/tmp/test_clean")
        fs.create_file("/tmp/test_clean/file1.tmp", contents="test" * 100)

        service = CleaningService(db)
        from pathlib import Path

        result = service.execute_clean(
            paths=[Path("/tmp/test_clean")],
            mode="dry-run",
            profile="developer",
        )

        assert result["success"] is True
        assert result["mode"] == "dry-run"

    def test_get_preview(self, db: Database, fs: FakeFilesystem) -> None:
        """Test getting preview."""
        # Create test files
        fs.create_dir("/tmp/test_preview")
        fs.create_file("/tmp/test_preview/file1.tmp", contents="test" * 100)

        service = CleaningService(db)
        from pathlib import Path

        preview = service.get_preview(paths=[Path("/tmp/test_preview")])

        assert "success" in preview or "total_files" in preview
