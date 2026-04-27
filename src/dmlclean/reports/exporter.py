# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Report exporters for DMLClean.

Provides export functionality for multiple formats:
- JSON (machine-readable)
- CSV (spreadsheet-compatible)
- HTML (web-viewable)
"""

from __future__ import annotations

import csv
import io
import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger


class ExportError(Exception):
    """Exception raised when export fails."""

    pass


class ReportExporter(ABC):
    """
    Abstract base class for report exporters.

    All exporters must implement the export() method.
    Subclasses handle specific formats (JSON, CSV, HTML).

    Example:
        ```python
        exporter = JSONExporter()
        json_output = exporter.export(data)
        ```
    """

    @abstractmethod
    def export(self, data: dict[str, Any]) -> str:
        """
        Export data to string format.

        Args:
            data: Data to export (dictionary format).

        Returns:
            str: Exported data as string.

        Raises:
            ExportError: If export fails.
        """
        pass

    def export_to_file(
        self,
        data: dict[str, Any],
        output_path: Path | str,
    ) -> Path:
        """
        Export data to a file.

        Args:
            data: Data to export.
            output_path: Path to output file.

        Returns:
            Path: Path to created file.

        Raises:
            ExportError: If file write fails.
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            content = self.export(data)
            output_path.write_text(content, encoding="utf-8")

            logger.info(f"Report exported to {output_path}")
            return output_path

        except Exception as e:
            raise ExportError(f"Failed to export to file: {e}") from e


class JSONExporter(ReportExporter):
    """
    Export reports to JSON format.

    Provides machine-readable output with:
    - Pretty printing (indent=2)
    - UTF-8 encoding
    - ISO 8601 datetime formatting

    Example:
        ```python
        exporter = JSONExporter()
        json_output = exporter.export(scan_result)
        ```
    """

    def __init__(self, indent: int = 2, ensure_ascii: bool = False) -> None:
        """
        Initialize JSON exporter.

        Args:
            indent: JSON indentation level (2 = pretty print).
            ensure_ascii: Escape non-ASCII characters.
        """
        self.indent = indent
        self.ensure_ascii = ensure_ascii

    def export(self, data: dict[str, Any]) -> str:
        """
        Export data to JSON string.

        Args:
            data: Data to export.

        Returns:
            str: JSON-formatted string.

        Raises:
            ExportError: If JSON serialization fails.
        """
        try:
            # Convert datetime objects to ISO format
            serialized_data = self._serialize_data(data)

            json_str = json.dumps(
                serialized_data,
                indent=self.indent,
                ensure_ascii=self.ensure_ascii,
                default=str,
            )

            logger.debug(f"Exported {len(data)} keys to JSON")
            return json_str

        except Exception as e:
            raise ExportError(f"JSON export failed: {e}") from e

    def _serialize_data(self, data: Any) -> Any:
        """
        Recursively serialize data for JSON compatibility.

        Args:
            data: Data to serialize.

        Returns:
            Any: Serialized data.
        """
        if isinstance(data, dict):
            return {k: self._serialize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_data(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, Path):
            return str(data)
        elif hasattr(data, "model_dump"):  # Pydantic model
            return self._serialize_data(data.model_dump())
        elif hasattr(data, "to_dict"):  # Custom to_dict method
            return self._serialize_data(data.to_dict())
        else:
            return data


class CSVExporter(ReportExporter):
    """
    Export reports to CSV format.

    Provides spreadsheet-compatible output with:
    - Configurable delimiter
    - UTF-8 encoding
    - Header row

    Example:
        ```python
        exporter = CSVExporter()
        csv_output = exporter.export(history_data)
        ```
    """

    def __init__(
        self,
        delimiter: str = ",",
        quoting: int = csv.QUOTE_MINIMAL,
    ) -> None:
        """
        Initialize CSV exporter.

        Args:
            delimiter: Field delimiter character.
            quoting: CSV quoting mode (csv.QUOTE_*).
        """
        self.delimiter = delimiter
        self.quoting = quoting

    def export(self, data: dict[str, Any]) -> str:
        """
        Export data to CSV string.

        Note: CSV works best with list-of-dicts data structure.
        For nested data, use JSON or HTML exporter.

        Args:
            data: Data to export (list of dicts or dict with 'rows' key).

        Returns:
            str: CSV-formatted string.

        Raises:
            ExportError: If CSV export fails.
        """
        try:
            output = io.StringIO()

            # Handle different data structures
            if isinstance(data, list):
                # List of dicts
                if not data:
                    logger.warning("Empty data list for CSV export")
                    return ""

                writer = csv.DictWriter(
                    output,
                    fieldnames=list(data[0].keys()),
                    delimiter=self.delimiter,
                    quoting=int(self.quoting),
                )
                writer.writeheader()
                writer.writerows(data)

            elif isinstance(data, dict):
                # Single dict or dict with 'rows' key
                if "rows" in data and "columns" in data:
                    # Structured format
                    writer = csv.DictWriter(
                        output,
                        fieldnames=data["columns"],
                        delimiter=self.delimiter,
                        quoting=int(self.quoting),
                    )
                    writer.writeheader()
                    writer.writerows(data["rows"])
                else:
                    # Simple key-value pairs
                    writer = csv.writer(
                        output,
                        delimiter=self.delimiter,
                        quoting=int(self.quoting),
                    )
                    writer.writerow(["Key", "Value"])
                    for key, value in data.items():
                        writer.writerow([str(key), str(value)])
            else:
                raise ExportError("Unsupported data type for CSV export")

            csv_str = output.getvalue()
            logger.debug(f"Exported {len(csv_str)} characters to CSV")
            return csv_str

        except Exception as e:
            raise ExportError(f"CSV export failed: {e}") from e


class HTMLExporter(ReportExporter):
    """
    Export reports to HTML format.

    Provides web-viewable output with:
    - Responsive design
    - Styled tables
    - Color-coded risk levels
    - Print-friendly layout

    Example:
        ```python
        exporter = HTMLExporter()
        html_output = exporter.export(scan_result)
        ```
    """

    def __init__(
        self,
        title: str = "DMLClean Report",
        include_css: bool = True,
    ) -> None:
        """
        Initialize HTML exporter.

        Args:
            title: HTML page title.
            include_css: Include inline CSS styles.
        """
        self.title = title
        self.include_css = include_css

    def export(self, data: dict[str, Any]) -> str:
        """
        Export data to HTML string.

        Args:
            data: Data to export.

        Returns:
            str: HTML-formatted string.

        Raises:
            ExportError: If HTML export fails.
        """
        try:
            html_parts = [
                "<!DOCTYPE html>",
                "<html lang='en'>",
                "<head>",
                f"<title>{self.title}</title>",
                "<meta charset='UTF-8'>",
                "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            ]

            # Add CSS styles
            if self.include_css:
                html_parts.extend(self._get_css_styles())

            html_parts.extend(
                [
                    "</head>",
                    "<body>",
                    f"<h1>{self.title}</h1>",
                    f"<p class='timestamp'>Generated: {datetime.now().isoformat()}</p>",
                ]
            )

            # Add content sections
            html_parts.extend(self._render_data_sections(data))

            html_parts.extend(
                [
                    "</body>",
                    "</html>",
                ]
            )

            html_str = "\n".join(html_parts)
            logger.debug(f"Exported {len(html_str)} characters to HTML")
            return html_str

        except Exception as e:
            raise ExportError(f"HTML export failed: {e}") from e

    def _get_css_styles(self) -> list[str]:
        """
        Get inline CSS styles for HTML report.

        Returns:
            list[str]: CSS style definitions.
        """
        return [
            "<style>",
            """
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }
            h2 {
                color: #34495e;
                margin-top: 30px;
            }
            .timestamp {
                color: #7f8c8d;
                font-size: 0.9em;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
                background-color: white;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            th, td {
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }
            th {
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            tr:hover {
                background-color: #f1f1f1;
            }
            .risk-low {
                background-color: #d4edda;
                color: #155724;
            }
            .risk-medium {
                background-color: #fff3cd;
                color: #856404;
            }
            .risk-high {
                background-color: #f8d7da;
                color: #721c24;
            }
            .risk-blocked {
                background-color: #dc3545;
                color: white;
            }
            .stat-card {
                display: inline-block;
                background-color: white;
                border-radius: 8px;
                padding: 20px;
                margin: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                min-width: 200px;
            }
            .stat-value {
                font-size: 2em;
                font-weight: bold;
                color: #3498db;
            }
            .stat-label {
                color: #7f8c8d;
                font-size: 0.9em;
            }
            .section {
                background-color: white;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            @media print {
                body {
                    background-color: white;
                }
                .section {
                    box-shadow: none;
                    border: 1px solid #ddd;
                }
            }
            """,
            "</style>",
        ]

    def _render_data_sections(self, data: dict[str, Any]) -> list[str]:
        """
        Render data sections to HTML.

        Args:
            data: Data to render.

        Returns:
            list[str]: HTML section strings.
        """
        sections = []

        # Render each top-level key as a section
        for key, value in data.items():
            if isinstance(value, dict):
                sections.extend(self._render_dict_section(key, value))
            elif isinstance(value, list):
                sections.extend(self._render_list_section(key, value))
            else:
                sections.extend(self._render_value_section(key, value))

        return sections

    def _render_dict_section(self, title: str, data: dict[str, Any]) -> list[str]:
        """
        Render a dictionary as an HTML table section.

        Args:
            title: Section title.
            data: Dictionary data.

        Returns:
            list[str]: HTML strings.
        """
        html = [
            "<div class='section'>",
            f"<h2>{title.replace('_', ' ').title()}</h2>",
            "<table>",
            "<thead><tr><th>Key</th><th>Value</th></tr></thead>",
            "<tbody>",
        ]

        for key, value in data.items():
            value_str = str(value)
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, indent=2)

            # Add risk level styling
            row_class = ""
            if key.lower() in ["low", "medium", "high", "blocked"]:
                row_class = f"class='risk-{key.lower()}'"

            html.append(f"<tr {row_class}><td>{key}</td><td><pre>{value_str}</pre></td></tr>")

        html.extend(
            [
                "</tbody>",
                "</table>",
                "</div>",
            ]
        )

        return html

    def _render_list_section(self, title: str, data: list[Any]) -> list[str]:
        """
        Render a list as an HTML table section.

        Args:
            title: Section title.
            data: List data.

        Returns:
            list[str]: HTML strings.
        """
        if not data:
            return [
                "<div class='section'>",
                f"<h2>{title.replace('_', ' ').title()}</h2>",
                "<p>No data available.</p>",
                "</div>",
            ]

        # Get columns from first item
        if isinstance(data[0], dict):
            columns = list(data[0].keys())
        else:
            columns = ["Value"]

        html = [
            "<div class='section'>",
            f"<h2>{title.replace('_', ' ').title()}</h2>",
            "<table>",
            "<thead><tr>",
        ]

        # Header row
        for col in columns:
            html.append(f"<th>{col}</th>")

        html.extend(
            [
                "</tr></thead>",
                "<tbody>",
            ]
        )

        # Data rows
        for item in data:
            html.append("<tr>")
            if isinstance(item, dict):
                for col in columns:
                    html.append(f"<td>{item.get(col, '')}</td>")
            else:
                html.append(f"<td>{item}</td>")
            html.append("</tr>")

        html.extend(
            [
                "</tbody>",
                "</table>",
                "</div>",
            ]
        )

        return html

    def _render_value_section(self, title: str, value: Any) -> list[str]:
        """
        Render a single value as an HTML section.

        Args:
            title: Section title.
            value: Value to render.

        Returns:
            list[str]: HTML strings.
        """
        return [
            "<div class='section'>",
            f"<h2>{title.replace('_', ' ').title()}</h2>",
            f"<p class='stat-value'>{value}</p>",
            "</div>",
        ]


def get_exporter(format: str) -> ReportExporter:
    """
    Factory function to get exporter by format name.

    Args:
        format: Export format name ('json', 'csv', 'html').

    Returns:
        ReportExporter: Exporter instance.

    Raises:
        ExportError: If format is not supported.

    Example:
        ```python
        exporter = get_exporter('json')
        output = exporter.export(data)
        ```
    """
    exporters: dict[str, type[ReportExporter]] = {
        "json": JSONExporter,
        "csv": CSVExporter,
        "html": HTMLExporter,
    }

    format_lower = format.lower()
    if format_lower not in exporters:
        raise ExportError(
            f"Unsupported export format: {format}. Supported formats: {', '.join(exporters.keys())}"
        )

    return exporters[format_lower]()


__all__ = [
    "CSVExporter",
    "ExportError",
    "HTMLExporter",
    "JSONExporter",
    "ReportExporter",
    "get_exporter",
]
