# DMLClean Configuration Guide

Complete guide to configuring DMLClean.

**Version:** 0.1.0  
**Last Updated:** March 2026

---

## 📋 Table of Contents

- [Configuration File Location](#configuration-file-location)
- [Configuration Structure](#configuration-structure)
- [General Settings](#general-settings)
- [Logging Settings](#logging-settings)
- [Notifications Settings](#notifications-settings)
- [Scheduling Settings](#scheduling-settings)
- [Scanner Settings](#scanner-settings)
- [Cleaner Settings](#cleaner-settings)
- [Protected Zone Settings](#protected-zone-settings)
- [Categories Configuration](#categories-configuration)
- [History Settings](#history-settings)
- [UI Settings](#ui-settings)
- [Environment Variables](#environment-variables)
- [Profiles](#profiles)
- [Examples](#examples)

---

## Configuration File Location

DMLClean stores configuration in platform-specific locations:

| Platform | Path |
|----------|------|
| **Windows** | `%APPDATA%\DML Labs\DMLClean\config.toml` |
| **macOS** | `~/Library/Application Support/DML Labs/DMLClean/config.toml` |
| **Linux** | `~/.config/DML Labs/DMLClean/config.toml` |

### Override Configuration Path

Use the `--config` flag or `DMLCLEAN_CONFIG` environment variable:

```bash
# Command line
dmlclean scan --config /path/to/custom.toml

# Environment variable
export DMLCLEAN_CONFIG=/path/to/custom.toml
```

---

## Configuration Structure

DMLClean uses TOML format for configuration:

```toml
version = "0.1.0"

[general]
default_scan_mode = "fast"
default_clean_mode = "dry-run"
# ... more settings

[logging]
level = "INFO"
# ... more settings

# ... other sections
```

### Sections

| Section | Description |
|---------|-------------|
| `[general]` | General application settings |
| `[logging]` | Logging configuration |
| `[notifications]` | Desktop notifications |
| `[scheduling]` | Scheduled cleaning jobs |
| `[scanner]` | File scanning behavior |
| `[cleaner]` | Cleaning operation settings |
| `[protected_zone]` | Protected file paths |
| `[categories]` | Cleaning category settings |
| `[history]` | History tracking |
| `[ui]` | User interface settings |

---

## General Settings

```toml
[general]
# Default scan mode: "fast", "deep", or "custom"
default_scan_mode = "fast"

# Default clean mode: "dry-run", "trash", or "permanent"
default_clean_mode = "dry-run"

# Default cleaning profile
default_profile = "developer"

# Confirm if cleaning > N MB
confirm_threshold_mb = 100

# Confirm if cleaning > N files
confirm_threshold_files = 1000

# Confirmation detail level: "summary" or "full"
confirmation_detail = "summary"

# Max worker threads (0 = auto-detect)
max_workers = 0

# Enable JSON output mode
json_output = false
```

### Options Explained

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `default_scan_mode` | String | `"fast"` | Default scan mode |
| `default_clean_mode` | String | `"dry-run"` | Default clean mode |
| `default_profile` | String | `"developer"` | Default profile |
| `confirm_threshold_mb` | Integer | `100` | Confirm if > N MB |
| `confirm_threshold_files` | Integer | `1000` | Confirm if > N files |
| `confirmation_detail` | String | `"summary"` | Detail level |
| `max_workers` | Integer | `0` | Thread count (0=auto) |
| `json_output` | Boolean | `false` | JSON output mode |

---

## Logging Settings

```toml
[logging]
# Log level: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
level = "INFO"

# Enable file logging
log_to_file = true

# Log rotation size
log_rotation = "10 MB"

# Log retention period
log_retention = "30 days"

# Log format: "text" or "json"
log_format = "text"
```

### Options Explained

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `level` | String | `"INFO"` | Log level |
| `log_to_file` | Boolean | `true` | File logging |
| `log_rotation` | String | `"10 MB"` | Rotation size |
| `log_retention` | String | `"30 days"` | Retention period |
| `log_format` | String | `"text"` | Output format |

### Log File Locations

| Platform | Path |
|----------|------|
| **Windows** | `%LOCALAPPDATA%\DML Labs\DMLClean\Logs\dmlclean.log` |
| **macOS** | `~/Library/Logs/DML Labs/DMLClean/dmlclean.log` |
| **Linux** | `~/.local/state/DML Labs/DMLClean/Logs/dmlclean.log` |

---

## Notifications Settings

```toml
[notifications]
# Enable desktop notifications
enabled = true

# Notify on scan completion
on_scan_complete = true

# Notify on clean completion
on_clean_complete = true

# Notify on errors
on_error = true

# Notify on scheduled runs
on_scheduled_run = true

# Notify on protected zone violations
on_protected_zone_violation = true
```

### Options Explained

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | Boolean | `true` | Enable notifications |
| `on_scan_complete` | Boolean | `true` | Scan complete |
| `on_clean_complete` | Boolean | `true` | Clean complete |
| `on_error` | Boolean | `true` | Errors |
| `on_scheduled_run` | Boolean | `true` | Scheduled runs |
| `on_protected_zone_violation` | Boolean | `true` | Protected violations |

---

## Scheduling Settings

```toml
[scheduling]
# Enable scheduled cleaning
enabled = false

# Scheduler backend: "apscheduler", "native-cron", "windows-task-scheduler"
backend = "apscheduler"

# Scheduled jobs (see below for examples)
[[scheduling.jobs]]
id = "daily-clean"
name = "Daily Clean"
cron_expression = "0 2 * * *"
# ... more job settings
```

### Scheduled Jobs

Add multiple jobs:

```toml
[[scheduling.jobs]]
id = "daily-clean"
name = "Daily Clean"
cron_expression = "0 2 * * *"
scan_mode = "fast"
clean_mode = "trash"
categories = ["browser", "dev_python", "system_junk"]
enabled = true

[[scheduling.jobs]]
id = "weekly-deep-clean"
name = "Weekly Deep Clean"
cron_expression = "0 3 * * 0"
scan_mode = "deep"
clean_mode = "trash"
profile = "developer"
categories = ["all"]
enabled = true
```

### Job Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `id` | String | (required) | Unique job ID |
| `name` | String | (required) | Human-readable name |
| `cron_expression` | String | (required) | Cron schedule |
| `scan_mode` | String | `"fast"` | Scan mode |
| `clean_mode` | String | `"trash"` | Clean mode |
| `categories` | Array | `[]` | Categories to clean |
| `profile` | String | `"developer"` | Profile to use |
| `enabled` | Boolean | `true` | Job active |

### Cron Expression Format

```
* * * * *
│ │ │ │ │
│ │ │ │ └─ Day of week (0-6, 0=Sunday)
│ │ │ └─── Month (1-12)
│ │ └───── Day of month (1-31)
│ └─────── Hour (0-23)
└───────── Minute (0-59)
```

**Examples:**
- `0 2 * * *` - Daily at 2:00 AM
- `0 3 * * 0` - Every Sunday at 3:00 AM
- `0 */4 * * *` - Every 4 hours
- `0 9-17 * * 1-5` - Every hour, 9 AM - 5 PM, weekdays

---

## Scanner Settings

```toml
[scanner]
# Follow symbolic links
follow_symlinks = false

# Max directory depth (0 = unlimited)
max_depth = 0

# Large file threshold in MB
large_file_threshold_mb = 500

# Stale file threshold in days
stale_file_days = 90

# Enable smart scan features
enable_smart_scan = true
```

### Options Explained

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `follow_symlinks` | Boolean | `false` | Follow symlinks |
| `max_depth` | Integer | `0` | Max depth (0=unlimited) |
| `large_file_threshold_mb` | Integer | `500` | Large file threshold |
| `stale_file_days` | Integer | `90` | Stale file threshold |
| `enable_smart_scan` | Boolean | `true` | Smart scan features |

---

## Cleaner Settings

```toml
[cleaner]
# Enable incremental cleaning
enable_incremental = true

# Minimum file size to clean (MB)
min_size_mb = 0

# Minimum file age to clean (days)
min_age_days = 0

# Minimum age for node_modules cleaning (days)
node_modules_min_age_days = 30
```

### Options Explained

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enable_incremental` | Boolean | `true` | Incremental cleaning |
| `min_size_mb` | Integer | `0` | Min file size (MB) |
| `min_age_days` | Integer | `0` | Min file age (days) |
| `node_modules_min_age_days` | Integer | `30` | node_modules min age |

---

## Protected Zone Settings

```toml
[protected_zone]
# Enable Protected Zone
enabled = true

# Active protection profiles
profiles = ["system-critical", "user-home"]

# Custom protected paths
custom_paths = [
    "~/important-project",
    "~/Documents/taxes",
]

# Custom protected glob patterns
custom_globs = [
    "**/*.env",
    "**/.secrets",
]

# Protect .git directories
protect_git_dirs = true

# Protect virtual environments
protect_venvs = true

# Protect files modified within N days
protect_recent_days = 1

# Additional protected path patterns
protected_paths = []
```

### Options Explained

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | Boolean | `true` | Enable protection |
| `profiles` | Array | `["system-critical", "user-home"]` | Protection profiles |
| `custom_paths` | Array | `[]` | Custom paths |
| `custom_globs` | Array | `[]` | Custom glob patterns |
| `protect_git_dirs` | Boolean | `true` | Protect .git |
| `protect_venvs` | Boolean | `true` | Protect venvs |
| `protect_recent_days` | Integer | `1` | Protect recent files |
| `protected_paths` | Array | `[]` | Additional patterns |

### Protected Paths (Default)

The following are **always protected**:
- Browser bookmarks, passwords, cookies
- `.git/` directories
- Virtual environments (`venv/`, `.venv/`)
- System-critical directories
- User home directory (configurable)

---

## Categories Configuration

Configure each cleaning category:

```toml
[categories.system_junk]
enabled = true
min_risk = "low"

[categories.browser]
enabled = true
min_risk = "low"

[categories.dev_python]
enabled = true
min_risk = "low"

[categories.dev_node]
enabled = false
min_risk = "medium"

[categories.dev_java]
enabled = false
min_risk = "medium"

[categories.dev_rust_cpp]
enabled = false
min_risk = "medium"

[categories.ide]
enabled = true
min_risk = "low"

[categories.gaming]
enabled = false
min_risk = "medium"

[categories.media]
enabled = false
min_risk = "medium"

[categories.messaging]
enabled = false
min_risk = "medium"

[categories.ai_ml]
enabled = false
min_risk = "high"

[categories.cloud_sync]
enabled = false
min_risk = "medium"

[categories.package_manager]
enabled = false
min_risk = "medium"

[categories.smart_scan]
enabled = true
min_risk = "low"
```

### Category Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | Boolean | Varies | Enable category |
| `min_risk` | String | `"low"` | Min risk level |

### Risk Levels

| Level | Description | Default Action |
|-------|-------------|----------------|
| `low` | 🟢 Safe to clean | Auto-clean |
| `medium` | 🟡 Review before clean | Confirm |
| `high` | 🔴 Potentially dangerous | Manual/opt-in |
| `blocked` | ⛔ Never clean | Blocked |

### Default-Enabled Categories

These categories are **enabled by default**:
- `system_junk` - OS temp files
- `browser` - Browser cache
- `dev_python` - Python cache
- `ide` - IDE cache
- `smart_scan` - Large/stale files

These categories are **disabled by default** (opt-in):
- `dev_node` - Node.js artifacts
- `dev_java` - Java artifacts
- `dev_rust_cpp` - Rust/C++ artifacts
- `gaming` - Game launcher cache
- `media` - Media editor cache
- `messaging` - Chat app cache
- `ai_ml` - ML framework cache
- `cloud_sync` - Cloud storage cache
- `package_manager` - Package manager cache

---

## History Settings

```toml
[history]
# Enable cleaning history
enabled = true

# Maximum history entries to keep
max_entries = 100

# Custom history storage path (empty = default)
storage_path = ""
```

### Options Explained

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | Boolean | `true` | Enable history |
| `max_entries` | Integer | `100` | Max entries |
| `storage_path` | String | `""` | Custom path |

---

## UI Settings

```toml
[ui]
# UI theme: "dmlclean", "default", "custom"
theme = "dmlclean"

# Color for low risk
color_risk_low = "green"

# Color for medium risk
color_risk_medium = "yellow"

# Color for high risk
color_risk_high = "red"
```

### Options Explained

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `theme` | String | `"dmlclean"` | UI theme |
| `color_risk_low` | String | `"green"` | Low risk color |
| `color_risk_medium` | String | `"yellow"` | Medium risk color |
| `color_risk_high` | String | `"red"` | High risk color |

---

## Environment Variables

Override configuration with environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `DMLCLEAN_CONFIG` | Config file path | `/path/to/config.toml` |
| `DMLCLEAN_HOME` | Storage directory | `~/DML Labs/DMLClean` |
| `DMLCLEAN_LOG_LEVEL` | Log level | `DEBUG` |
| `DMLCLEAN_QUIET` | Quiet mode | `true` |
| `DMLCLEAN_VERBOSE` | Verbose mode | `true` |
| `DMLCLEAN_DEFAULT_PROFILE` | Default profile | `developer` |
| `DMLCLEAN_DEFAULT_MODE` | Default mode | `trash` |

### Examples

```bash
# Override config path
export DMLCLEAN_CONFIG=/path/to/config.toml

# Override storage directory
export DMLCLEAN_HOME=~/custom-storage

# Enable debug logging
export DMLCLEAN_LOG_LEVEL=DEBUG

# Use custom profile
export DMLCLEAN_DEFAULT_PROFILE=system-admin
```

---

## Profiles

DMLClean includes 5 built-in profiles:

### `developer` (Default)

Safe for development work:
- ✅ Clean: Python cache, IDE cache, system temp
- ❌ Skip: `node_modules/`, build artifacts
- ⚠️ Confirm: Large files, old logs

### `designer`

Safe for design/media work:
- ✅ Clean: System temp, browser cache
- ❌ Skip: Adobe cache, Blender cache, media files
- ⚠️ Confirm: Large media files

### `system-admin`

Aggressive cleaning:
- ✅ Clean: All low/medium risk categories
- ❌ Skip: Only protected paths
- ⚠️ Confirm: High-risk categories

### `gamer`

Safe for gaming setups:
- ✅ Clean: System temp, browser cache
- ❌ Skip: Steam cache, Epic cache, NVIDIA shader cache
- ⚠️ Confirm: Game launcher cache (opt-in)

### `minimal`

Minimal cleaning:
- ✅ Clean: Only system temp files
- ❌ Skip: All dev/media/gaming categories
- ⚠️ Confirm: Everything else

---

## Examples

### Example 1: Developer Workstation

```toml
version = "0.1.0"

[general]
default_scan_mode = "fast"
default_clean_mode = "trash"
default_profile = "developer"
confirm_threshold_mb = 100

[notifications]
enabled = true
on_clean_complete = true

[protected_zone]
enabled = true
protect_git_dirs = true
protect_venvs = true

[categories]
system_junk = { enabled = true, min_risk = "low" }
browser = { enabled = true, min_risk = "low" }
dev_python = { enabled = true, min_risk = "low" }
dev_node = { enabled = false, min_risk = "medium" }
ide = { enabled = true, min_risk = "low" }
smart_scan = { enabled = true, min_risk = "low" }
```

### Example 2: CI/CD Server

```toml
version = "0.1.0"

[general]
default_scan_mode = "deep"
default_clean_mode = "permanent"
confirm_threshold_mb = 1000
json_output = true

[logging]
level = "WARNING"
log_to_file = true

[notifications]
enabled = false

[scanner]
follow_symlinks = false
max_depth = 10

[categories]
system_junk = { enabled = true, min_risk = "low" }
dev_python = { enabled = true, min_risk = "low" }
dev_node = { enabled = true, min_risk = "low" }
package_manager = { enabled = true, min_risk = "low" }
```

### Example 3: Aggressive Cleaning

```toml
version = "0.1.0"

[general]
default_clean_mode = "trash"
default_profile = "system-admin"
confirm_threshold_mb = 500

[protected_zone]
enabled = true
protect_git_dirs = true
protect_venvs = false  # Clean venvs

[categories]
system_junk = { enabled = true, min_risk = "low" }
browser = { enabled = true, min_risk = "low" }
dev_python = { enabled = true, min_risk = "low" }
dev_node = { enabled = true, min_risk = "medium" }
dev_java = { enabled = true, min_risk = "medium" }
dev_rust_cpp = { enabled = true, min_risk = "medium" }
ide = { enabled = true, min_risk = "low" }
gaming = { enabled = true, min_risk = "medium" }
media = { enabled = true, min_risk = "medium" }
messaging = { enabled = true, min_risk = "medium" }
ai_ml = { enabled = true, min_risk = "high" }
cloud_sync = { enabled = true, min_risk = "medium" }
package_manager = { enabled = true, min_risk = "low" }
smart_scan = { enabled = true, min_risk = "low" }
```

### Example 4: Scheduled Daily Cleaning

```toml
version = "0.1.0"

[scheduling]
enabled = true
backend = "apscheduler"

[[scheduling.jobs]]
id = "daily-clean"
name = "Daily Clean"
cron_expression = "0 2 * * *"
scan_mode = "fast"
clean_mode = "trash"
profile = "developer"
categories = ["system_junk", "browser", "dev_python"]
enabled = true

[[scheduling.jobs]]
id = "weekly-deep-clean"
name = "Weekly Deep Clean"
cron_expression = "0 3 * * 0"
scan_mode = "deep"
clean_mode = "trash"
profile = "developer"
categories = ["all"]
enabled = true
```

---

## Validation

Validate your configuration:

```bash
# Show config
dmlclean config show

# Validate config
dmlclean config validate

# Show config path
dmlclean config path
```

---

## Troubleshooting

### Config File Not Found

**Problem:** DMLClean can't find config file

**Solution:**
1. Check default location for your platform
2. Create config file manually
3. Or use `--config` flag to specify path

### Invalid Configuration

**Problem:** Error parsing config file

**Solution:**
1. Validate TOML syntax
2. Check option names (case-sensitive)
3. Verify option values (types, allowed values)
4. Run `dmlclean config validate`

### Environment Variables Not Working

**Problem:** Environment variables not overriding config

**Solution:**
1. Check variable names (must be exact)
2. Ensure variables are set before running DMLClean
3. Restart terminal after setting variables

---

## Additional Resources

- [CLI Reference](CLI_REFERENCE.md)
- [Quick Start](QUICKSTART.md)
- [FAQ](FAQ.md)
- [Troubleshooting](TROUBLESHOOTING.md)

---

**Developed by DML Labs**  
**Lead Engineer:** [@Devmayank-official](https://github.com/Devmayank-official)  
**Repository:** https://github.com/Devmayank-official/dml-clean
