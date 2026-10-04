"""Intern Insider (interninsider.me): a static site, no API.

Inventory comes from sitemap-seo/jobs-open (one URL per open posting, `lastmod`
is the date posted). Each job page carries a schema.org JobPosting JSON-LD block
plus a strip of badges (term, paid, visa). The site has no categories, so SWE is
decided from the URL slug before fetching, and pay/qualifications are parsed from
the description by the shared normalize layer. No employer apply link is exposed,
so `url` points at the Intern Insider page.

Each posting is its own request, so parsed records are cached by UUID under the
data dir and only UUIDs new to the sitemap are fetched. Entries that drop out of
the sitemap drop out of the cache.
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import html
import json
import re

from ..swe import is_swe
from ..util import get
from . import new_job

SITEMAP = "https://interninsider.me/sitemap-seo/jobs-open"
LOC_RE = re.compile(r"<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>")
LD_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
BADGE_BLOCK_RE = re.compile(r'seo-d1[^"]*"[^>]*>(.*?)</div>', re.S)
BADGE_RE = re.compile(r"<(?:a|span)\b[^>]*>(.*?)</(?:a|span)>", re.S)
TAG_RE = re.compile(r"<[^>]+>")
UUID_RE = re.compile(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$")
TERM_RE = re.compile(r"^(Spring|Summer|Fall|Winter) \d{4}$|^rolling$", re.I)
COUNTRY = {"US": "US", "USA": "US", "United States": "US", "CA": "CA", "Canada": "CA"}
SKIP_BADGES = {"New", "Paid", "Actively hiring", "Remote-friendly", "Visa sponsorship"}


def _cache_path():
    from ..store import data_dir
    d = data_dir() / "cache"
    d.mkdir(parents=True, exist_ok=True)
    return d / "interninsider.json"


def _load_cache() -> dict:
    p = _cache_path()
    if p.exists():
        try:
            return json.loads(p.read_text())
        except (OSError, ValueError):
            pass
    return {}


def _save_cache(cache: dict) -> None:
    _cache_path().write_text(json.dumps(cache, separators=(",", ":")))


def _slug_title(url: str) -> str:
    tail = url.rstrip("/").rsplit("/", 1)[-1]
    return UUID_RE.sub("", tail).rstrip("-").replace("-", " ")


def _uuid(url: str) -> str:
    m = UUID_RE.search(url.rstrip("/"))
    return m.group(1) if m else url


def _list_open_jobs() -> list[tuple[str, str]]:
    page = get(SITEMAP)
    if not page:
        return []
    rows = LOC_RE.findall(page)
    rows.sort(key=lambda r: r[1], reverse=True)
    return rows


def _parse_job(url: str, lastmod: str) -> dict | None:
    page = get(url)
    if not page:
        return None
    ld = next((json.loads(t) for t in LD_RE.findall(page) if '"JobPosting"' in t), None)
    if not ld:
        return None
    block = BADGE_BLOCK_RE.search(page)
    badges = [html.unescape(TAG_RE.sub("", b)).strip() for b in BADGE_RE.findall(block.group(1))] if block else []
    badges = [b for b in badges if b]
    org = ld.get("hiringOrganization") or {}
    locs = ld.get("jobLocation") or []
    if isinstance(locs, dict):
        locs = [locs]
    loc_strs, countries = [], set()
    for l in locs:
        a = l.get("address") or {}
        countries.add(COUNTRY.get(a.get("addressCountry") or "", a.get("addressCountry") or ""))
        s = ", ".join(x for x in [a.get("addressLocality"), a.get("addressRegion")] if x)
        if s:
            loc_strs.append(s)
    remote = ld.get("jobLocationType") == "TELECOMMUTE" or "Remote-friendly" in badges
    if remote:
        for req in (ld.get("applicantLocationRequirements") or []):
            countries.add(COUNTRY.get(req.get("name") or "", req.get("name") or ""))
    country = next((c for c in ("US", "CA") if c in countries), "")
    desc = html.unescape(TAG_RE.sub(" ", ld.get("description") or ""))
    posted = ld.get("datePosted") or lastmod
    try:
        posted_dt = dt.datetime.fromisoformat(posted)
    except ValueError:
        posted_dt = dt.datetime.fromisoformat(lastmod + "T00:00:00+00:00")
    if posted_dt.tzinfo is None:
        posted_dt = posted_dt.replace(tzinfo=dt.timezone.utc)
    terms = [b for b in badges if TERM_RE.match(b)]
    return {
        "id": _uuid(url),
        "country": country,
        "title": ld.get("title") or "",
        "company": org.get("name") or "",
        "locations": loc_strs or (["Remote"] if remote else []),
        "work_model": "Remote" if remote else "",
        "sponsorship_raw": "offers sponsorship" if "Visa sponsorship" in badges else "",
        "terms": terms,
        "posted_at": posted_dt.replace(microsecond=0).isoformat(),
        "url": url,
        "description": desc,
    }


def fetch(cfg: dict, max_age_days: int, now: float) -> list[dict]:
    countries = {c.upper() for c in cfg.get("countries", ["US", "CA"])}
    days = int(cfg.get("max_age_days", max_age_days))
    workers = int(cfg.get("workers", 8))
    cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).strftime("%Y-%m-%d")

    all_jobs = _list_open_jobs()
    wanted = [(u, lm) for u, lm in all_jobs if lm >= cutoff and is_swe(_slug_title(u))]
    cache = _load_cache()
    todo = [(u, lm) for u, lm in wanted if _uuid(u) not in cache]
    print(f"  interninsider: {len(all_jobs)} open, {len(wanted)} SWE within {days}d, {len(todo)} to fetch")

    failed = 0
    if todo:
        with cf.ThreadPoolExecutor(workers) as ex:
            for rec in ex.map(lambda j: _parse_job(*j), todo):
                if rec is None:
                    failed += 1
                else:
                    cache[rec["id"]] = rec
    keep = {_uuid(u) for u, _ in wanted}
    cache = {k: v for k, v in cache.items() if k in keep}
    _save_cache(cache)

    out: list[dict] = []
    for r in cache.values():
        if countries and r["country"] not in countries:
            continue
        out.append(new_job(
            source="interninsider", native_id=r["id"], kind="intern",
            title=r["title"], company=r["company"], locations=r["locations"],
            url=r["url"], posted_at=r["posted_at"], work_model=r["work_model"],
            terms=r["terms"], sponsorship_raw=r["sponsorship_raw"],
            description=r["description"],
        ))
    print(f"  interninsider: {len(out)} rows kept, {failed} pages failed or had no JSON-LD")
    return out
