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

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import Select, func, or_, select

from .database.models import AAPRecord, make_engine, make_session_factory
from .discovery.scoring import Matchable, rank

_DISCLAIMER = (
    "AAP Watcher is an aggregation tool and is not an authoritative source "
    "for funding decisions. Always verify eligibility, amounts, deadlines and "
    "application procedure on the official source."
)


def _record_to_response(rec: AAPRecord, include_disclaimer: bool = True) -> dict:
    out = _record_to_dict(rec)
    if include_disclaimer:
        out["disclaimer"] = _DISCLAIMER
    return out


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
  <input id="funding_type" placeholder="type de financement">
  <input id="eligible" placeholder="candidats éligibles">
  <input id="deadline_after" placeholder="deadline après (YYYY-MM-DD)">
  <input id="deadline_before" placeholder="deadline avant (YYYY-MM-DD)">
  <input id="amount_min" placeholder="montant min" type="number">
  <input id="amount_max" placeholder="montant max" type="number">
  <select id="sort"><option value="">tri</option>
    <option value="deadline_asc">échéance ↑</option>
    <option value="deadline_desc">échéance ↓</option>
    <option value="amount_asc">montant ↑</option>
    <option value="amount_desc">montant ↓</option></select>
  <button type="submit">Rechercher</button>
</form>
<p id="count"></p>
<table id="t"><thead><tr><th>Titre</th><th>Org</th><th>Échéance</th>
<th>Montant</th><th>Statut</th></tr></thead><tbody></tbody></table>
<script>
async function go(){
  const p=new URLSearchParams();
  const q=document.getElementById('q').value; if(q)p.set('q',q);
  const o=document.getElementById('org').value; if(o)p.set('organisation',o);
  const s=document.getElementById('status').value; if(s)p.set('status',s);
  const t=document.getElementById('topic').value; if(t)p.set('topic',t);
  const f=document.getElementById('funding_type').value; if(f)p.set('funding_type',f);
  const e=document.getElementById('eligible').value; if(e)p.set('eligible_applicants',e);
  const a2=document.getElementById('deadline_after').value; if(a2)p.set('deadline_after',a2);
  const d=document.getElementById('deadline_before').value; if(d)p.set('deadline_before',d);
  const mn=document.getElementById('amount_min').value; if(mn)p.set('amount_min',mn);
  const mx=document.getElementById('amount_max').value; if(mx)p.set('amount_max',mx);
  const so=document.getElementById('sort').value; if(so)p.set('sort',so);
  const r=await fetch('/api/aaps?'+p); const j=await r.json();
  document.getElementById('count').textContent=j.total+' résultat(s)';
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
        q: str | None = Query(None, description="Full-text search (space-separated terms, AND)",
                                  examples=["cancer ai"]),
        organisation: str | None = None,
        status: str | None = None,
        topic: str | None = None,
        funding_type: str | None = None,
        eligible_applicants: str | None = None,
        geographical_scope: str | None = None,
        deadline_after: str | None = None,
        deadline_before: str | None = None,
        amount_min: int | None = None,
        amount_max: int | None = None,
        sort: str | None = Query(None, description="deadline_asc|deadline_desc|amount_asc|amount_desc"),
        limit: int = Query(50, ge=1, le=500),
        offset: int = Query(0, ge=0),
    ) -> dict:
        _SEARCH_COLS = (
            AAPRecord.title, AAPRecord.description, AAPRecord.eligibility,
            AAPRecord.organisation, AAPRecord.research_topics,
        )
        conds: list = []
        if q:
            for term in q.split():
                like = f"%{term}%"
                conds.append(or_(*(c.ilike(like) for c in _SEARCH_COLS)))
        if organisation:
            conds.append(AAPRecord.organisation.ilike(f"%{organisation}%"))
        if status:
            conds.append(AAPRecord.status == status)
        if topic:
            conds.append(AAPRecord.research_topics.ilike(f"%{topic}%"))
        if funding_type:
            conds.append(AAPRecord.funding_type.ilike(f"%{funding_type}%"))
        if eligible_applicants:
            conds.append(AAPRecord.eligible_applicants.ilike(f"%{eligible_applicants}%"))
        if geographical_scope:
            conds.append(AAPRecord.geographical_scope.ilike(f"%{geographical_scope}%"))
        if deadline_after:
            conds.append(AAPRecord.deadline >= deadline_after)
        if deadline_before:
            conds.append(AAPRecord.deadline <= deadline_before)
        if amount_min is not None:
            conds.append(AAPRecord.amount_max >= amount_min)
        if amount_max is not None:
            conds.append(AAPRecord.amount_min <= amount_max)
        stmt: Select = select(AAPRecord)
        for c in conds:
            stmt = stmt.where(c)
        order = {
            "deadline_asc": (AAPRecord.deadline.asc().nullslast(),),
            "deadline_desc": (AAPRecord.deadline.desc().nullslast(),),
            "amount_asc": (AAPRecord.amount_max.asc().nullslast(),),
            "amount_desc": (AAPRecord.amount_max.desc().nullslast(),),
        }.get(sort, (AAPRecord.deadline.asc().nullslast(),))
        stmt = stmt.order_by(*order)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        with _sf()() as session:
            total = session.scalar(count_stmt) or 0
            rows = list(session.scalars(stmt.limit(limit).offset(offset)).all())
            return {
                "items": [_record_to_response(r) for r in rows],
                "total": total,
                "limit": limit,
                "offset": offset,
            }

    @app.get("/api/aaps/{aap_id}")
    def get_aap(aap_id: int) -> dict:
        with _sf()() as session:
            rec = session.get(AAPRecord, aap_id)
            if rec is None:
                raise HTTPException(status_code=404, detail="AAP not found")
            return _record_to_response(rec)

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
                {**_record_to_response(other), "similarity": round(score, 3)}
                for other, score in scored[:top] if score > 0
            ]

    @app.get("/api/profile/matches")
    def profile_matches(
        topics: str | None = Query(None, description="Comma-separated research topics"),
        technologies: str | None = Query(None, description="Comma-separated technologies"),
        amount_min: int | None = Query(None, description="Minimum funding sought"),
        geographies: str | None = Query(None, description="Comma-separated geographies"),
        limit: int = Query(50, ge=1, le=500),
    ) -> dict:
        research_topics = [t.strip() for t in topics.split(",") if t.strip()] if topics else []
        tech_terms = [t.strip() for t in technologies.split(",") if t.strip()] if technologies else []
        geo_terms = [g.strip() for g in geographies.split(",") if g.strip()] if geographies else []
        with _sf()() as session:
            rows = list(session.scalars(select(AAPRecord)).all())
        items = [
            Matchable(
                id=r.id, title=r.title,
                topics=[t for t in (r.research_topics or "").split(", ") if t],
                amount_max=r.amount_max, geographical_scope=r.geographical_scope, status=r.status,
            )
            for r in rows
        ]
        ranked = rank(
            research_topics=research_topics, technologies=tech_terms,
            amount_min=amount_min, geographies=geo_terms, item_pool=items,
        )
        by_id = {r.id: r for r in rows}
        out = []
        for m, rel in ranked[:limit]:
            rec = by_id.get(m.id)
            if rec is None:
                continue
            out.append({**_record_to_response(rec), "relevance": rel})
        return {"items": out, "total": len(out)}

    @app.get("/api/sources")
    def list_sources() -> list[str]:
        from .scrapers.sources import available_sources

        return available_sources()

    return app
