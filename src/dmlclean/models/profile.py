"""
Profile-related models for DMLClean.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CleanProfile(BaseModel):
    """
    A named cleaning profile with predefined settings.

    Attributes:
        name: Unique profile identifier.
        description: Human-readable description.
        scan_mode: Default scan mode (fast, deep, custom).
        clean_mode: Default clean mode (dry-run, trash, permanent).
        enabled_categories: List of enabled category names.
        min_age_days: Minimum file age to clean (0 = no minimum).
        min_size_mb: Minimum file size to clean in MB (0 = no minimum).
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., description="Unique profile identifier")
    description: str = Field(..., description="Human-readable description")
    scan_mode: str = Field(default="fast", description="Default scan mode")
    clean_mode: str = Field(default="dry-run", description="Default clean mode")
    enabled_categories: list[str] = Field(
        default_factory=list,
        description="List of enabled category names",
    )
    min_age_days: int = Field(default=0, ge=0, description="Minimum file age in days")
    min_size_mb: int = Field(default=0, ge=0, description="Minimum file size in MB")

    @property
    def category_count(self) -> int:
        """Get number of enabled categories."""
        return len(self.enabled_categories)

    def is_category_enabled(self, category: str) -> bool:
        """
        Check if a category is enabled in this profile.

        Args:
            category: Category name to check.

        Returns:
            bool: True if category is enabled.
        """
        return category in self.enabled_categories
