# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Async cleaning service for DMLClean.

Domain service for orchestrating cleaning operations.

DTO Integration:
    This service uses Pydantic v2 DTOs for all operations:
    - ScanRequest → ScanResult
    - CleanRequest → CleanResult

    All methods are async for non-blocking I/O operations.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import TYPE_CHECKING

from loguru import logger

from dmlclean.domain.events import (
    CleanOperationCompleted,
    CleanOperationFailed,
    EventBus,
)

if TYPE_CHECKING:
    from dmlclean.container import Container
    from dmlclean.dtos.clean import CleanRequest, CleanResult
    from dmlclean.dtos.scan import ScanRequest, ScanResult


class CleaningService:
    """
    Async domain service for cleaning operations.

    The CleaningService orchestrates the full cleaning pipeline:
    1. Scan: Discover files in target paths
    2. Analyze: Categorize and assign risk levels
    3. Filter: Apply user filters (age, size, categories)
    4. Execute: Perform cleaning operation
    5. Record: Log to history

    All methods are async for non-blocking I/O.

    Attributes:
        container: DI Container providing all dependencies.

    Example:
        ```python
        from dmlclean.container import Container

        container = Container.create()
        service = container.cleaning_service

        # Scan (async)
        scan_result = await service.execute_scan_async(
            paths=[Path("/tmp"), Path("/home/user/.cache")]
        )

        # Clean (async)
        clean_result = await service.execute_clean_async(
            paths=[Path("/tmp")],
            mode="trash",
            profile="developer",
        )
        ```
    """

    def __init__(self, container: Container) -> None:
        """
        Initialize the cleaning service.

        Args:
            container: DI Container providing all dependencies.
        """
        self.container = container
        self.db = container.db
        self.history_service = container.history_service
        logger.debug("CleaningService initialized")

    # ========================================================================
    # ASYNC METHODS (Primary API - Non-blocking)
    # ========================================================================

    async def execute_scan_async(self, request: ScanRequest) -> ScanResult:
        """
        Execute scan asynchronously (non-blocking).

        Args:
            request: Scan request DTO.

        Returns:
            ScanResult: Scan result DTO.
        """
        from dmlclean.dtos.scan import ScanResult as ScanResultDTO
        from dmlclean.dtos.scan import ScanStats

        logger.info(f"Starting {request.mode.value} scan of {len(request.paths)} paths")

        # Execute scan via pipeline (async)
        scan_result = await self.container.pipeline.scan_only(request.paths)

        # Analyze results (sync, fast operation)
        analyzer = self.container.analyzer
        analysis_result = analyzer.analyze(scan_result.paths)

        # Build result DTO
        stats = ScanStats(
            total_files=scan_result.stats.total_files,
            total_directories=scan_result.stats.total_directories,
            total_size_bytes=scan_result.stats.total_size_bytes,
            errors=scan_result.stats.errors,
            duration_seconds=scan_result.stats.duration_seconds,
            files_per_second=scan_result.stats.files_per_second,
        )

        result = ScanResultDTO(
            success=True,
            mode=request.mode.value,
            paths_scanned=len(request.paths),
            total_files=stats.total_files,
            total_size_bytes=stats.total_size_bytes,
            candidates=len(analysis_result.candidates),
            by_category=analysis_result.get_summary().get("by_category", {}),
            by_risk=analysis_result.get_summary().get("by_risk", {}),
            stats=stats,
        )

        logger.info(f"Scan complete: {result.candidates} candidates identified")

        # Publish scan completed event (triggers notification)
        import uuid

        from dmlclean.domain.events import EventBus, ScanCompleted

        logger.info("Publishing ScanCompleted event...")
        EventBus.publish(
            ScanCompleted(
                operation_id=str(uuid.uuid4()),
                mode=request.mode.value,
                paths_scanned=result.paths_scanned,
                files_found=result.total_files,
                size_bytes=result.total_size_bytes,
                candidates=result.candidates,
                duration_ms=int(result.stats.duration_seconds * 1000) if result.stats else 0,
                categories=request.categories,
            )
        )
        logger.info("ScanCompleted event published")

        return result

    async def execute_clean_async(self, request: CleanRequest) -> CleanResult:
        """
        Execute clean asynchronously (non-blocking).

        Args:
            request: Clean request DTO.

        Returns:
            CleanResult: Clean result DTO.
        """
        from dmlclean.dtos.clean import CleanResult as CleanResultDTO

        start_time = time.time()
        operation_id = str(uuid.uuid4())

        logger.info(
            f"Starting {request.mode.value} clean operation: "
            f"{len(request.paths)} paths, profile={request.profile.value}"
        )

        # Use container's pipeline with protected zone (async)
        result = await self.container.pipeline.run(
            roots=request.paths,
            mode=request.mode.value,
            categories=request.categories,
            min_age_days=request.min_age_days,
            min_size_mb=request.min_size_mb,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        # Build result DTO
        clean_result = CleanResultDTO(
            success=len(result.errors) == 0,
            operation_id=operation_id,
            mode=request.mode.value,
            profile=request.profile.value,
            files_deleted=result.clean_result.stats.deleted if result.clean_result else 0,
            files_failed=result.clean_result.stats.failed if result.clean_result else 0,
            files_skipped=result.clean_result.stats.skipped if result.clean_result else 0,
            size_bytes=result.clean_result.stats.total_size_bytes if result.clean_result else 0,
            duration_ms=duration_ms,
            errors=result.errors,
            manifest_id=result.manifest.id if result.manifest else None,
        )

        # Record in history and publish events (except for dry-run)
        if request.mode.value != "dry-run" and result.clean_result:
            if result.errors:
                EventBus.publish(
                    CleanOperationFailed(
                        operation_id=operation_id,
                        mode=request.mode.value,
                        profile=request.profile.value,
                        error_message=result.errors[0],
                        error_type="CleaningError",
                        paths_attempted=len(request.paths),
                    )
                )
            else:
                EventBus.publish(
                    CleanOperationCompleted(
                        operation_id=operation_id,
                        mode=request.mode.value,
                        profile=request.profile.value,
                        scan_mode="fast",
                        files_found=result.analysis_result.total_files
                        if result.analysis_result
                        else 0,
                        files_deleted=clean_result.files_deleted,
                        size_bytes=clean_result.size_bytes,
                        duration_ms=duration_ms,
                        categories=request.categories,
                        paths_cleaned=len(request.paths),
                    )
                )

            # Record in history (async)
            await self.history_service.record_operation_async(
                id=operation_id,
                mode=request.mode.value,
                profile=request.profile.value,
                scan_mode="fast",
                files_found=result.analysis_result.total_files if result.analysis_result else 0,
                files_deleted=clean_result.files_deleted,
                size_bytes=clean_result.size_bytes,
                duration_ms=duration_ms,
                categories=request.categories,
                status="complete" if not result.errors else "partial",
                error_message=result.errors[0] if result.errors else None,
            )

        logger.info(f"Clean operation complete: {clean_result.files_deleted} files deleted")

        return clean_result

    # ========================================================================
    # SYNC WRAPPERS (For CLI compatibility - blocking calls)
    # ========================================================================

    def execute_scan(self, request: ScanRequest) -> ScanResult:
        """
        Synchronous wrapper for execute_scan_async.

        Args:
            request: Scan request DTO.

        Returns:
            ScanResult: Scan result DTO.
        """
        return asyncio.run(self.execute_scan_async(request))

    def execute_clean(self, request: CleanRequest) -> CleanResult:
        """
        Synchronous wrapper for execute_clean_async.

        Args:
            request: Clean request DTO.

        Returns:
            CleanResult: Clean result DTO.
        """
        return asyncio.run(self.execute_clean_async(request))


__all__ = ["CleaningService"]
