"""
Default configuration values for DMLClean.

All default values are defined here and used as the base layer
in the configuration loading pipeline.
"""

from typing import Any


def get_defaults() -> dict[str, Any]:
    """
    Return the default configuration dictionary.

    Returns:
        dict[str, Any]: Default configuration values organized by section.
    """
    return {
        "general": {
            "version": "0.1.0",
            "default_scan_mode": "fast",
            "default_clean_mode": "dry-run",
            "default_profile": "developer",
            "confirm_threshold_mb": 100,
            "confirm_threshold_files": 1000,
            "confirmation_detail": "summary",
            "max_workers": 0,
            "json_output": False,
        },
        "logging": {
            "level": "INFO",
            "log_to_file": True,
            "log_rotation": "10 MB",
            "log_retention": "30 days",
            "log_format": "text",
        },
        "notifications": {
            "enabled": True,
            "on_scan_complete": True,
            "on_clean_complete": True,
            "on_error": True,
            "on_scheduled_run": True,
            "on_protected_zone_violation": True,
        },
        "scheduling": {
            "enabled": False,
            "backend": "apscheduler",
            "jobs": [],
        },
        "scanner": {
            "follow_symlinks": False,
            "max_depth": 0,
            "large_file_threshold_mb": 500,
            "stale_file_days": 90,
            "enable_smart_scan": True,
        },
        "cleaner": {
            "enable_incremental": True,
            "min_size_mb": 0,
            "min_age_days": 0,
            "node_modules_min_age_days": 30,
        },
        "protected_zone": {
            "enabled": True,
            "profiles": ["system-critical", "user-home"],
            "custom_paths": [],
            "custom_globs": [],
            "protect_git_dirs": True,
            "protect_venvs": True,
            "protect_recent_days": 1,
            "protected_paths": [
                # Browser data - never touch
                "**/Bookmarks",
                "**/Login Data",
                "**/Cookies",
                "**/Passwords",
                "**/History",
                # Git repositories
                "**/.git/**",
                "**/.git",
                # Virtual environments
                "**/venv/**",
                "**/.venv/**",
                "**/virtualenv/**",
                # System critical - Windows
                "C:\\Windows\\System32\\**",
                "C:\\Windows\\SysWOW64\\**",
                "C:\\Windows\\Microsoft.NET\\**",
                # System critical - macOS
                "/System/**",
                "/Applications/**",
                # System critical - Linux
                "/bin/**",
                "/sbin/**",
                "/usr/**",
                "/etc/**",
                "/lib/**",
                "/lib64/**",
            ],
        },
        "categories": {
            "system_junk": {"enabled": True, "min_risk": "low"},
            "browser": {"enabled": True, "min_risk": "low"},
            "dev_python": {"enabled": True, "min_risk": "low"},
            "dev_node": {"enabled": False, "min_risk": "medium"},
            "dev_java": {"enabled": False, "min_risk": "medium"},
            "dev_rust_cpp": {"enabled": False, "min_risk": "medium"},
            "ide": {"enabled": True, "min_risk": "low"},
            "gaming": {"enabled": False, "min_risk": "low"},
            "media": {"enabled": False, "min_risk": "medium"},
            "messaging": {"enabled": False, "min_risk": "low"},
            "ai_ml": {"enabled": False, "min_risk": "high"},
            "cloud_sync": {"enabled": False, "min_risk": "medium"},
            "package_manager": {"enabled": False, "min_risk": "medium"},
            "smart_scan": {"enabled": True, "min_risk": "low"},
        },
        "history": {
            "enabled": True,
            "max_entries": 100,
            "storage_path": "",
        },
        "ui": {
            "theme": "dmlclean",
            "color_risk_low": "green",
            "color_risk_medium": "yellow",
            "color_risk_high": "red",
        },
    }
