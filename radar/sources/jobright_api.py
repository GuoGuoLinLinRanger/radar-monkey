"""Jobright's minisite API, the backend behind intern-list.com and newgrad-jobs.com.

    POST https://jobright.ai/swan/mini-sites/list?position=N&count=M
    body: {"category": "intern:us:swe"}

No auth, no cookies. This returns a whole category in one request with structured
pay, work model, visa flag, industry and company size, so it is richer than the
GitHub README mirror in `jobright.py`. Category ids are listed in
`docs/jobright_categories.json`. Opt-in via `[sources.jobright_api]` in config.toml.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import urllib.request
from zoneinfo import ZoneInfo

from .. import normalize as N
from ..util import UA
from . import new_job

LIST_URL = "https://jobright.ai/swan/mini-sites/list?position={pos}&count={count}"
JOB_PAGE = "https://jobright.ai/jobs/info/{job_id}"
LA = ZoneInfo("America/Los_Angeles")

# Jobright salary strings: "$21.37-$28.84/hr", "CAD60-CAD65/hr", "$85000-$120000/yr"
SALARY_RE = re.compile(
    r"^(?P<cur>[A-Z€$£ ]*?)\s*(?P<lo>[\d.,]+)\s*-\s*(?P<cur2>[A-Z€$£ ]*?)\s*(?P<hi>[\d.,]+)\s*/(?P<unit>hr|yr|mon|wk|day)$")
CURRENCY = {"$": "USD", "US$": "USD", "US": "USD", "USD": "USD", "CAD": "CAD", "C$": "CAD"}
UNIT = {"hr": "hr", "yr": "yr", "mon": "mo", "wk": "wk"}  # "day" is unsupported by make_pay
# Jobright category id -> dashboard category label
CATEGORY_LABEL = {"swe": "Software", "data": "AI/ML/Data", "hardware": "Hardware",
                  "product": "Product", "quant": "Quant"}


def _post(url: str, body: dict) -> dict | None:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), method="POST",
        headers={"Content-Type": "application/json", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.load(r)
    except Exception:
        return None


def _fetch_category(category: str, page: int = 1000) -> list[dict]:
    rows: list[dict] = []
    pos = 0
    while True:
        res = _post(LIST_URL.format(pos=pos, count=page), {"category": category})
        if not res or not res.get("success"):
            break
        batch = res["result"]["jobList"]
        rows.extend(batch)
        pos += len(batch)
        if not batch or pos >= res["result"]["total"]:
            break
    return rows


def _fix_posted_at(ms: float) -> str:
    """Jobright serialises a Los Angeles wall clock as if it were UTC (7-8 h early).
    Reinterpret the naive value as LA time and convert back to UTC."""
    naive = dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).replace(tzinfo=None)
    return naive.replace(tzinfo=LA).astimezone(dt.timezone.utc).replace(microsecond=0).isoformat()


def _pay(salary: str | None) -> dict:
    if not salary or salary in ("N/A", "Unpaid"):
        return {}
    m = SALARY_RE.match(salary.strip())
    if not m:
        return {}
    unit = UNIT.get(m["unit"])
    if not unit:
        return {}
    lo, hi = float(m["lo"].replace(",", "")), float(m["hi"].replace(",", ""))
    cur = CURRENCY.get((m["cur"] or m["cur2"]).strip(), "USD")
    return N.make_pay(lo, hi, unit, cur)


def _sponsorship_raw(h1b: str | None) -> str:
    h = (h1b or "").strip().lower()
    if h == "yes":
        return "offers sponsorship"
    if h == "no":
        return "does not sponsor"
    return ""


def fetch(cfg: dict, max_age_days: int, now: float) -> list[dict]:
    countries = [c.lower() for c in cfg.get("countries", ["us", "ca"])]
    kinds = cfg.get("kinds", ["intern", "newgrad"])
    categories = cfg.get("categories", ["swe"])
    out: list[dict] = []
    seen: set[str] = set()
    for kind in kinds:
        for country in countries:
            for cat in categories:
                key = f"{kind}:{country}:{cat}"
                rows = _fetch_category(key)
                print(f"  jobright_api {key}: {len(rows)} rows")
                for row in rows:
                    jid = row.get("jobId")
                    if not jid or jid in seen:
                        continue
                    seen.add(jid)
                    p = row.get("properties") or {}
                    locs = [l.strip() for l in (p.get("location") or "").split(";") if l.strip()]
                    out.append(new_job(
                        source="jobright", native_id=jid, kind=kind,
                        title=p.get("title") or "", company=p.get("company") or "",
                        locations=locs, url=JOB_PAGE.format(job_id=jid),
                        posted_at=_fix_posted_at(row["postedAt"]) if row.get("postedAt") else "",
                        work_model=p.get("workModel") or "",
                        category=CATEGORY_LABEL.get(cat, ""),
                        sponsorship_raw=_sponsorship_raw(p.get("h1bSponsored")),
                        terms=[x for x in [p.get("hireTime") or "", p.get("graduateTime") or ""] if x],
                        pay=_pay(p.get("salary")),
                        description=(p.get("qualifications") or "")[:600],
                    ))
    return out
