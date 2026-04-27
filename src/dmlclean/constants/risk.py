"""
Risk level constants for DMLClean.

Defines the risk classification system for cleaning targets.
"""

from enum import Enum


class RiskLevel(Enum):
    """
    Risk levels for cleaning targets.

    Members:
        LOW: 🟢 Auto-clean default (safe to delete)
        MEDIUM: 🟡 Confirm before clean (review recommended)
        HIGH: 🔴 Manual/opt-in only (expensive to re-download)
        BLOCKED: ⛔ Never clean (critical system/user data)
    """

    LOW = "low"
    """🟢 Auto-clean default - safe to delete without confirmation."""

    MEDIUM = "medium"
    """🟡 Confirm before clean - review recommended."""

    HIGH = "high"
    """🔴 Manual/opt-in only - expensive to re-download (e.g., AI models)."""

    BLOCKED = "blocked"
    """⛔ Never clean - critical system or user data."""


# Risk level colors for Rich terminal output
RISK_COLORS: dict[RiskLevel, str] = {
    RiskLevel.LOW: "green",
    RiskLevel.MEDIUM: "yellow",
    RiskLevel.HIGH: "red",
    RiskLevel.BLOCKED: "bright_red",
}
"""Mapping of risk levels to Rich color names for terminal output."""

# Risk level emoji for quick visual identification
RISK_EMOJI: dict[RiskLevel, str] = {
    RiskLevel.LOW: "🟢",
    RiskLevel.MEDIUM: "🟡",
    RiskLevel.HIGH: "🔴",
    RiskLevel.BLOCKED: "⛔",
}
"""Mapping of risk levels to emoji for quick visual identification."""
