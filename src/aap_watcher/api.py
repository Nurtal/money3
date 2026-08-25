"""REST API + minimal web UI (Phase 6).

Exposes the stored AAPs with full-text search, advanced filters, per-AAP
detail, and a lightweight "similar AAP" endpoint (Jaccard over topics +
organisation — no embeddings required for a first version). FastAPI provides
OpenAPI docs at ``/docs`` for free, satisfying the "public API documentation"
item. The DB is read-only here; ingestion happens via the ``run``/``monitor``
commands.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import Select, select

from .database.models import AAPRecord, make_engine, make_session_factory

_INDEX_HTML = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<title>AAP Watcher</title>
<style>body{font-family:system-ui;margin:2rem;max-width:70rem}
input,select{margin:.2rem;padding:.3rem}
table{border-collapse:collapse;width:100%;margin-top:1rem}
td,th{border:1px solid #ccc;padding:.4rem;text-align:left;font-size:.9rem}</style>
</head><body>
<h1>AAP Watcher</h1>
<form id="f" onsubmit="return go()">
  <input id="q" placeholder="recherche (ex: cancer)">
  <input id="org" placeholder="organisation">
  <select id="status"><option value="">statut</option>
    <option>open</option><option>closing_soon</option><option>closed</option>
    <option>cancelled</option><option>upcoming</option></select>
  <input id="topic" placeholder="topic">
  <input id="deadline_before" placeholder="deadline avant (YYYY-MM-DD)">
  <input id="amount_min" placeholder="montant min" type="number">
  <button type="submit">Rechercher</button>
</form>
<table id="t"><thead><tr><th>Titre</th><th>Org</th><th>Échéance</th>
<th>Montant</th><th>Statut</th></tr></thead><tbody></tbody></table>
<script>
async function go(){
  const p=new URLSearchParams();
  const q=document.getElementById('q').value; if(q)p.set('q',q);
  const o=document.getElementById('org').value; if(o)p.set('organisation',o);
  const s=document.getElementById('status').value; if(s)p.set('status',s);
  const t=document.getElementById('topic').value; if(t)p.set('topic',t);
  const d=document.getElementById('deadline_before').value; if(d)p.set('deadline_before',d);
  const a=document.getElementById('amount_min').value; if(a)p.set('amount_min',a);
  const r=await fetch('/api/aaps?'+p); const j=await r.json();
  const tb=document.querySelector('#t tbody'); tb.innerHTML='';
  for(const x of j.items){const tr=document.createElement('tr');
    tr.innerHTML=`<td>${x.title||''}</td><td>${x.organisation||''}</td>
      <td>${x.deadline||''}</td><td>${x.amount_max??''}</td><td>${x.status||''}</td>`;
    tb.appendChild(tr);}
  return false;
}
go();
</script></body></html>"""


def _record_to_dict(rec: AAPRecord) -> dict:
    return {
        "id": rec.id,
        "title": rec.title,
        "organisation": rec.organisation,
        "description": rec.description,
        "amount_min": rec.amount_min,
        "amount_max": rec.amount_max,
        "currency": rec.currency,
        "opening_date": rec.opening_date,
        "deadline": rec.deadline,
        "eligibility": rec.eligibility,
        "research_topics": [t for t in (rec.research_topics or "").split(", ") if t],
        "geographical_scope": rec.geographical_scope,
        "funding_type": rec.funding_type,
        "application_url": rec.application_url,
        "source_url": rec.source_url,
        "status": rec.status,
        "extraction_method": rec.extraction_method,
        "confidence_score": rec.confidence_score,
        "version": rec.version,
        "scraped_at": rec.scraped_at.isoformat() if rec.scraped_at else None,
    }


def _similarity(a: AAPRecord, b: AAPRecord) -> float:
    ta = {t for t in (a.research_topics or "").split(", ") if t}
    tb = {t for t in (b.research_topics or "").split(", ") if t}
    if ta or tb:
        inter = len(ta & tb)
        union = len(ta | tb)
        jac = inter / union if union else 0.0
    else:
        jac = 0.0
    org_bonus = 0.25 if a.organisation and a.organisation == b.organisation else 0.0
    return min(1.0, jac + org_bonus)


def create_app(db_url: str = "sqlite:///aap_watcher.db") -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = make_engine(db_url)
        app.state.engine = engine
        app.state.session_factory = make_session_factory(engine)
        yield

    app = FastAPI(title="AAP Watcher API", version="0.1.0", lifespan=lifespan)

    def _sf():
        return app.state.session_factory

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return _INDEX_HTML

    @app.get("/api/aaps")
    def list_aaps(
        q: Optional[str] = Query(None, description="Full-text search"),
        organisation: Optional[str] = None,
        status: Optional[str] = None,
        topic: Optional[str] = None,
        deadline_before: Optional[str] = None,
        amount_min: Optional[int] = None,
        limit: int = Query(50, ge=1, le=500),
        offset: int = Query(0, ge=0),
    ) -> dict:
        stmt: Select = select(AAPRecord)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                (AAPRecord.title.ilike(like))
                | (AAPRecord.eligibility.ilike(like))
                | (AAPRecord.description.ilike(like))
                | (AAPRecord.organisation.ilike(like))
            )
        if organisation:
            stmt = stmt.where(AAPRecord.organisation.ilike(f"%{organisation}%"))
        if status:
            stmt = stmt.where(AAPRecord.status == status)
        if topic:
            stmt = stmt.where(AAPRecord.research_topics.ilike(f"%{topic}%"))
        if deadline_before:
            stmt = stmt.where(AAPRecord.deadline <= deadline_before)
        if amount_min is not None:
            stmt = stmt.where(AAPRecord.amount_max >= amount_min)
        stmt = stmt.order_by(AAPRecord.deadline.asc().nullslast()).limit(limit).offset(offset)
        with _sf()() as session:
            rows = list(session.scalars(stmt).all())
            return {"items": [_record_to_dict(r) for r in rows], "count": len(rows)}

    @app.get("/api/aaps/{aap_id}")
    def get_aap(aap_id: int) -> dict:
        with _sf()() as session:
            rec = session.get(AAPRecord, aap_id)
            if rec is None:
                raise HTTPException(status_code=404, detail="AAP not found")
            return _record_to_dict(rec)

    @app.get("/api/aaps/{aap_id}/similar")
    def similar_aaps(aap_id: int, top: int = Query(5, ge=1, le=50)) -> list[dict]:
        with _sf()() as session:
            rec = session.get(AAPRecord, aap_id)
            if rec is None:
                raise HTTPException(status_code=404, detail="AAP not found")
            all_rows = list(session.scalars(select(AAPRecord)).all())
            scored = [
                (other, _similarity(rec, other))
                for other in all_rows if other.id != rec.id
            ]
            scored.sort(key=lambda x: x[1], reverse=True)
            return [
                {**_record_to_dict(other), "similarity": round(score, 3)}
                for other, score in scored[:top] if score > 0
            ]

    @app.get("/api/sources")
    def list_sources() -> list[str]:
        from .scrapers.sources import available_sources

        return available_sources()

    return app
