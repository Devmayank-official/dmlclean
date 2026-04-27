# DMLClean FAQ

Frequently Asked Questions about DMLClean.

**Version:** 0.1.0  
**Last Updated:** March 2026

---

## 📋 Table of Contents

- [General Questions](#general-questions)
- [Installation](#installation)
- [Usage](#usage)
- [Safety & Security](#safety--security)
- [Performance](#performance)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

---

## General Questions

### What is DMLClean?

DMLClean is a production-grade, cross-platform CLI disk-cleaning utility. It scans for cleanable files (cache, temp files, build artifacts) and safely removes them to free up disk space.

### Who should use DMLClean?

DMLClean is designed for:
- **Developers** - Clean dev artifacts (Python cache, node_modules, build output)
- **System Administrators** - Automated cleaning on servers/workstations
- **Power Users** - Advanced control over what gets cleaned
- **Anyone** - Safe, easy disk cleanup with Protected Zone

### What platforms does DMLClean support?

DMLClean supports:
- ✅ **Windows** (10/11, x86_64)
- ✅ **macOS** (Intel & Apple Silicon)
- ✅ **Linux** (Ubuntu, Debian, Fedora, Arch, etc.)

### Is DMLClean free?

Yes! DMLClean is free and open-source under the Apache-2.0 license.

### How is DMLClean different from other cleaners?

**DMLClean advantages:**
- 🔒 **Safety First** - Protected Zone, dry-run preview, undo support
- 🛠️ **Developer-Focused** - Cleans dev artifacts other cleaners miss
- ⚡ **Fast** - Async scanning, parallel execution
- 🔧 **Configurable** - TOML config, profiles, categories
- 📦 **Cross-Platform** - Same tool on all platforms
- 🤖 **Automatable** - CLI, scheduling, JSON output

---

## Installation

### How do I install DMLClean?

**Windows:**
1. Download `dmlclean-windows-x86_64.exe` from [GitHub Releases](https://github.com/Devmayank-official/dmlclean/releases)
2. Run the installer or add to PATH
3. Verify: `dmlclean --version`

**Docker (All Platforms):**
```bash
docker pull ghcr.io/devmayank-official/dmlclean:latest
docker run -v /:/host dmlclean scan --path /host/tmp
```

**From Source:**
```bash
git clone https://github.com/Devmayank-official/dmlclean.git
cd dmlclean
pip install -e .
```

### Where is DMLClean installed?

**Windows:** `C:\Program Files\DMLClean\` or user-specified location  
**macOS:** `/usr/local/bin/dmlclean` or `/opt/homebrew/bin/dmlclean`  
**Linux:** `/usr/local/bin/dmlclean`

### How do I uninstall DMLClean?

**Windows:**
1. Run uninstaller (if installed)
2. Or delete installation directory
3. Remove from PATH if needed

**macOS/Linux:**
```bash
sudo rm /usr/local/bin/dmlclean
rm -rf ~/.local/share/DML\ Labs/DMLClean
rm -rf ~/.config/DML\ Labs/DMLClean
```

### Can I use DMLClean without installing?

Yes! Use Docker:
```bash
docker run -v /:/host ghcr.io/devmayank-official/dmlclean:latest scan --path /host/tmp
```

---

## Usage

### How do I use DMLClean?

**Basic workflow:**

1. **Scan** (preview what can be cleaned):
   ```bash
   dmlclean scan
   ```

2. **Clean** (execute cleaning):
   ```bash
   dmlclean clean --mode trash
   ```

3. **Undo** (if needed):
   ```bash
   dmlclean history undo
   ```

### What does `dry-run` mode do?

**Dry-run** mode shows what **would** be deleted without actually deleting anything. It's the default mode for safety.

```bash
dmlclean clean
# Shows preview, no files deleted
```

### What's the difference between `trash` and `permanent` mode?

| Mode | Description | Undo Support |
|------|-------------|--------------|
| **trash** | Moves files to OS Trash/Recycle Bin | ✅ Yes |
| **permanent** | Permanently deletes files | ❌ No |

**Recommendation:** Use `trash` mode by default, `permanent` only when sure.

### How do I clean specific file types?

Use the `--categories` flag:

```bash
# Clean only browser cache
dmlclean clean --categories browser --mode trash

# Clean Python cache and node_modules
dmlclean clean --categories dev_python,dev_node --mode trash

# Clean only system temp files
dmlclean clean --categories system_junk --mode trash
```

### How do I clean files older than N days?

Use the `--min-age` flag:

```bash
# Clean files older than 30 days
dmlclean clean --min-age 30 --mode trash

# Clean files older than 7 days
dmlclean clean --min-age 7 --mode trash
```

### How do I clean large files only?

Use the `--min-size` flag:

```bash
# Clean files larger than 100 MB
dmlclean clean --min-size 100 --mode trash

# Clean files larger than 1 GB
dmlclean clean --min-size 1000 --mode trash
```

### Can I automate cleaning?

Yes! Use scheduled cleaning:

```bash
# Add daily cleaning at 2 AM
dmlclean schedule add --name "Daily Clean" --cron "0 2 * * *" --mode trash

# List schedules
dmlclean schedule list
```

Or use cron/systemd directly:

```bash
# Cron job (daily at 2 AM)
0 2 * * * /usr/local/bin/dmlclean clean --mode trash --yes
```

### How do I exclude certain files from cleaning?

Add them to the Protected Zone:

```bash
# Add a protected path
dmlclean protect add ~/important-project

# Add a glob pattern
dmlclean protect add "**/*.env" --glob

# List protected paths
dmlclean protect list
```

### How do I undo a cleaning operation?

```bash
# View history
dmlclean history list

# Undo last operation
dmlclean history undo

# Undo specific operation
dmlclean history undo <operation-id>
```

**Note:** Undo only works for `trash` mode operations, not `permanent` mode.

---

## Safety & Security

### Is DMLClean safe to use?

**Yes!** DMLClean has multiple safety features:

1. ✅ **Protected Zone** - Critical files are never deleted
2. ✅ **Dry-Run Default** - Preview before any deletion
3. ✅ **Manifest Logging** - All deletions are logged
4. ✅ **Undo Support** - Restore from trash operations
5. ✅ **Confirmation Prompts** - Required for large deletions
6. ✅ **Risk Levels** - Color-coded risk assessment

### What files does DMLClean protect?

**Always protected:**
- Browser bookmarks, passwords, cookies
- `.git/` directories
- Virtual environments (`venv/`, `.venv/`)
- System-critical directories
- User home directory (configurable)
- Files modified within last 24 hours (default)

### Can DMLClean delete important files?

**No**, if you use it correctly:

1. **Always preview first:** `dmlclean clean` (dry-run)
2. **Review the preview:** Check what will be deleted
3. **Use trash mode:** `dmlclean clean --mode trash`
4. **Don't skip confirmations:** Review prompts
5. **Add important paths to Protected Zone**

### Does DMLClean send data anywhere?

**No!** DMLClean:
- ❌ No telemetry
- ❌ No data collection
- ❌ No network calls
- ❌ No cloud connectivity

DMLClean works entirely offline and is air-gapped compatible.

### Is my data private?

**Yes!** All operations happen locally on your machine. No data leaves your computer.

### Can I audit what DMLClean did?

Yes! Every operation is logged:

```bash
# View history
dmlclean history list

# Export history
dmlclean history export history.json

# View manifest
cat ~/.local/share/DML\ Labs/DMLClean/history/<manifest-id>.json
```

---

## Performance

### How fast is DMLClean?

**Typical scan times:**

| Scan Type | Files | Time |
|-----------|-------|------|
| Fast scan | 10K | < 2 seconds |
| Fast scan | 100K | < 5 seconds |
| Deep scan | 1M | < 15 seconds |

**Cleaning speed:**
- SSD: ~1,000 files/second
- HDD: ~100 files/second

### How much memory does DMLClean use?

**Typical memory usage:**
- Idle: < 50 MB
- Scanning: < 200 MB
- Deep scan (1M files): < 500 MB

### Can I use DMLClean on a slow computer?

Yes! DMLClean is optimized for performance:
- Async I/O for non-blocking operations
- Configurable thread pool
- Streaming processing (doesn't load all files into memory)
- Incremental scanning (reuses previous results)

### Does DMLClean slow down my system?

**No**, DMLClean:
- Uses configurable CPU priority
- Throttles I/O operations
- Runs in background
- Can be paused/stopped

For minimal impact, run during idle time or use scheduling.

---

## Configuration

### Where is the config file?

**Default locations:**

| Platform | Path |
|----------|------|
| **Windows** | `%APPDATA%\DML Labs\DMLClean\config.toml` |
| **macOS** | `~/Library/Application Support/DML Labs/DMLClean/config.toml` |
| **Linux** | `~/.config/DML Labs/DMLClean/config.toml` |

### How do I edit the config file?

```bash
# Open in editor
dmlclean config edit

# Or manually edit with text editor
# Windows: notepad "%APPDATA%\DML Labs\DMLClean\config.toml"
# macOS/Linux: nano ~/.config/DML\ Labs/DMLClean/config.toml
```

### What are profiles?

**Profiles** are pre-configured cleaning presets:

- **developer** - Safe for dev work (default)
- **designer** - Safe for design/media work
- **system-admin** - Aggressive cleaning
- **gamer** - Safe for gaming setups
- **minimal** - Minimal cleaning

Use a profile:
```bash
dmlclean clean --profile developer --mode trash
```

### How do I create a custom profile?

Export an existing profile and modify:

```bash
# Export developer profile
dmlclean profile export developer > my-profile.toml

# Edit my-profile.toml

# Import custom profile
dmlclean profile import my-profile.toml
```

### Can I use environment variables?

Yes! Override config with environment variables:

```bash
# Set config path
export DMLCLEAN_CONFIG=/path/to/config.toml

# Enable debug logging
export DMLCLEAN_LOG_LEVEL=DEBUG

# Use custom profile
export DMLCLEAN_DEFAULT_PROFILE=system-admin
```

---

## Troubleshooting

### Why is DMLClean not finding any files?

**Possible causes:**
1. ✅ No cleanable files exist (good!)
2. ✅ Categories are disabled
3. ✅ Paths are protected
4. ✅ Filters are too strict

**Solutions:**
```bash
# Enable more categories
dmlclean clean --categories all --mode trash

# Check protected paths
dmlclean protect list

# Use deep scan
dmlclean scan --mode deep
```

### Why did DMLClean skip some files?

**Files are skipped if:**
- They're in the Protected Zone
- They're too new (modified recently)
- They're too large (above threshold)
- Permission denied
- File in use by another process

**Check logs:**
```bash
dmlclean doctor
cat ~/.local/state/DML\ Labs/DMLClean/Logs/dmlclean.log
```

### Why is DMLClean slow?

**Possible causes:**
1. ✅ Scanning many files (deep scan)
2. ✅ Slow disk (HDD vs SSD)
3. ✅ Network drives
4. ✅ Many symlinks

**Solutions:**
```bash
# Use fast scan
dmlclean scan --mode fast

# Limit depth
# Edit config: [scanner] max_depth = 5

# Exclude network drives
# Add to Protected Zone
```

### Why did DMLClean fail to delete files?

**Possible causes:**
1. ✅ Permission denied
2. ✅ File in use
3. ✅ Protected Zone violation
4. ✅ Read-only files

**Solutions:**
```bash
# Check permissions
ls -la /path/to/files

# Close applications using files

# Check if protected
dmlclean protect check /path/to/files

# Run as admin (if needed)
sudo dmlclean clean --mode trash
```

### How do I report a bug?

1. Go to [GitHub Issues](https://github.com/Devmayank-official/dmlclean/issues)
2. Click "New Issue"
3. Select "Bug Report"
4. Fill in details:
   - DMLClean version
   - OS version
   - Steps to reproduce
   - Expected vs actual behavior
   - Logs (if applicable)

---

## Development

### How do I contribute to DMLClean?

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

**Quick start:**
```bash
# Fork repository
# Clone your fork
git clone https://github.com/YOUR_USERNAME/dmlclean.git
cd dmlclean

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Make changes, commit, push
# Create Pull Request
```

### How do I build from source?

```bash
# Clone repository
git clone https://github.com/Devmayank-official/dmlclean.git
cd dmlclean

# Install
pip install -e .

# Or build binary
pip install pyinstaller
pyinstaller dmlclean.spec --clean
```

### How do I run tests?

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=dmlclean --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_scanner.py
```

### How do I create a plugin?

See plugin documentation in [ARCHITECTURE.md](ARCHITECTURE.md).

**Basic plugin:**
```python
from dmlclean.plugins.base import CleanerPlugin, CleanCandidate, RiskLevel

class MyPlugin(CleanerPlugin):
    @property
    def name(self) -> str:
        return "my_plugin"
    
    @property
    def description(self) -> str:
        return "My custom plugin"
    
    async def scan(self, roots):
        for root in roots:
            # Scan logic here
            yield CleanCandidate(
                path=some_path,
                category=self.name,
                size_bytes=size,
                risk_level=RiskLevel.LOW,
                reason="Custom reason"
            )
```

---

## More Help

### Where can I get help?

- 📖 **Documentation:** [docs/](docs/)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/Devmayank-official/dmlclean/discussions)
- 🐛 **Issues:** [GitHub Issues](https://github.com/Devmayank-official/dmlclean/issues)
- 📧 **Email:** dmlclean@dmlabs.dev

### Is there a GUI?

Not yet! DMLClean is CLI-only for v0.1.0. GUI is planned for future releases.

### Can I use DMLClean in my commercial product?

Yes! DMLClean is Apache-2.0 licensed, which allows commercial use.

### Is there a mobile app?

Not yet! Mobile app is planned for future releases.

---

**Still have questions?**  
Open an issue on [GitHub](https://github.com/Devmayank-official/dmlclean/issues) or join [Discussions](https://github.com/Devmayank-official/dmlclean/discussions).

---

**Developed by DML Labs**  
**Lead Engineer:** [@Devmayank-official](https://github.com/Devmayank-official)  
**Repository:** https://github.com/Devmayank-official/dmlclean
Repository:** https://github.com/Devmayank-official/dml-clean
