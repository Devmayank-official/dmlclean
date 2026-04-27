"""
Named cleaning profiles for DMLClean.

Profiles are pre-configured sets of category settings optimized for
specific user types or use cases.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Profile:
    """
    A named cleaning profile with predefined category settings.

    Attributes:
        name: Unique profile identifier.
        description: Human-readable description.
        categories: Dictionary of category names to enabled state.
        scan_mode: Default scan mode (fast, deep, custom).
        clean_mode: Default clean mode (dry-run, trash, permanent).
        min_age_days: Minimum file age to clean.
        min_size_mb: Minimum file size to clean.
        scanner_settings: Optional scanner configuration overrides.
        cleaner_settings: Optional cleaner configuration overrides.
    """

    name: str
    description: str
    categories: dict[str, bool] = field(default_factory=dict)
    scan_mode: str = "fast"
    clean_mode: str = "dry-run"
    min_age_days: int = 0
    min_size_mb: int = 0
    scanner_settings: dict[str, Any] = field(default_factory=dict)
    cleaner_settings: dict[str, Any] = field(default_factory=dict)

    @property
    def enabled_categories(self) -> list[str]:
        """Get list of enabled category names."""
        return [cat for cat, enabled in self.categories.items() if enabled]


def get_profiles() -> dict[str, Profile]:
    """
    Return all available cleaning profiles.

    Returns:
        dict[str, Profile]: Mapping of profile name to Profile object.
    """
    return {
        "developer": Profile(
            name="developer",
            description="Optimized for software developers (Python, Node.js, Java, etc.)",
            categories={
                "system_junk": True,
                "browser": True,
                "dev_python": True,
                "dev_node": False,  # Opt-in due to HIGH risk
                "dev_java": False,
                "dev_rust_cpp": False,
                "ide": True,
                "gaming": False,
                "media": False,
                "messaging": False,
                "ai_ml": False,
                "cloud_sync": False,
                "package_manager": False,
                "smart_scan": True,
            },
            scanner_settings={
                "enable_smart_scan": True,
                "large_file_threshold_mb": 500,
            },
            cleaner_settings={
                "node_modules_min_age_days": 30,
                "min_age_days": 0,
            },
        ),
        "designer": Profile(
            name="designer",
            description="Optimized for designers (Adobe Creative Cloud, Blender, etc.)",
            categories={
                "system_junk": True,
                "browser": True,
                "dev_python": False,
                "dev_node": False,
                "dev_java": False,
                "dev_rust_cpp": False,
                "ide": False,
                "gaming": False,
                "media": True,  # Adobe/Blender cache
                "messaging": False,
                "ai_ml": False,
                "cloud_sync": False,
                "package_manager": False,
                "smart_scan": True,
            },
            scanner_settings={
                "enable_smart_scan": True,
                "large_file_threshold_mb": 1000,  # Higher threshold for media files
            },
            cleaner_settings={
                "min_age_days": 7,  # More conservative for media files
            },
        ),
        "system-admin": Profile(
            name="system-admin",
            description="Aggressive cleaning for system administrators",
            categories={
                "system_junk": True,
                "browser": True,
                "dev_python": True,
                "dev_node": True,
                "dev_java": True,
                "dev_rust_cpp": True,
                "ide": True,
                "gaming": True,
                "media": True,
                "messaging": True,
                "ai_ml": False,  # Still opt-in due to size
                "cloud_sync": True,
                "package_manager": True,
                "smart_scan": True,
            },
            scanner_settings={
                "enable_smart_scan": True,
                "large_file_threshold_mb": 200,
                "stale_file_days": 30,
            },
            cleaner_settings={
                "min_age_days": 0,
                "min_size_mb": 0,
            },
        ),
        "gamer": Profile(
            name="gamer",
            description="Optimized for gamers (Steam, Epic, NVIDIA cache cleanup)",
            categories={
                "system_junk": True,
                "browser": True,
                "dev_python": False,
                "dev_node": False,
                "dev_java": False,
                "dev_rust_cpp": False,
                "ide": False,
                "gaming": True,
                "media": False,
                "messaging": True,  # Discord cache
                "ai_ml": False,
                "cloud_sync": False,
                "package_manager": False,
                "smart_scan": True,
            },
            scanner_settings={
                "enable_smart_scan": True,
                "large_file_threshold_mb": 500,
            },
            cleaner_settings={
                "min_age_days": 0,
            },
        ),
        "minimal": Profile(
            name="minimal",
            description="Conservative cleaning - only safe system temp files",
            categories={
                "system_junk": True,
                "browser": True,
                "dev_python": False,
                "dev_node": False,
                "dev_java": False,
                "dev_rust_cpp": False,
                "ide": False,
                "gaming": False,
                "media": False,
                "messaging": False,
                "ai_ml": False,
                "cloud_sync": False,
                "package_manager": False,
                "smart_scan": False,
            },
            scanner_settings={
                "enable_smart_scan": False,
            },
            cleaner_settings={
                "min_age_days": 7,
            },
        ),
    }


def get_profile(name: str) -> Profile | None:
    """
    Get a profile by name.

    Args:
        name: Profile name (e.g., 'developer', 'designer', 'system-admin').

    Returns:
        Profile | None: Profile object if found, None otherwise.
    """
    profiles = get_profiles()
    return profiles.get(name)


def list_profiles() -> list[str]:
    """
    List all available profile names.

    Returns:
        list[str]: List of profile names.
    """
    return list(get_profiles().keys())
