"""
History Request/Result DTOs.
"""

from __future__ import annotations

from dataclasses import field
from typing import Any

from pydantic import BaseModel, Field


class HistoryRequest(BaseModel):
    """History query request."""

    limit: int = Field(default=10, ge=1, le=1000)
    profile: str | None = None
    status: str | None = None
    mode: str | None = None


class HistoryEntry(BaseModel):
    """History entry."""

    id: str
    timestamp: str
    mode: str
    profile: str
    files_deleted: int
    size_bytes: int
    status: str
    error_message: str | None = None


class HistoryListResult(BaseModel):
    """History list result."""

    entries: list[HistoryEntry] = field(default_factory=list)
    total: int = 0
    has_more: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entries": [e.model_dump() for e in self.entries],
            "total": self.total,
            "has_more": self.has_more,
        }


__all__ = ["HistoryEntry", "HistoryListResult", "HistoryRequest"]
