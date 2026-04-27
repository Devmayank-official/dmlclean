# Enterprise-Ready Storage Optimization & Lifecycle Orchestrator Architecture

## Overview

DML Clean is an enterprise-grade, module-driven framework engineered for automated system maintenance and storage lifecycle management. By leveraging a sophisticated Repository and Service-Layer architecture, DML Clean eliminates the unpredictability of traditional cleaning utilities.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Layer (Typer)                       │
│  scan | clean | schedule | config | protect | history | ... │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Core Engine Layer                         │
│  Scanner → Analyzer → Pipeline → Cleaner → Reporter         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Plugin Layer                              │
│  system_junk | browser | dev_python | dev_node | ...        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Safety Layer                              │
│  Protected Zone → Manifest → Undo Manager                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Storage Layer                              │
│  SQLite Database + File System                              │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
src/dmlclean/
├── cli/              # CLI commands (Typer application)
│   ├── commands/     # Individual command modules
│   ├── formatters/   # Output formatters (table, JSON, plain)
│   └── middleware/   # Error handling, update checks
├── config/           # Configuration management
├── constants/        # Application constants
├── core/             # Core engine
│   ├── scanner.py    # Async file system scanner
│   ├── analyzer.py   # Categorization and risk classification
│   ├── cleaner.py    # Deletion executor
│   ├── pipeline.py   # Orchestration
│   └── scheduler.py  # APScheduler integration
├── exceptions/       # Custom exception hierarchy
├── models/           # Pydantic data models
├── notifications/    # Desktop notifications
├── plugins/          # Cleaning plugins
├── reports/          # Report generation
├── safety/           # Safety mechanisms
│   ├── protected_zone.py
│   ├── manifest.py
│   └── undo.py
├── storage/          # SQLite persistence
│   ├── database.py
│   ├── paths.py
│   └── migrations/
└── utils/            # Utility functions
```

## Key Design Decisions

### 1. Async-First Scanner

The scanner uses async I/O for maximum performance:

```python
async def scan(self, roots: list[Path]) -> ScanResult:
    # Non-blocking file system operations
    ...
```

### 2. Plugin Architecture

All cleaning categories are implemented as plugins:

```python
class BasePlugin(ABC):
    @abstractmethod
    def scan(self, paths: list[Path]) -> list[CleanCandidate]:
        ...
```

### 3. Safety First

Every deletion goes through multiple safety checks:

1. **Protected Zone** - Check if path is protected
2. **Dry-Run Preview** - Show what would be deleted
3. **Manifest Logging** - Record all deletions
4. **Undo Support** - Restore from trash

### 4. Unified Storage Paths

All data stored under `~/DML Labs/DML Clean/`:

```python
STORAGE_BASE = Path.home() / "DML Labs" / "DML Clean"
```

## Data Flow

### Scan Operation

```
User → CLI → Scanner → Analyzer → Report
```

### Clean Operation

```
User → CLI → Scan → Protected Zone Check → Manifest → Cleaner → History
```

### Schedule Operation

```
User → CLI → Scheduler → APScheduler → Callback → Pipeline
```

## Testing Strategy

- **Unit Tests**: Individual modules (pyfakefs for file system)
- **Integration Tests**: Module interactions
- **E2E Tests**: Full CLI workflows

## Dependencies

| Category | Packages |
|----------|----------|
| CLI | typer, rich, click |
| Async | aiofiles, asyncio |
| Database | sqlite3 (stdlib) |
| Scheduling | apscheduler, croniter |
| Notifications | desktop-notifier, plyer |
| Utilities | platformdirs, psutil, send2trash, xxhash |

---

*For more details, see individual module docstrings.*
