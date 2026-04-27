"""
Data models package for DMLClean.

Pydantic v2 models for all data structures used in DMLClean.
All models use frozen=True for immutability.
"""

from dmlclean.models.clean import CleanResult
from dmlclean.models.history import HistoryEntry
from dmlclean.models.manifest import ManifestEntry, ManifestRecord
from dmlclean.models.profile import CleanProfile
from dmlclean.models.scan import CleanCandidate, ScanResult, ScanStats
from dmlclean.models.schedule import ScheduleJob
from dmlclean.models.trend import DiskTrendPoint, TrendSummary

__all__ = [
    "CleanCandidate",
    # Profile models
    "CleanProfile",
    # Clean models
    "CleanResult",
    # Trend models
    "DiskTrendPoint",
    # History models
    "HistoryEntry",
    # Manifest models
    "ManifestEntry",
    "ManifestRecord",
    "ScanResult",
    # Scan models
    "ScanStats",
    # Schedule models
    "ScheduleJob",
    "TrendSummary",
]
