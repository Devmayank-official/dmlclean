# DMLClean Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-12

### Initial Production Release

#### Added
- **Core Architecture**
  - Dependency Injection Container with lazy initialization
  - Repository Pattern with full CRUD operations
  - Unit of Work pattern for atomic transactions
  - Domain Events (EventBus) for decoupled communication
  - Service Layer with DTO-based APIs
  - Plugin System with 14 built-in cleaning plugins

- **CLI Layer**
  - 13 Typer-based commands (scan, clean, schedule, config, protect, history, report, doctor, profile, plugin, storage, trends, system)
  - Error handling middleware with Rich panels
  - Update check middleware (background PyPI version check)
  - Shell completions (bash, zsh, fish, PowerShell)
  - Output formatters (Strategy Pattern: table, JSON, plain)
  - CLI context/state management with persistence

- **Core Engine**
  - Async FileSystemScanner with ThreadPoolExecutor
  - PluginScanner with lazy loading and parallel execution
  - Analyzer with regex patterns for 14 categories
  - Cleaner with dry-run/trash/permanent modes
  - Pipeline orchestration (scan→analyze→clean)
  - APScheduler integration with SQLite persistence
  - Deduplicator with xxhash fingerprinting

- **Safety Layer**
  - Protected Zone with glob pattern matching
  - DeletionManifest with xxhash fingerprinting
  - UndoManager for trash restoration
  - Immutable system path protection

- **Storage Layer**
  - SQLite database with WAL mode
  - Database migrations (3 migration files)
  - Repository implementations (History, Manifest, Schedule, Protected, Trend)
  - Cross-platform path resolution (~/DML Labs/DML Clean/)

- **Data Models**
  - Pydantic v2 models for all entities
  - Request/Result DTOs for type-safe service APIs
  - Frozen models for immutability

- **Configuration**
  - TOML-based configuration with validation
  - Environment variable overrides
  - 5 built-in profiles (developer, designer, system-admin, gamer, minimal)
  - 14 cleaning category configurations

- **Notifications**
  - Event-driven notification handlers
  - Layered backend (desktop-notifier → plyer → graceful degradation)
  - Auto-notifications for clean complete, errors, protected zone violations

- **Exception Handling**
  - Hierarchical exception classes
  - Proper exit codes (0=success, 1=error, 2=config, 3=partial)
  - Rich traceback formatting

- **Documentation**
  - README.md with features and quickstart
  - ROADMAP.md (v0.1→v1.0)
  - ARCHITECTURE.md with system overview
  - SECURITY.md with security policy
  - CONTRIBUTING.md with contribution guidelines

- **Testing**
  - Unit tests (50+ test cases)
  - Integration tests for v2 architecture
  - Pytest fixtures for fake filesystem, database, repositories
  - 60%+ code coverage target

- **DevOps**
  - CI/CD pipeline (7-job GitHub Actions workflow)
  - Docker multi-stage build (4 stages)
  - PyInstaller binary builds
  - Pre-commit hooks (ruff, mypy, bandit)
  - Nox test automation

#### Security
- Protected Zone blocks critical paths by default
- Browser data (bookmarks, passwords, cookies) never touched
- Git directories always protected
- Virtual environments protected
- Manifest logging for audit trail
- No network calls (zero telemetry, air-gapped compatible)

#### Technical Stack
- Python 3.11+ required
- Typer for CLI
- Rich for terminal output
- Pydantic v2 for validation
- SQLite for persistence
- APScheduler for scheduling
- desktop-notifier + plyer for notifications

---

## [Unreleased]

### Planned for v0.2.0 (Beta)
- [ ] Plugin marketplace for third-party plugins
- [ ] Cloud storage cleaning (Google Drive, Dropbox, OneDrive)
- [ ] GUI/TUI application
- [ ] Incremental scanning with caching
- [ ] Real-time disk usage monitoring

---

**Note**: This is the initial production release (v0.1.0) with all critical architecture components complete.
