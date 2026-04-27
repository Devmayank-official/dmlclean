# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Async report service for DMLClean.

Domain service for generating reports and exports.
All methods are async for non-blocking I/O.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

from dmlclean.utils.sizes import humanize_size

if TYPE_CHECKING:
    from dmlclean.storage.database import Database
    from dmlclean.storage.history_repo import HistoryRepository


class ReportService:
    """Async domain service for report generation."""

    def __init__(self, db: Database, history_repo: HistoryRepository) -> None:
        self.db = db
        self.history_repo = history_repo
        logger.debug("ReportService initialized")

    async def generate_summary_async(
        self,
        days: int = 30,
        profile: str | None = None,
    ) -> dict[str, Any]:
        """Generate a summary report (async)."""
        stats = self.history_repo.get_summary(days=days)
        entries = self.history_repo.list_all(limit=1000)

        if profile:
            entries = [e for e in entries if e.profile == profile]

        total_operations = len(entries)
        successful = sum(1 for e in entries if e.status == "complete")
        failed = sum(1 for e in entries if e.status == "failed")
        partial = sum(1 for e in entries if e.status == "partial")

        by_profile: dict[str, dict[str, Any]] = {}
        for entry in entries:
            p = entry.profile
            if p not in by_profile:
                by_profile[p] = {"operations": 0, "files_deleted": 0, "size_bytes": 0}
            by_profile[p]["operations"] += 1
            by_profile[p]["files_deleted"] += entry.files_deleted
            by_profile[p]["size_bytes"] += entry.size_bytes

        by_mode: dict[str, int] = {}
        for entry in entries:
            mode = entry.mode
            by_mode[mode] = by_mode.get(mode, 0) + 1

        return {
            "period_days": days,
            "profile_filter": profile,
            "total_operations": total_operations,
            "successful": successful,
            "failed": failed,
            "partial": partial,
            "success_rate": (successful / total_operations * 100) if total_operations > 0 else 0,
            "total_files_deleted": stats.get("total_files_deleted", 0),
            "total_size_bytes": stats.get("total_size_bytes", 0),
            "total_size_human": humanize_size(stats.get("total_size_bytes", 0)),
            "avg_duration_ms": stats.get("avg_duration_ms", 0),
            "by_profile": by_profile,
            "by_mode": by_mode,
        }

    async def export_json_async(
        self,
        output_path: Path,
        days: int = 30,
        profile: str | None = None,
    ) -> int:
        """Export history to JSON (async)."""
        entries = self.history_repo.list_all(limit=1000)
        if profile:
            entries = [e for e in entries if e.profile == profile]

        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        entries = [e for e in entries if datetime.fromisoformat(e.timestamp).timestamp() >= cutoff]

        data = {
            "exported_at": datetime.now().isoformat(),
            "period_days": days,
            "profile_filter": profile,
            "total_entries": len(entries),
            "entries": [e.to_dict() for e in entries],
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(data, indent=2))
        logger.info(f"Exported {len(entries)} entries to JSON: {output_path}")
        return len(entries)

    async def export_csv_async(
        self,
        output_path: Path,
        days: int = 30,
        profile: str | None = None,
    ) -> int:
        """Export history to CSV (async)."""
        entries = self.history_repo.list_all(limit=1000)
        if profile:
            entries = [e for e in entries if e.profile == profile]

        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        entries = [e for e in entries if datetime.fromisoformat(e.timestamp).timestamp() >= cutoff]

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "id",
                    "timestamp",
                    "mode",
                    "profile",
                    "scan_mode",
                    "files_found",
                    "files_deleted",
                    "size_bytes",
                    "duration_ms",
                    "categories",
                    "status",
                    "error_message",
                ]
            )
            for entry in entries:
                writer.writerow(
                    [
                        entry.id,
                        entry.timestamp,
                        entry.mode,
                        entry.profile,
                        entry.scan_mode,
                        entry.files_found,
                        entry.files_deleted,
                        entry.size_bytes,
                        entry.duration_ms,
                        ",".join(entry.categories),
                        entry.status,
                        entry.error_message or "",
                    ]
                )

        logger.info(f"Exported {len(entries)} entries to CSV: {output_path}")
        return len(entries)

    async def export_html_async(
        self,
        output_path: Path,
        days: int = 30,
        profile: str | None = None,
    ) -> int:
        """Export history to HTML report (async)."""
        entries = self.history_repo.list_all(limit=1000)
        if profile:
            entries = [e for e in entries if e.profile == profile]

        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        entries = [e for e in entries if datetime.fromisoformat(e.timestamp).timestamp() >= cutoff]

        html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>DMLClean Report - {datetime.now().strftime("%Y-%m-%d")}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
th {{ background-color: #4CAF50; color: white; }}
.status-complete {{ color: green; }}
.status-failed {{ color: red; }}
</style></head><body>
<h1>DMLClean Cleaning Report</h1>
<p><strong>Period:</strong> Last {days} days</p>
<p><strong>Total Operations:</strong> {len(entries)}</p>
<table><tr><th>Date/Time</th><th>Mode</th><th>Profile</th><th>Files</th><th>Size</th><th>Status</th></tr>
"""
        for entry in entries:
            html += (
                f"<tr><td>{entry.timestamp[:19]}</td><td>{entry.mode}</td><td>{entry.profile}</td>"
            )
            html += f"<td>{entry.files_deleted:,}</td><td>{humanize_size(entry.size_bytes)}</td>"
            html += f"<td class='status-{entry.status}'>{entry.status}</td></tr>"
        html += "</table></body></html>"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html)
        logger.info(f"Exported {len(entries)} entries to HTML: {output_path}")
        return len(entries)

    # Sync wrappers
    def generate_summary(self, days: int = 30, profile: str | None = None) -> dict[str, Any]:
        import asyncio

        return asyncio.run(self.generate_summary_async(days, profile))

    def export_json(self, output_path: Path, days: int = 30, profile: str | None = None) -> int:
        import asyncio

        return asyncio.run(self.export_json_async(output_path, days, profile))

    def get_last_report(self) -> Any:
        """Get the last cleaning report entry."""
        entries = self.history_repo.list_all(limit=1)
        return entries[0] if entries else None

    def export_csv(self, output_path: Path, days: int = 30, profile: str | None = None) -> int:
        import asyncio

        return asyncio.run(self.export_csv_async(output_path, days, profile))

    def export_html(self, output_path: Path, days: int = 30, profile: str | None = None) -> int:
        import asyncio

        return asyncio.run(self.export_html_async(output_path, days, profile))

    def get_terminal_report(self, days: int = 30, profile: str | None = None) -> str:
        """Generate a terminal-friendly report (sync)."""
        summary = self.generate_summary(days=days, profile=profile)

        report = f"""
DMLClean Cleaning Report
{"=" * 50}
Period: Last {days} days
Profile: {profile or "All"}

Summary:
  Total Operations: {summary["total_operations"]}
  Successful: {summary["successful"]}
  Failed: {summary["failed"]}
  Success Rate: {summary["success_rate"]:.1f}%

Cleaning Statistics:
  Files Deleted: {summary["total_files_deleted"]:,}
  Space Freed: {summary["total_size_human"]}
  Avg Duration: {summary["avg_duration_ms"]:.0f}ms

By Mode:
"""
        for mode, count in summary["by_mode"].items():
            report += f"  {mode}: {count}\n"
        report += "\nBy Profile:\n"
        for profile_name, stats in summary["by_profile"].items():
            report += (
                f"  {profile_name}: {stats['operations']} ops, {stats['files_deleted']:,} files\n"
            )
        report += f"\n{'=' * 50}\n"
        return report


__all__ = ["ReportService"]
