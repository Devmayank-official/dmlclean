# DMLClean CLI Reference

Complete reference for all DMLClean commands and options.

**Version:** 0.1.0  
**Last Updated:** March 2026

---

## 📋 Table of Contents

- [Quick Reference](#quick-reference)
- [Global Options](#global-options)
- [Commands](#commands)
  - [`scan`](#scan) - Scan for cleanable files
  - [`clean`](#clean) - Execute cleaning operation
  - [`schedule`](#schedule) - Manage scheduled cleaning
  - [`config`](#config) - Manage configuration
  - [`protect`](#protect) - Manage Protected Zone
  - [`history`](#history) - View/undo operations
  - [`report`](#report) - Generate reports
  - [`doctor`](#doctor) - System diagnostics
  - [`profile`](#profile) - Profile management
  - [`plugin`](#plugin) - Plugin management
  - [`storage`](#storage) - Storage management
  - [`trends`](#trends) - Disk usage trends
  - [`system`](#system) - Version and self-update

---

## Quick Reference

```bash
# Basic scan
dmlclean scan

# Scan specific paths
dmlclean scan --path /tmp --path ~/.cache

# Deep scan with JSON output
dmlclean scan --mode deep --json

# Preview cleaning (dry-run)
dmlclean clean

# Clean with trash mode
dmlclean clean --mode trash

# Clean specific categories
dmlclean clean --categories browser,dev_python --mode trash

# Use a profile
dmlclean clean --profile developer --mode trash

# View history
dmlclean history list

# Undo last operation
dmlclean history undo

# Add protected path
dmlclean protect add ~/important-project

# Generate report
dmlclean report --format html --output report.html

# System diagnostics
dmlclean doctor
```

---

## Global Options

These options are available for all commands:

| Option | Short | Description |
|--------|-------|-------------|
| `--version` | `-v` | Show version and exit |
| `--verbose` | `-V` | Enable debug logging |
| `--quiet` | `-q` | Suppress all output except errors |
| `--config` | `-c` | Override config file location |
| `--help` | `-h` | Show help message |

### Examples

```bash
# Show version
dmlclean --version

# Enable verbose logging
dmlclean scan --verbose

# Quiet mode (cron-friendly)
dmlclean clean --quiet --mode trash

# Use custom config
dmlclean scan --config /path/to/custom.toml
```

---

## Commands

### `scan`

Scan for cleanable files.

#### Synopsis

```bash
dmlclean scan [OPTIONS]
```

#### Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--mode` | `-m` | `fast` | Scan mode: `fast`, `deep`, or `custom` |
| `--categories` | `-c` | all | Comma-separated categories to scan |
| `--path` | `-p` | platform defaults | Paths to scan (repeatable) |
| `--json` | | `false` | Output in JSON format |
| `--quiet` | `-q` | `false` | Suppress output |

#### Scan Modes

- **fast** (default) - Quick scan of common locations
- **deep** - Comprehensive scan including nested directories
- **custom** - Use custom configuration

#### Categories

Available categories:
- `system_junk` - OS temp files, logs, crash reports
- `browser` - Browser cache (Chrome, Edge, Firefox, Safari)
- `dev_python` - Python cache (`__pycache__`, `.pytest_cache`)
- `dev_node` - Node.js artifacts (`node_modules/`, `.next/`)
- `dev_java` - Java build artifacts (Gradle, Maven)
- `dev_rust_cpp` - Rust/C++ build artifacts
- `ide` - IDE cache (VS Code, JetBrains)
- `gaming` - Game launcher cache (Steam, Epic)
- `media` - Media editor cache (Adobe, Blender)
- `messaging` - Chat app cache (Discord, Slack, Zoom)
- `ai_ml` - ML framework cache (HuggingFace, PyTorch)
- `cloud_sync` - Cloud storage cache (OneDrive, Dropbox)
- `package_mgr` - Package manager cache (pip, npm, apt)
- `smart_scan` - Large files, duplicates, empty dirs

#### Examples

```bash
# Fast scan of default locations
dmlclean scan

# Deep scan
dmlclean scan --mode deep

# Scan specific paths
dmlclean scan --path /tmp --path ~/.cache

# Scan specific categories
dmlclean scan --categories browser,dev_python

# JSON output
dmlclean scan --json > scan-results.json

# Deep scan with JSON output
dmlclean scan --mode deep --categories all --json > results.json
```

#### Output Example

```
┌─────────────────────────────────────────┐
│ 🔍 Scan in Progress                     │
├─────────────────────────────────────────┤
│ Scanning 3 paths...                     │
│ Mode: fast | Categories: all            │
└─────────────────────────────────────────┘

✓ Scan Complete
Mode: fast | Files: 1,247 | Size: 456.78 MB

By Category:
┏━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┓
┃ Category     ┃ Files   ┃ Size     ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━┩
│ browser      │ 523     │ 234.56 MB│
│ dev_python   │ 312     │ 123.45 MB│
│ system_junk  │ 245     │ 67.89 MB │
│ ide          │ 167     │ 30.88 MB │
└──────────────┴─────────┴──────────┘

By Risk Level:
┏━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┓
┃ Risk Level   ┃ Files   ┃ Size     ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━┩
│ 🟢 LOW       │ 847     │ 345.67 MB│
│ 🟡 MEDIUM    │ 312     │ 89.12 MB │
│ 🔴 HIGH      │ 88      │ 21.99 MB │
└──────────────┴─────────┴──────────┘

Total: 1,247 candidates, 456.78 MB
Run 'dmlclean clean' to execute cleaning.
```

---

### `clean`

Execute cleaning operation.

#### Synopsis

```bash
dmlclean clean [OPTIONS]
```

#### Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--mode` | `-m` | `dry-run` | Clean mode: `dry-run`, `trash`, `permanent` |
| `--profile` | `-p` | `developer` | Cleaning profile |
| `--categories` | `-c` | all | Categories to clean |
| `--min-age` | | `0` | Only clean files older than N days |
| `--min-size` | | `0` | Only clean files larger than N MB |
| `--force` | `-f` | `false` | Skip confirmation (required for permanent) |
| `--yes` | `-y` | `false` | Skip confirmation prompts |
| `--path` | | platform defaults | Paths to clean |

#### Clean Modes

- **dry-run** (default) - Preview what would be deleted (no changes)
- **trash** - Move files to OS Trash (recoverable, supports undo)
- **permanent** - Permanently delete files (requires `--force`, no undo)

#### Cleaning Profiles

Built-in profiles:
- **developer** - Safe for development work (default)
- **designer** - Safe for design/media work
- **system-admin** - Aggressive cleaning
- **gamer** - Safe for gaming setups
- **minimal** - Minimal cleaning

#### Examples

```bash
# Preview (dry-run)
dmlclean clean

# Preview specific categories
dmlclean clean --categories browser,dev_python

# Trash mode
dmlclean clean --mode trash

# Trash mode with profile
dmlclean clean --mode trash --profile developer

# Trash mode with specific categories
dmlclean clean --mode trash --categories browser,dev_python

# Permanent mode (requires --force)
dmlclean clean --mode permanent --force

# Skip confirmation
dmlclean clean --mode trash --yes

# Only clean old files
dmlclean clean --mode trash --min-age 30

# Only clean large files
dmlclean clean --mode trash --min-size 100
```

#### Output Example

```
Starting cleaning... Mode=trash

┌─────────────────────────────────────────┐
│ ✓ Cleaning Complete                     │
├─────────────────────────────────────────┤
│ Operation ID: abc123...                 │
│ Mode: trash                             │
│ Profile: developer                      │
│ Files Deleted: 1,247                    │
│ Files Failed: 0                         │
│ Files Skipped: 23                       │
│ Total Size Freed: 456.78 MB             │
│ Duration: 2,345ms                       │
└─────────────────────────────────────────┘

Manifest ID: manifest-abc123
Use 'dmlclean history undo' to restore if needed.
```

#### Safety Features

1. **Protected Zone** - Critical files are never deleted
2. **Dry-Run Default** - Always preview first
3. **Manifest Logging** - All deletions are logged
4. **Undo Support** - Restore from trash operations
5. **Confirmation Prompts** - Required for large deletions

---

### `schedule`

Manage scheduled cleaning jobs.

#### Synopsis

```bash
dmlclean schedule [OPTIONS] COMMAND [ARGS]...
```

#### Subcommands

| Command | Description |
|---------|-------------|
| `list` | List all scheduled jobs |
| `add` | Add a new scheduled job |
| `remove` | Remove a scheduled job |
| `enable` | Enable a job |
| `disable` | Disable a job |
| `run` | Run a job manually |

#### Examples

```bash
# List all schedules
dmlclean schedule list

# Add daily cleaning at 2 AM
dmlclean schedule add --name "Daily Clean" --cron "0 2 * * *" --mode trash

# Add weekly cleaning (every Sunday at 3 AM)
dmlclean schedule add --name "Weekly Deep Clean" --cron "0 3 * * 0" --mode trash --profile developer

# Remove a schedule
dmlclean schedule remove "Daily Clean"

# Disable a schedule
dmlclean schedule disable "Daily Clean"

# Enable a schedule
dmlclean schedule enable "Daily Clean"

# Run a schedule manually
dmlclean schedule run "Daily Clean"
```

---

### `config`

Manage configuration.

#### Synopsis

```bash
dmlclean config [OPTIONS] COMMAND [ARGS]...
```

#### Subcommands

| Command | Description |
|---------|-------------|
| `show` | Show current configuration |
| `edit` | Edit configuration file |
| `path` | Show config file path |
| `reset` | Reset to defaults |
| `validate` | Validate configuration |

#### Examples

```bash
# Show current config
dmlclean config show

# Show config file path
dmlclean config path

# Edit config (opens in editor)
dmlclean config edit

# Reset to defaults
dmlclean config reset

# Validate config
dmlclean config validate
```

---

### `protect`

Manage Protected Zone.

#### Synopsis

```bash
dmlclean protect [OPTIONS] COMMAND [ARGS]...
```

#### Subcommands

| Command | Description |
|---------|-------------|
| `list` | List all protected paths |
| `add` | Add a protected path |
| `remove` | Remove a protected path |
| `check` | Check if a path is protected |

#### Examples

```bash
# List protected paths
dmlclean protect list

# Add a protected path
dmlclean protect add ~/important-project

# Add with glob pattern
dmlclean protect add "**/*.env" --glob

# Remove a protected path
dmlclean protect remove ~/important-project

# Check if path is protected
dmlclean protect check ~/important-project
```

---

### `history`

View and undo cleaning operations.

#### Synopsis

```bash
dmlclean history [OPTIONS] COMMAND [ARGS]...
```

#### Subcommands

| Command | Description |
|---------|-------------|
| `list` | List cleaning history |
| `undo` | Undo last operation |
| `show` | Show operation details |
| `export` | Export history |
| `clear` | Clear history |

#### Examples

```bash
# List history
dmlclean history list

# Show last 20 operations
dmlclean history list --limit 20

# Undo last operation
dmlclean history undo

# Show operation details
dmlclean history show <operation-id>

# Export history
dmlclean history export history.json

# Clear history
dmlclean history clear --older-than 30d
```

---

### `report`

Generate reports.

#### Synopsis

```bash
dmlclean report [OPTIONS]
```

#### Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--format` | `-f` | `terminal` | Output format: `terminal`, `json`, `csv`, `html` |
| `--output` | `-o` | stdout | Output file path |
| `--days` | `-d` | `30` | Days of history to include |
| `--include-trends` | | `true` | Include trend data |
| `--include-breakdowns` | | `true` | Include category breakdowns |

#### Examples

```bash
# Terminal report
dmlclean report

# JSON report
dmlclean report --format json --output report.json

# HTML report
dmlclean report --format html --output report.html

# CSV report
dmlclean report --format csv --output report.csv

# Last 7 days
dmlclean report --days 7

# Without trends
dmlclean report --no-trends
```

---

### `doctor`

System diagnostics.

#### Synopsis

```bash
dmlclean doctor [OPTIONS]
```

#### Examples

```bash
# Run diagnostics
dmlclean doctor

# Verbose output
dmlclean doctor --verbose

# JSON output
dmlclean doctor --json
```

#### Checks Performed

- Python version
- Dependencies
- Configuration file
- Database integrity
- Storage directories
- Permissions
- Plugin availability

---

### `profile`

Manage cleaning profiles.

#### Synopsis

```bash
dmlclean profile [OPTIONS] COMMAND [ARGS]...
```

#### Subcommands

| Command | Description |
|---------|-------------|
| `list` | List all profiles |
| `show` | Show profile details |
| `export` | Export profile |
| `import` | Import profile |

#### Examples

```bash
# List profiles
dmlclean profile list

# Show profile details
dmlclean profile show developer

# Export profile
dmlclean profile export developer > my-profile.toml

# Import profile
dmlclean profile import my-profile.toml
```

---

### `plugin`

Manage plugins.

#### Synopsis

```bash
dmlclean plugin [OPTIONS] COMMAND [ARGS]...
```

#### Subcommands

| Command | Description |
|---------|-------------|
| `list` | List all plugins |
| `info` | Show plugin details |
| `enable` | Enable a plugin |
| `disable` | Disable a plugin |

#### Examples

```bash
# List plugins
dmlclean plugin list

# Show plugin info
dmlclean plugin info browser

# Enable plugin
dmlclean plugin enable dev_node

# Disable plugin
dmlclean plugin disable dev_node
```

---

### `storage`

Manage storage directories.

#### Synopsis

```bash
dmlclean storage [OPTIONS] COMMAND [ARGS]...
```

#### Subcommands

| Command | Description |
|---------|-------------|
| `path` | Show storage path |
| `cleanup` | Cleanup storage |
| `backup` | Backup storage |
| `restore` | Restore from backup |

#### Examples

```bash
# Show storage path
dmlclean storage path

# Cleanup old files
dmlclean storage cleanup --older-than 30d

# Backup database
dmlclean storage backup

# Restore from backup
dmlclean storage restore backup-2026-03-01.db
```

---

### `trends`

View disk usage trends.

#### Synopsis

```bash
dmlclean trends [OPTIONS]
```

#### Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--days` | `-d` | `30` | Days of data to show |
| `--format` | `-f` | `terminal` | Output format |
| `--json` | | `false` | JSON output |

#### Examples

```bash
# Show trends
dmlclean trends

# Last 90 days
dmlclean trends --days 90

# JSON output
dmlclean trends --json
```

---

### `system`

System commands.

#### Synopsis

```bash
dmlclean system [OPTIONS] COMMAND [ARGS]...
```

#### Subcommands

| Command | Description |
|---------|-------------|
| `version` | Show version info |
| `self-update` | Update DMLClean |
| `info` | Show system info |

#### Examples

```bash
# Show version
dmlclean system version

# Check for updates
dmlclean system self-update --check

# Update
dmlclean system self-update

# System info
dmlclean system info
```

---

## Exit Codes

DMLClean uses standard exit codes:

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error |
| `2` | Configuration error |
| `3` | Partial success (some files failed) |
| `64` | Usage error (wrong arguments) |
| `65` | Data format error |
| `66` | File not found |
| `67` | Permission denied |
| `68` | Protected zone violation |
| `69` | Database error |
| `70` | Plugin error |

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DMLCLEAN_CONFIG` | Override config path | Platform default |
| `DMLCLEAN_HOME` | Override storage directory | Platform default |
| `DMLCLEAN_LOG_LEVEL` | Set log level | `INFO` |
| `DMLCLEAN_QUIET` | Suppress output | `false` |
| `DMLCLEAN_VERBOSE` | Enable debug logging | `false` |

---

## Configuration File

Default locations:

| Platform | Path |
|----------|------|
| **Windows** | `%APPDATA%\DML Labs\DMLClean\config.toml` |
| **macOS** | `~/Library/Application Support/DML Labs/DMLClean/config.toml` |
| **Linux** | `~/.config/DML Labs/DMLClean/config.toml` |

See [CONFIGURATION.md](docs/CONFIGURATION.md) for full configuration reference.

---

## Getting Help

```bash
# General help
dmlclean --help

# Command help
dmlclean scan --help
dmlclean clean --help

# Subcommand help
dmlclean schedule add --help
dmlclean protect add --help
```

---

## Additional Resources

- [Installation Guide](docs/INSTALLATION.md)
- [Quick Start](docs/QUICKSTART.md)
- [Configuration](docs/CONFIGURATION.md)
- [FAQ](docs/FAQ.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

---

**Developed by DML Labs**  
**Lead Engineer:** [@Devmayank-official](https://github.com/Devmayank-official)  
**Repository:** https://github.com/Devmayank-official/dml-clean
