"""Keeps data/jobs.json across runs: remembers when we first saw each job,
folds duplicates from different sites into one row, and marks closed postings."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from . import normalize as N
from .sources import boards
from .util import now_iso, parse_iso

SOURCE_RANK = {"watch": 0, "simplify": 1, "jobright": 2}  # whose apply link wins


def data_dir() -> Path:
    d = Path(os.environ.get("RADAR_DATA_DIR", "data"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def load() -> dict:
    p = data_dir() / "jobs.json"
    if p.exists():
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            pass
    return {"generated": "", "jobs": []}


def _merge_into(a: dict, b: dict) -> None:
    """Fold job b into job a (same id)."""
    if SOURCE_RANK.get(b["sources"][0], 9) < SOURCE_RANK.get(a["sources"][0], 9):
        # b has the better apply link: swap the primary url
        if a["url"] and a["url"] not in a["alt_urls"]:
            a["alt_urls"].append(a["url"])
        a["url"], a["ats"] = b["url"], b["ats"]
    elif b["url"] and b["url"] != a["url"] and b["url"] not in a["alt_urls"]:
        a["alt_urls"].append(b["url"])
    for s in b["sources"]:
        if s not in a["sources"]:
            a["sources"].append(s)
    for s in b["source_ids"]:
        if s not in a["source_ids"]:
            a["source_ids"].append(s)
    for loc in b["locations"]:
        if loc not in a["locations"]:
            a["locations"].append(loc)
    a["countries"] = N.countries_of(a["locations"])
    for t in b["terms"]:
        if t not in a["terms"]:
            a["terms"].append(t)
    for k in ("work_model", "description", "qualifications", "pay", "degrees"):
        if not a.get(k) and b.get(k):
            a[k] = b[k]
    if a["sponsorship"] == "unknown":
        a["sponsorship"] = b["sponsorship"]
    a["remote_ok"] = a["remote_ok"] or b["remote_ok"]
    a["active"] = a["active"] or b["active"]
    if b["posted_at"] > a["posted_at"]:
        a["posted_at"] = b["posted_at"]


def merge(fresh: list[dict], cfg: dict) -> tuple[dict, list[str]]:
    old = {j["id"]: j for j in load()["jobs"]}
    now = now_iso()
    now_ts = time.time()

    # 1. fold this run's duplicates
    run: dict[str, dict] = {}
    for j in fresh:
        if j["id"] in run:
            _merge_into(run[j["id"]], j)
        else:
            run[j["id"]] = j

    # 2. carry history forward
    new_ids = []
    for jid in [k for k, j in run.items() if not j["active"] and k not in old]:
        del run[jid]  # closed before we ever saw it: not interesting
    for jid, j in run.items():
        prev = old.get(jid)
        if prev:
            j["first_seen"] = prev.get("first_seen") or now
            for k in ("description", "qualifications", "pay", "enriched"):
                if not j.get(k) and prev.get(k):
                    j[k] = prev[k]
            if prev.get("active") and not j["active"]:
                j["closed_at"] = now
            elif not j["active"]:
                j["closed_at"] = prev.get("closed_at") or now
        else:
            j["first_seen"] = now
            new_ids.append(jid)
        j["last_seen"] = now

    # 3. keep jobs we didn't see this run (Jobright only lists 7 days; that's not "closed")
    keep_cfg = cfg.get("keep", {})
    max_age = keep_cfg.get("max_age_days", 60) * 86400
    grace = keep_cfg.get("closed_grace_days", 14) * 86400
    for jid, j in old.items():
        if jid not in run:
            run[jid] = j
    jobs = []
    for j in run.values():
        if now_ts - parse_iso(j.get("posted_at") or j.get("first_seen", "")) > max_age:
            continue
        if not j["active"] and now_ts - parse_iso(j.get("closed_at", now)) > grace:
            continue
        jobs.append(j)

    # 4. enrichment: pay + full text from public ATS APIs
    en = cfg.get("enrich", {})
    if en.get("enabled", True):
        todo = [j for j in jobs if j["active"] and not j.get("enriched") and j["ats"] in ("Greenhouse", "Lever", "Ashby", "Workday")]
        todo.sort(key=lambda j: j["posted_at"], reverse=True)
        done = 0
        for j in todo[: en.get("max_per_run", 250)]:
            try:
                info = boards.lookup(j["url"])
            except Exception:
                info = None
            j["enriched"] = now
            if not info:
                continue
            text = info.get("text") or ""
            j["description"] = j.get("description") or text[:8000]
            j["qualifications"] = j.get("qualifications") or N.qualifications_from(text)
            j["pay"] = j.get("pay") or info.get("pay") or {}
            if j["sponsorship"] == "unknown":
                j["sponsorship"] = N.sponsorship_of("", text)
            if not j["work_model"] and info.get("model"):
                j["work_model"] = info["model"]
            done += 1
            time.sleep(0.15)
        print(f"  enriched {done} postings with pay/description")

    jobs.sort(key=lambda j: j["posted_at"], reverse=True)
    return {"generated": now, "jobs": jobs}, new_ids


def save(db: dict, new_ids: list[str]) -> None:
    d = data_dir()
    (d / "jobs.json").write_text(json.dumps(db, separators=(",", ":")))
    (d / "last_run.json").write_text(json.dumps({"at": db["generated"], "new": new_ids}))
