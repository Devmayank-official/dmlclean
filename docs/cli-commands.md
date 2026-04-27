# DML Clean CLI Commands

Complete reference for all DML Clean CLI commands.

---

## Usage Pattern

```bash
dmlclean [GLOBAL OPTIONS] COMMAND [COMMAND OPTIONS]
```

---

## Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--version` | `-v` | Show version and exit |
| `--verbose` | `-V` | Enable debug logging |
| `--quiet` | `-q` | Suppress all output except errors |
| `--config PATH` | `-c` | Override config file location |
| `--help` | `-h` | Show help message |

---

## Commands

### `dmlclean scan`

Scan for cleanable files.

```bash
dmlclean scan [OPTIONS]
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--mode` | `-m` | `fast` | Scan mode: `fast`, `deep`, or `custom` |
| `--categories` | `-c` | - | Comma-separated list of categories |
| `--path` | `-p` | - | Additional paths to scan (repeatable) |
| `--json` | - | `false` | Output in JSON format |
| `--quiet` | `-q` | `false` | Suppress output (cron-friendly) |
| `--help` | `-h` | - | Show help |

**Examples:**

```bash
# Fast scan of default locations
dmlclean scan

# Deep scan with JSON output
dmlclean scan --mode deep --json > results.json

# Scan specific categories
dmlclean scan --categories browser,dev_python

# Scan specific paths
dmlclean scan --path /tmp --path C:\Temp
```

---

### `dmlclean clean`

Execute cleaning operation.

```bash
dmlclean clean [OPTIONS]
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--mode` | `-m` | `dry-run` | Clean mode: `dry-run`, `trash`, or `permanent` |
| `--profile` | `-p` | `developer` | Cleaning profile |
| `--categories` | `-c` | - | Comma-separated categories |
| `--min-age` | - | `0` | Only clean files older than N days |
| `--min-size` | - | `0` | Only clean files larger than N MB |
| `--force` | `-f` | `false` | Required for permanent mode on large operations |
| `--yes` | `-y` | `false` | Skip confirmation prompts |
| `--json` | - | `false` | Output in JSON format |
| `--path` | - | - | Paths to clean (repeatable) |
| `--help` | `-h` | - | Show help |

**Examples:**

```bash
# Preview what would be deleted (default)
dmlclean clean

# Move files to trash
dmlclean clean --mode trash

# Permanently delete (requires --force)
dmlclean clean --mode permanent --force

# Use a profile
dmlclean clean --profile developer --mode trash

# Only old/large files
dmlclean clean --min-age 30 --min-size 10
```

---

### `dmlclean schedule`

Manage scheduled cleaning operations.

```bash
dmlclean schedule <COMMAND> [OPTIONS]
```

**Subcommands:**

#### `dmlclean schedule add`

Add a new cleaning schedule.

```bash
dmlclean schedule add <NAME> <CRON_EXPRESSION> [OPTIONS]
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--mode` | `-m` | `trash` | Clean mode |
| `--categories` | `-c` | - | Categories to clean |
| `--help` | `-h` | - | Show help |

**Examples:**

```bash
# Daily cleanup at 3 AM
dmlclean schedule add "Daily Cleanup" "0 3 * * *"

# Weekly cleanup on Sunday at 2 AM
dmlclean schedule add "Weekly Cleanup" "0 2 * * 0" --mode trash
```

#### `dmlclean schedule remove`

Remove a scheduled job.

```bash
dmlclean schedule remove <JOB_ID>
```

#### `dmlclean schedule list`

List all scheduled jobs.

```bash
dmlclean schedule list
```

#### `dmlclean schedule install`

Install a schedule as a native OS task.

```bash
dmlclean schedule install <JOB_ID>
```

#### `dmlclean schedule uninstall`

Remove a native OS scheduled task.

```bash
dmlclean schedule uninstall <JOB_ID>
```

---

### `dmlclean config`

Manage configuration.

```bash
dmlclean config <COMMAND> [OPTIONS]
```

**Subcommands:**

#### `dmlclean config show`

Show current configuration.

```bash
dmlclean config show
```

#### `dmlclean config edit`

Edit configuration file.

```bash
dmlclean config edit
```

#### `dmlclean config get`

Get a configuration value.

```bash
dmlclean config get SECTION.KEY
```

#### `dmlclean config set`

Set a configuration value.

```bash
dmlclean config set SECTION.KEY VALUE
```

---

### `dmlclean protect`

Manage Protected Zone.

```bash
dmlclean protect <COMMAND> [OPTIONS]
```

**Subcommands:**

#### `dmlclean protect add`

Add a protected path.

```bash
dmlclean protect add <PATH> [--description DESC] [--glob]
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--description` | - | Human-readable description |
| `--glob` | `false` | Treat as glob pattern |
| `--help` | - | Show help |

**Examples:**

```bash
# Add exact path
dmlclean protect add ~/important-project

# Add glob pattern
dmlclean protect add "**/*.important" --glob --description "Important files"
```

#### `dmlclean protect remove`

Remove a protected path.

```bash
dmlclean protect remove <PATH_OR_ID>
```

#### `dmlclean protect list`

List all protected paths.

```bash
dmlclean protect list
```

#### `dmlclean protect check`

Check if a path is protected.

```bash
dmlclean protect check <PATH>
```

---

### `dmlclean history`

View and manage cleaning history.

```bash
dmlclean history <COMMAND> [OPTIONS]
```

**Subcommands:**

#### `dmlclean history list`

List past cleaning operations.

```bash
dmlclean history list [--limit N]
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--limit` | `-l` | `10` | Maximum entries to show |
| `--help` | `-h` | - | Show help |

#### `dmlclean history undo`

Restore files from a trash operation.

```bash
dmlclean history undo [MANIFEST_ID] [--yes]
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--yes` | `-y` | `false` | Skip confirmation |
| `--help` | `-h` | - | Show help |

#### `dmlclean history clear`

Clear all cleaning history.

```bash
dmlclean history clear
```

#### `dmlclean history export`

Export history to JSON.

```bash
dmlclean history export [OUTPUT_FILE]
```

---

### `dmlclean report`

Generate reports.

```bash
dmlclean report <COMMAND> [OPTIONS]
```

**Subcommands:**

#### `dmlclean report summary`

Generate summary report.

```bash
dmlclean report summary [--days N] [--profile PROFILE]
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--days` | `30` | Number of days to summarize |
| `--profile` | - | Filter by profile |
| `--help` | - | Show help |

#### `dmlclean report export`

Export report to file.

```bash
dmlclean report export <FORMAT> <OUTPUT_FILE> [--days N]
```

**Formats:** `json`, `csv`, `html`

---

### `dmlclean doctor`

System diagnostics.

```bash
dmlclean doctor
```

Checks:
- Python version
- Dependencies
- Configuration
- Storage directories
- Database integrity
- Permissions

---

### `dmlclean profile`

Manage cleaning profiles.

```bash
dmlclean profile <COMMAND> [OPTIONS]
```

**Subcommands:**

#### `dmlclean profile list`

List available profiles.

```bash
dmlclean profile list
```

#### `dmlclean profile show`

Show profile details.

```bash
dmlclean profile show <PROFILE_NAME>
```

#### `dmlclean profile use`

Set default profile.

```bash
dmlclean profile use <PROFILE_NAME>
```

---

### `dmlclean plugin`

Manage plugins.

```bash
dmlclean plugin <COMMAND> [OPTIONS]
```

**Subcommands:**

#### `dmlclean plugin list`

List available plugins.

```bash
dmlclean plugin list
```

#### `dmlclean plugin install`

Install a plugin.

```bash
dmlclean plugin install <PLUGIN_NAME> [--version VERSION]
```

#### `dmlclean plugin uninstall`

Uninstall a plugin.

```bash
dmlclean plugin uninstall <PLUGIN_NAME>
```

#### `dmlclean plugin update`

Update plugin(s).

```bash
dmlclean plugin update [PLUGIN_NAME]
```

---

### `dmlclean storage`

Manage storage directories.

```bash
dmlclean storage <COMMAND> [OPTIONS]
```

**Subcommands:**

#### `dmlclean storage info`

Show storage information.

```bash
dmlclean storage info
```

#### `dmlclean storage relocate`

Relocate storage directories.

```bash
dmlclean storage relocate <NEW_PATH>
```

---

### `dmlclean trends`

View disk usage trends.

```bash
dmlclean trends [OPTIONS]
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--days` | `30` | Number of days to show |
| `--mount-point` | - | Filter by mount point |
| `--help` | - | Show help |

---

### `dmlclean system`

System commands.

```bash
dmlclean system <COMMAND> [OPTIONS]
```

**Subcommands:**

#### `dmlclean system version`

Show version information.

```bash
dmlclean system version
```

#### `dmlclean system self-update`

Update DML Clean.

```bash
dmlclean system self-update
```

---

## Exit Codes

| Code | Description |
|------|-------------|
| `0` | Success |
| `1` | General error |
| `2` | Invalid command or arguments |
| `3` | Configuration error |
| `4` | Protected zone violation |
| `5` | Operation cancelled by user |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DMLCLEAN_CONFIG` | Override config file location |
| `DMLCLEAN_LOG_LEVEL` | Set logging level |
| `DMLCLEAN_LOG_FILE` | Set log file location |
| `DMLCLEAN_GENERAL_DEFAULT_SCAN_MODE` | Default scan mode |
| `DMLCLEAN_GENERAL_DEFAULT_CLEAN_MODE` | Default clean mode |
| `DMLCLEAN_GENERAL_DEFAULT_PROFILE` | Default profile |

See [Environment Variables](env.md) for complete list.

---

## Examples

### Daily Cleanup Script

```bash
#!/bin/bash
# Daily cleanup at 3 AM

dmlclean clean --mode trash --profile developer --yes
```

### Weekly Deep Clean

```bash
#!/bin/bash
# Weekly deep clean on Sunday

dmlclean scan --mode deep --json > /tmp/scan-results.json
dmlclean clean --mode trash --profile system-admin --force
```

### Protected Project Directory

```bash
# Protect your project directory
dmlclean protect add ~/my-project --description "My important project"

# Verify protection
dmlclean protect check ~/my-project
```

### Automated Reports

```bash
#!/bin/bash
# Generate monthly report

dmlclean report summary --days 30 --json > monthly-report.json
dmlclean report export html monthly-report.html --days 30
```

---

For more information, see:
- [Installation](installation.md)
- [Quick Start](QUICKSTART.md)
- [Configuration](config.md)
