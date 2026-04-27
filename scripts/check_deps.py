#!/usr/bin/env python3
"""
Check dependencies for DMLClean.

Verifies that all required dependencies are installed.
"""

import sys
from importlib import import_module
from pathlib import Path


def check_dependencies() -> bool:
    """Check if all dependencies are installed."""
    # Read dependencies from pyproject.toml
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        print("Error: pyproject.toml not found")
        return False

    content = pyproject_path.read_text()

    # Extract dependencies (simple parsing)
    deps = [
        "typer",
        "rich",
        "psutil",
        "send2trash",
        "platformdirs",
        "aiofiles",
        "apscheduler",
        "loguru",
        "pydantic",
        "xxhash",
        "humanize",
        "watchdog",
        "croniter",
        "parsedatetime",
    ]

    dev_deps = [
        "pytest",
        "pyfakefs",
        "ruff",
        "mypy",
        "bandit",
        "hatch",
        "pyinstaller",
    ]

    all_ok = True

    print("Checking core dependencies...")
    for dep in deps:
        try:
            import_module(dep.replace("-", "_"))
            print(f"  ✓ {dep}")
        except ImportError:
            print(f"  ✗ {dep} - MISSING")
            all_ok = False

    print("\nChecking dev dependencies...")
    for dep in dev_deps:
        try:
            import_module(dep.replace("-", "_"))
            print(f"  ✓ {dep}")
        except ImportError:
            print(f"  ✗ {dep} - MISSING (optional)")

    return all_ok


def main() -> None:
    """Main function."""
    print("=" * 50)
    print("DMLClean - Dependency Check")
    print("=" * 50)
    print()

    all_ok = check_dependencies()

    print()
    print("=" * 50)
    if all_ok:
        print("✓ All dependencies are installed!")
    else:
        print("✗ Some dependencies are missing")
        print("\nInstall with:")
        print("  pip install -e '.[dev]'")
        sys.exit(1)


if __name__ == "__main__":
    main()
