"""
Storage module for DMLClean.

SQLite-based persistence layer for:
- Cleaning history
- Deletion manifests
- Scheduled jobs
- Protected paths
- Disk usage trends

Repositories follow the Repository Pattern with full CRUD operations.

Example:
    ```python
    from dmlclean.storage import (
        get_database,
        HistoryRepository,
        ScheduleRepository,
        ProtectedRepository,
        ManifestRepository,
        TrendRepository,
    )

    db = get_database()

    # Use repositories
    history_repo = HistoryRepository(db)
    schedule_repo = ScheduleRepository(db)
    protected_repo = ProtectedRepository(db)
    manifest_repo = ManifestRepository(db)
    trend_repo = TrendRepository(db)
    ```
"""

from dmlclean.storage.database import Database, get_database
from dmlclean.storage.history_repo import HistoryEntry, HistoryRepository
from dmlclean.storage.manifest_repo import ManifestRecord, ManifestRepository
from dmlclean.storage.paths import (
    ensure_all_dirs,
    get_base_dir,
    get_cache_dir,
    get_config_dir,
    get_data_dir,
    get_db_path,
    get_history_dir,
    get_logs_dir,
    get_manifests_dir,
    get_reports_dir,
)
from dmlclean.storage.protected_repo import ProtectedPathEntry, ProtectedRepository
from dmlclean.storage.repository import Repository, RepositoryProtocol
from dmlclean.storage.schedule_repo import ScheduleEntry, ScheduleRepository
from dmlclean.storage.trend_repo import DiskTrendEntry, TrendRepository
from dmlclean.storage.uow import UnitOfWork

__all__ = [
    # Database
    "Database",
    # Trend
    "DiskTrendEntry",
    # History
    "HistoryEntry",
    "HistoryRepository",
    # Manifest
    "ManifestRecord",
    "ManifestRepository",
    # Protected
    "ProtectedPathEntry",
    "ProtectedRepository",
    # Repository Base
    "Repository",
    "RepositoryProtocol",
    # Schedule
    "ScheduleEntry",
    "ScheduleRepository",
    "TrendRepository",
    # Unit of Work
    "UnitOfWork",
    # Paths
    "ensure_all_dirs",
    "get_base_dir",
    "get_cache_dir",
    "get_config_dir",
    "get_data_dir",
    "get_database",
    "get_db_path",
    "get_history_dir",
    "get_logs_dir",
    "get_manifests_dir",
    "get_reports_dir",
]
