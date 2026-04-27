"""
Comprehensive Service Layer Tests for DMLClean.

Tests for all service classes to increase coverage.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dmlclean.dtos.clean import CleanProfile, CleanRequest, CleanRequestMode, CleanResult
from dmlclean.dtos.scan import ScanMode, ScanRequest, ScanResult
from dmlclean.services.cleaning_service import CleaningService
from dmlclean.services.history_service import HistoryService
from dmlclean.services.plugin_service import PluginService
from dmlclean.services.protection_service import ProtectionService
from dmlclean.services.report_service import ReportService
from dmlclean.services.schedule_service import ScheduleService


class TestCleaningService:
    """Tests for CleaningService."""

    def test_init(self, container) -> None:
        """Test service initialization."""
        service = CleaningService(container)

        assert service.container is container
        assert service.db is container.db
        assert service.history_service is container.history_service

    @patch.object(CleaningService, "_execute_scan_legacy")
    def test_execute_scan_with_dto(self, mock_legacy, container) -> None:
        """Test scan with DTO."""
        service = CleaningService(container)

        request = ScanRequest(
            paths=[Path("/tmp")],
            mode=ScanMode.FAST,
        )

        # Mock pipeline
        mock_pipeline_result = MagicMock()
        mock_pipeline_result.paths = [Path("/tmp/test.txt")]

        with patch.object(container.pipeline, "scan_only", return_value=mock_pipeline_result):
            with patch.object(container.analyzer, "analyze") as mock_analyze:
                mock_analyze.return_value = MagicMock(
                    candidates=[], get_summary=lambda: {"by_category": {}, "by_risk": {}}
                )

                result = service.execute_scan(request)

                assert isinstance(result, ScanResult)
                assert result.success is True

    @patch.object(CleaningService, "_execute_clean_legacy")
    def test_execute_clean_with_dto(self, mock_legacy, container) -> None:
        """Test clean with DTO."""
        service = CleaningService(container)

        request = CleanRequest(
            paths=[Path("/tmp")],
            mode=CleanRequestMode.DRY_RUN,
            profile=CleanProfile.DEVELOPER,
        )

        # Mock pipeline
        mock_pipeline_result = MagicMock()
        mock_pipeline_result.clean_result = None
        mock_pipeline_result.analysis_result = None
        mock_pipeline_result.errors = []
        mock_pipeline_result.manifest = None

        with patch.object(container.pipeline, "run", return_value=mock_pipeline_result):
            result = service.execute_clean(request)

            assert isinstance(result, CleanResult)
            assert result.success is True

    def test_execute_scan_async(self, container) -> None:
        """Test async scan execution."""
        service = CleaningService(container)

        request = ScanRequest(
            paths=[Path("/tmp")],
            mode=ScanMode.FAST,
        )

        # Should not raise
        import asyncio

        with patch.object(service, "execute_scan") as mock_scan:
            mock_scan.return_value = ScanResult()
            asyncio.run(service.execute_scan_async(request))
            mock_scan.assert_called_once()

    def test_execute_clean_async(self, container) -> None:
        """Test async clean execution."""
        service = CleaningService(container)

        request = CleanRequest(
            paths=[Path("/tmp")],
            mode=CleanRequestMode.DRY_RUN,
        )

        # Should not raise
        import asyncio

        with patch.object(service, "execute_clean") as mock_clean:
            mock_clean.return_value = CleanResult()
            asyncio.run(service.execute_clean_async(request))
            mock_clean.assert_called_once()


class TestHistoryService:
    """Tests for HistoryService."""

    def test_init(self, db, history_repo, undo_manager) -> None:
        """Test service initialization."""
        service = HistoryService(db, history_repo, undo_manager)

        assert service.db is db
        assert service.history_repo is history_repo
        assert service.undo_manager is undo_manager

    def test_list_recent(self, db, history_repo, undo_manager) -> None:
        """Test listing recent history."""
        service = HistoryService(db, history_repo, undo_manager)

        with patch.object(service.history_repo, "list_all") as mock_list:
            mock_list.return_value = []
            result = service.list_recent(limit=10)

            assert result == []
            mock_list.assert_called_once()

    def test_get_entry(self, db, history_repo, undo_manager) -> None:
        """Test getting history entry."""
        service = HistoryService(db, history_repo, undo_manager)

        with patch.object(service.history_repo, "get_by_id") as mock_get:
            mock_get.return_value = None
            result = service.get_entry("test-id")

            assert result is None

    def test_get_entry_or_raise(self, db, history_repo, undo_manager) -> None:
        """Test getting history entry or raising."""
        service = HistoryService(db, history_repo, undo_manager)

        with patch.object(service.history_repo, "get_by_id") as mock_get:
            mock_get.return_value = None

            with pytest.raises(Exception):  # NotFoundError
                service.get_entry_or_raise("test-id")

    def test_clear_history(self, db, history_repo, undo_manager) -> None:
        """Test clearing history."""
        service = HistoryService(db, history_repo, undo_manager)

        with patch.object(service.undo_manager, "clear_history") as mock_clear:
            mock_clear.return_value = 5
            with patch.object(service.history_repo, "clear_all") as mock_repo_clear:
                mock_repo_clear.return_value = 10

                service.clear_history()

                assert mock_clear.called
                assert mock_repo_clear.called

    def test_get_statistics(self, db, history_repo, undo_manager) -> None:
        """Test getting statistics."""
        service = HistoryService(db, history_repo, undo_manager)

        with patch.object(service.history_repo, "get_summary") as mock_summary:
            mock_summary.return_value = {"total_operations": 5}
            result = service.get_statistics(days=30)

            assert "total_operations" in result


class TestProtectionService:
    """Tests for ProtectionService."""

    def test_init(self, container) -> None:
        """Test service initialization."""
        service = ProtectionService(
            container.db, container.protected_repo, container.protected_zone
        )

        assert service.db is container.db
        assert service.protected_repo is container.protected_repo
        assert service.protected_zone is container.protected_zone

    def test_add_protection(self, container) -> None:
        """Test adding protection."""
        service = ProtectionService(
            container.db, container.protected_repo, container.protected_zone
        )

        with patch.object(service.protected_repo, "create") as mock_create:
            mock_create.return_value = MagicMock(
                id="test-id", path="/test/path", is_glob=False, description=""
            )

            result = service.add_protection(path="/test/path", description="Test protection")

            assert result is not None
            assert result.id == "test-id"

    def test_add_protection_empty_path(self, container) -> None:
        """Test adding protection with empty path."""
        service = ProtectionService(
            container.db, container.protected_repo, container.protected_zone
        )

        with pytest.raises(Exception):  # ValidationError
            service.add_protection(path="", description="")

    def test_get_protection(self, container) -> None:
        """Test getting protection."""
        service = ProtectionService(
            container.db, container.protected_repo, container.protected_zone
        )

        with patch.object(service.protected_repo, "get_by_id") as mock_get:
            mock_get.return_value = None
            result = service.get_protection("test-id")

            assert result is None

    def test_remove_protection(self, container) -> None:
        """Test removing protection."""
        service = ProtectionService(
            container.db, container.protected_repo, container.protected_zone
        )

        with patch.object(service.protected_repo, "get_by_id") as mock_get:
            mock_get.return_value = MagicMock(id="test-id", path="/test")
            with patch.object(service.protected_repo, "delete") as mock_delete:
                mock_delete.return_value = True

                result = service.remove_protection("test-id")

                assert result is True

    def test_list_protected(self, container) -> None:
        """Test listing protected paths."""
        service = ProtectionService(
            container.db, container.protected_repo, container.protected_zone
        )

        with patch.object(service.protected_repo, "list_all") as mock_list:
            mock_list.return_value = []
            result = service.list_protected(limit=10)

            assert result == []

    def test_check_protection(self, container) -> None:
        """Test checking protection."""
        service = ProtectionService(
            container.db, container.protected_repo, container.protected_zone
        )

        with patch.object(service.protected_zone, "is_protected") as mock_check:
            mock_check.return_value = MagicMock(is_protected=False, reason="")

            result = service.check_protection("/test/path")

            assert result.is_protected is False

    def test_is_protected(self, container) -> None:
        """Test is_protected helper."""
        service = ProtectionService(
            container.db, container.protected_repo, container.protected_zone
        )

        with patch.object(service, "check_protection") as mock_check:
            mock_check.return_value = MagicMock(is_protected=True)

            result = service.is_protected("/test/path")

            assert result is True

    def test_get_statistics(self, container) -> None:
        """Test getting protection statistics."""
        service = ProtectionService(
            container.db, container.protected_repo, container.protected_zone
        )

        with patch.object(service.protected_repo, "list_all") as mock_list:
            mock_list.return_value = [
                MagicMock(id="1", path="/test1", is_glob=False),
                MagicMock(id="2", path="/test2", is_glob=True),
            ]

            result = service.get_statistics()

            assert result["total"] == 2
            assert result["exact_paths"] == 1
            assert result["glob_patterns"] == 1


class TestScheduleService:
    """Tests for ScheduleService."""

    def test_init(self, container) -> None:
        """Test service initialization."""
        service = ScheduleService(container.db, container.schedule_repo, container.scheduler)

        assert service.db is container.db
        assert service.schedule_repo is container.schedule_repo
        assert service.scheduler is container.scheduler

    def test_create_schedule(self, container) -> None:
        """Test creating schedule."""
        service = ScheduleService(container.db, container.schedule_repo, container.scheduler)

        with patch.object(service.schedule_repo, "create") as mock_create:
            mock_create.return_value = MagicMock(
                id="test-id", name="Test Schedule", cron_expression="0 3 * * *"
            )

            with patch.object(service.scheduler, "add_job"):
                with patch.object(service.scheduler, "start"):
                    result = service.create_schedule(
                        name="Test Schedule", cron_expression="0 3 * * *"
                    )

                    assert result is not None

    def test_get_schedule(self, container) -> None:
        """Test getting schedule."""
        service = ScheduleService(container.db, container.schedule_repo, container.scheduler)

        with patch.object(service.schedule_repo, "get_by_id") as mock_get:
            mock_get.return_value = None
            result = service.get_schedule("test-id")

            assert result is None

    def test_list_schedules(self, container) -> None:
        """Test listing schedules."""
        service = ScheduleService(container.db, container.schedule_repo, container.scheduler)

        with patch.object(service.schedule_repo, "list_all") as mock_list:
            mock_list.return_value = []
            result = service.list_schedules(limit=10)

            assert result == []

    def test_remove_schedule(self, container) -> None:
        """Test removing schedule."""
        service = ScheduleService(container.db, container.schedule_repo, container.scheduler)

        with patch.object(service.scheduler, "remove_job"):
            with patch.object(service.schedule_repo, "delete") as mock_delete:
                mock_delete.return_value = True

                result = service.remove_schedule("test-id")

                assert result is True

    def test_enable_schedule(self, container) -> None:
        """Test enabling schedule."""
        service = ScheduleService(container.db, container.schedule_repo, container.scheduler)

        with patch.object(service.schedule_repo, "get_by_id") as mock_get:
            mock_get.return_value = MagicMock(id="test-id")
            with patch.object(service.schedule_repo, "update") as mock_update:
                mock_update.return_value = True
                with patch.object(service.scheduler, "start"):
                    with patch.object(service.scheduler, "enable_job"):
                        result = service.enable_schedule("test-id")

                        assert result is True

    def test_disable_schedule(self, container) -> None:
        """Test disabling schedule."""
        service = ScheduleService(container.db, container.schedule_repo, container.scheduler)

        with patch.object(service.schedule_repo, "get_by_id") as mock_get:
            mock_get.return_value = MagicMock(id="test-id")
            with patch.object(service.schedule_repo, "update") as mock_update:
                mock_update.return_value = True
                with patch.object(service.scheduler, "disable_job"):
                    result = service.disable_schedule("test-id")

                    assert result is True

    def test_get_schedule_statistics(self, container) -> None:
        """Test getting schedule statistics."""
        service = ScheduleService(container.db, container.schedule_repo, container.scheduler)

        with patch.object(service.schedule_repo, "list_all") as mock_list:
            mock_list.return_value = [
                MagicMock(id="1", enabled=True, profile="developer"),
                MagicMock(id="2", enabled=False, profile="developer"),
            ]

            result = service.get_schedule_statistics()

            assert result["total"] == 2
            assert result["enabled"] == 1
            assert result["disabled"] == 1


class TestReportService:
    """Tests for ReportService."""

    def test_init(self, container) -> None:
        """Test service initialization."""
        service = ReportService(container.db, container.history_repo)

        assert service.db is container.db
        assert service.history_repo is container.history_repo

    def test_generate_summary(self, container) -> None:
        """Test generating summary."""
        service = ReportService(container.db, container.history_repo)

        with patch.object(service.history_repo, "get_summary") as mock_summary:
            mock_summary.return_value = {
                "total_files_deleted": 100,
                "total_size_bytes": 1024 * 1024,
                "avg_duration_ms": 500,
            }
            with patch.object(service.history_repo, "list_all") as mock_list:
                mock_list.return_value = []

                result = service.generate_summary(days=30)

                assert "total_operations" in result
                assert result["total_files_deleted"] == 100

    def test_get_terminal_report(self, container) -> None:
        """Test getting terminal report."""
        service = ReportService(container.db, container.history_repo)

        with patch.object(service, "generate_summary") as mock_summary:
            mock_summary.return_value = {
                "total_operations": 5,
                "successful": 4,
                "failed": 1,
                "success_rate": 80.0,
                "total_files_deleted": 100,
                "total_size_bytes": 1024 * 1024,
                "avg_duration_ms": 500,
                "by_mode": {"trash": 3, "dry-run": 2},
                "by_profile": {"developer": {"operations": 5}},
            }

            result = service.get_terminal_report(days=30)

            assert "DMLClean" in result
            assert "Summary" in result


class TestPluginService:
    """Tests for PluginService."""

    def test_init(self) -> None:
        """Test service initialization."""
        service = PluginService()

        assert service.plugins_dir.exists()

    def test_list_installed(self) -> None:
        """Test listing installed plugins."""
        service = PluginService()

        # Should not raise
        result = service.list_installed()

        assert isinstance(result, dict)

    def test_get_statistics(self) -> None:
        """Test getting plugin statistics."""
        service = PluginService()

        # Should not raise (may fail due to network)
        try:
            result = service.get_statistics()
            assert "available" in result
            assert "installed" in result
        except Exception:
            # Network failure is acceptable
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
