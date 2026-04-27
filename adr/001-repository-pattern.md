# ADR 001: Repository Pattern with Generic Type Support

**Date:** 2026-03-11  
**Status:** Accepted  
**Deciders:** DML Labs  
**Technical Story:** DMLClean v0.1.0 Architecture

---

## Context and Problem Statement

DMLClean v0.1.0 started with direct database access in CLI commands and core engine. This approach led to:

1. **Tight coupling** between business logic and data access
2. **Duplicated CRUD code** across different modules
3. **Difficult testing** - hard to mock database operations
4. **Inconsistent error handling** - ad-hoc exception handling throughout
5. **No clear abstraction** for data access layer

We needed a consistent pattern for data access that would:
- Provide clear separation of concerns
- Reduce code duplication
- Enable easy testing with mocks
- Standardize error handling
- Support future database migrations

---

## Decision Drivers

- **Modularity**: Clear separation between business logic and data access
- **Testability**: Easy to mock repositories for unit testing
- **Consistency**: Standard CRUD interface across all entities
- **Type Safety**: Full type hints with Generic type support
- **Extensibility**: Easy to add new entities and repositories
- **Error Handling**: Consistent exception hierarchy

---

## Considered Options

### Option 1: Active Record Pattern
Each model handles its own persistence (e.g., `HistoryEntry.save()`).

**Pros:**
- Simple, less code
- Intuitive for beginners

**Cons:**
- Tight coupling between models and database
- Harder to test
- Violates Single Responsibility Principle

### Option 2: Repository Pattern with Generic Base Class
Separate repository classes with a generic base class providing CRUD operations.

**Pros:**
- Clear separation of concerns
- Easy to test with mocks
- Consistent interface across repositories
- Type-safe with Generics

**Cons:**
- More boilerplate code
- Learning curve for team

### Option 3: Data Mapper Pattern (ORM)
Use SQLAlchemy or similar ORM for all data access.

**Pros:**
- Powerful query capabilities
- Database agnostic
- Auto-migrations via Alembic

**Cons:**
- Heavy dependency
- Performance overhead
- Learning curve
- Overkill for SQLite-only application

---

## Decision Outcome

**Chosen: Option 2 - Repository Pattern with Generic Base Class**

We will implement:

1. **Generic `Repository[T]` base class** in `storage/repository.py`
   - Abstract methods: `get_by_id()`, `list_all()`, `create()`, `update()`, `delete()`, `exists()`, `count()`
   - Type parameter `T` for entity type
   - Protocol `RepositoryProtocol[T]` for type hints

2. **Repository exception hierarchy** in `exceptions/repository.py`
   - `RepositoryError` (base)
   - `NotFoundError`
   - `DuplicateError`
   - `IntegrityError`
   - `DataError`
   - `OptimisticLockError`

3. **Concrete repositories** for each entity:
   - `HistoryRepository(Repository[HistoryEntry])`
   - `ScheduleRepository(Repository[ScheduleEntry])`
   - `ProtectedRepository(Repository[ProtectedPathEntry])`
   - `ManifestRepository(Repository[ManifestRecord])`
   - `TrendRepository(Repository[DiskTrendEntry])`

4. **Service Layer** to orchestrate repositories:
   - `HistoryService`
   - `ScheduleService`
   - `ProtectionService`
   - `PluginService`
   - `CleaningService`
   - `ReportService`

---

## Implementation Details

### Repository Base Class

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")

class Repository(ABC, Generic[T]):
    def __init__(self, model_class: type[T]) -> None:
        self.model_class = model_class

    @abstractmethod
    def get_by_id(self, id: str) -> T | None: ...

    @abstractmethod
    def list_all(self, limit: int = 100, offset: int = 0) -> list[T]: ...

    @abstractmethod
    def create(self, entity: T) -> str: ...

    @abstractmethod
    def update(self, id: str, **kwargs: Any) -> bool: ...

    @abstractmethod
    def delete(self, id: str) -> bool: ...

    @abstractmethod
    def exists(self, id: str) -> bool: ...

    @abstractmethod
    def count(self) -> int: ...
```

### Exception Hierarchy

```python
class RepositoryError(DMLCleanError): ...
class NotFoundError(RepositoryError): ...
class DuplicateError(RepositoryError): ...
class IntegrityError(RepositoryError): ...
class DataError(RepositoryError): ...
class OptimisticLockError(RepositoryError): ...
```

### Example Repository

```python
class HistoryRepository(Repository[HistoryEntry]):
    def __init__(self, db: Database) -> None:
        super().__init__(HistoryEntry)
        self.db = db

    def get_by_id(self, id: str) -> HistoryEntry | None:
        row = self.db.fetchone("SELECT * FROM history WHERE id = ?", (id,))
        return HistoryEntry.from_row(row) if row else None

    def create(self, entry: HistoryEntry) -> str:
        # ... validation ...
        with self.db.transaction():
            self.db.execute("INSERT INTO history ...", values)
        return entry.id
```

---

## Consequences

### Positive

- ✅ **Improved testability**: Repositories can be mocked in service tests
- ✅ **Consistent API**: All repositories follow same pattern
- ✅ **Type safety**: Full type hints with Generic support
- ✅ **Clear responsibilities**: Repositories handle data access, services handle business logic
- ✅ **Easy to extend**: Adding new entity requires only new repository class

### Negative

- ⚠️ **More boilerplate**: Each repository needs ~200-300 lines of CRUD code
- ⚠️ **Learning curve**: Team needs to understand Generic types and ABC
- ⚠️ **Initial development time**: Takes longer to implement than Active Record

### Risks

- **Risk**: Over-engineering for simple SQLite application
  - **Mitigation**: Start with minimal repositories, add more as needed
- **Risk**: Generic type complexity confuses team
  - **Mitigation**: Provide clear examples and documentation

---

## Compliance and Conformance

- Follows SOLID principles (Single Responsibility, Dependency Inversion)
- Aligns with Domain-Driven Design (DDD) repository pattern
- Compatible with Python typing system (PEP 484, 585)

---

## Notes

This decision enables the Service Layer pattern (ADR 002) and provides foundation for clean architecture.

---

## Related Decisions

- ADR 002: Service Layer for Domain Logic
- ADR 003: Plugin Discovery via GitHub Releases + Local Cache
- ADR 004: SQLite-Only Database Strategy

---

## References

- [Repository Pattern - Martin Fowler](https://martinfowler.com/eaaCatalog/repository.html)
- [Python Generic Types](https://docs.python.org/3/library/typing.html#typing.Generic)
- [Domain-Driven Design - Eric Evans](https://domainlanguage.com/ddd/)
