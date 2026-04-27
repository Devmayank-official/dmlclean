# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Dependency Injection Container for DMLClean.

This module provides a centralized container for managing all application
dependencies. The container follows the Dependency Injection pattern to:
- Centralize dependency configuration
- Make testing easier (mock container)
- Clarify dependency graph
- Enable swapping implementations

Example:
    ```python
    from dmlclean.container import Container

    # Create container with all dependencies
    container = Container.create()

    # Access dependencies
    db = container.db
    config = container.config
    scanner = container.scanner

    # Create services with container
    from dmlclean.services import CleaningService
    service = CleaningService(container)

    # Or use container's service factory
    service = container.cleaning_service
    ```
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

from loguru import logger

from dmlclean.config.loader import ConfigLoader
from dmlclean.config.schema import ConfigSchema
from dmlclean.core.analyzer import Analyzer
from dmlclean.core.cleaner import Cleaner
from dmlclean.core.deduplicator import Deduplicator
from dmlclean.core.pipeline import Pipeline
from dmlclean.core.plugin_scanner import PluginScanConfig, PluginScanner
from dmlclean.core.scanner import FileSystemScanner
from dmlclean.core.scheduler import Scheduler

# Import notification handlers to register event handlers
from dmlclean.notifications import handlers  # noqa: F401 - registers event handlers
from dmlclean.safety.protected_zone import ProtectedZone
from dmlclean.safety.undo import UndoManager
from dmlclean.services.cleaning_service import CleaningService
from dmlclean.services.history_service import HistoryService
from dmlclean.services.plugin_service import PluginService
from dmlclean.services.protection_service import ProtectionService
from dmlclean.services.report_service import ReportService
from dmlclean.services.schedule_service import ScheduleService
from dmlclean.storage.database import Database, get_database
from dmlclean.storage.history_repo import HistoryRepository
from dmlclean.storage.manifest_repo import ManifestRepository
from dmlclean.storage.protected_repo import ProtectedRepository
from dmlclean.storage.schedule_repo import ScheduleRepository
from dmlclean.storage.trend_repo import TrendRepository


@dataclass
class Container:
    """
    Dependency Injection Container for DMLClean.

    The Container centralizes all application dependencies and provides
    a single point of configuration. It uses lazy initialization via
    @cached_property to create dependencies only when needed.

    Attributes:
        db: Database connection.
        config: Configuration loader.
        protected_zone: Protected zone manager.
        scanner: File system scanner.
        analyzer: File analyzer.
        cleaner: File cleaner.
        deduplicator: Duplicate file detector.
        scheduler: Job scheduler.
        undo_manager: Undo operation manager.

    Example:
        ```python
        # Create container
        container = Container.create()

        # Access dependencies
        db = container.db
        config = container.config

        # Create services
        cleaning_service = CleaningService(container)
        history_service = HistoryService(container.db)

        # Or use container's cached services
        cleaning_service = container.cleaning_service
        history_service = container.history_service
        ```
    """

    # Core dependencies
    db: Database
    config: ConfigLoader
    config_schema: ConfigSchema

    # Safety components
    protected_zone: ProtectedZone
    undo_manager: UndoManager

    # Core engine components
    scanner: FileSystemScanner = field(default_factory=FileSystemScanner)
    plugin_scanner: PluginScanner | None = None
    analyzer: Analyzer | None = None
    cleaner: Cleaner = field(default_factory=Cleaner)
    deduplicator: Deduplicator = field(default_factory=Deduplicator)
    scheduler: Scheduler | None = None
    pipeline: Pipeline | None = None

    # Repositories (lazy-initialized)
    _history_repo: HistoryRepository | None = field(default=None, repr=False)
    _manifest_repo: ManifestRepository | None = field(default=None, repr=False)
    _protected_repo: ProtectedRepository | None = field(default=None, repr=False)
    _schedule_repo: ScheduleRepository | None = field(default=None, repr=False)
    _trend_repo: TrendRepository | None = field(default=None, repr=False)

    # Services (lazy-initialized)
    _cleaning_service: CleaningService | None = field(default=None, repr=False)
    _history_service: HistoryService | None = field(default=None, repr=False)
    _schedule_service: ScheduleService | None = field(default=None, repr=False)
    _protection_service: ProtectionService | None = field(default=None, repr=False)
    _plugin_service: PluginService | None = field(default=None, repr=False)
    _report_service: ReportService | None = field(default=None, repr=False)

    @classmethod
    def create(cls, config_path: Path | None = None) -> Container:
        """
        Factory method to create a fully-configured container.

        This method initializes all core dependencies with proper
        configuration and wiring. Use this as the primary entry point
        for creating the application container.

        Args:
            config_path: Optional custom config path.

        Returns:
            Container: Fully-configured dependency container.

        Example:
            ```python
            # Create container with default config
            container = Container.create()

            # Create container with custom config
            container = Container.create(Path("/custom/config.toml"))
            ```
        """
        logger.debug("Creating DI Container...")

        # Initialize database
        db = get_database()
        logger.debug("Database initialized")

        # Initialize configuration
        config = ConfigLoader(config_path=config_path)
        config.load()
        config_schema = config.schema
        logger.debug("Configuration loaded")

        # Initialize protected zone
        protected_zone = ProtectedZone(
            enabled=config_schema.protected_zone.enabled,
            custom_paths=config_schema.protected_zone.custom_paths,
            custom_globs=config_schema.protected_zone.custom_globs,
            protect_git_dirs=config_schema.protected_zone.protect_git_dirs,
            protect_venvs=config_schema.protected_zone.protect_venvs,
            protect_recent_days=config_schema.protected_zone.protect_recent_days,
        )
        logger.debug("ProtectedZone initialized")

        # Initialize undo manager
        undo_manager = UndoManager()
        logger.debug("UndoManager initialized")

        # Initialize analyzer with config
        analyzer = Analyzer(
            category_configs=dict(config_schema.categories) if config_schema.categories else None
        )
        logger.debug("Analyzer initialized")

        # Initialize plugin scanner (modular, scalable architecture)
        enabled_categories = None
        if config_schema.categories:
            enabled_categories = [
                cat_name
                for cat_name, cat_config in config_schema.categories.items()
                if cat_config.enabled
            ]

        # Plugin service for plugin management
        plugin_service = PluginService()
        logger.debug("PluginService initialized")

        plugin_scan_config = PluginScanConfig(
            enabled_categories=enabled_categories,
            use_plugins=True,
            fallback_to_regex=True,
            parallel_execution=True,
            timeout_per_plugin=30.0,
        )
        logger.debug(f"PluginScanConfig created: {plugin_scan_config}")

        # Initialize scheduler
        scheduler = Scheduler(db)
        logger.debug("Scheduler initialized")

        # Initialize pipeline with plugin scanner (uses plugin_service)
        plugin_scanner = PluginScanner(plugin_loader=plugin_service, config=plugin_scan_config)
        pipeline = Pipeline(scanner=plugin_scanner, protected_zone=protected_zone)
        logger.debug("Pipeline initialized with PluginScanner")

        # Create container instance
        container = cls(
            db=db,
            config=config,
            config_schema=config_schema,
            protected_zone=protected_zone,
            undo_manager=undo_manager,
            scanner=FileSystemScanner(
                follow_symlinks=config_schema.scanner.follow_symlinks,
                max_depth=config_schema.scanner.max_depth,
            ),
            plugin_scanner=plugin_scanner,
            analyzer=analyzer,
            cleaner=Cleaner(),
            deduplicator=Deduplicator(),
            scheduler=scheduler,
            pipeline=pipeline,
        )

        logger.info("DI Container created successfully")
        return container

    @property
    def history_repo(self) -> HistoryRepository:
        """Lazy-initialized HistoryRepository."""
        if self._history_repo is None:
            self._history_repo = HistoryRepository(self.db)
        return self._history_repo

    @property
    def manifest_repo(self) -> ManifestRepository:
        """Lazy-initialized ManifestRepository."""
        if self._manifest_repo is None:
            self._manifest_repo = ManifestRepository(self.db)
        return self._manifest_repo

    @property
    def protected_repo(self) -> ProtectedRepository:
        """Lazy-initialized ProtectedRepository."""
        if self._protected_repo is None:
            self._protected_repo = ProtectedRepository(self.db)
        return self._protected_repo

    @property
    def schedule_repo(self) -> ScheduleRepository:
        """Lazy-initialized ScheduleRepository."""
        if self._schedule_repo is None:
            self._schedule_repo = ScheduleRepository(self.db)
        return self._schedule_repo

    @property
    def trend_repo(self) -> TrendRepository:
        """Lazy-initialized TrendRepository."""
        if self._trend_repo is None:
            self._trend_repo = TrendRepository(self.db)
        return self._trend_repo

    @cached_property
    def cleaning_service(self) -> CleaningService:
        """Lazy-initialized CleaningService."""
        return CleaningService(self)

    @cached_property
    def history_service(self) -> HistoryService:
        """Lazy-initialized HistoryService."""
        return HistoryService(self.db, self.history_repo, self.undo_manager)

    @cached_property
    def schedule_service(self) -> ScheduleService:
        """Lazy-initialized ScheduleService."""
        assert self.scheduler is not None  # Initialized in create()
        return ScheduleService(self.db, self.schedule_repo, self.scheduler)

    @cached_property
    def protection_service(self) -> ProtectionService:
        """Lazy-initialized ProtectionService."""
        return ProtectionService(self.db, self.protected_repo, self.protected_zone)

    @cached_property
    def plugin_service(self) -> PluginService:
        """Lazy-initialized PluginService."""
        return PluginService()

    @cached_property
    def report_service(self) -> ReportService:
        """Lazy-initialized ReportService."""
        return ReportService(self.db, self.history_repo)

    def close(self) -> None:
        """
        Clean up container resources.

        This should be called when shutting down the application to
        properly close database connections and release resources.

        Example:
            ```python
            container = Container.create()
            try:
                # Use container
                service = container.cleaning_service
                result = service.execute_clean(...)
            finally:
                container.close()
            ```
        """
        logger.debug("Closing DI Container...")
        self.db.close()
        logger.info("DI Container closed")


# Global container instance (for CLI usage)
_container: Container | None = None


def get_container(config_path: Path | None = None) -> Container:
    """
    Get or create the global container instance.

    This function provides a singleton container for the application.
    It creates the container on first call and reuses it thereafter.

    Args:
        config_path: Optional custom config path.

    Returns:
        Container: Global container instance.

    Example:
        ```python
        # Get global container
        container = get_container()

        # Access services
        service = container.cleaning_service
        result = service.execute_scan(...)
        ```
    """
    global _container

    if _container is None:
        _container = Container.create(config_path)
    elif config_path and _container.config.config_path != config_path:
        # Different config requested, recreate container
        _container.close()
        _container = Container.create(config_path)

    return _container


def close_container() -> None:
    """
    Close and reset the global container instance.

    This should be called when shutting down the application to
    properly clean up resources.

    Example:
        ```python
        try:
            container = get_container()
            # Use container...
        finally:
            close_container()
        ```
    """
    global _container

    if _container is not None:
        _container.close()
        _container = None
        logger.debug("Global container closed")


__all__ = [
    "Container",
    "close_container",
    "get_container",
]
