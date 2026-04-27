# DMLClean Troubleshooting Guide

Solutions to common DMLClean issues.

**Version:** 0.1.0  
**Last Updated:** March 2026

---

## 📋 Table of Contents

- [Installation Issues](#installation-issues)
- [Scan Issues](#scan-issues)
- [Clean Issues](#clean-issues)
- [Performance Issues](#performance-issues)
- [Configuration Issues](#configuration-issues)
- [Database Issues](#database-issues)
- [Notification Issues](#notification-issues)
- [Schedule Issues](#schedule-issues)
- [Windows-Specific](#windows-specific)
- [macOS-Specific](#macos-specific)
- [Linux-Specific](#linux-specific)
- [Error Codes](#error-codes)
- [Getting Help](#getting-help)

---

## Installation Issues

### Issue: "Command not found: dmlclean"

**Symptoms:**
```bash
bash: dmlclean: command not found
```

**Causes:**
1. DMLClean not installed
2. Not in PATH
3. Installation failed

**Solutions:**

**Windows:**
```powershell
# Verify installation
where dmlclean

# If not found, reinstall
# Download from GitHub Releases and run installer

# Or add to PATH manually
setx PATH "%PATH%;C:\Program Files\DMLClean"
```

**macOS/Linux:**
```bash
# Verify installation
which dmlclean

# If not found, check installation
pip show dmlclean

# Reinstall if needed
pip install --force-reinstall dmlclean

# Or add to PATH
export PATH="$HOME/.local/bin:$PATH"
```

---

### Issue: "Permission denied" during installation

**Symptoms:**
```bash
error: Permission denied: '/usr/local/bin'
```

**Solutions:**

**macOS/Linux:**
```bash
# Use --user flag
pip install --user dmlclean

# Or use sudo (not recommended)
sudo pip install dmlclean

# Or use virtual environment
python -m venv venv
source venv/bin/activate
pip install dmlclean
```

**Windows:**
```powershell
# Run as Administrator
# Right-click PowerShell > Run as Administrator
pip install dmlclean
```

---

### Issue: Docker image pull failed

**Symptoms:**
```bash
Error response from daemon: pull access denied
```

**Solutions:**
```bash
# Login to GitHub Container Registry
docker login ghcr.io -u YOUR_USERNAME -p YOUR_TOKEN

# Or use Docker Hub
docker pull devmayankofficial/dml-clean:latest

# Check Docker daemon is running
docker ps
```

---

## Scan Issues

### Issue: No files found during scan

**Symptoms:**
```
✓ Scan Complete
Mode: fast | Files: 0 | Size: 0 B
```

**Causes:**
1. No cleanable files exist
2. Wrong scan paths
3. Categories disabled
4. Too many filters

**Solutions:**

```bash
# 1. Check scan paths
dmlclean scan --path /tmp --path ~/.cache

# 2. Enable all categories
dmlclean scan --categories all

# 3. Use deep scan
dmlclean scan --mode deep

# 4. Check configuration
dmlclean config show

# 5. Verify files exist
ls -la /tmp
ls -la ~/.cache
```

---

### Issue: Scan is very slow

**Symptoms:**
- Scan takes > 30 seconds
- System becomes unresponsive

**Causes:**
1. Deep scan on large directories
2. Network drives
3. Many symlinks
4. Slow disk (HDD)

**Solutions:**

```bash
# 1. Use fast scan
dmlclean scan --mode fast

# 2. Limit scan depth
# Edit config.toml:
[scanner]
max_depth = 5

# 3. Exclude network drives
dmlclean protect add /mnt/network-drive

# 4. Scan specific paths only
dmlclean scan --path /tmp --path ~/.cache

# 5. Reduce worker threads
# Edit config.toml:
[general]
max_workers = 2
```

---

### Issue: Scan crashes with error

**Symptoms:**
```
Error: OSError: [Errno 24] Too many open files
```

**Solutions:**

**macOS/Linux:**
```bash
# Increase file descriptor limit
ulimit -n 4096

# Make permanent (add to ~/.bashrc or ~/.zshrc)
echo "ulimit -n 4096" >> ~/.bashrc
```

**Windows:**
```powershell
# Restart computer
# Windows has fixed limit, restart may help
```

---

## Clean Issues

### Issue: Files not deleted

**Symptoms:**
- Clean operation completes
- Files still present

**Causes:**
1. Protected Zone blocking
2. Permission denied
3. Files in use
4. Dry-run mode

**Solutions:**

```bash
# 1. Check if protected
dmlclean protect check /path/to/files

# 2. Check permissions
ls -la /path/to/files

# 3. Close applications using files

# 4. Verify mode (not dry-run)
dmlclean clean --mode trash

# 5. Check logs
cat ~/.local/state/DML\ Labs/DMLClean/Logs/dmlclean.log
```

---

### Issue: "Permission denied" during clean

**Symptoms:**
```
Error: Permission denied: /path/to/file
```

**Solutions:**

**macOS/Linux:**
```bash
# Check file permissions
ls -la /path/to/file

# Fix permissions (if safe)
sudo chmod 644 /path/to/file

# Or run as sudo (use with caution)
sudo dmlclean clean --mode trash
```

**Windows:**
```powershell
# Run as Administrator
# Right-click > Run as Administrator

# Or take ownership
takeown /f "C:\path\to\file"
icacls "C:\path\to\file" /grant administrators:F
```

---

### Issue: Undo doesn't work

**Symptoms:**
```bash
dmlclean history undo
# Files not restored
```

**Causes:**
1. Used permanent mode (no undo)
2. Trash emptied
3. Manifest missing

**Solutions:**

```bash
# 1. Check operation mode
dmlclean history list
# Undo only works for "trash" mode, not "permanent"

# 2. Check trash/recycle bin
# If emptied, files cannot be recovered

# 3. Check manifest exists
ls ~/.local/share/DML\ Labs/DMLClean/history/
```

**Prevention:**
- Always use `--mode trash` for reversible operations
- Don't empty trash immediately after cleaning
- Keep manifest files

---

### Issue: Wrong files deleted

**Symptoms:**
- Important files deleted
- Unexpected files removed

**Immediate Actions:**

```bash
# 1. Stop cleaning immediately
# Press Ctrl+C if running

# 2. Check what was deleted
dmlclean history list

# 3. Try to undo
dmlclean history undo

# 4. Check trash/recycle bin
# Restore files manually if needed
```

**Prevention:**
- Always preview first: `dmlclean clean` (dry-run)
- Review preview carefully
- Use Protected Zone for important paths
- Use `--mode trash` not `--mode permanent`
- Add confirmations: don't use `--yes` flag

---

## Performance Issues

### Issue: High CPU usage

**Symptoms:**
- CPU at 100% during scan/clean
- System slowdown

**Solutions:**

```bash
# 1. Reduce worker threads
# Edit config.toml:
[general]
max_workers = 2

# 2. Use fast scan
dmlclean scan --mode fast

# 3. Limit scan depth
# Edit config.toml:
[scanner]
max_depth = 5

# 4. Schedule during idle time
dmlclean schedule add --name "Night Clean" --cron "0 3 * * *" --mode trash
```

---

### Issue: High memory usage

**Symptoms:**
- Memory usage > 1 GB
- System becomes slow

**Solutions:**

```bash
# 1. Scan smaller directories
dmlclean scan --path /tmp

# 2. Use streaming mode (default)
# DMLClean already streams, doesn't load all files into memory

# 3. Reduce batch size
# Edit config.toml:
[scanner]
max_depth = 5
```

---

### Issue: Disk I/O bottleneck

**Symptoms:**
- Disk activity at 100%
- Slow file operations

**Solutions:**

```bash
# 1. Reduce I/O priority (Linux)
ionice -c3 dmlclean clean --mode trash

# 2. Use scheduling
# Run during off-hours
dmlclean schedule add --name "Night Clean" --cron "0 3 * * *"

# 3. Clean smaller batches
dmlclean clean --categories system_junk --mode trash
dmlclean clean --categories browser --mode trash
```

---

## Configuration Issues

### Issue: Config file not found

**Symptoms:**
```
Error: Config file not found: /path/to/config.toml
```

**Solutions:**

```bash
# 1. Check default location
# Windows: %APPDATA%\DML Labs\DMLClean\config.toml
# macOS: ~/Library/Application Support/DML Labs/DMLClean/config.toml
# Linux: ~/.config/DML Labs/DMLClean/config.toml

# 2. Create config file
dmlclean config edit

# 3. Use custom path
export DMLCLEAN_CONFIG=/path/to/config.toml

# 4. Reset to defaults
dmlclean config reset
```

---

### Issue: Invalid configuration

**Symptoms:**
```
Error: Invalid configuration: [error details]
```

**Solutions:**

```bash
# 1. Validate TOML syntax
# Use online validator: https://toml.io/en/

# 2. Check option names (case-sensitive)
# Compare with example config

# 3. Validate with DMLClean
dmlclean config validate

# 4. Reset to defaults
dmlclean config reset
```

---

### Issue: Environment variables not working

**Symptoms:**
- Environment variables ignored
- Config not overridden

**Solutions:**

```bash
# 1. Check variable names (exact match required)
export DMLCLEAN_CONFIG=/path/to/config.toml  # Correct
export DMLCLEANconfig=/path/to/config.toml  # Wrong

# 2. Verify variables are set
echo $DMLCLEAN_CONFIG

# 3. Set before running command
DMLCLEAN_CONFIG=/path/to/config.toml dmlclean scan

# 4. Add to shell config (permanent)
echo "export DMLCLEAN_CONFIG=/path/to/config.toml" >> ~/.bashrc
source ~/.bashrc
```

---

## Database Issues

### Issue: Database locked

**Symptoms:**
```
Error: database is locked
```

**Causes:**
1. Another DMLClean instance running
2. Previous instance didn't close properly
3. Database corruption

**Solutions:**

```bash
# 1. Close other DMLClean instances
ps aux | grep dmlclean
kill <pid>

# 2. Remove lock file
# Windows: %LOCALAPPDATA%\DML Labs\DMLClean\data\dml_clean.db-shm
# macOS/Linux: ~/.local/share/DML\ Labs/DMLClean/data/dml_clean.db-shm

rm ~/.local/share/DML\ Labs/DMLClean/data/dml_clean.db-shm
rm ~/.local/share/DML\ Labs/DMLClean/data/dml_clean.db-wal

# 3. Restart computer (if lock persists)

# 4. Backup and recreate database
cp ~/.local/share/DML\ Labs/DMLClean/data/dml_clean.db ~/.local/share/DML\ Labs/DMLClean/data/dml_clean.db.backup
rm ~/.local/share/DML\ Labs/DMLClean/data/dml_clean.db
dmlclean doctor  # Recreates database
```

---

### Issue: Database corruption

**Symptoms:**
```
Error: database disk image is malformed
```

**Solutions:**

```bash
# 1. Backup database
cp ~/.local/share/DML\ Labs/DMLClean/data/dml_clean.db dml_clean.db.backup

# 2. Try to repair
sqlite3 ~/.local/share/DML\ Labs/DMLClean/data/dml_clean.db "PRAGMA integrity_check;"

# 3. Recreate database
rm ~/.local/share/DML\ Labs/DMLClean/data/dml_clean.db
dmlclean doctor

# 4. Restore data from backup (if needed)
# History will be lost, but DMLClean will work
```

---

## Notification Issues

### Issue: Notifications not showing

**Symptoms:**
- Cleaning completes but no notification
- Notifications disabled

**Solutions:**

```bash
# 1. Check notification settings
# Edit config.toml:
[notifications]
enabled = true
on_clean_complete = true

# 2. Test notifications
dmlclean doctor

# 3. Check OS notification settings
# Windows: Settings > System > Notifications
# macOS: System Preferences > Notifications
# Linux: Settings > Notifications

# 4. Install notification libraries
pip install desktop-notifier plyer
```

---

### Issue: Notifications not working on Linux

**Symptoms:**
- Notifications work on Windows/macOS but not Linux

**Solutions:**

```bash
# 1. Install notification daemon
# Ubuntu/Debian:
sudo apt install notification-daemon

# Fedora:
sudo dnf install notification-daemon

# 2. Check D-Bus is running
systemctl --user status dbus

# 3. Test with notify-send
notify-send "Test" "Notification test"
```

---

## Schedule Issues

### Issue: Scheduled cleaning not running

**Symptoms:**
- Schedule added but never runs
- No cleaning at scheduled time

**Solutions:**

```bash
# 1. Check schedule status
dmlclean schedule list

# 2. Enable schedule
dmlclean schedule enable "Daily Clean"

# 3. Check DMLClean is running
# Scheduler requires DMLClean to be running

# 4. Use system scheduler instead
# Cron (macOS/Linux):
crontab -e
# Add: 0 2 * * * /usr/local/bin/dmlclean clean --mode trash --yes

# Task Scheduler (Windows):
# Create basic task in Task Scheduler
```

---

### Issue: Schedule runs but fails

**Symptoms:**
- Schedule triggers
- Cleaning fails

**Solutions:**

```bash
# 1. Check logs
cat ~/.local/state/DML\ Labs/DMLClean/Logs/dmlclean.log

# 2. Test schedule manually
dmlclean schedule run "Daily Clean"

# 3. Check permissions
# Scheduled tasks may run with different user

# 4. Use full paths in schedule
# Edit config.toml:
[[scheduling.jobs]]
cron_expression = "0 2 * * *"
# Use absolute paths
```

---

## Windows-Specific

### Issue: Windows Defender warning

**Symptoms:**
- Windows Defender flags DMLClean
- Binary blocked

**Solutions:**

```powershell
# 1. Verify download
# Check SHA256 checksum from GitHub Releases

# 2. Add to Windows Defender exclusions
# Settings > Update & Security > Windows Security
# > Virus & threat protection > Manage settings
# > Exclusions > Add an exclusion

# 3. Unblock file
powershell -Command "Unblock-File -Path 'C:\path\to\dmlclean.exe'"

# 4. Submit to Microsoft for whitelisting
# https://www.microsoft.com/en-us/wdsi/filesubmission
```

---

### Issue: Path too long on Windows

**Symptoms:**
```
Error: Path too long: C:\...\very\long\path
```

**Solutions:**

```powershell
# 1. Enable long paths in Windows
# Registry: HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem
# Set: LongPathsEnabled = 1

# 2. Or use PowerShell
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
  -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# 3. Restart computer
```

---

## macOS-Specific

### Issue: "App can't be opened" on macOS

**Symptoms:**
- macOS blocks DMLClean binary
- "Unidentified developer" warning

**Solutions:**

```bash
# 1. Allow in Security settings
# System Preferences > Security & Privacy > General
# Click "Allow Anyway"

# 2. Or remove quarantine attribute
xattr -d com.apple.quarantine /usr/local/bin/dmlclean

# 3. Or use sudo
sudo xattr -rd com.apple.quarantine /usr/local/bin/dmlclean
```

---

### Issue: Apple Silicon (M1/M2) compatibility

**Symptoms:**
- Binary doesn't run on M1/M2 Mac

**Solutions:**

```bash
# 1. Use Rosetta 2
softwareupdate --install-rosetta

# 2. Or use Docker (native ARM support)
docker pull ghcr.io/devmayank-official/dml-clean:latest

# 3. Or install from source
pip install dmlclean
```

---

## Linux-Specific

### Issue: "No such file or directory" on Linux

**Symptoms:**
```bash
bash: ./dmlclean: No such file or directory
```

**Causes:**
1. Wrong architecture
2. Missing libraries

**Solutions:**

```bash
# 1. Check architecture
file dmlclean
uname -m

# 2. Install required libraries
# Ubuntu/Debian:
sudo apt install libc6 libgcc1

# 3. Or use Python version
pip install dmlclean

# 4. Or use Docker
docker pull ghcr.io/devmayank-official/dml-clean:latest
```

---

### Issue: Desktop notifications not working on Linux

**Symptoms:**
- No notifications on Linux desktop

**Solutions:**

```bash
# 1. Install notification daemon
sudo apt install notification-daemon  # Ubuntu/Debian
sudo dnf install notification-daemon  # Fedora

# 2. Check D-Bus
systemctl --user status dbus

# 3. Test with notify-send
notify-send "Test" "Test notification"

# 4. Install plyer
pip install plyer
```

---

## Error Codes

DMLClean uses standard exit codes:

| Code | Meaning | Common Causes | Solutions |
|------|---------|---------------|-----------|
| `0` | Success | - | - |
| `1` | General error | Unknown error | Check logs |
| `2` | Config error | Invalid config | `dmlclean config validate` |
| `3` | Partial success | Some files failed | Check error messages |
| `64` | Usage error | Wrong arguments | Check command syntax |
| `65` | Data format error | Invalid data | Check input format |
| `66` | File not found | Missing file | Check file exists |
| `67` | Permission denied | No permissions | Check permissions |
| `68` | Protected zone violation | Protected file | Check Protected Zone |
| `69` | Database error | DB locked/corrupt | See Database Issues |
| `70` | Plugin error | Plugin failed | Check plugin logs |

---

## Getting Help

### Still having issues?

**1. Check logs:**
```bash
# View logs
dmlclean doctor --verbose

# Log file location
# Windows: %LOCALAPPDATA%\DML Labs\DMLClean\Logs\dmlclean.log
# macOS/Linux: ~/.local/state/DML\ Labs/DMLClean/Logs/dmlclean.log

# Tail logs (real-time)
tail -f ~/.local/state/DML\ Labs/DMLClean/Logs/dmlclean.log
```

**2. Run diagnostics:**
```bash
dmlclean doctor
```

**3. Check documentation:**
- [FAQ](FAQ.md)
- [CLI Reference](CLI_REFERENCE.md)
- [Configuration](CONFIGURATION.md)
- [Quick Start](QUICKSTART.md)

**4. Get help from community:**
- 💬 [GitHub Discussions](https://github.com/Devmayank-official/dml-clean/discussions)
- 🐛 [GitHub Issues](https://github.com/Devmayank-official/dml-clean/issues)
- 📧 Email: dmlclean@dmlabs.dev

**5. Report a bug:**
```bash
# Gather information
dmlclean doctor --json > system-info.json

# Include in bug report:
# - DMLClean version
# - OS version
# - Steps to reproduce
# - Expected vs actual behavior
# - Logs (system-info.json)
```

---

## Quick Reference

### Common Commands

```bash
# Diagnostics
dmlclean doctor

# View logs
dmlclean doctor --verbose

# Reset configuration
dmlclean config reset

# Clear cache
dmlclean storage cleanup

# View history
dmlclean history list

# Test notifications
dmlclean doctor

# Validate config
dmlclean config validate
```

### Log Locations

| Platform | Log File |
|----------|----------|
| **Windows** | `%LOCALAPPDATA%\DML Labs\DMLClean\Logs\dmlclean.log` |
| **macOS** | `~/Library/Logs/DML Labs/DMLClean/dmlclean.log` |
| **Linux** | `~/.local/state/DML Labs/DMLClean/Logs/dmlclean.log` |

### Config Locations

| Platform | Config File |
|----------|-------------|
| **Windows** | `%APPDATA%\DML Labs\DMLClean\config.toml` |
| **macOS** | `~/Library/Application Support/DML Labs/DMLClean/config.toml` |
| **Linux** | `~/.config/DML Labs/DMLClean/config.toml` |

---

**Developed by DML Labs**  
**Lead Engineer:** [@Devmayank-official](https://github.com/Devmayank-official)  
**Repository:** https://github.com/Devmayank-official/dml-clean
