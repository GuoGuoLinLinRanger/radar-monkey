"""Every source returns a list of dicts built by new_job(), so the rest of the pipeline
never has to care where a posting came from."""
from __future__ import annotations

from .. import normalize as N
from ..util import clean_url, slug, short_hash


def job_id(company: str, title: str, kind: str) -> str:
    """Stable id: same company + title + kind = same job, whichever site listed it.
    The tracker keys on this, so don't change it lightly."""
    return short_hash(f"{slug(company)}|{slug(title)}|{kind}")


def new_job(*, source: str, native_id: str, kind: str, title: str, company: str,
            locations: list[str], url: str, posted_at: str, work_model: str = "",
            terms: list[str] | None = None, category: str = "", sponsorship_raw: str = "",
            degrees: list[str] | None = None, active: bool = True, description: str = "",
            pay: dict | None = None) -> dict:
    title = (title or "").strip()
    company = (company or "").strip()
    locations = [l.strip() for l in (locations or []) if l and l.strip()]
    url = clean_url(url)
    model, remote_ok = N.work_model_of(work_model, locations)
    terms = list(terms or []) or N.terms_from_title(title)
    terms = [t for t in terms if t and t != "N/A"]
    job = {
        "id": job_id(company, title, kind),
        "kind": kind,
        "title": title,
        "company": company,
        "locations": locations,
        "countries": N.countries_of(locations),
        "work_model": model,
        "remote_ok": remote_ok,
        "url": url,
        "ats": N.ats_of(url),
        "posted_at": posted_at,
        "terms": terms,
        "category": N.category_of(category, title),
        "sponsorship": N.sponsorship_of(sponsorship_raw, description),
        "degrees": list(degrees or []),
        "flags": N.title_flags(title),
        "active": bool(active),
        "sources": [source],
        "source_ids": [f"{source}:{native_id}"],
        "alt_urls": [],
        "pay": pay or (N.pay_from_text(description) if description else {}),
        "description": description[:8000] if description else "",
        "qualifications": N.qualifications_from(description) if description else "",
    }
    return job
