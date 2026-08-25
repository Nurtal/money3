"""Repository: persistence, raw-source storage, versioning and change detection.

Phase 5 (production monitoring): the database preserves historical versions
rather than overwriting AAPs (README: database, extraction history). Each store
attempt compares the incoming extraction to the latest stored version and either
inserts a new record (new / modified / deadline-changed / cancelled) or records
no change. This is what lets the monitor detect new, modified, re-deadlined and
cancelled calls over time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select

from ..benchmark.normalisation import normalize_text, normalize_value
from .models import AAPRecord, Base, RawDocument

_COMPARED = (
    "title", "organisation", "description", "amount_max", "currency",
    "deadline", "eligibility", "status", "funding_type", "geographical_scope",
)

_CANCEL_KW = (
    "annul", "annulé", "annulée", "cancelled", "clôturé", "cloture",
    "terminé", "terminée", "suspendu", "abandonné", "abandonnee",
)


@dataclass
class ChangeEvent:
    type: str  # new | unchanged | modified | deadline_changed | cancelled
    version: int
    key: str


class Repository:
    def __init__(self, session_factory):
        self._sf = session_factory

    def init_db(self, engine) -> None:
        Base.metadata.create_all(engine)

    def exists(self, dedupe_key: str) -> bool:
        with self._sf() as session:
            return (
                session.scalar(
                    select(AAPRecord.id).where(AAPRecord.dedupe_key == dedupe_key)
                )
                is not None
            )

    def latest(self, dedupe_key: str) -> Optional[AAPRecord]:
        with self._sf() as session:
            return session.scalar(
                select(AAPRecord)
                .where(AAPRecord.dedupe_key == dedupe_key)
                .order_by(AAPRecord.version.desc())
                .limit(1)
            )

    def history(self, dedupe_key: str) -> list[AAPRecord]:
        with self._sf() as session:
            return list(
                session.scalars(
                    select(AAPRecord)
                    .where(AAPRecord.dedupe_key == dedupe_key)
                    .order_by(AAPRecord.version.asc())
                ).all()
            )

    def save_raw(self, source_url: str, body: str, content_type: Optional[str] = None) -> None:
        with self._sf() as session:
            session.add(RawDocument(source_url=source_url, body=body, content_type=content_type))
            session.commit()

    @staticmethod
    def _extraction_fields(extraction) -> dict:
        out = {}
        for f in _COMPARED:
            val = getattr(extraction, f, None)
            if f == "status":
                out[f] = (val.value if hasattr(val, "value") else str(val)).lower()
            elif f in ("amount_max", "deadline"):
                out[f] = normalize_value(f, val)
            else:
                out[f] = normalize_text(val)
        return out

    def save_aap(self, extraction) -> ChangeEvent:
        """Persist an extraction, preserving history and detecting changes."""
        key = extraction.dedupe_key()
        prev = self.latest(key)
        if prev is None:
            version = 1
            ctype = "new"
        else:
            prev_norm = {f: self._norm_record(prev, f) for f in _COMPARED}
            new_fields = self._extraction_fields(extraction)
            cancelled = self._is_cancelled(extraction)
            if prev_norm == new_fields and not (cancelled and prev.status != "cancelled"):
                return ChangeEvent("unchanged", prev.version, key)
            version = prev.version + 1
            if cancelled and prev.status != "cancelled":
                ctype = "cancelled"
            elif (
                prev_norm.get("deadline") != new_fields.get("deadline")
                and all(
                    prev_norm.get(f) == new_fields.get(f)
                    for f in _COMPARED if f != "deadline"
                )
            ):
                ctype = "deadline_changed"
            else:
                ctype = "modified"

        status_val = extraction.status.value if hasattr(extraction.status, "value") else str(extraction.status)
        if ctype == "cancelled":
            status_val = "cancelled"
        record = AAPRecord(
            dedupe_key=key,
            version=version,
            title=extraction.title,
            organisation=extraction.organisation,
            description=extraction.description,
            amount_min=extraction.amount_min,
            amount_max=extraction.amount_max,
            currency=extraction.currency,
            opening_date=extraction.opening_date,
            deadline=extraction.deadline,
            eligibility=extraction.eligibility,
            eligible_applicants=", ".join(extraction.eligible_applicants),
            research_topics=", ".join(extraction.research_topics),
            geographical_scope=extraction.geographical_scope,
            project_duration=extraction.project_duration,
            funding_type=extraction.funding_type,
            application_url=extraction.application_url,
            source_url=extraction.source_url,
            documents=", ".join(extraction.documents),
            contact=extraction.contact,
            status=status_val,
            extraction_method=extraction.extraction_method,
            confidence_score=extraction.confidence_score,
            source_text=extraction.provenance.source_text if extraction.provenance else None,
        )
        with self._sf() as session:
            session.add(record)
            session.commit()
        return ChangeEvent(ctype, version, key)

    @staticmethod
    def _norm_record(rec: AAPRecord, field: str):
        val = getattr(rec, field)
        if field == "status":
            return str(val).lower()
        if field in ("amount_max", "deadline"):
            return normalize_value(field, val)
        return normalize_text(val)

    @staticmethod
    def _is_cancelled(extraction) -> bool:
        status_val = extraction.status.value if hasattr(extraction.status, "value") else str(extraction.status)
        if status_val == "cancelled":
            return True
        text = (extraction.provenance.source_text or "") if extraction.provenance else ""
        low = text.lower()
        return any(kw in low for kw in _CANCEL_KW)
