# Quick Start Guide

Get up and running with DMLClean in 5 minutes!

## Step 1: Install

```bash
pipx install dmlclean
```

## Step 2: Scan

Run a quick scan to see what can be cleaned:

```bash
dmlclean scan
```

You'll see output like:

```
✓ Scan Complete
Mode: fast | Files: 1234 | Size: 500.00 MB

By Category:
┌──────────────┬───────┬──────────┐
│ Category     │ Files │ Size     │
├──────────────┼───────┼──────────┤
│ system_junk  │ 500   │ 200 MB   │
│ browser      │ 400   │ 150 MB   │
│ dev_python   │ 334   │ 150 MB   │
└──────────────┴───────┴──────────┘
```

## Step 3: Preview (Dry-Run)

See what would be deleted without actually deleting:

```bash
dmlclean clean
```

This runs in **dry-run mode** by default (safe!).

## Step 4: Clean

When you're ready, move files to trash:

```bash
dmlclean clean --mode trash
```

## Step 5: Protect Important Files

Add paths that should never be cleaned:

```bash
dmlclean protect add ~/important-project
```

## Step 6: View History

See past cleaning operations:

```bash
dmlclean history list
```

## Common Commands

| Command | Description |
|---------|-------------|
| `dmlclean scan` | Scan for cleanable files |
| `dmlclean clean` | Preview what would be deleted |
| `dmlclean clean --mode trash` | Move files to trash |
| `dmlclean protect add <path>` | Protect a path |
| `dmlclean history list` | View cleaning history |
| `dmlclean doctor` | Run diagnostics |

## Next Steps

- [Usage Guide](usage.md) - Learn all commands in detail
- [Configuration](configuration.md) - Customize settings
- [CLI Reference](cli-reference.md) - Complete command reference

---

**Need Help?**

- Run `dmlclean --help` for general help
- Run `dmlclean <command> --help` for command-specific help
- Check [Issues](https://github.com/dmlclean/dmlclean/issues) for known problems
