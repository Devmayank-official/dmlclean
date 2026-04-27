# Contributing to DMLClean

Thank you for your interest in contributing to DMLClean! This document provides guidelines and instructions for contributing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

---

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to maintain a welcoming and inclusive community.

---

## Getting Started

### What You Can Work On

- 🐛 Bug fixes
- ✨ New features
- 📝 Documentation improvements
- 🧪 Test coverage improvements
- 🔒 Security enhancements
- 🎨 UI/UX improvements
- 📦 Performance optimizations

### Finding Issues

- Look for issues labeled [`good first issue`](https://github.com/dmlclean/dmlclean/labels/good%20first%20issue) for beginner-friendly tasks
- Check [`help wanted`](https://github.com/dmlclean/dmlclean/labels/help%20wanted) for issues needing contributions
- Browse the [roadmap](ROADMAP.md) for upcoming features

---

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- pip or pipx

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/dmlclean/dmlclean.git
cd dmlclean

# Run the setup script
# On Unix/macOS:
./scripts/setup.sh

# On Windows:
.\scripts\setup.bat
```

### Manual Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Unix/macOS:
source .venv/bin/activate
# On Windows:
.\.venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

---

## How to Contribute

### 1. Fork the Repository

```bash
# Click "Fork" on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/dmlclean.git
cd dmlclean
```

### 2. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-123
```

### 3. Make Your Changes

- Follow the [coding standards](#coding-standards)
- Write tests for new features
- Update documentation as needed

### 4. Test Your Changes

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=dmlclean --cov-report=term-missing

# Run linters
ruff check src/ tests/
ruff format src/ tests/

# Run type checker
mypy --strict src/

# Run security scan
bandit -r src/ -ll
```

### 5. Commit Your Changes

```bash
# Add changes
git add .

# Commit with conventional commits format
git commit -m "feat: add new cleaning category for XYZ"
# or
git commit -m "fix: resolve issue with protected zone detection"
```

### 6. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create a Pull Request on GitHub
```

---

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use [ruff](https://github.com/astral-sh/ruff) for linting and formatting
- Maximum line length: 100 characters
- Use type hints on all functions

### Type Hints

```python
# ✅ Good
def calculate_size(path: Path) -> int:
    """Calculate total size of directory."""
    ...

# ❌ Bad
def calculate_size(path):  # Missing type hints
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def clean_files(
    paths: list[Path],
    mode: str = "dry-run",
) -> CleanResult:
    """
    Clean files from specified paths.

    Args:
        paths: List of file paths to clean.
        mode: Clean mode ('dry-run', 'trash', 'permanent').

    Returns:
        CleanResult: Result of cleaning operation.

    Raises:
        ProtectedZoneError: If path is protected.
    """
```

### Error Handling

- Use custom exceptions from `dmlclean.exceptions`
- Never use bare `except:` clauses
- Always provide meaningful error messages

```python
# ✅ Good
try:
    result = process_file(path)
except FileNotFoundError as e:
    logger.error(f"File not found: {path}")
    raise

# ❌ Bad
try:
    result = process_file(path)
except:
    pass
```

---

## Testing

### Writing Tests

- Use pytest for all tests
- Use pyfakefs for file system tests (never touch real disk)
- Follow the naming convention: `test_*.py` files, `test_*` functions
- Aim for >90% test coverage on new code

### Example Test

```python
def test_scanner_finds_temp_files(fake_fs: FakeFilesystem) -> None:
    """Test that scanner identifies temporary files."""
    # Create test files
    test_file = Path("/tmp/test.tmp")
    fake_fs.create_file(test_file, contents="test")

    # Run scanner
    scanner = FileSystemScanner()
    result = asyncio.run(scanner.scan([Path("/tmp")]))

    # Assert
    assert len(result.paths) > 0
    assert test_file in result.paths
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/unit/test_scanner.py

# Run with coverage
pytest tests/ --cov=dmlclean --cov-report=html

# Run tests in parallel
pytest tests/ -n auto
```

---

## Pull Request Process

### Before Submitting

1. ✅ All tests pass
2. ✅ Linters pass (`ruff check`, `ruff format`)
3. ✅ Type checker passes (`mypy --strict`)
4. ✅ Security scan passes (`bandit`)
5. ✅ Coverage is ≥70%
6. ✅ Documentation is updated

### PR Title Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat: Add new feature`
- `fix: Fix bug in scanner`
- `docs: Update README`
- `test: Add tests for cleaner`
- `refactor: Improve error handling`
- `chore: Update dependencies`

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Linters pass
- [ ] Type checking passes

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

---

## Reporting Issues

### Bug Reports

Use the bug report template and include:

- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Python version
- Operating system
- DMLClean version
- Error messages/logs

### Feature Requests

- Describe the feature
- Explain the use case
- Provide examples if possible

### Security Issues

**DO NOT** create public issues for security vulnerabilities. See [SECURITY.md](SECURITY.md) for responsible disclosure.

---

## Questions?

- 💬 [GitHub Discussions](https://github.com/dmlclean/dmlclean/discussions)
- 📧 Email: dmlclean@dmlabs.dev

---

Thank you for contributing to DMLClean! 🎉
