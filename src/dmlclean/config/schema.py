"""
Pydantic schema for DMLClean configuration validation.

This module defines the structure and validation rules for the
TOML configuration file using Pydantic v2.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class ScanMode(str, Enum):
    """Valid scan modes for DMLClean."""

    FAST = "fast"
    DEEP = "deep"
    CUSTOM = "custom"


class CleanMode(str, Enum):
    """Valid clean modes for DMLClean."""

    DRY_RUN = "dry-run"
    TRASH = "trash"
    PERMANENT = "permanent"


class RiskLevel(str, Enum):
    """Risk levels for cleaning targets."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ConfirmationDetail(str, Enum):
    """Detail level for confirmation panels."""

    SUMMARY = "summary"
    FULL = "full"


class LogFormat(str, Enum):
    """Log output format."""

    TEXT = "text"
    JSON = "json"


class SchedulerBackend(str, Enum):
    """Scheduler backend options."""

    APSCHEDULER = "apscheduler"
    NATIVE_CRON = "native-cron"
    WINDOWS_TASK_SCHEDULER = "windows-task-scheduler"


class Theme(str, Enum):
    """UI theme options."""

    DMLCLEAN = "dmlclean"
    DEFAULT = "default"
    CUSTOM = "custom"


class CategoryConfig(BaseModel):
    """Configuration for a single cleaning category."""

    enabled: bool = Field(default=False, description="Whether this category is enabled")
    min_risk: RiskLevel = Field(default=RiskLevel.LOW, description="Minimum risk level to clean")


class GeneralConfig(BaseModel):
    """General configuration options."""

    version: str = Field(default="0.1.0", description="Config file version")
    default_scan_mode: ScanMode = Field(default=ScanMode.FAST, description="Default scan mode")
    default_clean_mode: CleanMode = Field(
        default=CleanMode.DRY_RUN, description="Default clean mode"
    )
    default_profile: str = Field(default="developer", description="Default cleaning profile")
    confirm_threshold_mb: int = Field(default=100, ge=1, description="Confirm if cleaning > N MB")
    confirm_threshold_files: int = Field(
        default=1000, ge=1, description="Confirm if cleaning > N files"
    )
    confirmation_detail: ConfirmationDetail = Field(
        default=ConfirmationDetail.SUMMARY, description="Detail level for confirmation"
    )
    max_workers: int = Field(default=0, ge=0, description="Max worker threads (0 = auto)")
    json_output: bool = Field(default=False, description="Enable JSON output mode")


class LoggingConfig(BaseModel):
    """Logging configuration options."""

    level: str = Field(default="INFO", description="Logging level")
    log_to_file: bool = Field(default=True, description="Enable file logging")
    log_rotation: str = Field(default="10 MB", description="Log rotation size")
    log_retention: str = Field(default="30 days", description="Log retention period")
    log_format: LogFormat = Field(default=LogFormat.TEXT, description="Log output format")

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate logging level is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()


class NotificationsConfig(BaseModel):
    """Notification configuration options."""

    enabled: bool = Field(default=True, description="Enable desktop notifications")
    on_scan_complete: bool = Field(default=True, description="Notify on scan completion")
    on_clean_complete: bool = Field(default=True, description="Notify on clean completion")
    on_error: bool = Field(default=True, description="Notify on errors")
    on_scheduled_run: bool = Field(default=True, description="Notify on scheduled runs")
    on_protected_zone_violation: bool = Field(
        default=True, description="Notify on protected zone violations"
    )


class JobConfig(BaseModel):
    """Configuration for a scheduled job."""

    id: str = Field(..., description="Unique job identifier")
    name: str = Field(..., description="Human-readable job name")
    cron_expression: str = Field(..., description="Cron expression or natural language")
    scan_mode: ScanMode = Field(default=ScanMode.FAST, description="Scan mode for this job")
    clean_mode: CleanMode = Field(default=CleanMode.DRY_RUN, description="Clean mode for this job")
    categories: list[str] = Field(default_factory=list, description="Categories to clean")
    enabled: bool = Field(default=True, description="Whether this job is active")


class SchedulingConfig(BaseModel):
    """Scheduling configuration options."""

    enabled: bool = Field(default=False, description="Enable scheduled cleaning")
    backend: SchedulerBackend = Field(
        default=SchedulerBackend.APSCHEDULER, description="Scheduler backend"
    )
    jobs: list[JobConfig] = Field(default_factory=list, description="List of scheduled jobs")


class ScannerConfig(BaseModel):
    """Scanner configuration options."""

    follow_symlinks: bool = Field(default=False, description="Follow symbolic links")
    max_depth: int = Field(default=0, ge=0, description="Max directory depth (0 = unlimited)")
    large_file_threshold_mb: int = Field(default=500, ge=1, description="Large file threshold")
    stale_file_days: int = Field(default=90, ge=1, description="Stale file threshold")
    enable_smart_scan: bool = Field(default=True, description="Enable smart scan features")


class CleanerConfig(BaseModel):
    """Cleaner configuration options."""

    enable_incremental: bool = Field(default=True, description="Enable incremental cleaning")
    min_size_mb: int = Field(default=0, ge=0, description="Minimum file size to clean")
    min_age_days: int = Field(default=0, ge=0, description="Minimum file age to clean")
    node_modules_min_age_days: int = Field(
        default=30, ge=0, description="Minimum age for node_modules cleaning"
    )


class ProtectedZoneConfig(BaseModel):
    """Protected Zone configuration options."""

    enabled: bool = Field(default=True, description="Enable Protected Zone")
    profiles: list[str] = Field(
        default_factory=lambda: ["system-critical", "user-home"],
        description="Active protection profiles",
    )
    custom_paths: list[str] = Field(default_factory=list, description="Custom protected paths")
    custom_globs: list[str] = Field(
        default_factory=list, description="Custom protected glob patterns"
    )
    protect_git_dirs: bool = Field(default=True, description="Protect .git directories")
    protect_venvs: bool = Field(default=True, description="Protect virtual environments")
    protect_recent_days: int = Field(
        default=1, ge=0, description="Protect files modified within N days"
    )
    protected_paths: list[str] = Field(
        default_factory=list, description="List of protected path patterns"
    )


class HistoryConfig(BaseModel):
    """History configuration options."""

    enabled: bool = Field(default=True, description="Enable cleaning history")
    max_entries: int = Field(default=100, ge=1, description="Maximum history entries to keep")
    storage_path: str = Field(default="", description="Custom history storage path")


class UIConfig(BaseModel):
    """UI configuration options."""

    theme: Theme = Field(default=Theme.DMLCLEAN, description="UI theme")
    color_risk_low: str = Field(default="green", description="Color for low risk")
    color_risk_medium: str = Field(default="yellow", description="Color for medium risk")
    color_risk_high: str = Field(default="red", description="Color for high risk")


class ConfigSchema(BaseModel):
    """
    Root configuration schema for DMLClean.

    This is the main Pydantic model that validates the entire TOML
    configuration file. All sections are optional and will use defaults
    if not specified.
    """

    general: GeneralConfig = Field(default_factory=GeneralConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    notifications: NotificationsConfig = Field(default_factory=NotificationsConfig)
    scheduling: SchedulingConfig = Field(default_factory=SchedulingConfig)
    scanner: ScannerConfig = Field(default_factory=ScannerConfig)
    cleaner: CleanerConfig = Field(default_factory=CleanerConfig)
    protected_zone: ProtectedZoneConfig = Field(default_factory=ProtectedZoneConfig)
    categories: dict[str, CategoryConfig] = Field(default_factory=dict)
    history: HistoryConfig = Field(default_factory=HistoryConfig)
    ui: UIConfig = Field(default_factory=UIConfig)

    @model_validator(mode="after")
    def validate_categories(self) -> ConfigSchema:
        """Validate that all category risk levels are valid."""
        valid_categories = {
            "system_junk",
            "browser",
            "dev_python",
            "dev_node",
            "dev_java",
            "dev_rust_cpp",
            "ide",
            "gaming",
            "media",
            "messaging",
            "ai_ml",
            "cloud_sync",
            "package_manager",
            "smart_scan",
        }
        for key in self.categories:
            if key not in valid_categories:
                # Allow unknown categories but warn (could be custom plugins)
                pass
        return self

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the schema to a dictionary.

        Returns:
            dict[str, Any]: Configuration as a nested dictionary.
        """
        return self.model_dump(mode="json")
