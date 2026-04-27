"""
Pytest configuration and shared fixtures for DMLClean tests.

Uses pyfakefs for fake filesystem testing - never touches real disk.
"""

from __future__ import annotations

# ruff: noqa: S108  # reason: tests legitimately use /tmp paths
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

if TYPE_CHECKING:
    from dmlclean.services.cleaning_service import CleaningService
    from dmlclean.services.history_service import HistoryService
    from dmlclean.services.protection_service import ProtectionService
    from dmlclean.services.report_service import ReportService
    from dmlclean.services.schedule_service import ScheduleService
    from dmlclean.storage.database import Database
    from dmlclean.storage.history_repo import HistoryRepository
    from dmlclean.storage.manifest_repo import ManifestRepository
    from dmlclean.storage.protected_repo import ProtectedRepository
    from dmlclean.storage.schedule_repo import ScheduleRepository
    from dmlclean.storage.trend_repo import TrendRepository


@pytest.fixture
def fake_fs(fs: FakeFilesystem) -> FakeFilesystem:
    """
    Provide a fake filesystem for testing.

    This fixture uses pyfakefs to create an isolated fake
    filesystem that doesn't touch the real disk.

    Args:
        fs: pyfakefs fixture.

    Returns:
        FakeFilesystem: Fake filesystem instance.
    """
    # Create common test directories (pyfakefs creates these by default on some platforms)
    try:
        fs.create_dir("/tmp")
    except FileExistsError:
        pass

    try:
        fs.create_dir("/home/testuser")
    except FileExistsError:
        pass

    try:
        fs.create_dir("/home/testuser/.cache")
    except FileExistsError:
        pass

    if sys.platform == "win32":
        try:
            fs.create_dir("C:/Windows/Temp")
        except FileExistsError:
            pass
        try:
            fs.create_dir("C:/Users/testuser/AppData/Local/Temp")
        except FileExistsError:
            pass

    return fs


@pytest.fixture
def sample_temp_files(fake_fs: FakeFilesystem) -> list[Path]:
    """
    Create sample temporary files for testing.

    Args:
        fake_fs: Fake filesystem fixture.

    Returns:
        list[Path]: List of created file paths.
    """
    files = [
        Path("/tmp/test1.tmp"),
        Path("/tmp/test2.tmp"),
        Path("/tmp/test.log"),
        Path("/home/testuser/.cache/cache1.dat"),
        Path("/home/testuser/.cache/cache2.dat"),
    ]

    for file_path in files:
        fake_fs.create_file(file_path, contents="test content" * 100)

    return files


@pytest.fixture
def sample_python_artifacts(fake_fs: FakeFilesystem) -> list[Path]:
    """
    Create sample Python development artifacts.

    Args:
        fake_fs: Fake filesystem fixture.

    Returns:
        list[Path]: List of created file paths.
    """
    # Create __pycache__ directory with .pyc files
    pycache_dir = Path("/project/__pycache__")
    fake_fs.create_dir(pycache_dir)

    files = [
        pycache_dir / "module.cpython-311.pyc",
        pycache_dir / "utils.cpython-311.pyc",
        Path("/project/.pytest_cache"),
        Path("/project/.mypy_cache"),
    ]

    for file_path in files:
        if file_path.suffix:
            fake_fs.create_file(file_path, contents="fake content")
        else:
            fake_fs.create_dir(file_path)

    return files


@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Set common environment variables for tests.

    Args:
        monkeypatch: pytest monkeypatch fixture.
    """
    monkeypatch.setenv("DMLCLEAN_TEST_MODE", "true")
    monkeypatch.setenv("HOME", "/home/testuser")
    monkeypatch.setenv("USERPROFILE", "/home/testuser")

    if sys.platform == "win32":
        monkeypatch.setenv("TEMP", "C:\\Users\\testuser\\AppData\\Local\\Temp")
        monkeypatch.setenv("TMP", "C:\\Users\\testuser\\AppData\\Local\\Temp")
    else:
        monkeypatch.setenv("TEMP", "/tmp")
        monkeypatch.setenv("TMP", "/tmp")


@pytest.fixture
def config_path(fake_fs: FakeFilesystem) -> Path:
    """
    Provide a test config file path.

    Args:
        fake_fs: Fake filesystem fixture.

    Returns:
        Path: Config file path.
    """
    config_dir = Path("/home/testuser/.config/DML Labs/dmlclean")
    fake_fs.create_dir(config_dir)
    return config_dir / "config.toml"


@pytest.fixture
def db_path(fake_fs: FakeFilesystem) -> Path:
    """
    Provide a test database file path.

    Args:
        fake_fs: Fake filesystem fixture.

    Returns:
        Path: Database file path.
    """
    data_dir = Path("/home/testuser/.local/share/DML Labs/DML Clean/data")
    fake_fs.create_dir(data_dir)
    return data_dir / "dml_clean.db"


@pytest.fixture
def db(tmp_path: Path) -> Database:
    """
    Create a test database for testing.

    Uses pytest's tmp_path which works on all platforms.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Database: Database instance with migrations applied.
    """
    from dmlclean.storage.database import Database

    # Use tmp_path (works on all platforms)
    db_path = tmp_path / "test.db"

    db = Database(db_path)
    db.connect()
    db.run_migrations()
    yield db
    db.close()


@pytest.fixture
def history_repo(db: Database) -> HistoryRepository:
    """
    Create a HistoryRepository instance for testing.

    Args:
        db: Database fixture.

    Returns:
        HistoryRepository: Repository instance.
    """
    from dmlclean.storage.history_repo import HistoryRepository

    return HistoryRepository(db)


@pytest.fixture
def schedule_repo(db: Database) -> ScheduleRepository:
    """
    Create a ScheduleRepository instance for testing.

    Args:
        db: Database fixture.

    Returns:
        ScheduleRepository: Repository instance.
    """
    from dmlclean.storage.schedule_repo import ScheduleRepository

    return ScheduleRepository(db)


@pytest.fixture
def protected_repo(db: Database) -> ProtectedRepository:
    """
    Create a ProtectedRepository instance for testing.

    Args:
        db: Database fixture.

    Returns:
        ProtectedRepository: Repository instance.
    """
    from dmlclean.storage.protected_repo import ProtectedRepository

    return ProtectedRepository(db)


@pytest.fixture
def manifest_repo(db: Database) -> ManifestRepository:
    """
    Create a ManifestRepository instance for testing.

    Args:
        db: Database fixture.

    Returns:
        ManifestRepository: Repository instance.
    """
    from dmlclean.storage.manifest_repo import ManifestRepository

    return ManifestRepository(db)


@pytest.fixture
def trend_repo(db: Database) -> TrendRepository:
    """
    Create a TrendRepository instance for testing.

    Args:
        db: Database fixture.

    Returns:
        TrendRepository: Repository instance.
    """
    from dmlclean.storage.trend_repo import TrendRepository

    return TrendRepository(db)


@pytest.fixture
def history_service(db: Database) -> HistoryService:
    """
    Create a HistoryService instance for testing.

    Args:
        db: Database fixture.

    Returns:
        HistoryService: Service instance.
    """
    from dmlclean.services.history_service import HistoryService

    return HistoryService(db)


@pytest.fixture
def protection_service(db: Database) -> ProtectionService:
    """
    Create a ProtectionService instance for testing.

    Args:
        db: Database fixture.

    Returns:
        ProtectionService: Service instance.
    """
    from dmlclean.services.protection_service import ProtectionService

    return ProtectionService(db)


@pytest.fixture
def schedule_service(db: Database) -> ScheduleService:
    """
    Create a ScheduleService instance for testing.

    Args:
        db: Database fixture.

    Returns:
        ScheduleService: Service instance.
    """
    from dmlclean.services.schedule_service import ScheduleService

    return ScheduleService(db)


@pytest.fixture
def report_service(db: Database) -> ReportService:
    """
    Create a ReportService instance for testing.

    Args:
        db: Database fixture.

    Returns:
        ReportService: Service instance.
    """
    from dmlclean.services.report_service import ReportService

    return ReportService(db)


@pytest.fixture
def cleaning_service(db: Database) -> CleaningService:
    """
    Create a CleaningService instance for testing.

    Args:
        db: Database fixture.

    Returns:
        CleaningService: Service instance.
    """
    from dmlclean.services.cleaning_service import CleaningService

    return CleaningService(db)
