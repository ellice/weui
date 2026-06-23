from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

SessionType = Literal["private", "group", "unknown"]


@dataclass(frozen=True)
class ControlLocator:
    """A simple, serializable description of a UI control."""

    title: str | None = None
    title_re: str | None = None
    auto_id: str | None = None
    control_type: str | None = None
    class_name: str | None = None
    found_index: int | None = None

    def to_search_criteria(self) -> dict[str, Any]:
        criteria: dict[str, Any] = {}
        if self.title is not None:
            criteria["title"] = self.title
        if self.title_re is not None:
            criteria["title_re"] = self.title_re
        if self.auto_id is not None:
            criteria["auto_id"] = self.auto_id
        if self.control_type is not None:
            criteria["control_type"] = self.control_type
        if self.class_name is not None:
            criteria["class_name"] = self.class_name
        return criteria


@dataclass(frozen=True)
class SessionSummary:
    """Metadata extracted from the conversation list."""

    name: str
    session_type: SessionType = "unknown"
    preview: str = ""
    unread_count: int = 0
    raw_text: str = ""


@dataclass(frozen=True)
class MessageChunk:
    """A single chunk of outbound text."""

    content: str
    index: int
    is_last: bool


@dataclass(frozen=True)
class SendResult:
    """Structured result for a send operation."""

    target: str
    chunks: tuple[MessageChunk, ...] = field(default_factory=tuple)
    attachments: tuple[Path, ...] = field(default_factory=tuple)
