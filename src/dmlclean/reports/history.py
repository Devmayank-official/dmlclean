# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
History report generator for DMLClean.

Provides statistical analysis and reporting for cleaning history:
- Summary statistics
- Trend analysis
- Category breakdowns
- Time-based reports
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from dmlclean.models.history import HistoryEntry
    from dmlclean.storage.database import Database
    from dmlclean.storage.history_repo import HistoryRepository


@dataclass
class CleaningStats:
    """
    Summary statistics for cleaning history.

    Attributes:
        total_operations: Total number of cleaning operations.
        successful_operations: Number of successful operations.
        failed_operations: Number of failed operations.
        total_files_deleted: Total files deleted across all operations.
        total_size_freed: Total size freed in bytes.
        avg_files_per_operation: Average files deleted per operation.
        avg_size_per_operation: Average size freed per operation.
        first_operation: Date of first operation.
        last_operation: Date of last operation.
        most_used_mode: Most frequently used clean mode.
        most_used_profile: Most frequently used profile.
        top_categories: Top cleaning categories by size.
    """

    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_files_deleted: int = 0
    total_size_freed: int = 0
    avg_files_per_operation: float = 0.0
    avg_size_per_operation: float = 0.0
    first_operation: datetime | None = None
    last_operation: datetime | None = None
    most_used_mode: str | None = None
    most_used_profile: str | None = None
    top_categories: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, str | int | float | None | dict[str, int]]:
        """Convert to dictionary for reporting."""
        from dmlclean.utils.sizes import humanize_size

        return {
            "total_operations": self.total_operations,
            "successful_operations": self.successful_operations,
            "failed_operations": self.failed_operations,
            "total_files_deleted": self.total_files_deleted,
            "total_size_freed": self.total_size_freed,
            "total_size_freed_human": humanize_size(self.total_size_freed),
            "avg_files_per_operation": round(self.avg_files_per_operation, 2),
            "avg_size_per_operation": self.avg_size_per_operation,
            "avg_size_per_operation_human": humanize_size(int(self.avg_size_per_operation)),
            "first_operation": self.first_operation.isoformat() if self.first_operation else None,
            "last_operation": self.last_operation.isoformat() if self.last_operation else None,
            "most_used_mode": self.most_used_mode,
            "most_used_profile": self.most_used_profile,
            "top_categories": self.top_categories,
        }


@dataclass
class TrendData:
    """
    Data point for trend analysis.

    Attributes:
        date: Date for this data point.
        operations_count: Number of operations on this date.
        files_deleted: Files deleted on this date.
        size_freed: Size freed on this date.
    """

    date: datetime
    operations_count: int = 0
    files_deleted: int = 0
    size_freed: int = 0

    def to_dict(self) -> dict[str, str | int]:
        """Convert to dictionary for JSON serialization."""
        from dmlclean.utils.sizes import humanize_size

        return {
            "date": self.date.strftime("%Y-%m-%d"),
            "operations_count": self.operations_count,
            "files_deleted": self.files_deleted,
            "size_freed": self.size_freed,
            "size_freed_human": humanize_size(self.size_freed),
        }


class HistoryReporter:
    """
    Generate reports and statistics from cleaning history.

    This class provides:
    - Summary statistics calculation
    - Trend analysis over time
    - Category breakdowns
    - Time-based filtering

    Attributes:
        db: Database connection.
        history_repo: History repository.

    Example:
        ```python
        from dmlclean.container import get_container

        container = get_container()
        reporter = HistoryReporter(container.db, container.history_repo)

        # Get summary statistics
        stats = reporter.get_summary_stats()

        # Get trend data
        trends = reporter.get_trend_data(days=30)

        # Get category breakdown
        categories = reporter.get_category_breakdown()
        ```
    """

    def __init__(
        self,
        db: Database,
        history_repo: HistoryRepository,
    ) -> None:
        """
        Initialize the history reporter.

        Args:
            db: Database connection.
            history_repo: History repository.
        """
        self.db = db
        self.history_repo = history_repo

        logger.debug("HistoryReporter initialized")

    def get_summary_stats(self) -> CleaningStats:
        """
        Calculate summary statistics for all cleaning history.

        Returns:
            CleaningStats: Summary statistics object.

        Example:
            ```python
            stats = reporter.get_summary_stats()
            print(f"Total operations: {stats.total_operations}")
            print(f"Total size freed: {stats.total_size_freed_human}")
            ```
        """
        logger.info("Calculating summary statistics...")

        # Get all history entries
        entries = self.history_repo.list_all(limit=10000)  # Large limit for stats

        if not entries:
            logger.debug("No history entries found")
            return CleaningStats()

        # Calculate statistics
        total_ops = len(entries)
        successful = sum(1 for e in entries if e.status == "complete")
        failed = sum(1 for e in entries if e.status == "failed")
        total_files = sum(e.files_deleted for e in entries)
        total_size = sum(e.size_bytes for e in entries)

        # Find date range
        timestamps = [e.timestamp for e in entries if e.timestamp]
        first_op = min(timestamps) if timestamps else None
        last_op = max(timestamps) if timestamps else None

        # Find most used mode and profile
        mode_counts: dict[str, int] = {}
        profile_counts: dict[str, int] = {}

        for entry in entries:
            mode_counts[entry.mode] = mode_counts.get(entry.mode, 0) + 1
            profile_counts[entry.profile] = profile_counts.get(entry.profile, 0) + 1

        most_used_mode = max(mode_counts, key=lambda k: mode_counts[k]) if mode_counts else None
        most_used_profile = (
            max(profile_counts, key=lambda k: profile_counts[k]) if profile_counts else None
        )

        # Calculate averages
        avg_files = total_files / total_ops if total_ops > 0 else 0.0
        avg_size = total_size / total_ops if total_ops > 0 else 0.0

        # Get top categories
        top_categories = self._get_top_categories(entries)

        stats = CleaningStats(
            total_operations=total_ops,
            successful_operations=successful,
            failed_operations=failed,
            total_files_deleted=total_files,
            total_size_freed=total_size,
            avg_files_per_operation=avg_files,
            avg_size_per_operation=avg_size,
            first_operation=first_op,
            last_operation=last_op,
            most_used_mode=most_used_mode,
            most_used_profile=most_used_profile,
            top_categories=top_categories,
        )

        logger.info(
            f"Summary stats calculated: {total_ops} operations, "
            f"{total_files} files, {total_size} bytes"
        )

        return stats

    def get_trend_data(
        self,
        days: int = 30,
        group_by: str = "day",
    ) -> list[TrendData]:
        """
        Get trend data for the specified time period.

        Args:
            days: Number of days to analyze.
            group_by: Grouping level ('day', 'week', 'month').

        Returns:
            list[TrendData]: List of trend data points.

        Example:
            ```python
            trends = reporter.get_trend_data(days=30)
            for trend in trends:
                print(f"{trend.date}: {trend.files_deleted} files")
            ```
        """
        logger.info(f"Calculating trend data for last {days} days...")

        # Get history entries for time period
        cutoff_date = datetime.now() - timedelta(days=days)
        entries = self.history_repo.list_all(limit=10000)

        # Filter by date
        filtered = [e for e in entries if e.timestamp and e.timestamp >= cutoff_date]  # type: ignore[operator]

        if not filtered:
            logger.debug("No history entries found for time period")
            return []

        # Group by date
        grouped: dict[str, TrendData] = {}

        for entry in filtered:
            if not entry.timestamp:
                continue

            # Group by date
            date_key = entry.timestamp.strftime("%Y-%m-%d")

            if date_key not in grouped:
                grouped[date_key] = TrendData(date=entry.timestamp)  # type: ignore[arg-type]

            grouped[date_key].operations_count += 1
            grouped[date_key].files_deleted += entry.files_deleted
            grouped[date_key].size_freed += entry.size_bytes

        # Convert to sorted list
        trends = sorted(grouped.values(), key=lambda t: t.date)

        logger.info(f"Trend data calculated: {len(trends)} data points")
        return trends

    def get_category_breakdown(
        self,
        days: int | None = None,
    ) -> dict[str, dict[str, int | float]]:  # type: ignore[return]
        """
        Get breakdown of cleaning by category.

        Args:
            days: Optional number of days to filter (None = all time).

        Returns:
            dict[str, dict[str, int]]: Category breakdown with counts and sizes.

        Example:
            ```python
            breakdown = reporter.get_category_breakdown(days=30)
            for category, data in breakdown.items():
                print(f"{category}: {data['count']} files, {data['size_bytes']} bytes")
            ```
        """
        logger.info("Calculating category breakdown...")

        # Filter by date (reuse for all breakdown methods)
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            entries = self.history_repo.list_all(limit=10000)
            entries = [e for e in entries if e.timestamp and e.timestamp >= cutoff_date]  # type: ignore[operator]
        else:
            entries = self.history_repo.list_all(limit=10000)

        if not entries:
            return {}

        # Aggregate by category
        categories: dict[str, dict[str, int]] = {}

        for entry in entries:
            # Get categories from entry
            entry_categories = entry.categories or []

            for category in entry_categories:
                if category not in categories:
                    categories[category] = {"count": 0, "size_bytes": 0, "operations": 0}

                categories[category]["count"] += entry.files_deleted
                categories[category]["size_bytes"] += entry.size_bytes
                categories[category]["operations"] += 1

        # Calculate percentages
        total_size = sum(data["size_bytes"] for data in categories.values())

        for category, data in categories.items():
            if total_size > 0:
                data["percentage"] = round((data["size_bytes"] / total_size) * 100, 2)
            else:
                data["percentage"] = 0.0

        # Sort by size
        sorted_categories = dict(
            sorted(
                categories.items(),
                key=lambda x: x[1]["size_bytes"],
                reverse=True,
            )
        )

        logger.info(f"Category breakdown calculated: {len(sorted_categories)} categories")
        return sorted_categories

    def get_mode_breakdown(
        self,
        days: int | None = None,
    ) -> dict[str, dict[str, int]]:
        """
        Get breakdown of cleaning by mode.

        Args:
            days: Optional number of days to filter (None = all time).

        Returns:
            dict[str, dict[str, int]]: Mode breakdown with counts and sizes.
        """
        logger.info("Calculating mode breakdown...")

        # Filter by date (reuse for all breakdown methods)
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            entries = self.history_repo.list_all(limit=10000)
            entries = [e for e in entries if e.timestamp and e.timestamp >= cutoff_date]  # type: ignore[operator]
        else:
            entries = self.history_repo.list_all(limit=10000)

        if not entries:
            return {}

        # Aggregate by mode
        modes: dict[str, dict[str, int]] = {}

        for entry in entries:
            mode = entry.mode

            if mode not in modes:
                modes[mode] = {"count": 0, "size_bytes": 0, "files_deleted": 0}

            modes[mode]["count"] += 1
            modes[mode]["size_bytes"] += entry.size_bytes
            modes[mode]["files_deleted"] += entry.files_deleted

        logger.info(f"Mode breakdown calculated: {len(modes)} modes")
        return modes

    def get_profile_breakdown(
        self,
        days: int | None = None,
    ) -> dict[str, dict[str, int]]:
        """
        Get breakdown of cleaning by profile.

        Args:
            days: Optional number of days to filter (None = all time).

        Returns:
            dict[str, dict[str, int]]: Profile breakdown with counts and sizes.
        """
        logger.info("Calculating profile breakdown...")

        # Filter by date (reuse for all breakdown methods)
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            entries = self.history_repo.list_all(limit=10000)
            entries = [e for e in entries if e.timestamp and e.timestamp >= cutoff_date]  # type: ignore[operator]
        else:
            entries = self.history_repo.list_all(limit=10000)

        if not entries:
            return {}

        # Aggregate by profile
        profiles: dict[str, dict[str, int]] = {}

        for entry in entries:
            profile = entry.profile

            if profile not in profiles:
                profiles[profile] = {"count": 0, "size_bytes": 0, "files_deleted": 0}

            profiles[profile]["count"] += 1
            profiles[profile]["size_bytes"] += entry.size_bytes
            profiles[profile]["files_deleted"] += entry.files_deleted

        logger.info(f"Profile breakdown calculated: {len(profiles)} profiles")
        return profiles

    def _get_top_categories(
        self,
        entries: list[HistoryEntry],
        limit: int = 10,
    ) -> dict[str, int]:
        """
        Get top cleaning categories by size.

        Args:
            entries: List of history entries.
            limit: Maximum number of categories to return.

        Returns:
            dict[str, int]: Top categories with sizes.
        """
        categories: dict[str, int] = {}

        for entry in entries:
            entry_categories = entry.categories or []

            for category in entry_categories:
                categories[category] = categories.get(category, 0) + entry.size_bytes

        # Sort and limit
        sorted_cats = dict(
            sorted(
                categories.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:limit]
        )

        return sorted_cats

    def generate_report(
        self,
        days: int = 30,
        include_trends: bool = True,
        include_breakdowns: bool = True,
    ) -> dict[str, str | int | float | list | dict]:  # type: ignore[type-arg]
        """
        Generate comprehensive history report.

        Args:
            days: Number of days to include.
            include_trends: Whether to include trend data.
            include_breakdowns: Whether to include breakdowns.

        Returns:
            dict: Comprehensive report data.

        Example:
            ```python
            report = reporter.generate_report(days=30)
            print(f"Total operations: {report['total_operations']}")
            print(f"Trend data points: {len(report.get('trends', []))}")
            ```
        """
        logger.info(f"Generating comprehensive report for last {days} days...")

        report: dict[str, str | int | float | dict] = {
            "generated_at": datetime.now().isoformat(),
            "period_days": days,
        }

        # Add summary statistics
        stats = self.get_summary_stats()
        report["summary"] = stats.to_dict()

        # Add trend data
        if include_trends:
            trends = self.get_trend_data(days=days)
            report["trends"] = [t.to_dict() for t in trends]

        # Add breakdowns
        if include_breakdowns:
            report["category_breakdown"] = self.get_category_breakdown(days=days)
            report["mode_breakdown"] = self.get_mode_breakdown(days=days)
            report["profile_breakdown"] = self.get_profile_breakdown(days=days)

        logger.info("Comprehensive report generated")
        return report


__all__ = [
    "CleaningStats",
    "HistoryReporter",
    "TrendData",
]
