# Enterprise-Ready Storage Optimization & Lifecycle Orchestrator

**DML Clean is an enterprise-grade, module-driven framework engineered for automated system maintenance and storage lifecycle management. By leveraging a sophisticated Repository and Service-Layer architecture, DML Clean eliminates the unpredictability of traditional cleaning utilities.**

**The platform features an advanced "Safe-Trash" transaction logic with full undo capability, alongside granular Pydantic-validated configuration profiles for diverse workloads (Dev, Ops, Design). Built on a high-concurrency Python architecture with transactional SQLite persistence and an event-driven notification bus, DML Clean is engineered to empower organizations with the empirical data and deterministic safety required to optimize disk health and maintain infrastructure productivity at scale.**

[![PyPI version](https://img.shields.io/pypi/v/dmlclean.svg)](https://pypi.org/project/dmlclean/)
[![Python versions](https://img.shields.io/pypi/pyversions/dmlclean.svg)](https://pypi.org/project/dmlclean/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-yellow.svg)](https://opensource.org/licenses/Apache-2.0)

---

## Welcome to the DML Clean Documentation

DML Clean is an enterprise-grade, module-driven framework engineered for automated system maintenance and storage lifecycle management. By leveraging a sophisticated Repository and Service-Layer architecture, DML Clean eliminates the unpredictability of traditional cleaning utilities.

- 🗑️ System junk files (temp files, logs, crash reports)
- 🌐 Browser cache (Chrome, Edge, Firefox, Safari)
- 🐍 Python development artifacts (`__pycache__`, `.pytest_cache`, etc.)
- 🟢 Node.js artifacts (`node_modules/`, `.next/`, etc.)
- ☕ Java build output (Gradle, Maven)
- 🦀 Rust/C++ build artifacts
- 💻 IDE cache (VS Code, JetBrains)
- 🎮 Gaming cache (Steam, Epic, NVIDIA)
- 🎨 Media cache (Adobe, Blender)
- 💬 Messaging cache (Discord, Telegram, Zoom)
- 🤖 AI/ML cache (HuggingFace, PyTorch)
- ☁️ Cloud sync cache (OneDrive, Google Drive)

---

## Key Features

### 🔍 Smart Scanning
- **Fast mode**: Quick scan of common locations (default)
- **Deep mode**: Comprehensive scan with full recursion
- **Custom mode**: User-defined scan parameters

### 🛡️ Safety First
- **Protected Zone**: Never touch critical files (bookmarks, passwords, .git, etc.)
- **Dry-run default**: Always preview before deletion
- **Trash mode**: Recoverable deletion with undo support
- **Manifest logging**: Complete audit trail of all operations

### 📅 Automation
- **Scheduled cleaning**: Cron-based automation
- **Native integration**: Exports to cron (Linux/macOS) or Task Scheduler (Windows)
- **Desktop notifications**: Get notified when cleaning completes

### 📊 Rich Reporting
- **Terminal dashboards**: Beautiful Rich-formatted output
- **JSON/CSV/HTML export**: Generate reports for compliance
- **History tracking**: View and undo past operations

### 🔌 Extensible
- **Plugin system**: Extend with custom cleaning categories
- **GitHub registry**: Discover and install community plugins
- **Profiles**: Pre-configured settings for different user types

---

## Quick Start

### Installation

```bash
# Recommended: pipx (isolated installation)
pipx install dmlclean

# Alternative: pip
pip install dmlclean
```

### Basic Usage

```bash
# 1. Scan (dry-run by default)
dmlclean scan

# 2. Clean (preview first)
dmlclean clean --mode dry-run

# 3. Execute cleaning
dmlclean clean --mode trash

# 4. View history
dmlclean history list

# 5. Undo last operation
dmlclean history undo
```

---

## Documentation Structure

### User Guide
- **[Installation](installation.md)**: Install DMLClean on Windows, macOS, or Linux
- **[Quick Start](QUICKSTART.md)**: Get started in 5 minutes
- **[CLI Commands](cli-commands.md)**: Complete command reference
- **[Configuration](config.md)**: Customize DMLClean behavior

### Developer Guide
- **[Architecture](ARCHITECTURE.md)**: System architecture overview
- **[Repository Pattern](repositories.md)**: Data access layer design
- **[Service Layer](services.md)**: Business logic organization
- **[Plugin System](plugins.md)**: Extend DMLClean with plugins
- **[API Reference](api/repositories.md)**: Auto-generated API docs

### Contributing
- **[Contributing](CONTRIBUTING.md)**: How to contribute
- **[Code of Conduct](CODE_OF_CONDUCT.md)**: Community standards
- **[Security](SECURITY.md)**: Report vulnerabilities

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Layer (Typer)                       │
│  scan | clean | schedule | config | protect | history | ... │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│  CleaningService | HistoryService | ScheduleService | ...   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Repository Layer                            │
│  HistoryRepository | ScheduleRepository | ProtectedRepo |.. │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Storage Layer                              │
│  SQLite Database + File System                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Support

- **Documentation**: https://dmlclean.github.io
- **Issues**: https://github.com/dmlclean/dmlclean/issues
- **Discussions**: https://github.com/dmlclean/dmlclean/discussions
- **PyPI**: https://pypi.org/project/dmlclean/

---

## License

**Apache License 2.0** - See [LICENSE](LICENSE) for details.

---

*Built with ❤️ by DML Labs*
