"""Notification interface (Phase 5).

Notifiers consume a list of :class:`ChangeNotice` (one per detected change:
new / modified / deadline_changed / cancelled) and deliver them through a
channel (currently email, others can be added later). The notifier stays
decoupled from the database: it only sees already-built notice objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class ChangeNotice:
    """Human-readable summary of a single monitored change."""

    type: str
    key: str
    version: int
    title: str | None
    organisation: str | None
    deadline: str | None
    status: str | None
    application_url: str | None
    source_url: str | None


class Notifier(Protocol):
    """Deliver a batch of change notices. Must not raise on one bad notice."""

    def send(self, notices: list[ChangeNotice]) -> None: ...
