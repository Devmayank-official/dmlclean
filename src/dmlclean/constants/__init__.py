"""
Constants package for DMLClean.

Centralized application constants including:
- App metadata (name, version, storage paths)
- Risk levels and colors
- Supported formats and modes
- User-facing messages
"""

from dmlclean.constants.app import (
    APP_BINARY,
    APP_NAME,
    APP_VERSION,
    MIN_PYTHON,
    STORAGE_APP,
    STORAGE_ORG,
)
from dmlclean.constants.formats import (
    DATE_FORMATS,
    SUPPORTED_CLEAN_MODES,
    SUPPORTED_OUTPUT_FORMATS,
    SUPPORTED_SCAN_MODES,
)
from dmlclean.constants.messages import (
    MSG_CONFIRM_PERMANENT,
    MSG_DRY_RUN_HEADER,
    MSG_IMMUTABLE_BLOCKED,
    MSG_NOTHING_TO_CLEAN,
    MSG_PROTECTED_BLOCKED,
    MSG_SELF_STORAGE_PROTECTED,
    MSG_UNDO_EMPTY,
)
from dmlclean.constants.risk import RISK_COLORS, RiskLevel

__all__ = [
    "APP_BINARY",
    # App metadata
    "APP_NAME",
    "APP_VERSION",
    "DATE_FORMATS",
    "MIN_PYTHON",
    "MSG_CONFIRM_PERMANENT",
    # Messages
    "MSG_DRY_RUN_HEADER",
    "MSG_IMMUTABLE_BLOCKED",
    "MSG_NOTHING_TO_CLEAN",
    "MSG_PROTECTED_BLOCKED",
    "MSG_SELF_STORAGE_PROTECTED",
    "MSG_UNDO_EMPTY",
    "RISK_COLORS",
    "STORAGE_APP",
    "STORAGE_ORG",
    "SUPPORTED_CLEAN_MODES",
    # Formats
    "SUPPORTED_OUTPUT_FORMATS",
    "SUPPORTED_SCAN_MODES",
    # Risk levels
    "RiskLevel",
]
