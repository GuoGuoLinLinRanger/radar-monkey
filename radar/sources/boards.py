"""Company job boards via the official public APIs of Greenhouse, Lever and Ashby.

Used two ways:
  * fetch()  - the watchlist: poll a company's whole board, keep early-career titles.
  * lookup() - enrichment: given one posting URL, get pay + full text.
"""
from __future__ import annotations

import re

from .. import normalize as N
from ..util import get, iso_from_ts, strip_html
from . import new_job

INTERN_RE = re.compile(r"(?i)intern|co-?op|placement|apprentice")

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


def board_jobs(ats: str, board: str) -> list[dict]:
    key = (ats, board.lower())
    if key not in _board_cache:
        try:
            _board_cache[key] = LOADERS[ats](board)
        except Exception as e:  # one bad board never breaks the run
            print(f"  {ats}/{board}: {e}")
            _board_cache[key] = []
    return _board_cache[key]


# ---------- watchlist source ----------

def fetch(cfg: dict, max_age_days: int, now: float) -> list[dict]:
    rx = re.compile(cfg.get("title_regex") or r"(?i)intern|new ?grad")
    out: list[dict] = []
    for b in cfg.get("boards", []):
        ats, board = b.get("ats", "").lower(), b.get("board", "")
        if ats not in LOADERS or not board:
            continue
        keep = 0
        for j in board_jobs(ats, board):
            if not rx.search(j["title"]):
                continue
            kind = "intern" if INTERN_RE.search(j["title"]) else "newgrad"
            company = b.get("company") or board.replace("-", " ").title()
            out.append(new_job(
                source="watch", native_id=f"{ats}:{board}:{j['id']}", kind=kind,
                title=j["title"], company=company, locations=j["locations"], url=j["url"],
                posted_at=j["posted"] or iso_from_ts(now), work_model=j["model"],
                description=j["text"], pay=j["pay"],
            ))
            keep += 1
        print(f"  watch {ats}/{board}: {keep} early-career postings")
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
