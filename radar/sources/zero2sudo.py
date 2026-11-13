"""zero2sudo community job list.

@zero2sudo posts new intern/new-grad drops to Instagram stories (which expire in 24h and
have no API) and a newsletter. A community repo mirrors those drops into a single jobs.json,
refreshed daily, with real apply links. We pull that JSON the same way we pull Simplify.

Caveat: this is an unofficial mirror reconstructed from story screenshots, so a few postings
carry only a bare ATS domain instead of a deep link; those are skipped. Every kept posting
is folded against the other sources by the deduper, so overlaps don't double up.
"""
from __future__ import annotations

from datetime import date

from ..util import get, short_hash
from . import new_job

_KIND = {"internship": "intern", "intern": "intern", "new_grad": "newgrad", "newgrad": "newgrad"}


def _has_path(url: str) -> bool:
    """True if the url points at an actual posting, not just a bare ATS domain."""
    if not url or "://" not in url:
        return False
    rest = url.split("://", 1)[1]
    path = rest.split("/", 1)[1] if "/" in rest else ""
    return bool(path.strip("/?#"))


def _fix(s: str) -> str:
    """Repair the UTF-8-as-Latin-1 mojibake in some notes (e.g. 'â€"' -> '—')."""
    s = s or ""
    if "Ã" in s or "â€" in s:
        try:
            return s.encode("latin-1", "ignore").decode("utf-8", "ignore")
        except Exception:
            return s
    return s


def _iso(date_seen: str) -> str:
    try:
        return date.fromisoformat(date_seen).isoformat() + "T00:00:00+00:00"
    except Exception:
        return ""


def fetch(cfg: dict, max_age_days: int, now: float) -> list[dict]:
    url = cfg.get("url", "https://raw.githubusercontent.com/officialjackliu/zero2sudo-jobs/main/jobs.json")
    data = get(url, as_json=True, timeout=90)
    if not isinstance(data, list):
        print(f"  zero2sudo: could not load {url}")
        return []
    cutoff = date.fromtimestamp(now - max_age_days * 86400)
    out: list[dict] = []
    skipped = 0
    for x in data:
        apply_url = (x.get("apply_url") or "").strip()
        if not _has_path(apply_url):
            skipped += 1
            continue
        seen = x.get("date_seen") or ""
        try:
            if seen and date.fromisoformat(seen) < cutoff:
                continue
        except Exception:
            pass
        title = (x.get("position") or "").strip()
        company = (x.get("company") or "").strip()
        if not title or not company:
            continue
        kind = _KIND.get((x.get("type") or "").lower(), "intern")
        loc = (x.get("location") or "").strip()
        out.append(new_job(
            source="zero2sudo", native_id=short_hash(company + "|" + title), kind=kind,
            title=title, company=company, locations=[loc] if loc else [], url=apply_url,
            posted_at=_iso(seen), description=_fix(x.get("notes") or ""),
        ))
    print(f"  zero2sudo: {len(out)} postings ({skipped} skipped, no deep link)")
    return out
