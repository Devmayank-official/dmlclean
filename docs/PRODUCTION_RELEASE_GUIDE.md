# DMLClean Production Release Guide

This guide covers everything needed to release DMLClean to production.

---

## ✅ Pre-Release Checklist

### 1. Code Quality Gates

```bash
# All tests must pass
pytest tests/ --cov-fail-under=70

# No linting errors
ruff check src/ tests/
ruff format --check src/ tests/

# No type errors
mypy --strict src/

# No security issues
bandit -r src/ -ll
```

### 2. Update Version

```bash
# Bump version (choose one)
python scripts/bump_version.py patch  # 0.1.0 → 0.1.1
python scripts/bump_version.py minor  # 0.1.0 → 0.2.0
python scripts/bump_version.py major  # 0.1.0 → 1.0.0

# Verify version
dmlclean version
```

### 3. Update Documentation

- [ ] Update `CHANGELOG.md` with release notes
- [ ] Update `README.md` if features changed
- [ ] Update version in `docs/installation.md`

---

## 🚀 Release Process

### Step 1: Create Release Tag

```bash
# Commit all changes
git add .
git commit -m "chore: release v0.1.0"

# Create tag
git tag -a v0.1.0 -m "Release v0.1.0"

# Push tag (this triggers CI/CD)
git push origin main --tags
```

### Step 2: CI/CD Automatically Builds

GitHub Actions will automatically:

1. ✅ Run quality checks (lint, type-check, security)
2. ✅ Run matrix tests (3 Python × 3 OS = 9 combinations)
3. ✅ Build PyPI package (wheel + sdist)
4. ✅ Build Docker image (multi-arch)
5. ✅ Build binaries (Windows .exe, macOS .app, Linux)
6. ✅ Create GitHub Release with all artifacts

**Monitor:** https://github.com/dmlclean/dmlclean/actions

---

## 📦 Distribution Channels

### 1. PyPI (Automatic)

**Status:** ✅ Configured in CI/CD

**What happens:**
- Wheel and sdist uploaded to PyPI
- Available via: `pip install dmlclean`

**Manual verification:**
```bash
pip install dmlclean==0.1.0
dmlclean version
```

**Secrets required:**
- `PYPI_API_TOKEN` in GitHub repository settings

---

### 2. Docker - ghcr.io (Automatic)

**Status:** ✅ Configured in CI/CD

**What happens:**
- Multi-arch image built (linux/amd64, linux/arm64)
- Pushed to: `ghcr.io/dmlclean/dmlclean:latest`
- Tagged with version: `ghcr.io/dmlclean/dmlclean:v0.1.0`

**Manual verification:**
```bash
docker pull ghcr.io/dmlclean/dmlclean:latest
docker run ghcr.io/dmlclean/dmlclean version
```

**Secrets required:**
- GitHub Packages access (automatic for repo owners)

---

### 3. GitHub Releases (Automatic)

**Status:** ✅ Configured in CI/CD

**What happens:**
- GitHub Release created from tag
- Binaries attached:
  - `dmlclean-windows-x86_64.exe`
  - `dmlclean-macos-x86_64`
  - `dmlclean-macos-arm64`
  - `dmlclean-linux-x86_64`
- SHA256 checksums generated

**Download:** https://github.com/dmlclean/dmlclean/releases

---

### 4. Homebrew (Manual - Optional)

**Status:** ❌ Not automated

**Steps:**
1. Create Homebrew tap repository
2. Generate formula with `scripts/gen_homebrew_formula.py`
3. Submit to homebrew-core or maintain tap

**Commands:**
```bash
# Generate formula
python scripts/gen_homebrew_formula.py v0.1.0

# Submit to tap
brew tap dmlclean/dmlclean
brew install dmlclean
```

---

## 🔐 Code Signing (Optional but Recommended)

### Windows (.exe)

**Required:**
- Code signing certificate (e.g., DigiCert, Sectigo)
- Sign with `signtool.exe`

```powershell
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist/dmlclean.exe
```

### macOS (.app)

**Required:**
- Apple Developer ID
- Notarization for Gatekeeper

```bash
# Sign
codesign --sign "Developer ID" --timestamp --options runtime dist/dmlclean.app

# Notarize
xcrun notarytool submit dist/dmlclean.app --apple-id "your@email.com" --password "app-password"
```

### Linux

**Optional:**
- GPG sign release files
- Create .deb or .rpm packages

---

## 🧪 Post-Release Verification

### 1. Verify PyPI Installation

```bash
pipx install dmlclean
dmlclean version
# Should show: 0.1.0
```

### 2. Verify Docker

```bash
docker pull ghcr.io/dmlclean/dmlclean:latest
docker run --rm ghcr.io/dmlclean/dmlclean version
```

### 3. Verify Binary

Download from GitHub Releases and run:
```bash
./dmlclean version
```

### 4. Monitor Issues

Watch for:
- Installation issues
- Platform-specific bugs
- Performance regressions

---

## 📊 Release Metrics

Track these after each release:

- **PyPI Downloads:** https://pypistats.org/packages/dmlclean
- **Docker Pulls:** https://ghcr.io/dmlclean/dmlclean
- **GitHub Stars:** Watch for spikes
- **Issues/PRs:** Community engagement

---

## 🔧 Troubleshooting

### PyPI Publish Fails

**Check:**
1. Version number is unique (not already on PyPI)
2. `PYPI_API_TOKEN` secret is valid
3. Token has "upload" permissions

### Docker Push Fails

**Check:**
1. GitHub Packages enabled in repository settings
2. `GITHUB_TOKEN` has write permissions
3. Image tags are unique

### Binary Build Fails

**Check:**
1. All dependencies are in `hiddenimports`
2. PyInstaller version is compatible
3. Build machine has required libraries

---

## 📝 Release Notes Template

```markdown
## [0.1.0] - 2026-03-01

### Added
- Initial release of DMLClean
- 14 cleaning categories
- Cross-platform support (Windows, macOS, Linux)
- Protected Zone safety feature
- Undo support for trash operations
- Scheduled cleaning with cron integration

### Security
- Protected Zone blocks critical paths
- Manifest logging for all operations
- No network calls (air-gapped compatible)

### Known Issues
- [List any known issues]

### Upgrade Notes
- First release - no upgrade path needed
```

---

## 🎯 Next Release Planning

After each release:

1. Review GitHub issues and PRs
2. Plan next milestone
3. Update ROADMAP.md
4. Communicate with community

---

**Questions?** Open an issue on GitHub or contact dmlclean@dmlabs.dev
