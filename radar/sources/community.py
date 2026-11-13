"""Extra Simplify-schema listings.json feeds maintained by other students.

Same file format as SimplifyJobs, so each feed reuses simplify.job_from_row(). Configure
any number of feeds in [sources.community_lists]; each is {url, kind, source}. The deduper
folds anything that overlaps Simplify, so only genuinely new postings survive.
"""
from __future__ import annotations

from ..util import get
from .simplify import job_from_row


def fetch(cfg: dict, max_age_days: int, now: float) -> list[dict]:
    out: list[dict] = []
    for feed in cfg.get("feeds", []):
        url = feed.get("url")
        kind = feed.get("kind", "intern")
        source = feed.get("source", "community")
        if not url:
            continue
        data = get(url, as_json=True, timeout=90)
        if not isinstance(data, list):
            print(f"  {source} ({kind}): could not load {url}")
            continue
        cutoff = now - max_age_days * 86400
        n = 0
        for x in data:
            if not x.get("is_visible", True):
                continue
            posted = x.get("date_posted") or x.get("date_updated") or 0
            if posted and posted < cutoff:
                continue
            out.append(job_from_row(x, kind, source))
            n += 1
        print(f"  {source} ({kind}): {n} postings")
    return out
