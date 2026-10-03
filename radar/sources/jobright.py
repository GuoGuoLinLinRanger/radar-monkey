"""Jobright's public daily lists on GitHub (README markdown tables)."""
from __future__ import annotations

import re
from datetime import datetime, timezone

from ..util import get
from . import new_job

LINK = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")


def _cell_text(c: str) -> tuple[str, str]:
    m = LINK.search(c)
    if m:
        return m.group(1).strip(" *"), m.group(2).strip()
    return re.sub(r"[*_`]", "", c).strip(), ""


def _date(s: str, now: datetime) -> str:
    s = s.strip()
    for fmt in ("%b %d", "%b %d, %Y", "%Y-%m-%d"):
        try:
            d = datetime.strptime(s, fmt)
        except ValueError:
            continue
        if fmt == "%b %d":
            d = d.replace(year=now.year)
            if d > now.replace(tzinfo=None):
                d = d.replace(year=now.year - 1)
        d = d.replace(hour=12, tzinfo=timezone.utc)
        return min(d, now).replace(microsecond=0).isoformat()
    return now.replace(microsecond=0).isoformat()


def fetch(cfg: dict, max_age_days: int, now_ts: float) -> list[dict]:
    now = datetime.fromtimestamp(now_ts, timezone.utc)
    out: list[dict] = []
    for r in cfg.get("repos", []):
        repo, kind = r["repo"], r.get("kind", "newgrad")
        text = None
        for branch in ("master", "main"):
            text = get(f"https://raw.githubusercontent.com/{repo}/{branch}/README.md")
            if text:
                break
        if not text:
            print(f"  jobright {repo}: not found")
            continue
        company = ""
        n = 0
        for line in text.splitlines():
            if not line.startswith("|") or "---" in line or "Job Title" in line:
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 5:
                continue
            co, _ = _cell_text(cells[0])
            if co and co != "↳":
                company = co
            title, link = _cell_text(cells[1])
            if not title or not link:
                continue
            native = re.search(r"/jobs/info/([0-9a-f]+)", link)
            locs = [l.strip() for l in re.split(r";|<br>|\s/\s", cells[2]) if l.strip()]
            out.append(new_job(
                source="jobright", native_id=native.group(1) if native else link, kind=kind,
                title=title, company=company, locations=locs, url=link,
                posted_at=_date(cells[4], now), work_model=cells[3],
                category=r.get("category", ""),
            ))
            n += 1
        print(f"  jobright {repo}: {n} postings")
    return out
