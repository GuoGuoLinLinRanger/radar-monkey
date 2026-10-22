"""Company job boards via the official public APIs of Greenhouse, Lever and Ashby.

Used two ways:
  * fetch()  - the watchlist: poll a company's whole board, keep early-career titles.
  * lookup() - enrichment: given one posting URL, get pay + full text.
"""
from __future__ import annotations

import re
import time
import urllib.parse
from datetime import datetime, timezone

from .. import normalize as N
from ..util import get, iso_from_ts, post_json, strip_html
from . import new_job

INTERN_RE = re.compile(r"(?i)\bintern(?!ational)|co-?op|\bplacement\b|apprentice")

_board_cache: dict[tuple[str, str], list[dict]] = {}


# ---------- raw board loaders -> common shape ----------

def _greenhouse(board: str) -> list[dict]:
    d = get(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true", as_json=True)
    jobs = (d or {}).get("jobs") or []
    out = []
    for j in jobs:
        text = strip_html(j.get("content", ""))
        out.append({
            "id": str(j.get("id")), "title": j.get("title", ""),
            "locations": [(j.get("location") or {}).get("name", "")],
            "url": j.get("absolute_url", ""),
            "posted": j.get("first_published") or j.get("updated_at") or "",
            "text": text, "pay": N.pay_from_text(text), "model": "",
        })
    return out


def _lever(board: str) -> list[dict]:
    d = get(f"https://api.lever.co/v0/postings/{board}?mode=json", as_json=True)
    out = []
    for j in d if isinstance(d, list) else []:
        cats = j.get("categories") or {}
        lists = "\n".join(f"{l.get('text','')}\n{strip_html(l.get('content',''))}" for l in j.get("lists") or [])
        text = (j.get("descriptionPlain") or "") + "\n" + lists + "\n" + (j.get("additionalPlain") or "")
        pay = {}
        sr = j.get("salaryRange") or {}
        if sr.get("min") or sr.get("max"):
            unit = {"per-hour-wage": "hr", "per-month-salary": "mo", "per-week-salary": "wk"}.get(sr.get("interval", ""), "yr")
            pay = N.make_pay(sr.get("min"), sr.get("max"), unit, sr.get("currency") or "USD")
        out.append({
            "id": j.get("id", ""), "title": j.get("text", ""),
            "locations": cats.get("allLocations") or [cats.get("location", "")],
            "url": j.get("hostedUrl", ""), "posted": iso_from_ts(j.get("createdAt")),
            "text": text.strip(), "pay": pay or N.pay_from_text(text),
            "model": {"remote": "Remote", "hybrid": "Hybrid", "on-site": "On Site"}.get(j.get("workplaceType", ""), ""),
        })
    return out


def _ashby(board: str) -> list[dict]:
    d = get(f"https://api.ashbyhq.com/posting-api/job-board/{board}?includeCompensation=true", as_json=True)
    out = []
    for j in (d or {}).get("jobs") or []:
        if j.get("isListed") is False:
            continue
        locs = [j.get("location", "")] + [s.get("location", "") for s in j.get("secondaryLocations") or []]
        pay = {}
        for c in ((j.get("compensation") or {}).get("summaryComponents") or []):
            if c.get("compensationType") in ("Salary", "Hourly") and (c.get("minValue") or c.get("maxValue")):
                iv = (c.get("interval") or "").upper()
                unit = "hr" if "HOUR" in iv else "mo" if "MONTH" in iv else "wk" if "WEEK" in iv else "yr"
                pay = N.make_pay(c.get("minValue"), c.get("maxValue"), unit, c.get("currencyCode") or "USD")
                break
        text = j.get("descriptionPlain") or strip_html(j.get("descriptionHtml", ""))
        model = {"Remote": "Remote", "Hybrid": "Hybrid", "OnSite": "On Site"}.get(j.get("workplaceType", ""), "")
        out.append({
            "id": j.get("id", ""), "title": j.get("title", ""), "locations": locs,
            "url": j.get("jobUrl") or j.get("applyUrl") or "", "posted": j.get("publishedAt", ""),
            "text": text, "pay": pay or N.pay_from_text(text),
            "model": model or ("Remote" if j.get("isRemote") else ""),
        })
    return out


LOADERS = {"greenhouse": _greenhouse, "lever": _lever, "ashby": _ashby}


def _cached(key: tuple, fn) -> list[dict]:
    if key not in _board_cache:
        try:
            _board_cache[key] = fn()
        except Exception as e:  # one bad board never breaks the run
            print(f"  {key[0]}/{key[1]}: {e}")
            _board_cache[key] = []
    return _board_cache[key]


def board_jobs(ats: str, board: str) -> list[dict]:
    return _cached((ats, board.lower()), lambda: LOADERS[ats](board))


# ---------- Workday: whole board via the public CXS JSON endpoint ----------
# A tenant's board at https://TENANT.wdN.myworkdayjobs.com/SITE is backed by
#   POST https://TENANT.wdN.myworkdayjobs.com/wday/cxs/TENANT/SITE/jobs
# which pages 20 at a time. We query a few early-career search terms so we pull the
# intern / new-grad slice without walking the whole (often 1000+ posting) board.
_WD_TERMS = ["intern", "co-op", "graduate", "university"]


def _wd_posted(text: str) -> str:
    t = (text or "").lower()
    if "today" in t or "just posted" in t:
        days = 0
    elif "yesterday" in t:
        days = 1
    else:
        m = re.search(r"(\d+)\+?\s*day", t)
        if m:
            days = int(m.group(1))
        else:
            m = re.search(r"(\d+)\+?\s*month", t)
            days = int(m.group(1)) * 30 if m else None
    return iso_from_ts(time.time() - days * 86400) if days is not None else ""


def _workday(tenant: str, wd: str, site: str, terms: list[str] | None = None) -> list[dict]:
    base = f"https://{tenant}.{wd}.myworkdayjobs.com"
    api = f"{base}/wday/cxs/{tenant}/{site}/jobs"
    seen: set[str] = set()
    out: list[dict] = []
    for term in (terms or _WD_TERMS):
        offset = 0
        while offset < 100:
            d = post_json(api, {"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": term})
            posts = (d or {}).get("jobPostings") or []
            if not posts:
                break
            for j in posts:
                path = j.get("externalPath") or ""
                if not path or path in seen:
                    continue
                seen.add(path)
                bullets = j.get("bulletFields") or []
                out.append({
                    "id": (bullets[0] if bullets else "") or path,
                    "title": j.get("title", ""),
                    "locations": [j.get("locationsText", "")],
                    "url": f"{base}/{site}{path}",
                    "posted": _wd_posted(j.get("postedOn", "")),
                    "text": "", "pay": {}, "model": "",
                })
            if offset + 20 >= ((d or {}).get("total") or 0):
                break
            offset += 20
    return out


# ---------- Amazon: its own public search JSON (amazon.jobs) ----------
_AMZ_TERMS = ["software development engineer intern", "software engineer intern",
              "software development engineer new grad", "software engineer new grad"]


def _amz_posted(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip())
    for fmt in ("%B %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            pass
    return ""


def _amazon(terms: list[str] | None = None, country: str = "USA") -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for q in (terms or _AMZ_TERMS):
        url = ("https://www.amazon.jobs/en/search.json?base_query=" + urllib.parse.quote(q)
               + "&result_limit=100&sort=recent&normalized_country_code[]=" + country)
        d = get(url, as_json=True)
        for j in (d or {}).get("jobs") or []:
            jid = j.get("id_icims") or j.get("id") or ""
            if not jid or jid in seen:
                continue
            seen.add(jid)
            text = strip_html(j.get("description") or j.get("basic_qualifications") or "")
            out.append({
                "id": jid, "title": j.get("title", ""),
                "locations": [j.get("normalized_location") or j.get("location", "")],
                "url": "https://www.amazon.jobs" + (j.get("job_path") or ""),
                "posted": _amz_posted(j.get("posted_date", "")),
                "text": text, "pay": N.pay_from_text(text), "model": "",
            })
    return out


# ---------- watchlist source ----------

def _board_for(b: dict):
    """Returns (jobs, label) for one watch-board config, or (None, '') to skip it."""
    ats = b.get("ats", "").lower()
    if ats == "workday":
        tenant, site = b.get("tenant", ""), b.get("site", "")
        if not tenant or not site:
            return None, ""
        wd = b.get("wd", "wd1")
        return _cached(("workday", f"{tenant}/{site}"), lambda: _workday(tenant, wd, site, b.get("terms"))), tenant
    if ats == "amazon":
        country = b.get("country", "USA")
        return _cached(("amazon", country), lambda: _amazon(b.get("terms"), country)), "amazon"
    board = b.get("board", "")
    if ats in LOADERS and board:
        return board_jobs(ats, board), board
    return None, ""


def fetch(cfg: dict, max_age_days: int, now: float) -> list[dict]:
    rx = re.compile(cfg.get("title_regex") or r"(?i)intern|new ?grad")
    out: list[dict] = []
    for b in cfg.get("boards", []):
        ats = b.get("ats", "").lower()
        jobs, label = _board_for(b)
        if jobs is None:
            continue
        keep = 0
        for j in jobs:
            if not rx.search(j["title"]):
                continue
            kind = "intern" if INTERN_RE.search(j["title"]) else "newgrad"
            company = b.get("company") or label.replace("-", " ").title()
            out.append(new_job(
                source="watch", native_id=f"{ats}:{label}:{j['id']}", kind=kind,
                title=j["title"], company=company, locations=j["locations"], url=j["url"],
                posted_at=j["posted"] or iso_from_ts(now), work_model=j["model"],
                description=j["text"], pay=j["pay"],
            ))
            keep += 1
        print(f"  watch {ats}/{label}: {keep} early-career postings")
    return out


# ---------- enrichment of a single posting URL ----------

def lookup(url: str) -> dict | None:
    """Returns {"text","pay","model"} for a Greenhouse/Lever/Ashby posting URL, else None."""
    m = re.search(r"greenhouse\.io/(?:embed/job_app\?for=)?([\w-]+)/jobs/(\d+)", url) \
        or re.search(r"greenhouse\.io/embed/job_app\?for=([\w-]+)&token=(\d+)", url)
    if m:
        board, jid = m.group(1), m.group(2)
        d = get(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{jid}?pay_transparency=true", as_json=True)
        if not d:
            return None
        text = strip_html(d.get("content", ""))
        pay = {}
        for r in d.get("pay_input_ranges") or []:
            lo, hi = (r.get("min_cents") or 0) / 100, (r.get("max_cents") or 0) / 100
            unit = "hr" if max(lo, hi) < 500 else "yr"
            pay = N.make_pay(lo, hi, unit, r.get("currency_type") or "USD")
            if pay:
                break
        return {"text": text, "pay": pay or N.pay_from_text(text), "model": ""}
    m = re.search(r"jobs\.lever\.co/([\w.-]+)/([0-9a-f-]{36})", url)
    if m:
        for j in board_jobs("lever", m.group(1)):
            if j["id"] == m.group(2):
                return j
        return None
    m = re.search(r"jobs\.ashbyhq\.com/([^/?#]+)/([0-9a-f-]{36})", url)
    if m:
        for j in board_jobs("ashby", m.group(1)):
            if j["id"] == m.group(2):
                return j
        return None
    return lookup_workday(url)


# Workday maps a public careers URL to a JSON "CXS" endpoint. A page like
#   https://TENANT.wdN.myworkdayjobs.com/[lang/]SITE/job/PATH
# is served as JSON at
#   https://TENANT.wdN.myworkdayjobs.com/wday/cxs/TENANT/SITE/job/PATH
# Some tenants return 403/404; those are skipped like any other miss.
_WD_RE = re.compile(
    r"https?://([\w-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Za-z]{2}/)?([^/]+)/job/(.+?)/?$"
)
_WD_MODEL = {"remote": "Remote", "hybrid": "Hybrid", "onsite": "On Site", "on-site": "On Site"}


def lookup_workday(url: str) -> dict | None:
    m = _WD_RE.match(url)
    if not m:
        return None
    tenant, wd, site, path = m.groups()
    api = f"https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/job/{path}"
    d = get(api, as_json=True)
    info = (d or {}).get("jobPostingInfo") or {}
    text = strip_html(info.get("jobDescription", ""))
    if not text:
        return None
    model = _WD_MODEL.get((info.get("remoteType") or "").strip().lower(), "")
    return {"text": text, "pay": N.pay_from_text(text), "model": model}
