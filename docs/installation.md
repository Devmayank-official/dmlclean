# Installation Guide

This guide covers all installation methods for DMLClean.

## Prerequisites

- **Python**: 3.11 or higher
- **pip** or **pipx** (recommended)

---

## Method 1: pipx (Recommended)

pipx installs Python applications in isolated environments.

```bash
# Install pipx (if not already installed)
pip install pipx
pipx ensurepath

# Install DMLClean
pipx install dmlclean
```

**Benefits:**
- ✅ Isolated from other Python packages
- ✅ No dependency conflicts
- ✅ Easy to update and uninstall

---

## Method 2: pip

```bash
pip install dmlclean
```

Or for a specific version:

```bash
pip install dmlclean==0.1.0
```

---

## Method 3: From Source

```bash
# Clone the repository
git clone https://github.com/dmlclean/dmlclean.git
cd dmlclean

# Install in development mode
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

---

## Method 4: Docker

```bash
# Pull from Docker Hub
docker pull dmlclean/dmlclean:latest

# Run scan
docker run -v /:/host dmlclean/dmlclean:latest scan --path /host/tmp
```

---

## Method 5: Binary Download

Download pre-built binaries from [GitHub Releases](https://github.com/dmlclean/dmlclean/releases):

- `dmlclean-linux-x86_64`
- `dmlclean-macos-x86_64`
- `dmlclean-macos-arm64`
- `dmlclean-windows-x86_64.exe`

---

## Method 6: Homebrew (macOS)

```bash
# Add the DMLClean tap
brew tap dmlclean/homebrew-dmlclean

# Install
brew install dmlclean
```

---

## Verify Installation

```bash
# Check version
dmlclean --version

# Show help
dmlclean --help

# Run diagnostics
dmlclean doctor
```

---

## Uninstall

### pipx
```bash
pipx uninstall dmlclean
```

### pip
```bash
pip uninstall dmlclean
```

### Binary
```bash
# Just delete the binary file
rm /usr/local/bin/dmlclean
```

---

## Next Steps

- [Quick Start Guide](QUICKSTART.md) - Get started in 5 minutes
- [Usage Guide](usage.md) - Learn all commands
- [Configuration](configuration.md) - Customize DMLClean
