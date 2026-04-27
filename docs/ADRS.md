# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records for DMLClean.

## ADR Index

| Number | Title | Status | Date |
|--------|-------|--------|------|
| [ADR-001](#adr-001-dependency-injection-container) | Dependency Injection Container | ✅ Accepted | 2026-03-11 |
| [ADR-002](#adr-002-unit-of-work-pattern) | Unit of Work Pattern | ✅ Accepted | 2026-03-11 |
| [ADR-003](#adr-003-domain-events-system) | Domain Events System | ✅ Accepted | 2026-03-11 |
| [ADR-004](#adr-004-repository-protocol-abstraction) | Repository Protocol Abstraction | ⏳ Proposed | 2026-03-11 |
| [ADR-005](#adr-005-service-layer-enrichment) | Service Layer Enrichment | ⏳ Proposed | 2026-03-11 |

---

## ADR-001: Dependency Injection Container

**Status:** ✅ Accepted  
**Date:** March 11, 2026  
**Author:** DML Labs Architecture Team  

### Context

DMLClean services were instantiating their own dependencies directly:

```python
class CleaningService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.history_service = HistoryService(db)  # Hardcoded
        self.scanner = FileSystemScanner()         # Hardcoded
```

This created several problems:
1. **Hard to Test** - Couldn't mock dependencies without patching
2. **Tight Coupling** - Services knew about concrete implementations
3. **Configuration Scattering** - Dependency setup code duplicated everywhere
4. **Unclear Dependencies** - Hard to see the full dependency graph

### Decision

Implement a **Dependency Injection (DI) Container** pattern:

```python
class Container:
    """Centralized dependency management."""
    
    db: Database
    config: ConfigLoader
    scanner: FileSystemScanner
    analyzer: Analyzer
    # ... all dependencies
    
    @classmethod
    def create(cls) -> "Container":
        """Factory method to create fully-configured container."""
        # Initialize all dependencies here
        ...
    
    @cached_property
    def cleaning_service(self) -> CleaningService:
        """Lazy-initialized service."""
        return CleaningService(self)
```

**Usage:**
```python
# Application startup
container = Container.create()

# Access services
service = container.cleaning_service

# Access repositories
repo = container.history_repo

# Cleanup
container.close()
```

### Consequences

#### Positive ✅
- **Single Configuration Point** - All dependencies configured in one place
- **Easy Testing** - Mock container or inject test doubles
- **Clear Dependencies** - Container shows full dependency graph
- **Lazy Loading** - `@cached_property` for performance
- **Consistent Lifecycle** - Container manages initialization and cleanup

#### Negative ⚠️
- **Learning Curve** - Team must understand DI pattern
- **Slight Overhead** - One extra layer of indirection
- **Container Dependency** - Code depends on `Container` class

#### Mitigation
- Provide clear documentation and examples
- Use type hints for IDE autocomplete
- Keep container interface simple and intuitive

### Implementation

- **File:** `src/dmlclean/container.py`
- **Lines:** 320
- **Status:** ✅ Implemented

### References

- [Dependency Injection Pattern](https://en.wikipedia.org/wiki/Dependency_injection)
- [Python Dependency Injection](https://realpython.com/dependency-injection-python/)

---

## ADR-002: Unit of Work Pattern

**Status:** ✅ Accepted  
**Date:** March 11, 2026  
**Author:** DML Labs Architecture Team  

### Context

DMLClean had multiple repositories (History, Manifest, Schedule, etc.) but no way to coordinate transactions across them:

```python
# In service layer
with db.transaction():
    history_repo.create(entry)
    # If this fails, manifest is left in inconsistent state
    manifest_repo.create(manifest)
```

Problems:
1. **No Atomic Operations** - Multi-repo changes weren't atomic
2. **Transaction Scattering** - Transaction logic in every service
3. **Error-Prone** - Easy to forget transaction boundaries
4. **Hard to Test** - Transaction logic mixed with business logic

### Decision

Implement the **Unit of Work (UoW) Pattern**:

```python
class UnitOfWork:
    """Atomic multi-repository operations."""
    
    history: HistoryRepository
    manifest: ManifestRepository
    protected: ProtectedRepository
    schedule: ScheduleRepository
    trend: TrendRepository
    
    @contextmanager
    def commit(self) -> Generator[UnitOfWork, None, None]:
        """Execute operations atomically."""
        try:
            yield self
            self.db._connection.commit()
        except Exception:
            self.db._connection.rollback()
            raise
```

**Usage:**
```python
with UnitOfWork(db).commit() as uow:
    uow.history.create(entry)
    uow.manifest.create(manifest)
    uow.protected.add(path)
    # All commit atomically, or all rollback on error
```

### Consequences

#### Positive ✅
- **Atomic Operations** - All-or-nothing transaction semantics
- **Clear Boundaries** - Transaction scope is explicit
- **Consistent Error Handling** - Automatic rollback on failure
- **All Repositories Available** - Single context for all data access
- **Testable** - Easy to test transaction boundaries

#### Negative ⚠️
- **Additional Abstraction** - One more layer to understand
- **Repository Coupling** - UoW knows about all repositories
- **SQLite-Specific** - Implementation tied to SQLite transactions

#### Mitigation
- Provide clear documentation and examples
- Use type hints for IDE support
- Consider abstracting transaction backend in future

### Implementation

- **File:** `src/dmlclean/storage/uow.py`
- **Lines:** 205
- **Status:** ✅ Implemented

### References

- [Unit of Work Pattern](https://martinfowler.com/eaaCatalog/unitOfWork.html)
- [Patterns of Enterprise Application Architecture](https://martinfowler.com/eaaCatalog/)

---

## ADR-003: Domain Events System

**Status:** ✅ Accepted  
**Date:** March 11, 2026  
**Author:** DML Labs Architecture Team  

### Context

DMLClean had no way to observe domain occurrences:

```python
class CleaningService:
    def execute_clean(self, ...) -> dict[str, Any]:
        # ... cleaning logic
        return result  # No way to observe this happened
```

Problems:
1. **Tight Coupling** - Services had to call notifications, logging, metrics directly
2. **Hard to Extend** - Adding side effects required modifying core logic
3. **No Auditing** - Couldn't easily track what happened in the system
4. **Violation of SRP** - Services doing too much (cleaning + logging + notifications)

### Decision

Implement a **Domain Events System**:

```python
# Define events
@dataclass
class CleanOperationCompleted(DomainEvent):
    operation_id: str
    files_deleted: int
    size_bytes: int
    duration_ms: int
    # ...

# Publish events (automatic in services)
EventBus.publish(CleanOperationCompleted(...))

# Subscribe to events
@event_handler(CleanOperationCompleted)
def log_clean(event: CleanOperationCompleted) -> None:
    logger.info(f"Cleaned {event.files_deleted} files")

@event_handler(CleanOperationCompleted)
def notify_user(event: CleanOperationCompleted) -> None:
    Notifier.send(f"Freed {humanize_size(event.size_bytes)}")
```

**Events Defined:**
1. `CleanOperationCompleted`
2. `CleanOperationFailed`
3. `ProtectedPathAdded`
4. `ProtectedPathRemoved`
5. `ScheduleCreated`
6. `ScheduleExecuted`
7. `UndoPerformed`

### Consequences

#### Positive ✅
- **Decoupled Architecture** - Services don't know about observers
- **Easy to Extend** - Add handlers without modifying core logic
- **Follows Open/Closed Principle** - Open for extension, closed for modification
- **Auditing Support** - Easy to add audit logging
- **Testable** - Events can be captured and verified in tests

#### Negative ⚠️
- **Eventual Consistency** - Handlers run asynchronously (if we make them async)
- **Debugging Complexity** - Harder to trace event flow
- **Performance Overhead** - Event dispatch adds latency
- **Memory Usage** - In-memory event bus holds handler references

#### Mitigation
- Keep handlers synchronous for now (can make async later)
- Add logging to event dispatch for debugging
- Monitor performance impact
- Clear handler lifecycle management

### Implementation

- **File:** `src/dmlclean/domain/events.py`
- **Lines:** 445
- **Status:** ✅ Implemented

### References

- [Domain Events Pattern](https://martinfowler.com/eaaCatalog/DomainEvent.html)
- [Event-Driven Architecture](https://en.wikipedia.org/wiki/Event-driven_architecture)

---

## ADR-004: Repository Protocol Abstraction

**Status:** ⏳ Proposed  
**Date:** March 11, 2026  
**Author:** DML Labs Architecture Team  

### Context

Repositories currently depend on concrete `Database` class:

```python
class HistoryRepository:
    def __init__(self, db: Database) -> None:
        self.db = db  # Depends on concrete class
```

This makes it hard to:
- Swap database implementations
- Test with in-memory stores
- Mock for unit tests

### Decision (Proposed)

Define **Repository Protocols** (interfaces):

```python
class DatabaseProtocol(Protocol):
    """Protocol for database operations."""
    
    def execute(self, query: str, params: Any | None = ...) -> sqlite3.Cursor:
        ...
    
    def fetchone(self, query: str, params: Any | None = ...) -> sqlite3.Row | None:
        ...
    
    @contextmanager
    def transaction(self) -> Generator[None, None, None]:
        ...

class HistoryRepository:
    def __init__(self, db: DatabaseProtocol) -> None:
        self.db = db  # Depends on protocol
```

### Consequences (Expected)

#### Positive ✅
- **Dependency Inversion** - Depend on abstractions, not concretions
- **Testability** - Easy to mock database
- **Swappable Implementations** - Can swap SQLite for PostgreSQL, etc.
- **Clear Interface** - Protocol defines exact database contract

#### Negative ⚠️
- **Additional Complexity** - One more abstraction layer
- **Type Checking Overhead** - More mypy configuration needed
- **Limited Benefit Now** - Only using SQLite currently

### Status

**Deferred** until we need multiple database backends or better test mocking.

---

## ADR-005: Service Layer Enrichment

**Status:** ⏳ Proposed  
**Date:** March 11, 2026  
**Author:** DML Labs Architecture Team  

### Context

Services are currently thin wrappers around repositories:

```python
class ProtectionService:
    def add_protection(self, path: str, ...) -> ProtectedPathEntry:
        # Just calls repo directly
        return self.protected_repo.create(...)
```

Domain logic should live in services, not repositories.

### Decision (Proposed)

**Enrich services with domain logic:**

```python
class ProtectionService:
    def add_protection(self, path: str, description: str = "", is_glob: bool = False) -> ProtectedPathEntry:
        """
        Add a protected path with full validation.
        
        Domain Logic:
        1. Validate path exists (warn if not)
        2. Normalize path (resolve symlinks, absolute)
        3. Check for conflicts (subpath of existing protection)
        4. Check for immutables (can't protect C:\Windows)
        5. Create entry
        """
        # 1. Validate and normalize
        path_obj = Path(path)
        if not path_obj.exists():
            logger.warning(f"Path does not exist: {path}")
        
        normalized_path = str(path_obj.resolve())
        
        # 2. Check for conflicts
        existing = self.protected_repo.list_all()
        for entry in existing:
            if self._is_subpath_of(normalized_path, entry.path):
                raise ProtectedZoneError(
                    f"Path {normalized_path} is already protected by {entry.path}"
                )
        
        # 3. Check immutables
        if self._is_immutable_path(normalized_path):
            raise ImmutableProtectionError(
                f"Cannot protect immutable path: {normalized_path}"
            )
        
        # 4. Create entry
        return self.protected_repo.create(
            id=str(uuid.uuid4()),
            path=normalized_path,
            description=description,
            is_glob=is_glob,
        )
```

### Consequences (Expected)

#### Positive ✅
- **Rich Domain Logic** - Business rules in services, not repos
- **Validation** - Input validation before repository calls
- **Consistency** - All services follow same pattern
- **Testable** - Domain logic easy to test in isolation

#### Negative ⚠️
- **More Code** - Services become larger
- **Potential Duplication** - Some validation logic might duplicate
- **Performance** - Extra validation adds latency

### Status

**In Progress** - Will be implemented in Phase 2.

---

**Last Updated:** March 11, 2026  
**Version:** 0.1.0-alpha  

---

*These ADRs are living documents. Update them as the architecture evolves.*
