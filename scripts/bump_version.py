#!/usr/bin/env python3
"""
Bump version script for DMLClean.

Usage:
    python scripts/bump_version.py [major|minor|patch]
"""

import re
import sys
from pathlib import Path


def get_current_version(pyproject_path: Path) -> str:
    """Get current version from pyproject.toml."""
    content = pyproject_path.read_text()
    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if not match:
        raise ValueError("Version not found in pyproject.toml")
    return match.group(1)


def bump_version(version: str, bump_type: str) -> str:
    """Bump version based on type."""
    major, minor, patch = map(int, version.split("."))

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

    return f"{major}.{minor}.{patch}"


def update_version(new_version: str, pyproject_path: Path) -> None:
    """Update version in pyproject.toml."""
    content = pyproject_path.read_text()
    content = re.sub(
        r'(version\s*=\s*")([^"]+)(")',
        f'\\g<1>{new_version}\\g<3>',
        content,
    )
    pyproject_path.write_text(content)


def main() -> None:
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python bump_version.py [major|minor|patch]")
        sys.exit(1)

    bump_type = sys.argv[1].lower()
    if bump_type not in ("major", "minor", "patch"):
        print(f"Invalid bump type: {bump_type}")
        print("Usage: python bump_version.py [major|minor|patch]")
        sys.exit(1)

    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    pyproject_path = project_root / "pyproject.toml"

    # Get current version
    current_version = get_current_version(pyproject_path)
    print(f"Current version: {current_version}")

    # Bump version
    new_version = bump_version(current_version, bump_type)
    print(f"New version: {new_version}")

    # Update version
    update_version(new_version, pyproject_path)
    print(f"Updated {pyproject_path}")

    # Update __init__.py
    init_path = project_root / "src" / "dmlclean" / "__init__.py"
    if init_path.exists():
        content = init_path.read_text()
        content = re.sub(
            r'(__version__\s*=\s*")([^"]+)(")',
            f'\\g<1>{new_version}\\g<3>',
            content,
        )
        init_path.write_text(content)
        print(f"Updated {init_path}")

    print("\nVersion bump complete!")


if __name__ == "__main__":
    main()
