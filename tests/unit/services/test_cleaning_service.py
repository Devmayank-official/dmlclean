# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Tests for cleaning service.

Comprehensive test coverage for CleaningService.
"""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from dmlclean.dtos.clean import CleanProfile, CleanRequest, CleanRequestMode
from dmlclean.dtos.scan import ScanMode, ScanRequest
from dmlclean.services.cleaning_service import CleaningService


class TestCleaningService:
    """Test cleaning service."""

    def test_init(self, container) -> None:
        """Test service initialization."""
        service = CleaningService(container)
        assert service.container == container
        assert service.db == container.db
        assert service.history_service == container.history_service

    @pytest.mark.asyncio
    async def test_execute_scan_async(self, container, mocker) -> None:
        """Test async scan execution."""
        service = CleaningService(container)

        # Mock pipeline scan
        mock_scan_result = mocker.Mock()
        mock_scan_result.stats.total_files = 100
        mock_scan_result.stats.total_directories = 10
        mock_scan_result.stats.total_size_bytes = 1024000
        mock_scan_result.stats.errors = 0
        mock_scan_result.stats.duration_seconds = 1.5
        mock_scan_result.stats.files_per_second = 66.67
        mock_scan_result.paths = [Path("/tmp")]

        mock_pipeline = mocker.Mock()
        mock_pipeline.scan_only = AsyncMock(return_value=mock_scan_result)
        container.pipeline = mock_pipeline

        # Mock analyzer
        mock_analyzer = mocker.Mock()
        mock_analysis = mocker.Mock()
        mock_analysis.candidates = []
        mock_analysis.get_summary.return_value = {"by_category": {}, "by_risk": {}}
        mock_analyzer.analyze.return_value = mock_analysis
        container.analyzer = mock_analyzer

        request = ScanRequest(paths=[Path("/tmp")], mode=ScanMode.FAST)
        result = await service.execute_scan_async(request)

        assert result.success is True
        assert result.total_files == 100
        assert result.candidates == 0

    @pytest.mark.asyncio
    async def test_execute_clean_async(self, container, mocker) -> None:
        """Test async clean execution."""
        service = CleaningService(container)

        # Mock pipeline run
        mock_clean_result = mocker.Mock()
        mock_clean_result.stats.deleted = 50
        mock_clean_result.stats.failed = 0
        mock_clean_result.stats.skipped = 10
        mock_clean_result.stats.total_size_bytes = 512000

        mock_manifest = mocker.Mock()
        mock_manifest.id = "test-manifest-id"

        mock_pipeline_result = mocker.Mock()
        mock_pipeline_result.clean_result = mock_clean_result
        mock_pipeline_result.manifest = mock_manifest
        mock_pipeline_result.errors = []
        mock_pipeline_result.analysis_result = None

        mock_pipeline = mocker.Mock()
        mock_pipeline.run = AsyncMock(return_value=mock_pipeline_result)
        container.pipeline = mock_pipeline

        # Mock history service
        mock_history = mocker.Mock()
        mock_history.record_operation_async = AsyncMock()
        service.history_service = mock_history

        request = CleanRequest(
            paths=[Path("/tmp")], mode=CleanRequestMode.TRASH, profile=CleanProfile.DEVELOPER
        )
        result = await service.execute_clean_async(request)

        assert result.success is True
        assert result.files_deleted == 50
        assert result.size_bytes == 512000

    def test_execute_scan_sync_wrapper(self, container, mocker) -> None:
        """Test sync wrapper for scan."""
        service = CleaningService(container)

        # Mock async method
        mock_async_result = mocker.Mock()
        service.execute_scan_async = AsyncMock(return_value=mock_async_result)

        request = ScanRequest(paths=[Path("/tmp")], mode=ScanMode.FAST)
        result = service.execute_scan(request)

        assert result == mock_async_result

    def test_execute_clean_sync_wrapper(self, container, mocker) -> None:
        """Test sync wrapper for clean."""
        service = CleaningService(container)

        # Mock async method
        mock_async_result = mocker.Mock()
        service.execute_clean_async = AsyncMock(return_value=mock_async_result)

        request = CleanRequest(
            paths=[Path("/tmp")], mode=CleanRequestMode.TRASH, profile=CleanProfile.DEVELOPER
        )
        result = service.execute_clean(request)

        assert result == mock_async_result


__all__ = ["TestCleaningService"]
