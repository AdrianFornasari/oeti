from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class FetchedDocument:
    url: str
    status_code: int
    mime_type: str | None
    body: bytes
    retrieved_at: datetime
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ParsedDocument:
    url: str
    title: str | None
    published_at: datetime | None
    language: str | None
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
