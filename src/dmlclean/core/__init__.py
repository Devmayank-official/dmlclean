"""
Core engine modules for DMLClean.

This package provides:
- Async file system scanner
- Analyzer and risk classifier
- Cleaner execution pipeline
- Scheduler integration
- Deduplicator for finding duplicate files
- Pipeline orchestration
"""

from dmlclean.core.analyzer import AnalysisResult, Analyzer
from dmlclean.core.cleaner import Cleaner, CleanResult
from dmlclean.core.deduplicator import Deduplicator
from dmlclean.core.pipeline import Pipeline
from dmlclean.core.scanner import FileSystemScanner, ScanResult
from dmlclean.core.scheduler import Scheduler

__all__ = [
    "AnalysisResult",
    "Analyzer",
    "CleanResult",
    "Cleaner",
    "Deduplicator",
    "FileSystemScanner",
    "Pipeline",
    "ScanResult",
    "Scheduler",
]
