"""Notifications (Phase 5): deliver detected AAP changes over configurable channels."""

from .base import ChangeNotice, Notifier
from .email import EmailNotifier, build_digest

__all__ = ["ChangeNotice", "EmailNotifier", "Notifier", "build_digest"]
