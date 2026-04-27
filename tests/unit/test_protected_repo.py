# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for ProtectedRepository."""

from __future__ import annotations

import pytest

from dmlclean.exceptions.repository import DataError, DuplicateError
from dmlclean.storage.database import Database
from dmlclean.storage.protected_repo import ProtectedRepository


@pytest.fixture
def repo(db: Database) -> ProtectedRepository:
    """Create ProtectedRepository instance."""
    return ProtectedRepository(db)


class TestProtectedRepositoryCreate:
    """Tests for ProtectedRepository.create()"""

    def test_create_success(self, repo: ProtectedRepository) -> None:
        """Test successful protected path creation."""
        entry = repo.create(id="prot-001", path="/home/user/important")
        assert entry.id == "prot-001"
        assert entry.path == "/home/user/important"
        assert entry.is_glob is False

    def test_create_glob_pattern(self, repo: ProtectedRepository) -> None:
        """Test creating glob pattern."""
        entry = repo.create(id="prot-002", path="**/*.important", is_glob=True)
        assert entry.is_glob is True

    def test_create_duplicate_raises_error(self, repo: ProtectedRepository) -> None:
        """Test duplicate creation raises error."""
        repo.create(id="prot-003", path="/home/user/test")
        with pytest.raises(DuplicateError):
            repo.create(id="prot-004", path="/home/user/test")

    def test_create_empty_id_raises_error(self, repo: ProtectedRepository) -> None:
        """Test empty ID raises error."""
        with pytest.raises(DataError, match="ID cannot be empty"):
            repo.create(id="", path="/home/user/test")

    def test_create_empty_path_raises_error(self, repo: ProtectedRepository) -> None:
        """Test empty path raises error."""
        with pytest.raises(DataError, match="Path cannot be empty"):
            repo.create(id="prot-005", path="")


class TestProtectedRepositoryGet:
    """Tests for ProtectedRepository.get_by_id()"""

    def test_get_existing(self, repo: ProtectedRepository) -> None:
        """Test getting existing entry."""
        repo.create(id="prot-006", path="/home/user/test")
        entry = repo.get_by_id("prot-006")
        assert entry is not None
        assert entry.path == "/home/user/test"

    def test_get_nonexistent(self, repo: ProtectedRepository) -> None:
        """Test getting non-existent entry."""
        entry = repo.get_by_id("nonexistent")
        assert entry is None


class TestProtectedRepositoryGetByPath:
    """Tests for ProtectedRepository.get_by_path()"""

    def test_get_by_path_existing(self, repo: ProtectedRepository) -> None:
        """Test getting by existing path."""
        repo.create(id="prot-007", path="/home/user/test")
        entry = repo.get_by_path("/home/user/test")
        assert entry is not None
        assert entry.id == "prot-007"

    def test_get_by_path_nonexistent(self, repo: ProtectedRepository) -> None:
        """Test getting by non-existent path."""
        entry = repo.get_by_path("/nonexistent")
        assert entry is None


class TestProtectedRepositoryList:
    """Tests for ProtectedRepository.list_all()"""

    def test_list_empty(self, repo: ProtectedRepository) -> None:
        """Test listing when empty."""
        entries = repo.list_all()
        assert len(entries) == 0

    def test_list_with_entries(self, repo: ProtectedRepository) -> None:
        """Test listing with entries."""
        repo.create(id="prot-008", path="/home/user/test1")
        repo.create(id="prot-009", path="/home/user/test2")
        entries = repo.list_all()
        assert len(entries) == 2

    def test_list_glob_filter(self, repo: ProtectedRepository) -> None:
        """Test filtering by glob status."""
        repo.create(id="prot-010", path="/home/user/path", is_glob=False)
        repo.create(id="prot-011", path="**/*.glob", is_glob=True)
        entries = repo.list_all(is_glob=True)
        assert len(entries) == 1
        assert entries[0].is_glob is True


class TestProtectedRepositoryUpdate:
    """Tests for ProtectedRepository.update()"""

    def test_update_success(self, repo: ProtectedRepository) -> None:
        """Test successful update."""
        repo.create(id="prot-012", path="/home/user/test")
        result = repo.update("prot-012", description="Updated description")
        assert result is True
        entry = repo.get_by_id("prot-012")
        assert entry is not None
        assert entry.description == "Updated description"

    def test_update_nonexistent(self, repo: ProtectedRepository) -> None:
        """Test updating non-existent entry."""
        result = repo.update("nonexistent", description="Test")
        assert result is False

    def test_update_no_fields_raises_error(self, repo: ProtectedRepository) -> None:
        """Test updating with no fields."""
        repo.create(id="prot-013", path="/home/user/test")
        with pytest.raises(DataError, match="No valid fields"):
            repo.update("prot-013", invalid_field="value")


class TestProtectedRepositoryDelete:
    """Tests for ProtectedRepository.delete()"""

    def test_delete_success(self, repo: ProtectedRepository) -> None:
        """Test successful deletion."""
        repo.create(id="prot-014", path="/home/user/test")
        result = repo.delete("prot-014")
        assert result is True
        assert repo.get_by_id("prot-014") is None

    def test_delete_nonexistent(self, repo: ProtectedRepository) -> None:
        """Test deleting non-existent entry."""
        result = repo.delete("nonexistent")
        assert result is False


class TestProtectedRepositoryExists:
    """Tests for ProtectedRepository.exists()"""

    def test_exists_by_id(self, repo: ProtectedRepository) -> None:
        """Test exists by ID."""
        repo.create(id="prot-015", path="/home/user/test")
        assert repo.exists("prot-015") is True

    def test_exists_false(self, repo: ProtectedRepository) -> None:
        """Test exists returns False."""
        assert repo.exists("nonexistent") is False


class TestProtectedRepositoryExistsByPath:
    """Tests for ProtectedRepository.exists_by_path()"""

    def test_exists_by_path_true(self, repo: ProtectedRepository) -> None:
        """Test exists_by_path returns True."""
        repo.create(id="prot-016", path="/home/user/test")
        assert repo.exists_by_path("/home/user/test") is True

    def test_exists_by_path_false(self, repo: ProtectedRepository) -> None:
        """Test exists_by_path returns False."""
        assert repo.exists_by_path("/nonexistent") is False


class TestProtectedRepositoryCount:
    """Tests for ProtectedRepository.count()"""

    def test_count_empty(self, repo: ProtectedRepository) -> None:
        """Test count when empty."""
        assert repo.count() == 0

    def test_count_with_entries(self, repo: ProtectedRepository) -> None:
        """Test count with entries."""
        repo.create(id="prot-017", path="/home/user/test1")
        repo.create(id="prot-018", path="/home/user/test2")
        assert repo.count() == 2


class TestProtectedRepositoryClearAll:
    """Tests for ProtectedRepository.clear_all()"""

    def test_clear_all_success(self, repo: ProtectedRepository) -> None:
        """Test clearing all entries."""
        repo.create(id="prot-019", path="/home/user/test1")
        repo.create(id="prot-020", path="/home/user/test2")
        count = repo.clear_all()
        assert count == 2
        assert repo.count() == 0
