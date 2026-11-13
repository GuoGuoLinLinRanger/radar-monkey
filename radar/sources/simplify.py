"""SimplifyJobs public GitHub lists (internships + new grad).

The row -> job mapping lives in job_from_row() so other sources that publish the same
listings.json schema (e.g. the vanshb03 student-curated lists) can reuse it verbatim.
"""
from __future__ import annotations

from ..util import get, iso_from_ts, short_hash
from . import new_job


def _fix(s: str) -> str:
    """Repair UTF-8-as-Latin-1 mojibake some mirrors carry (e.g. 'ï¿½' -> proper chars)."""
    s = s or ""
    if "Ã" in s or "â€" in s or "�" in s:
        try:
            return s.encode("latin-1", "ignore").decode("utf-8", "ignore")
        except Exception:
            return s
    return s


def job_from_row(x: dict, kind: str, source: str = "simplify") -> dict:
    """Map one listings.json row (Simplify schema) to a job record."""
    posted = x.get("date_posted") or x.get("date_updated") or 0
    nid = x.get("id") or short_hash((x.get("company_name") or "") + (x.get("title") or "") + (x.get("url") or ""))
    return new_job(
        source=source, native_id=str(nid), kind=kind,
        title=_fix(x.get("title", "")), company=_fix(x.get("company_name", "")),
        locations=[_fix(l) for l in (x.get("locations") or [])], url=x.get("url", ""),
        posted_at=iso_from_ts(posted), terms=x.get("terms") or [],
        category=x.get("category", ""), sponsorship_raw=x.get("sponsorship", ""),
        degrees=x.get("degrees") or [], active=bool(x.get("active", True)),
    )


def fetch(cfg: dict, max_age_days: int, now: float) -> list[dict]:
    out: list[dict] = []
    for kind, key in (("intern", "intern_url"), ("newgrad", "newgrad_url")):
        url = cfg.get(key)
        if not url:
            continue
        data = get(url, as_json=True, timeout=90)
        if not isinstance(data, list):
            print(f"  simplify {kind}: could not load {url}")
            continue
        cutoff = now - max_age_days * 86400
        n = 0
        for x in data:
            if not x.get("is_visible", True):
                continue
            posted = x.get("date_posted") or x.get("date_updated") or 0
            if posted and posted < cutoff:
                continue
            out.append(job_from_row(x, kind, "simplify"))
            n += 1
        print(f"  simplify {kind}: {n} postings")
    return out
