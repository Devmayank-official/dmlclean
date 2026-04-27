"""
Analyzer and risk classifier for DMLClean.

Categorizes scanned files and assigns risk levels based on
path patterns, file types, and configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from loguru import logger


class RiskLevel(str, Enum):
    """Risk levels for cleaning targets."""

    LOW = "low"  # 🟢 Auto-clean default
    MEDIUM = "medium"  # 🟡 Confirm before clean
    HIGH = "high"  # 🔴 Manual/opt-in only
    BLOCKED = "blocked"  # ⛔ Never clean (protected)


class Category(str, Enum):
    """Cleaning categories."""

    SYSTEM_JUNK = "system_junk"
    BROWSER = "browser"
    DEV_PYTHON = "dev_python"
    DEV_NODE = "dev_node"
    DEV_JAVA = "dev_java"
    DEV_RUST_CPP = "dev_rust_cpp"
    IDE = "ide"
    GAMING = "gaming"
    MEDIA = "media"
    MESSAGING = "messaging"
    AI_ML = "ai_ml"
    CLOUD_SYNC = "cloud_sync"
    PACKAGE_MANAGER = "package_manager"
    SMART_SCAN = "smart_scan"
    UNKNOWN = "unknown"


@dataclass
class CleanCandidate:
    """
    A file or directory identified for potential cleaning.

    Attributes:
        path: Absolute path to the item.
        category: Cleaning category.
        size_bytes: Size in bytes.
        risk_level: Assigned risk level.
        reason: Why this item was identified.
        last_accessed: Last access timestamp.
        last_modified: Last modification timestamp.
        is_directory: Whether this is a directory.
        hash_value: File hash (for duplicate detection).
        metadata: Additional metadata.
    """

    path: Path
    category: Category
    size_bytes: int
    risk_level: RiskLevel
    reason: str
    last_accessed: float | None = None
    last_modified: float | None = None
    is_directory: bool = False
    hash_value: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "path": str(self.path),
            "category": self.category.value,
            "size_bytes": self.size_bytes,
            "size_human": self._humanize_size(self.size_bytes),
            "risk_level": self.risk_level.value,
            "reason": self.reason,
            "last_accessed": self.last_accessed,
            "last_modified": self.last_modified,
            "is_directory": self.is_directory,
            "hash_value": self.hash_value,
            "metadata": self.metadata,
        }

    @staticmethod
    def _humanize_size(size_bytes: int) -> str:
        """Convert bytes to human-readable format."""
        size: float = size_bytes
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"


@dataclass
class AnalysisResult:
    """
    Result of analyzing scanned files.

    Attributes:
        candidates: List of clean candidates.
        by_category: Files grouped by category.
        by_risk: Files grouped by risk level.
        total_size_bytes: Total size of all candidates.
        total_files: Total number of files.
        total_directories: Total number of directories.
    """

    candidates: list[CleanCandidate] = field(default_factory=list)
    by_category: dict[Category, list[CleanCandidate]] = field(default_factory=dict)
    by_risk: dict[RiskLevel, list[CleanCandidate]] = field(default_factory=dict)
    total_size_bytes: int = 0
    total_files: int = 0
    total_directories: int = 0

    def add_candidate(self, candidate: CleanCandidate) -> None:
        """Add a candidate to the result."""
        self.candidates.append(candidate)
        self.total_size_bytes += candidate.size_bytes

        if candidate.is_directory:
            self.total_directories += 1
        else:
            self.total_files += 1

        # Group by category
        if candidate.category not in self.by_category:
            self.by_category[candidate.category] = []
        self.by_category[candidate.category].append(candidate)

        # Group by risk
        if candidate.risk_level not in self.by_risk:
            self.by_risk[candidate.risk_level] = []
        self.by_risk[candidate.risk_level].append(candidate)

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the analysis."""
        return {
            "total_files": self.total_files,
            "total_directories": self.total_directories,
            "total_size_bytes": self.total_size_bytes,
            "total_size_human": self._humanize_size(self.total_size_bytes),
            "by_category": {
                cat.value: {
                    "count": len(items),
                    "size_bytes": sum(c.size_bytes for c in items),
                }
                for cat, items in self.by_category.items()
            },
            "by_risk": {
                risk.value: {
                    "count": len(items),
                    "size_bytes": sum(c.size_bytes for c in items),
                }
                for risk, items in self.by_risk.items()
            },
        }

    @staticmethod
    def _humanize_size(size_bytes: int) -> str:
        """Convert bytes to human-readable format."""
        size: float = size_bytes
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"


class Analyzer:
    """
    Analyzer for categorizing and classifying scanned files.

    The Analyzer takes scanned file paths and:
    1. Categorizes them based on path patterns
    2. Assigns risk levels based on category and location
    3. Filters based on configuration (age, size, etc.)

    Attributes:
        category_configs: Configuration for each category.
        min_age_days: Minimum file age to consider.
        min_size_mb: Minimum file size to consider.
    """

    def __init__(
        self,
        category_configs: dict[str, dict[str, Any]] | None = None,
        min_age_days: int = 0,
        min_size_mb: int = 0,
    ) -> None:
        """
        Initialize the analyzer.

        Args:
            category_configs: Category configuration (enabled, min_risk).
            min_age_days: Minimum file age in days.
            min_size_mb: Minimum file size in MB.
        """
        self.category_configs = category_configs or {}
        self.min_age_days = min_age_days
        self.min_size_mb = min_size_mb

        # Build pattern matchers for each category
        self._category_patterns = self._build_category_patterns()

        logger.debug(f"Analyzer initialized: min_age={min_age_days}d, min_size={min_size_mb}MB")

    def _build_category_patterns(self) -> dict[Category, list[tuple[str, RiskLevel, str]]]:
        """
        Build path patterns for each category.

        Returns:
            dict[Category, list[tuple[str, RiskLevel, str]]]: Patterns with risk and reason.
        """

        patterns: dict[Category, list[tuple[str, RiskLevel, str]]] = {cat: [] for cat in Category}

        # System Junk
        patterns[Category.SYSTEM_JUNK] = [
            (r".*[\\/](Temp|tmp)[\\/].*\.(tmp|temp)$", RiskLevel.LOW, "Temporary file"),
            (r".*[\\/](Temp|TMP)[\\/]", RiskLevel.MEDIUM, "System temp directory"),
            (r".*[\\/]\.log$", RiskLevel.LOW, "Log file"),
            (r".*[\\/](Logs|logs)[\\/]", RiskLevel.LOW, "Log directory"),
            (r".*\.dmp$", RiskLevel.LOW, "Memory dump file"),
            (r".*\.crash$", RiskLevel.LOW, "Crash report file"),
            (r".*\.stackdump$", RiskLevel.LOW, "Stack dump file"),
            (r".*\.bak$", RiskLevel.MEDIUM, "Backup file"),
            (r".*\.old$", RiskLevel.LOW, "Old file"),
        ]

        # Browser Cache
        patterns[Category.BROWSER] = [
            (
                r".*[\\/]Google[\\/]Chrome[\\/].*[\\/](Cache|Code Cache|GPUCache)",
                RiskLevel.LOW,
                "Chrome cache",
            ),
            (
                r".*[\\/]Microsoft[\\/]Edge[\\/].*[\\/](Cache|Code Cache)",
                RiskLevel.LOW,
                "Edge cache",
            ),
            (r".*[\\/]Mozilla[\\/]Firefox[\\/].*[\\/]cache2", RiskLevel.LOW, "Firefox cache"),
            (r".*[\\/]Safari[\\/](Caches|Cache)", RiskLevel.LOW, "Safari cache"),
            (
                r".*[\\/](Chrome|Edge|Firefox|Safari).*[\\/]Crashpad",
                RiskLevel.LOW,
                "Browser crash reports",
            ),
        ]

        # Python Development
        patterns[Category.DEV_PYTHON] = [
            (r".*[\\/]__pycache__[\\/]", RiskLevel.LOW, "Python bytecode cache"),
            (r".*\.pyc$", RiskLevel.LOW, "Python compiled file"),
            (r".*\.pyo$", RiskLevel.LOW, "Python optimized file"),
            (r".*[\\/]\.pytest_cache[\\/]", RiskLevel.LOW, "Pytest cache"),
            (r".*[\\/]\.mypy_cache[\\/]", RiskLevel.LOW, "MyPy cache"),
            (r".*[\\/]\.ruff_cache[\\/]", RiskLevel.LOW, "Ruff cache"),
            (r".*[\\/]\.tox[\\/]", RiskLevel.LOW, "Tox environment"),
            (r".*[\\/]\.nox[\\/]", RiskLevel.LOW, "Nox environment"),
            (
                r".*[\\/](build|dist)[\\/](?!.*[\\/](src|lib)[\\/])",
                RiskLevel.MEDIUM,
                "Build artifacts",
            ),
            (r".*\.egg-info[\\/]", RiskLevel.LOW, "Python egg info"),
            (r".*[\\/]\.ipynb_checkpoints[\\/]", RiskLevel.MEDIUM, "Jupyter checkpoint"),
        ]

        # Node.js Development
        patterns[Category.DEV_NODE] = [
            (r".*[\\/]node_modules[\\/]", RiskLevel.HIGH, "Node.js dependencies (opt-in)"),
            (r".*[\\/]\.next[\\/]", RiskLevel.LOW, "Next.js build output"),
            (r".*[\\/]\.nuxt[\\/]", RiskLevel.LOW, "Nuxt.js build output"),
            (r".*[\\/]\.svelte-kit[\\/]", RiskLevel.LOW, "SvelteKit build output"),
            (r".*[\\/]\.vite[\\/]", RiskLevel.LOW, "Vite cache"),
            (r".*[\\/]\.turbo[\\/]", RiskLevel.LOW, "Turborepo cache"),
            (r".*\.eslintcache$", RiskLevel.LOW, "ESLint cache"),
            (r".*\.tsbuildinfo$", RiskLevel.LOW, "TypeScript build info"),
            (r".*[\\/](npm-cache|npm)[\\/]", RiskLevel.LOW, "npm cache"),
        ]

        # Java Development
        patterns[Category.DEV_JAVA] = [
            (r".*[\\/]build[\\/]", RiskLevel.MEDIUM, "Gradle build output"),
            (r".*[\\/]\.gradle[\\/]", RiskLevel.MEDIUM, "Gradle cache"),
            (r".*[\\/]target[\\/]", RiskLevel.MEDIUM, "Maven target"),
            (r".*\.class$", RiskLevel.LOW, "Java class file"),
            (r".*[\\/]\.m2[\\/]", RiskLevel.HIGH, "Maven local repository"),
        ]

        # Rust/C++ Development
        patterns[Category.DEV_RUST_CPP] = [
            (r".*[\\/]target[\\/](?!.*[\\/]src[\\/])", RiskLevel.MEDIUM, "Rust/CMake build output"),
            (r".*[\\/]cmake-build-.*[\\/]", RiskLevel.MEDIUM, "CMake build directory"),
            (r".*\.o$", RiskLevel.LOW, "Object file"),
            (r".*\.obj$", RiskLevel.LOW, "Object file"),
            (r".*\.pdb$", RiskLevel.LOW, "Debug symbols"),
            (r".*\.ilk$", RiskLevel.LOW, "Linker file"),
        ]

        # IDE
        patterns[Category.IDE] = [
            (r".*[\\/]Code[\\/](Cache|CachedData|GPUCache)", RiskLevel.LOW, "VS Code cache"),
            (r".*[\\/]\.history[\\/]", RiskLevel.MEDIUM, "VS Code local history"),
            (r".*[\\/]JetBrains[\\/]", RiskLevel.MEDIUM, "JetBrains global cache"),
            (r".*[\\/]\.idea[\\/]", RiskLevel.HIGH, "JetBrains project settings"),
            (r".*[\\/]out[\\/](?=.*\.idea)", RiskLevel.MEDIUM, "JetBrains output"),
        ]

        # Gaming
        patterns[Category.GAMING] = [
            (r".*[\\/]Steam[\\/]appcache[\\/]", RiskLevel.LOW, "Steam appcache"),
            (r".*[\\/]Steam[\\/]logs[\\/]", RiskLevel.LOW, "Steam logs"),
            (r".*[\\/]Steam[\\/]shadercache[\\/]", RiskLevel.LOW, "Steam shader cache"),
            (r".*[\\/]EpicGamesLauncher[\\/]Saved[\\/]Logs[\\/]", RiskLevel.LOW, "Epic Games logs"),
            (
                r".*[\\/]EpicGamesLauncher[\\/]Saved[\\/]webcache[\\/]",
                RiskLevel.LOW,
                "Epic web cache",
            ),
            (r".*[\\/]NVIDIA[\\/]DXCache[\\/]", RiskLevel.LOW, "NVIDIA DirectX cache"),
            (r".*[\\/]NVIDIA[\\/]GLCache[\\/]", RiskLevel.LOW, "NVIDIA OpenGL cache"),
        ]

        # Media/Creative
        patterns[Category.MEDIA] = [
            (r".*[\\/]Adobe[\\/].*[\\/]Media Cache", RiskLevel.MEDIUM, "Adobe media cache"),
            (r".*[\\/]Adobe[\\/].*[\\/]Peak Files", RiskLevel.LOW, "Adobe peak files"),
            (r".*[\\/]Blender.*[\\/]temp", RiskLevel.LOW, "Blender temp"),
        ]

        # Messaging
        patterns[Category.MESSAGING] = [
            (r".*[\\/]Discord[\\/]Cache", RiskLevel.LOW, "Discord cache"),
            (r".*[\\/]Telegram Desktop[\\/]tdata[\\/]temp", RiskLevel.LOW, "Telegram temp"),
            (r".*[\\/]Zoom[\\/]logs", RiskLevel.LOW, "Zoom logs"),
            (r".*[\\/]Microsoft[\\/]Teams[\\/]Cache", RiskLevel.LOW, "Teams cache"),
        ]

        # AI/ML
        patterns[Category.AI_ML] = [
            (r".*[\\/]huggingface[\\/]", RiskLevel.HIGH, "HuggingFace cache (large models)"),
            (r".*[\\/]torch[\\/]", RiskLevel.HIGH, "PyTorch cache"),
            (r".*[\\/]keras[\\/]", RiskLevel.HIGH, "Keras cache"),
        ]

        # Cloud Sync
        patterns[Category.CLOUD_SYNC] = [
            (r".*[\\/]OneDrive[\\/]logs", RiskLevel.LOW, "OneDrive logs"),
            (r".*[\\/]Google[\\/]DriveFS", RiskLevel.MEDIUM, "Google Drive FS cache"),
            (r".*[\\/]Dropbox[\\/]cache", RiskLevel.LOW, "Dropbox cache"),
        ]

        # Package Managers
        patterns[Category.PACKAGE_MANAGER] = [
            (r".*[\\/]pip[\\/]Cache", RiskLevel.LOW, "pip cache"),
            (r".*[\\/]\.cache[\\/]pip", RiskLevel.LOW, "pip cache (Unix)"),
            (r".*[\\/]\.npm[\\/]", RiskLevel.LOW, "npm global cache"),
            (r".*[\\/]\.gradle[\\/]caches", RiskLevel.MEDIUM, "Gradle cache"),
            (r".*[\\/](apt|dnf|pacman)[\\/]cache", RiskLevel.MEDIUM, "Linux package manager cache"),
        ]

        # Smart Scan
        patterns[Category.SMART_SCAN] = [
            (r".*\.DS_Store$", RiskLevel.LOW, "macOS metadata"),
            (r".*Thumbs\.db$", RiskLevel.LOW, "Windows thumbnail cache"),
            (r".*desktop\.ini$", RiskLevel.MEDIUM, "Windows folder config"),
            (r".*~$", RiskLevel.LOW, "Editor backup file"),
            (r".*\.swp$", RiskLevel.LOW, "Vim swap file"),
            (r".*\.orig$", RiskLevel.MEDIUM, "Merge conflict original"),
            (r".*\.rej$", RiskLevel.MEDIUM, "Patch reject file"),
        ]

        return patterns

    def analyze(
        self,
        paths: list[Path],
        scan_stats: dict[str, Any] | None = None,
    ) -> AnalysisResult:
        """
        Analyze a list of paths and categorize them.

        Args:
            paths: List of file paths to analyze.
            scan_stats: Optional scan statistics for context.

        Returns:
            AnalysisResult: Complete analysis result.
        """

        result = AnalysisResult()

        for path in paths:
            try:
                candidate = self._analyze_path(path)
                if candidate:
                    # Apply filters
                    if self._should_filter(candidate):
                        logger.debug(f"Filtered out: {path} (age/size filter)")
                        continue

                    # Check if category is enabled
                    if not self._is_category_enabled(candidate.category):
                        logger.debug(f"Category disabled: {candidate.category}")
                        continue

                    result.add_candidate(candidate)

            except Exception as e:
                logger.warning(f"Error analyzing {path}: {e}")

        logger.info(f"Analysis complete: {len(result.candidates)} candidates identified")
        return result

    def _analyze_path(self, path: Path) -> CleanCandidate | None:
        """
        Analyze a single path and create a candidate.

        Args:
            path: Path to analyze.

        Returns:
            CleanCandidate | None: Candidate if path matches a category.
        """
        import re

        path_str = str(path)
        is_dir = path.is_dir()

        # Get file metadata
        try:
            stat = path.stat()
            size = stat.st_size if not is_dir else 0
            atime = stat.st_atime
            mtime = stat.st_mtime
        except OSError:
            size = 0
            atime = None
            mtime = None

        # Find matching category
        best_match: tuple[Category, RiskLevel, str] | None = None

        for category, patterns in self._category_patterns.items():
            for pattern, risk, reason in patterns:
                if re.search(pattern, path_str, re.IGNORECASE):
                    best_match = (category, risk, reason)
                    break
            if best_match:
                break

        if not best_match:
            return None

        category, risk_level, reason = best_match

        return CleanCandidate(
            path=path,
            category=category,
            size_bytes=size,
            risk_level=risk_level,
            reason=reason,
            last_accessed=atime,
            last_modified=mtime,
            is_directory=is_dir,
        )

    def _should_filter(self, candidate: CleanCandidate) -> bool:
        """
        Check if a candidate should be filtered out.

        Args:
            candidate: Candidate to check.

        Returns:
            bool: True if candidate should be filtered.
        """
        import time

        # Filter by age
        if self.min_age_days > 0 and candidate.last_modified:
            age_seconds = time.time() - candidate.last_modified
            age_days = age_seconds / (24 * 60 * 60)
            if age_days < self.min_age_days:
                return True

        # Filter by size
        if self.min_size_mb > 0:
            size_mb = candidate.size_bytes / (1024 * 1024)
            if size_mb < self.min_size_mb:
                return True

        return False

    def _is_category_enabled(self, category: Category) -> bool:
        """
        Check if a category is enabled in configuration.

        Args:
            category: Category to check.

        Returns:
            bool: True if category is enabled.
        """
        config = self.category_configs.get(category.value)
        if config is None:
            return True  # Default to enabled if not configured
        # Access attribute directly from CategoryConfig object
        return bool(config.enabled)

    def get_category_for_path(self, path: Path) -> Category | None:
        """
        Get the category for a single path.

        Args:
            path: Path to categorize.

        Returns:
            Category | None: Category if matched.
        """
        candidate = self._analyze_path(path)
        return candidate.category if candidate else None

    def get_risk_for_path(self, path: Path) -> RiskLevel | None:
        """
        Get the risk level for a single path.

        Args:
            path: Path to classify.

        Returns:
            RiskLevel | None: Risk level if matched.
        """
        candidate = self._analyze_path(path)
        return candidate.risk_level if candidate else None
