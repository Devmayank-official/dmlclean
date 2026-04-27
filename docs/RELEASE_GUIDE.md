# DMLClean v0.1.0 - Binary Build & Release Guide

**Version:** 0.1.0  
**Status:** Production Ready  
**Last Updated:** 2026-03-13

---

## 📋 Table of Contents

- [Windows Binary Build](#windows-binary-build)
- [SHA256 Checksums](#sha256-checksums)
- [VirusTotal Scan](#virustotal-scan)
- [Testing on Windows VM](#testing-on-windows-vm)
- [Docker Image Build](#docker-image-build)
- [Release Checklist](#release-checklist)

---

## Windows Binary Build

### Prerequisites

```bash
# Ensure you have:
- Python 3.11+ installed
- pip install pyinstaller hatch
- Git repository clean
- All tests passing
```

### Build Steps

#### Step 1: Clean Build Environment

```bash
# Windows PowerShell (Run as Administrator)
cd C:\Users\Santosh\Desktop\hetrick-ai-main\Dmlclean

# Clean previous builds
Remove-Item -Recurse -Force build, dist, *.egg-info -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force __pycache__, .pytest_cache, .mypy_cache -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .ruff_cache, .coverage, htmlcov -ErrorAction SilentlyContinue

# Verify clean
git status
```

#### Step 2: Build Python Package

```bash
# Build wheel and source distribution
hatch build --clean

# Verify build output
ls dist/
# Should see:
# - dmlclean-0.1.0-py3-none-any.whl
# - dmlclean-0.1.0.tar.gz
```

#### Step 3: Build PyInstaller Binary

```bash
# Build Windows executable
pyinstaller dmlclean.spec --clean --noconfirm

# Output will be in:
# dist/dmlclean.exe

# Verify binary
.\dist\dmlclean.exe --version
.\dist\dmlclean.exe --help
```

#### Step 4: Test Binary Functionality

```bash
# Test all major commands
.\dist\dmlclean.exe version
.\dist\dmlclean.exe scan --help
.\dist\dmlclean.exe clean --help
.\dist\dmlclean.exe doctor

# Test actual scan (dry-run)
.\dist\dmlclean.exe scan --path C:\Windows\Temp --mode fast

# Test clean preview
.\dist\dmlclean.exe clean --mode dry-run --path C:\Windows\Temp
```

---

## SHA256 Checksums

### Generate Checksums

```bash
# Windows PowerShell
cd dist

# Generate SHA256 checksums
sha256sum * > SHA256SUMS.txt

# Or using PowerShell native command
Get-FileHash *.exe, *.whl, *.tar.gz -Algorithm SHA256 | 
  Format-List | 
  Out-File SHA256SUMS.txt

# Verify checksums
sha256sum -c SHA256SUMS.txt
```

### Example SHA256SUMS.txt

```
a1b2c3d4e5f6...  dmlclean-0.1.0-py3-none-any.whl
f6e5d4c3b2a1...  dmlclean-0.1.0.tar.gz
1234567890abcdef...  dmlclean.exe
```

---

## VirusTotal Scan

### Upload to VirusTotal

**Option 1: Web Interface**

1. Go to https://www.virustotal.com
2. Click "Choose file"
3. Select `dist/dmlclean.exe`
4. Click "Confirm"
5. Wait for scan results (2-5 minutes)
6. Save report URL for release notes

**Option 2: PowerShell Script**

```powershell
# Upload to VirusTotal API
$apiKey = "YOUR_VIRUSTOTAL_API_KEY"
$filePath = "dist\dmlclean.exe"

# Upload file
$response = Invoke-RestMethod `
  -Uri "https://www.virustotal.com/api/v3/files" `
  -Method POST `
  -Headers @{
    "x-apikey" = $apiKey
  } `
  -Form @{
    file = Get-Item $filePath
  }

# Get analysis URL
$analysisUrl = $response.data.links.self
Write-Host "Analysis URL: $analysisUrl"
```

### Include in Release

Add to GitHub Release notes:

```markdown
## Security Scan

✅ VirusTotal Scan: [View Report](https://www.virustotal.com/gui/file/...)
- Scanned by: 70+ antivirus engines
- Detections: 0/70 (Clean)
- Scan Date: 2026-03-13
```

---

## Testing on Windows VM

### Test Environment Setup

**Recommended VM Configuration:**

- **OS:** Windows 10/11 (64-bit)
- **RAM:** 4GB minimum
- **Storage:** 20GB free space
- **Network:** Isolated (for security testing)

### Test Checklist

#### 1. Installation Test

```powershell
# Download binary from GitHub Releases
# Run installer or copy to PATH

# Verify installation
dmlclean --version
dmlclean --help
```

**Expected:** Commands work, no errors

---

#### 2. Scan Test

```powershell
# Scan temp directory
dmlclean scan --path C:\Windows\Temp

# Scan user cache
dmlclean scan --path $env:LOCALAPPDATA\Temp

# Deep scan
dmlclean scan --mode deep --path C:\Users\Public
```

**Expected:**
- Finds cleanable files
- Shows category breakdown
- No crashes or errors

---

#### 3. Clean Test (Dry-Run)

```powershell
# Preview cleaning
dmlclean clean --mode dry-run --path C:\Windows\Temp

# With specific categories
dmlclean clean --categories system_junk --mode dry-run
```

**Expected:**
- Shows files that would be deleted
- No files actually deleted
- Protected zone respected

---

#### 4. Clean Test (Trash Mode)

```powershell
# Create test files
New-Item -Path C:\temp\test.tmp -ItemType File -Force
New-Item -Path C:\temp\test.log -ItemType File -Force

# Clean to trash
dmlclean clean --mode trash --path C:\temp --yes

# Verify files moved to Recycle Bin
# Check Recycle Bin for test files
```

**Expected:**
- Files moved to Recycle Bin
- Can be restored from Recycle Bin
- No data loss

---

#### 5. Protected Zone Test

```powershell
# Add protected path
dmlclean protect add C:\Users\Public\Important

# Verify protection
dmlclean protect check C:\Users\Public\Important

# Try to clean protected path (should be blocked)
dmlclean clean --path C:\Users\Public\Important --mode trash
```

**Expected:**
- Path added to protected list
- Check shows "protected"
- Clean operation skips protected files

---

#### 6. Undo Test

```powershell
# Create test files
New-Item -Path C:\temp\undo-test.txt -ItemType File -Force

# Clean to trash
dmlclean clean --mode trash --path C:\temp --yes

# View history
dmlclean history list

# Undo last operation
dmlclean history undo

# Verify file restored
Test-Path C:\temp\undo-test.txt
```

**Expected:**
- File restored from trash
- History shows undo operation
- No data loss

---

#### 7. Performance Test

```powershell
# Measure scan time
Measure-Command {
  dmlclean scan --path C:\Users
}

# Measure clean time
Measure-Command {
  dmlclean clean --mode trash --path C:\temp --yes
}
```

**Expected:**
- Fast scan: < 5 seconds for 100K files
- Clean: < 10 seconds for 1K files
- Memory usage < 200MB

---

#### 8. Error Handling Test

```powershell
# Test invalid path
dmlclean scan --path Z:\NonExistent

# Test permission denied
dmlclean scan --path C:\System Volume Information

# Test invalid config
dmlclean --config C:\invalid\config.toml scan
```

**Expected:**
- Graceful error messages
- Non-zero exit codes
- No crashes

---

## Docker Image Build

### Multi-Architecture Build

#### Prerequisites

```bash
# Install Docker Desktop
# Enable Docker Buildx
docker buildx create --use
docker buildx inspect --bootstrap
```

#### Build Commands

```bash
# Login to registries
docker login ghcr.io -u Devmayank-official -p YOUR_GITHUB_TOKEN
docker login -u devmayankofficial -p YOUR_DOCKER_HUB_TOKEN

# Build multi-arch image
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ghcr.io/devmayank-official/dml-clean:0.1.0 \
  -t ghcr.io/devmayank-official/dml-clean:latest \
  -t devmayankofficial/dml-clean:0.1.0 \
  -t devmayankofficial/dml-clean:latest \
  --push \
  .

# Verify build
docker buildx imagetools inspect ghcr.io/devmayank-official/dml-clean:0.1.0
```

#### Test Docker Image

```bash
# Test scan
docker run --rm \
  -v /:/host:ro \
  ghcr.io/devmayank-official/dml-clean:0.1.0 \
  scan --path /host/tmp

# Test clean (dry-run)
docker run --rm \
  -v /:/host:ro \
  ghcr.io/devmayank-official/dml-clean:0.1.0 \
  clean --mode dry-run --path /host/tmp

# Test with config
docker run --rm \
  -v ./config.toml:/home/dmlclean/.config/DML\ Labs/DMLClean/config.toml \
  ghcr.io/devmayank-official/dml-clean:0.1.0 \
  scan
```

---

## Release Checklist

### Pre-Release (1 Week Before)

- [ ] All tests passing
- [ ] Documentation complete
- [ ] CI/CD pipeline working
- [ ] Binary builds tested
- [ ] Docker images built
- [ ] Security scans complete
- [ ] Release notes drafted

### Release Day

#### Morning (9:00 AM)

- [ ] Final test on Windows VM
- [ ] Generate SHA256 checksums
- [ ] Upload to VirusTotal
- [ ] Create Git tag: `git tag -a v0.1.0 -m "v0.1.0 - Production Ready"`
- [ ] Push tag: `git push origin v0.1.0`

#### Afternoon (2:00 PM)

- [ ] CI/CD auto-builds triggered
- [ ] Monitor build progress
- [ ] Verify all artifacts created
- [ ] Review GitHub Release draft
- [ ] Add VirusTotal link to release notes
- [ ] Add checksums to release notes

#### Evening (6:00 PM)

- [ ] Publish GitHub Release
- [ ] Verify downloads working
- [ ] Test Docker images
- [ ] Update website/documentation
- [ ] Send announcement emails

### Post-Release (Next Day)

- [ ] Monitor GitHub Issues
- [ ] Monitor GitHub Discussions
- [ ] Check download statistics
- [ ] Respond to user feedback
- [ ] Document any issues found
- [ ] Plan v0.1.1 bugfix release if needed

---

## Release Notes Template

```markdown
# DMLClean v0.1.0 - Production Ready

**Release Date:** 2026-03-13

## 🎉 What's New

DMLClean v0.1.0 is the first production-ready release featuring:

### Core Features
- 🔍 Smart scanning with 14 cleaning categories
- 🧹 Safe cleaning with Protected Zone
- ↩️ Undo support for trash operations
- 📊 Rich terminal reports
- 🔔 Desktop notifications
- 📅 Scheduled cleaning
- 🐳 Docker support

### Safety Features
- Protected Zone (blocks critical files)
- Dry-run preview (default)
- Manifest logging
- Undo support
- Risk level classification

### Technical Excellence
- Type-safe Python (Pydantic v2)
- Async I/O for performance
- Cross-platform (Windows/macOS/Linux)
- 70%+ test coverage
- CI/CD pipeline

## 📦 Installation

### Windows Binary
```bash
# Download dmlclean.exe from GitHub Releases
# Add to PATH or run directly
dmlclean.exe --version
```

### Docker
```bash
docker pull ghcr.io/devmayank-official/dml-clean:0.1.0
docker run -v /:/host:ro ghcr.io/devmayank-official/dml-clean:0.1.0 scan --path /host/tmp
```

### From Source
```bash
pip install git+https://github.com/Devmayank-official/dml-clean.git@v0.1.0
```

## 🔒 Security

- ✅ VirusTotal Scan: [View Report](https://www.virustotal.com/...)
- ✅ SHA256 Checksums: Included in release assets
- ✅ No telemetry (air-gapped compatible)
- ✅ No network calls
- ✅ Local-only operation

## 📊 Statistics

- **Lines of Code:** 15,000+
- **Test Coverage:** 70%+
- **Documentation:** 12 files
- **CLI Commands:** 13
- **Cleaning Plugins:** 14
- **Built-in Profiles:** 5

## 🐛 Known Issues

- None at this time

## 📝 Documentation

- [Installation Guide](https://github.com/Devmayank-official/dml-clean/blob/main/docs/INSTALLATION.md)
- [Quick Start](https://github.com/Devmayank-official/dml-clean/blob/main/docs/QUICKSTART.md)
- [CLI Reference](https://github.com/Devmayank-official/dml-clean/blob/main/docs/CLI_REFERENCE.md)
- [Configuration](https://github.com/Devmayank-official/dml-clean/blob/main/docs/CONFIGURATION.md)
- [FAQ](https://github.com/Devmayank-official/dml-clean/blob/main/docs/FAQ.md)
- [Troubleshooting](https://github.com/Devmayank-official/dml-clean/blob/main/docs/TROUBLESHOOTING.md)

## 🙏 Acknowledgments

Thanks to all contributors and early testers!

## 📅 What's Next

v0.2.0 will include:
- PyPI publishing
- More cleaning categories
- GUI application (TBD)
- Performance improvements

---

**Developed by DML Labs**  
**Lead Engineer:** [@Devmayank-official](https://github.com/Devmayank-official)
```

---

## Quick Reference

### Build Commands Summary

```bash
# Clean
Remove-Item -Recurse -Force build, dist, *.egg-info

# Build package
hatch build --clean

# Build binary
pyinstaller dmlclean.spec --clean --noconfirm

# Generate checksums
sha256sum * > SHA256SUMS.txt

# Docker build
docker buildx build --platform linux/amd64,linux/arm64 -t ghcr.io/devmayank-official/dml-clean:0.1.0 --push .

# Create release
git tag -a v0.1.0 -m "v0.1.0 - Production Ready"
git push origin v0.1.0
```

---

**Developed by DML Labs**  
**Lead Engineer:** [@Devmayank-official](https://github.com/Devmayank-official)  
**Repository:** https://github.com/Devmayank-official/dml-clean
