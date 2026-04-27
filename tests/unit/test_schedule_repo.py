# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for ScheduleRepository."""

from __future__ import annotations

import pytest

from dmlclean.exceptions.repository import DataError, DuplicateError
from dmlclean.storage.database import Database
from dmlclean.storage.schedule_repo import ScheduleRepository


@pytest.fixture
def repo(db: Database) -> ScheduleRepository:
    """Create ScheduleRepository instance."""
    return ScheduleRepository(db)


class TestScheduleRepositoryCreate:
    """Tests for ScheduleRepository.create()"""

    def test_create_success(self, repo: ScheduleRepository) -> None:
        """Test successful schedule creation."""
        entry = repo.create(
            id="sched-001",
            name="Daily Cleanup",
            cron_expression="0 3 * * *",
            enabled=True,
        )
        assert entry.id == "sched-001"
        assert entry.name == "Daily Cleanup"
        assert entry.enabled is True

    def test_create_duplicate_raises_error(self, repo: ScheduleRepository) -> None:
        """Test duplicate creation raises error."""
        repo.create(id="sched-002", name="Test", cron_expression="0 3 * * *")
        with pytest.raises(DuplicateError):
            repo.create(id="sched-002", name="Test", cron_expression="0 3 * * *")

    def test_create_empty_id_raises_error(self, repo: ScheduleRepository) -> None:
        """Test empty ID raises error."""
        with pytest.raises(DataError, match="ID cannot be empty"):
            repo.create(id="", name="Test", cron_expression="0 3 * * *")

    def test_create_empty_name_raises_error(self, repo: ScheduleRepository) -> None:
        """Test empty name raises error."""
        with pytest.raises(DataError, match="name cannot be empty"):
            repo.create(id="sched-003", name="", cron_expression="0 3 * * *")

    def test_create_empty_cron_raises_error(self, repo: ScheduleRepository) -> None:
        """Test empty cron raises error."""
        with pytest.raises(DataError, match="cron_expression cannot be empty"):
            repo.create(id="sched-004", name="Test", cron_expression="")


class TestScheduleRepositoryGet:
    """Tests for ScheduleRepository.get_by_id()"""

    def test_get_existing(self, repo: ScheduleRepository) -> None:
        """Test getting existing entry."""
        repo.create(id="sched-005", name="Test", cron_expression="0 3 * * *")
        entry = repo.get_by_id("sched-005")
        assert entry is not None
        assert entry.name == "Test"

    def test_get_nonexistent(self, repo: ScheduleRepository) -> None:
        """Test getting non-existent entry."""
        entry = repo.get_by_id("nonexistent")
        assert entry is None


class TestScheduleRepositoryList:
    """Tests for ScheduleRepository.list_all()"""

    def test_list_empty(self, repo: ScheduleRepository) -> None:
        """Test listing when empty."""
        entries = repo.list_all()
        assert len(entries) == 0

    def test_list_with_entries(self, repo: ScheduleRepository) -> None:
        """Test listing with entries."""
        repo.create(id="sched-006", name="Test1", cron_expression="0 3 * * *")
        repo.create(id="sched-007", name="Test2", cron_expression="0 4 * * *")
        entries = repo.list_all()
        assert len(entries) == 2

    def test_list_enabled_filter(self, repo: ScheduleRepository) -> None:
        """Test filtering by enabled status."""
        repo.create(id="sched-008", name="Enabled", cron_expression="0 3 * * *", enabled=True)
        repo.create(id="sched-009", name="Disabled", cron_expression="0 3 * * *", enabled=False)
        entries = repo.list_all(enabled=True)
        assert len(entries) == 1
        assert entries[0].enabled is True


class TestScheduleRepositoryUpdate:
    """Tests for ScheduleRepository.update()"""

    def test_update_success(self, repo: ScheduleRepository) -> None:
        """Test successful update."""
        repo.create(id="sched-010", name="Test", cron_expression="0 3 * * *")
        result = repo.update("sched-010", enabled=False)
        assert result is True
        entry = repo.get_by_id("sched-010")
        assert entry is not None
        assert entry.enabled is False

    def test_update_nonexistent(self, repo: ScheduleRepository) -> None:
        """Test updating non-existent entry."""
        result = repo.update("nonexistent", enabled=False)
        assert result is False

    def test_update_no_fields_raises_error(self, repo: ScheduleRepository) -> None:
        """Test updating with no fields."""
        repo.create(id="sched-011", name="Test", cron_expression="0 3 * * *")
        with pytest.raises(DataError, match="No valid fields"):
            repo.update("sched-011", invalid_field="value")


class TestScheduleRepositoryDelete:
    """Tests for ScheduleRepository.delete()"""

    def test_delete_success(self, repo: ScheduleRepository) -> None:
        """Test successful deletion."""
        repo.create(id="sched-012", name="Test", cron_expression="0 3 * * *")
        result = repo.delete("sched-012")
        assert result is True
        assert repo.get_by_id("sched-012") is None

    def test_delete_nonexistent(self, repo: ScheduleRepository) -> None:
        """Test deleting non-existent entry."""
        result = repo.delete("nonexistent")
        assert result is False


class TestScheduleRepositoryExists:
    """Tests for ScheduleRepository.exists()"""

    def test_exists_true(self, repo: ScheduleRepository) -> None:
        """Test exists returns True."""
        repo.create(id="sched-013", name="Test", cron_expression="0 3 * * *")
        assert repo.exists("sched-013") is True

    def test_exists_false(self, repo: ScheduleRepository) -> None:
        """Test exists returns False."""
        assert repo.exists("nonexistent") is False


class TestScheduleRepositoryCount:
    """Tests for ScheduleRepository.count()"""

    def test_count_empty(self, repo: ScheduleRepository) -> None:
        """Test count when empty."""
        assert repo.count() == 0

    def test_count_with_entries(self, repo: ScheduleRepository) -> None:
        """Test count with entries."""
        repo.create(id="sched-014", name="Test1", cron_expression="0 3 * * *")
        repo.create(id="sched-015", name="Test2", cron_expression="0 3 * * *")
        assert repo.count() == 2


class TestScheduleRepositoryMarkRun:
    """Tests for ScheduleRepository.mark_run()"""

    def test_mark_run_success(self, repo: ScheduleRepository) -> None:
        """Test marking successful run."""
        repo.create(id="sched-016", name="Test", cron_expression="0 3 * * *")
        result = repo.mark_run("sched-016", success=True)
        assert result is True

    def test_mark_run_failure(self, repo: ScheduleRepository) -> None:
        """Test marking failed run."""
        repo.create(id="sched-017", name="Test", cron_expression="0 3 * * *")
        result = repo.mark_run("sched-017", success=False, error_message="Test error")
        assert result is True
        entry = repo.get_by_id("sched-017")
        assert entry is not None
        assert entry.fail_count == 1
        assert entry.last_error == "Test error"


class TestScheduleRepositoryClearAll:
    """Tests for ScheduleRepository.clear_all()"""

    def test_clear_all_success(self, repo: ScheduleRepository) -> None:
        """Test clearing all entries."""
        repo.create(id="sched-018", name="Test1", cron_expression="0 3 * * *")
        repo.create(id="sched-019", name="Test2", cron_expression="0 3 * * *")
        count = repo.clear_all()
        assert count == 2
        assert repo.count() == 0


class TestScheduleRepositoryGetEnabled:
    """Tests for ScheduleRepository.get_enabled()"""

    def test_get_enabled(self, repo: ScheduleRepository) -> None:
        """Test getting enabled schedules."""
        repo.create(id="sched-020", name="Enabled", cron_expression="0 3 * * *", enabled=True)
        repo.create(id="sched-021", name="Disabled", cron_expression="0 3 * * *", enabled=False)
        enabled = repo.get_enabled()
        assert len(enabled) == 1
        assert enabled[0].enabled is True


class TestScheduleRepositoryGetByProfile:
    """Tests for ScheduleRepository.get_by_profile()"""

    def test_get_by_profile(self, repo: ScheduleRepository) -> None:
        """Test getting schedules by profile."""
        repo.create(id="sched-022", name="Dev", cron_expression="0 3 * * *", profile="developer")
        repo.create(
            id="sched-023", name="Admin", cron_expression="0 3 * * *", profile="system-admin"
        )
        entries = repo.get_by_profile("developer")
        assert len(entries) == 1
        assert entries[0].profile == "developer"
