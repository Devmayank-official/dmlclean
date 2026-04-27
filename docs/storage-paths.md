# Storage Paths Guide

DMLClean stores all its data in a unified location for easy management.

## Unified Storage Location

All DMLClean data is stored under:

```
~/DML Labs/DML Clean/
```

This expands to:

| Platform | Base Path |
|----------|-----------|
| **Windows** | `C:\Users\%USERNAME%\DML Labs\DML Clean\` |
| **macOS** | `/Users/%USERNAME%/DML Labs/DML Clean/` |
| **Linux** | `/home/%USERNAME%/DML Labs/DML Clean/` |

---

## Directory Structure

```
DML Clean/
├── config/
│   ├── config.toml          # Main configuration file
│   └── profiles/            # Custom profiles
├── data/
│   ├── dml_clean.db         # SQLite database
│   ├── state.json           # Incremental scan state
│   └── migrations/          # Database migrations
├── history/
│   ├── manifests/           # Deletion manifests (JSON)
│   └── reports/             # Generated reports
├── logs/
│   └── dmlclean.log         # Application logs
└── cache/
    └── temp/                # Temporary files
```

---

## Key Files

### Configuration

**Location:** `config/config.toml`

Main configuration file with all settings.

### Database

**Location:** `data/dml_clean.db`

SQLite database storing:
- Cleaning history
- Scheduled jobs
- Protected paths
- Disk usage trends

### Logs

**Location:** `logs/dmlclean.log`

Application logs with rotation (10 MB, 30 days retention).

### Manifests

**Location:** `history/manifests/`

JSON files recording every deletion operation for audit and undo.

---

## Accessing Storage

### View Storage Info

```bash
dmlclean storage info
```

Output:
```
Base Directory: C:\Users\Santosh\DML Labs\DML Clean

┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Location  ┃ Path                                 ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Config    │ C:\Users\Santosh\DML Labs\DML Clean\config │
│ Data      │ C:\Users\Santosh\DML Labs\DML Clean\data   │
│ History   │ C:\Users\Santosh\DML Labs\DML Clean\history│
│ Logs      │ C:\Users\Santosh\DML Labs\DML Clean\logs   │
│ Cache     │ C:\Users\Santosh\DML Labs\DML Clean\cache  │
└───────────┴──────────────────────────────────────┘
```

### Open Storage Directory

```bash
dmlclean storage open
```

Opens the base storage directory in file explorer.

### Backup Storage

```bash
dmlclean storage backup ~/dmlclean-backup.zip
```

Creates a backup of all DMLClean data.

### Restore Storage

```bash
dmlclean storage restore ~/dmlclean-backup.zip
```

Restores from a backup file.

---

## Environment Variables

Override storage location:

```bash
# Not currently supported - uses unified paths
# Future versions may support DMLCLEAN_STORAGE_BASE
```

---

## Migration

To move DMLClean data to a new location:

1. Backup current data:
   ```bash
   dmlclean storage backup backup.zip
   ```

2. Manually move the `DML Labs/DML Clean` folder

3. Restore if needed:
   ```bash
   dmlclean storage restore backup.zip
   ```

---

## Cleanup

To reset all DMLClean data:

```bash
dmlclean storage reset --yes
```

**Warning:** This deletes all history, schedules, and configuration!

---

## Cross-Platform Sync

You can sync your configuration across platforms by syncing:

- `config/config.toml`
- `config/profiles/`

But **NOT** the database (`data/dml_clean.db`) as it contains platform-specific paths.
