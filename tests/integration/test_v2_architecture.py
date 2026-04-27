"""
Integration Tests for DMLClean v2 Architecture.

End-to-end tests for:
- Scan → Clean workflow
- Plugin integration
- Event-driven notifications
- CLI → Service integration
- State persistence

Run with:
    pytest tests/integration/test_v2_architecture.py -v
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dmlclean.cli.context import CLIContext
from dmlclean.container import Container
from dmlclean.dtos.clean import CleanProfile, CleanRequest, CleanRequestMode
from dmlclean.dtos.scan import ScanMode, ScanRequest


class TestV2Architecture:
    """Test v2 architecture components."""

    @pytest.fixture
    def container(self) -> Container:
        """Create test container."""
        return Container.create()

    @pytest.fixture
    def test_paths(self, tmp_path: Path) -> list[Path]:
        """Create test directory structure."""
        # Create test files
        test_dir = tmp_path / "test_scan"
        test_dir.mkdir()

        # Create temp files
        (test_dir / "temp1.tmp").write_text("test content" * 100)
        (test_dir / "temp2.tmp").write_text("test content" * 200)
        (test_dir / "cache.dat").write_text("cache data" * 50)

        # Create subdirectory with files
        cache_dir = test_dir / "cache"
        cache_dir.mkdir()
        (cache_dir / "file1.cache").write_text("cache" * 100)

        return [test_dir]

    def test_container_creation(self, container: Container) -> None:
        """Test container creates all dependencies."""
        assert container.db is not None
        assert container.config is not None
        assert container.scanner is not None
        assert container.plugin_scanner is not None
        assert container.cleaning_service is not None
        assert container.history_service is not None
        assert container.protected_zone is not None

    def test_scan_with_dto(self, container: Container, test_paths: list[Path]) -> None:
        """Test scan using DTOs."""
        service = container.cleaning_service

        # Create request DTO
        request = ScanRequest(
            paths=test_paths,
            mode=ScanMode.FAST,
        )

        # Execute scan
        result = service.execute_scan(request)

        # Assert result
        assert result.success is True
        assert result.total_files > 0
        assert result.total_size_bytes > 0
        assert result.candidates >= 0

    def test_clean_with_dto(self, container: Container, test_paths: list[Path]) -> None:
        """Test clean using DTOs."""
        service = container.cleaning_service

        # Create request DTO (dry-run for safety)
        request = CleanRequest(
            paths=test_paths,
            mode=CleanRequestMode.DRY_RUN,
            profile=CleanProfile.DEVELOPER,
        )

        # Execute clean
        result = service.execute_clean(request)

        # Assert result
        assert result.success is True
        assert result.operation_id != ""
        assert result.mode == "dry-run"
        # In dry-run, files_deleted should be 0
        assert result.files_deleted == 0

    def test_scan_clean_workflow(
        self,
        container: Container,
        test_paths: list[Path],
    ) -> None:
        """Test complete scan → clean workflow."""
        service = container.cleaning_service

        # Step 1: Scan
        scan_request = ScanRequest(
            paths=test_paths,
            mode=ScanMode.FAST,
        )
        scan_result = service.execute_scan(scan_request)

        assert scan_result.success is True

        # Step 2: Clean (dry-run)
        clean_request = CleanRequest(
            paths=test_paths,
            mode=CleanRequestMode.DRY_RUN,
            profile=CleanProfile.DEVELOPER,
        )
        clean_result = service.execute_clean(clean_request)

        assert clean_result.success is True

        # Verify workflow consistency
        assert clean_result.files_deleted == 0  # Dry-run

    def test_context_state_persistence(
        self,
        tmp_path: Path,
        test_paths: list[Path],
    ) -> None:
        """Test CLI context state persistence."""
        # Create context with temp directory
        context = CLIContext(state_dir=tmp_path)

        # Create mock scan result
        mock_result = {
            "mode": "fast",
            "paths": [str(p) for p in test_paths],
            "total_files": 10,
            "total_size_bytes": 1024 * 1024,
            "candidates": 5,
            "by_category": {"system_junk": {"count": 3, "size_bytes": 512}},
            "by_risk": {"low": {"count": 5, "size_bytes": 1024}},
        }

        # Save scan result
        context.save_scan_result(mock_result)

        # Retrieve scan result
        saved_state = context.get_last_scan_result()

        assert saved_state is not None
        assert saved_state.total_files == 10
        assert saved_state.total_size_bytes == 1024 * 1024
        assert saved_state.candidates == 5

    def test_context_clear_state(self, tmp_path: Path) -> None:
        """Test clearing context state."""
        context = CLIContext(state_dir=tmp_path)

        # Save mock result
        context.save_scan_result(
            {
                "mode": "fast",
                "paths": ["/tmp"],
                "total_files": 10,
                "total_size_bytes": 1024,
                "candidates": 5,
            }
        )

        # Clear state
        context.clear_scan_result()

        # Verify cleared
        saved_state = context.get_last_scan_result()
        assert saved_state is None

    def test_plugin_scanner_creation(self, container: Container) -> None:
        """Test plugin scanner is created."""
        plugin_scanner = container.plugin_scanner

        assert plugin_scanner is not None
        assert plugin_scanner.config is not None
        assert plugin_scanner.config.use_plugins is True
        assert plugin_scanner.config.parallel_execution is True

    def test_event_bus_integration(self, container: Container) -> None:
        """Test event bus publishes events."""
        from dmlclean.domain.events import CleanOperationCompleted, EventBus

        events_published = []

        # Subscribe to event
        @EventBus.subscribe(CleanOperationCompleted)
        def capture_event(event: CleanOperationCompleted) -> None:
            events_published.append(event)

        # Execute clean (triggers event)
        service = container.cleaning_service
        request = CleanRequest(
            paths=[Path("/tmp")],
            mode=CleanRequestMode.DRY_RUN,
            profile=CleanProfile.DEVELOPER,
        )

        # Should not raise
        service.execute_clean(request)

        # Verify event was published
        assert len(events_published) == 1
        assert events_published[0].mode == "dry-run"

    def test_formatter_factory(self) -> None:
        """Test formatter factory creates correct formatters."""
        from dmlclean.cli.formatters.factory import (
            get_formatter,
        )

        # Test JSON formatter
        json_formatter = get_formatter("json")
        assert json_formatter.get_format_name() == "json"

        # Test table formatter
        table_formatter = get_formatter("table")
        assert table_formatter.get_format_name() == "table"

        # Test plain formatter
        plain_formatter = get_formatter("plain")
        assert plain_formatter.get_format_name() == "plain"

        # Test from flags
        json_from_flag = get_formatter(json_output=True)
        assert json_from_flag.get_format_name() == "json"

    def test_notification_manager(self) -> None:
        """Test notification manager."""
        from dmlclean.notifications import NotificationManager

        manager = NotificationManager(enabled=False)  # Disabled for tests

        # Should not raise
        backend_info = manager.get_backend_info()

        assert "backend" in backend_info
        assert "available" in backend_info
        assert "enabled" in backend_info

    def test_dto_serialization(self) -> None:
        """Test DTO serialization."""
        from dmlclean.dtos.clean import CleanRequest, CleanRequestMode
        from dmlclean.dtos.scan import ScanMode, ScanRequest

        # Scan request
        scan_req = ScanRequest(
            paths=[Path("/tmp")],
            mode=ScanMode.DEEP,
            categories=["browser"],
        )
        scan_dict = scan_req.to_dict()

        assert scan_dict["mode"] == "deep"
        assert scan_dict["categories"] == ["browser"]

        # Clean request
        clean_req = CleanRequest(
            paths=[Path("/tmp")],
            mode=CleanRequestMode.TRASH,
            profile=CleanProfile.DEVELOPER,
        )
        clean_dict = clean_req.to_dict()

        assert clean_dict["mode"] == "trash"
        assert clean_dict["profile"] == "developer"


class TestBackwardCompatibility:
    """Test backward compatibility with legacy APIs."""

    @pytest.fixture
    def container(self) -> Container:
        """Create test container."""
        return Container.create()

    def test_legacy_scan_api(self, container: Container, tmp_path: Path) -> None:
        """Test legacy scan API still works."""
        service = container.cleaning_service

        # Create test file
        test_file = tmp_path / "test.tmp"
        test_file.write_text("test")

        # Call with legacy API (paths as list)
        result = service._execute_scan_legacy(
            paths=[tmp_path],
            mode="fast",
        )

        assert isinstance(result, dict)
        assert "success" in result
        assert result["success"] is True

    def test_legacy_clean_api(self, container: Container, tmp_path: Path) -> None:
        """Test legacy clean API still works."""
        service = container.cleaning_service

        # Create test file
        test_file = tmp_path / "test.tmp"
        test_file.write_text("test")

        # Call with legacy API
        result = service._execute_clean_legacy(
            paths=[tmp_path],
            mode="dry-run",
            profile="developer",
        )

        assert isinstance(result, dict)
        assert "success" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
