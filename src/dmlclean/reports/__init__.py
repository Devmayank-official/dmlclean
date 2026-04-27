# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Reports package for DMLClean.

This module provides report generation capabilities:
- Terminal reports with Rich formatting
- Export to JSON/CSV/HTML formats
- History reports with statistics

Example:
    ```python
    from dmlclean.reports import TerminalReporter, ReportExporter

    # Generate terminal report
    reporter = TerminalReporter()
    reporter.render_scan_result(scan_result)

    # Export to JSON
    exporter = ReportExporter(format="json")
    json_output = exporter.export(data)
    ```
"""

from dmlclean.reports.exporter import CSVExporter, HTMLExporter, JSONExporter, ReportExporter
from dmlclean.reports.history import HistoryReporter
from dmlclean.reports.terminal import TerminalReporter

__all__ = [
    "CSVExporter",
    "HTMLExporter",
    "HistoryReporter",
    "JSONExporter",
    "ReportExporter",
    "TerminalReporter",
]
