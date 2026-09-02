"""Database layer (SQLAlchemy 2.0).

Local development uses SQLite; production targets PostgreSQL. The schema
preserves historical versions rather than overwriting AAPs (README: database).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    sessionmaker,
)


class Base(DeclarativeBase):
    pass


class AAPRecord(Base):
    """Stored, normalised AAP row with provenance."""

    __tablename__ = "aaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dedupe_key: Mapped[str] = mapped_column(String, index=True, unique=False)
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    organisation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    amount_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    amount_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    opening_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    deadline: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    eligibility: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    eligible_applicants: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    research_topics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    geographical_scope: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    project_duration: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    funding_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    application_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    documents: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="unknown")
    extraction_method: Mapped[str] = mapped_column(String, default="unknown")
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class RawDocument(Base):
    """Raw downloaded source, kept for traceability and re-extraction."""

    __tablename__ = "raw_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_url: Mapped[str] = mapped_column(Text, index=True)
    content_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    body: Mapped[str] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class Notification(Base):
    """Records that a given AAP version's change was already notified.

    Phase 5: prevents the monitor from re-sending the same change event
    (new/modified/deadline_changed/cancelled) on every pass.
    """

    __tablename__ = "notifications"
    __table_args__ = (UniqueConstraint("dedupe_key", "version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dedupe_key: Mapped[str] = mapped_column(String, index=True)
    version: Mapped[int] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String)
    notified_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


def make_engine(url: str = "sqlite:///aap_watcher.db") -> "Engine":  # noqa: F821
    return create_engine(url, future=True)


def make_session_factory(engine) -> "sessionmaker":  # noqa: F821
    return sessionmaker(bind=engine, expire_on_commit=False)
