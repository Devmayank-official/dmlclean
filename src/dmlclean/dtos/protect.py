"""
Protect Request/Result DTOs.
"""

from __future__ import annotations

from dataclasses import field
from typing import Any

from pydantic import BaseModel


class ProtectRequest(BaseModel):
    """Protect zone request."""

    path: str
    description: str = ""
    is_glob: bool = False


class ProtectionEntry(BaseModel):
    """Protection entry."""

    id: str
    path: str
    description: str
    is_glob: bool
    created_at: str


class ProtectResult(BaseModel):
    """Protect operation result."""

    success: bool = True
    entry: ProtectionEntry | None = None
    message: str = ""
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "entry": self.entry.model_dump() if self.entry else None,
            "message": self.message,
            "errors": self.errors,
        }


__all__ = ["ProtectRequest", "ProtectResult", "ProtectionEntry"]
