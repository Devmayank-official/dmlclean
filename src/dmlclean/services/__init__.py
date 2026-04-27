# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Service Layer package for DMLClean.

The service layer contains domain services that orchestrate business logic
across multiple repositories and core components. Services provide a clean
abstraction for CLI commands and other consumers.

Architecture:
    ```
    CLI Commands → Services → Repositories → Database
                       ↓
                   Core Engine (Scanner, Analyzer, Cleaner)
    ```

Services:
    - CleaningService: Orchestrates scan/analyze/clean pipeline
    - HistoryService: Manages cleaning history operations
    - ScheduleService: Manages scheduled cleaning jobs
    - ProtectionService: Manages protected zone configuration
    - PluginService: Manages plugin discovery and installation
    - ReportService: Generates reports and exports

Example:
    ```python
    from dmlclean.services import (
        CleaningService,
        HistoryService,
        ScheduleService,
        ProtectionService,
        PluginService,
        ReportService,
    )
    from dmlclean.storage import get_database

    # Get database connection
    db = get_database()

    # Create services
    cleaning_service = CleaningService(db)
    history_service = HistoryService(db)
    schedule_service = ScheduleService(db)
    protection_service = ProtectionService(db)
    plugin_service = PluginService()
    report_service = ReportService(db)

    # Use services
    result = cleaning_service.execute_scan(paths=[Path("/tmp")])
    history = history_service.list_recent(limit=10)
    ```
"""

from dmlclean.services.cleaning_service import CleaningService
from dmlclean.services.history_service import HistoryService
from dmlclean.services.plugin_service import PluginService
from dmlclean.services.protection_service import ProtectionService
from dmlclean.services.report_service import ReportService
from dmlclean.services.schedule_service import ScheduleService

__all__ = [
    "CleaningService",
    "HistoryService",
    "PluginService",
    "ProtectionService",
    "ReportService",
    "ScheduleService",
]
