"""
Protected Zone implementation for DMLClean.

The Protected Zone prevents accidental deletion of critical files and
directories by enforcing path-based, glob-based, and metadata-based
protection rules.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from loguru import logger


class ProtectionSource(str, Enum):
    """Source of a protection rule."""

    BUILTIN = "builtin"
    PROFILE = "profile"
    CUSTOM_PATH = "custom_path"
    CUSTOM_GLOB = "custom_glob"
    GIT_DIR = "git_dir"
    VENV = "venv"
    RECENT_FILE = "recent_file"


@dataclass
class ProtectionRule:
    """
    A single protection rule.

    Attributes:
        pattern: Path pattern or glob to match.
        source: Source of this protection rule.
        description: Human-readable description of what is protected.
        is_glob: Whether the pattern is a glob pattern.
        case_sensitive: Whether matching is case-sensitive.
    """

    pattern: str
    source: ProtectionSource
    description: str = ""
    is_glob: bool = False
    case_sensitive: bool = False

    def matches(self, path: Path) -> bool:
        """
        Check if a path matches this protection rule.

        Args:
            path: Path to check.

        Returns:
            bool: True if the path is protected by this rule.
        """
        path_str = str(path)
        pattern = self.pattern

        # Handle glob patterns
        if self.is_glob:
            if "**" in pattern:
                # Recursive glob - check if any part of path matches
                return self._match_recursive(path_str, pattern)
            else:
                # Simple glob
                return fnmatch.fnmatch(path_str, pattern)

        # Handle exact path matches
        if self.case_sensitive:
            return path_str == self.pattern
        else:
            return path_str.lower() == self.pattern.lower()

    def _match_recursive(self, path_str: str, pattern: str) -> bool:
        """
        Match a recursive glob pattern against a path.

        Args:
            path_str: Path as string.
            pattern: Glob pattern with ** wildcards.

        Returns:
            bool: True if pattern matches.
        """
        # Convert glob pattern to regex-like matching
        # ** matches any number of directories
        parts = pattern.split("**")
        if len(parts) == 2:
            prefix, suffix = parts
            suffix = suffix.lstrip("\\/")

            if prefix and not path_str.startswith(prefix):
                return False
            if suffix:
                return fnmatch.fnmatch(path_str, f"*{suffix}")
            return True

        # Fallback to simple fnmatch
        return fnmatch.fnmatch(path_str, pattern.replace("**", "*"))


@dataclass
class ProtectionResult:
    """
    Result of a protection check.

    Attributes:
        is_protected: Whether the path is protected.
        matching_rules: List of rules that matched (if any).
        reason: Human-readable reason for protection.
    """

    is_protected: bool
    matching_rules: list[ProtectionRule] = field(default_factory=list)
    reason: str = ""


class ProtectedZone:
    """
    Protected Zone manager for DMLClean.

    The Protected Zone maintains a set of protection rules and checks
    paths against them before any cleaning operation.

    Attributes:
        rules: List of active protection rules.
        enabled: Whether protection is enabled.
    """

    def __init__(
        self,
        enabled: bool = True,
        protected_paths: list[str] | None = None,
        custom_paths: list[str] | None = None,
        custom_globs: list[str] | None = None,
        protect_git_dirs: bool = True,
        protect_venvs: bool = True,
        protect_recent_days: int = 1,
    ) -> None:
        """
        Initialize the Protected Zone.

        Args:
            enabled: Whether protection is enabled.
            protected_paths: Built-in protected path patterns.
            custom_paths: User-defined protected paths.
            custom_globs: User-defined protected glob patterns.
            protect_git_dirs: Whether to protect .git directories.
            protect_venvs: Whether to protect virtual environments.
            protect_recent_days: Protect files modified within N days.
        """
        self.enabled = enabled
        self.rules: list[ProtectionRule] = []
        self._protect_recent_days = protect_recent_days

        # Load rules from configuration
        self._load_rules(
            protected_paths=protected_paths or [],
            custom_paths=custom_paths or [],
            custom_globs=custom_globs or [],
            protect_git_dirs=protect_git_dirs,
            protect_venvs=protect_venvs,
        )

        logger.debug(f"ProtectedZone initialized with {len(self.rules)} rules")

    def _load_rules(
        self,
        protected_paths: list[str],
        custom_paths: list[str],
        custom_globs: list[str],
        protect_git_dirs: bool,
        protect_venvs: bool,
    ) -> None:
        """
        Load protection rules from configuration.

        Args:
            protected_paths: Built-in protected path patterns.
            custom_paths: User-defined protected paths.
            custom_globs: User-defined protected glob patterns.
            protect_git_dirs: Whether to protect .git directories.
            protect_venvs: Whether to protect virtual environments.
        """
        # Built-in protected paths
        for pattern in protected_paths:
            self.rules.append(
                ProtectionRule(
                    pattern=pattern,
                    source=ProtectionSource.BUILTIN,
                    description=f"Built-in protected path: {pattern}",
                    is_glob="*" in pattern or "?" in pattern,
                )
            )

        # Custom paths (exact matches)
        for path in custom_paths:
            self.rules.append(
                ProtectionRule(
                    pattern=path,
                    source=ProtectionSource.CUSTOM_PATH,
                    description=f"Custom protected path: {path}",
                    is_glob=False,
                )
            )

        # Custom globs
        for pattern in custom_globs:
            self.rules.append(
                ProtectionRule(
                    pattern=pattern,
                    source=ProtectionSource.CUSTOM_GLOB,
                    description=f"Custom protected glob: {pattern}",
                    is_glob=True,
                )
            )

        # Git directory protection
        if protect_git_dirs:
            self.rules.append(
                ProtectionRule(
                    pattern="**/.git/**",
                    source=ProtectionSource.GIT_DIR,
                    description="Git repository directory",
                    is_glob=True,
                )
            )
            self.rules.append(
                ProtectionRule(
                    pattern="**/.git",
                    source=ProtectionSource.GIT_DIR,
                    description="Git repository root",
                    is_glob=True,
                )
            )

        # Virtual environment protection
        if protect_venvs:
            for venv_pattern in ["**/venv/**", "**/.venv/**", "**/virtualenv/**"]:
                self.rules.append(
                    ProtectionRule(
                        pattern=venv_pattern,
                        source=ProtectionSource.VENV,
                        description=f"Virtual environment: {venv_pattern}",
                        is_glob=True,
                    )
                )

    def is_protected(self, path: Path) -> ProtectionResult:
        """
        Check if a path is protected.

        Args:
            path: Path to check.

        Returns:
            ProtectionResult: Result containing protection status and matching rules.
        """
        if not self.enabled:
            return ProtectionResult(is_protected=False)

        matching_rules: list[ProtectionRule] = []

        for rule in self.rules:
            if rule.matches(path):
                matching_rules.append(rule)

        if matching_rules:
            reasons = [rule.description for rule in matching_rules]
            return ProtectionResult(
                is_protected=True,
                matching_rules=matching_rules,
                reason="Protected: " + "; ".join(reasons),
            )

        # Check recent file protection
        if self._protect_recent_days > 0:
            if self._is_recently_modified(path):
                return ProtectionResult(
                    is_protected=True,
                    matching_rules=[],
                    reason=f"File modified within {self._protect_recent_days} day(s)",
                )

        return ProtectionResult(is_protected=False)

    def _is_recently_modified(self, path: Path) -> bool:
        """
        Check if a path was modified within the recent days threshold.

        Args:
            path: Path to check.

        Returns:
            bool: True if recently modified.
        """
        import time

        try:
            if not path.exists():
                return False

            mtime = path.stat().st_mtime
            age_seconds = time.time() - mtime
            age_days = age_seconds / (24 * 60 * 60)

            return age_days < self._protect_recent_days
        except OSError:
            return False

    def check_paths(self, paths: list[Path]) -> dict[Path, ProtectionResult]:
        """
        Check multiple paths for protection.

        Args:
            paths: List of paths to check.

        Returns:
            dict[Path, ProtectionResult]: Mapping of path to protection result.
        """
        return {path: self.is_protected(path) for path in paths}

    def filter_protected(
        self, paths: list[Path]
    ) -> tuple[list[Path], list[tuple[Path, ProtectionResult]]]:
        """
        Filter out protected paths from a list.

        Args:
            paths: List of paths to filter.

        Returns:
            tuple[list[Path], list[tuple[Path, ProtectionResult]]]:
                Tuple of (safe paths, list of (protected path, result) tuples)
        """
        safe_paths: list[Path] = []
        protected: list[tuple[Path, ProtectionResult]] = []

        for path in paths:
            result = self.is_protected(path)
            if result.is_protected:
                protected.append((path, result))
            else:
                safe_paths.append(path)

        return safe_paths, protected

    def add_rule(
        self,
        pattern: str,
        source: ProtectionSource = ProtectionSource.CUSTOM_PATH,
        description: str = "",
        is_glob: bool = False,
    ) -> None:
        """
        Add a new protection rule.

        Args:
            pattern: Path pattern or glob.
            source: Source of this rule.
            description: Human-readable description.
            is_glob: Whether the pattern is a glob.
        """
        self.rules.append(
            ProtectionRule(
                pattern=pattern,
                source=source,
                description=description or f"Protected: {pattern}",
                is_glob=is_glob,
            )
        )
        logger.debug(f"Added protection rule: {pattern}")

    def remove_rule(self, pattern: str) -> bool:
        """
        Remove a protection rule by pattern.

        Args:
            pattern: Pattern to remove.

        Returns:
            bool: True if a rule was removed.
        """
        initial_count = len(self.rules)
        self.rules = [r for r in self.rules if r.pattern != pattern]
        removed = len(self.rules) < initial_count

        if removed:
            logger.debug(f"Removed protection rule: {pattern}")

        return removed

    def get_rules(self) -> list[ProtectionRule]:
        """
        Get all protection rules.

        Returns:
            list[ProtectionRule]: List of all rules.
        """
        return self.rules.copy()

    @staticmethod
    def get_history_dir() -> Path:
        """
        Get the directory for storing protection-related history.

        Returns:
            Path: History directory path.
        """
        from dmlclean.storage.paths import get_history_dir

        return get_history_dir()
