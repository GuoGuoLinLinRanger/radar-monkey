"""SimplifyJobs public GitHub lists (internships + new grad)."""
from __future__ import annotations

from ..util import get, iso_from_ts
from . import new_job


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
            if posted < cutoff:
                continue
            out.append(new_job(
                source="simplify", native_id=str(x.get("id")), kind=kind,
                title=x.get("title", ""), company=x.get("company_name", ""),
                locations=x.get("locations") or [], url=x.get("url", ""),
                posted_at=iso_from_ts(posted), terms=x.get("terms") or [],
                category=x.get("category", ""), sponsorship_raw=x.get("sponsorship", ""),
                degrees=x.get("degrees") or [], active=bool(x.get("active", True)),
            ))
            n += 1
        print(f"  simplify {kind}: {n} postings")
    return out
