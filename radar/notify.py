"""Ping Discord about NEW postings that match your alert rules in config.toml."""
from __future__ import annotations

import json
import os
import urllib.request

from .store import data_dir, load
from .util import UA


def matches(job: dict, rule: dict) -> bool:
    t = job["title"].lower()
    if rule.get("kind") and job["kind"] != rule["kind"]:
        return False
    if rule.get("countries") and not set(rule["countries"]) & set(job["countries"]):
        return False
    if rule.get("sources") and not set(rule["sources"]) & set(job["sources"]):
        return False
    if rule.get("categories") and job["category"] not in rule["categories"]:
        return False
    if rule.get("any_words") and not any(w.lower() in t for w in rule["any_words"]):
        return False
    if any(w.lower() in t for w in rule.get("none_words", [])):
        return False
    if rule.get("companies") and job["company"].lower() not in [c.lower() for c in rule["companies"]]:
        return False
    if rule.get("hide_citizen_only") and job["sponsorship"] == "citizen":
        return False
    if rule.get("min_hourly") and (job.get("pay") or {}).get("hourly_max", 0) < rule["min_hourly"]:
        return False
    return True


def _line(j: dict) -> str:
    pay = j.get("pay") or {}
    p = f" · ${pay['hourly_min']:.0f}–{pay['hourly_max']:.0f}/hr" if pay.get("hourly_max") else ""
    loc = j["locations"][0] if j["locations"] else ""
    more = f" +{len(j['locations'])-1}" if len(j["locations"]) > 1 else ""
    return f"• **{j['company']}** — [{j['title']}]({j['url']}) · {loc}{more}{p}"


def _post(webhook: str, content: str) -> None:
    req = urllib.request.Request(webhook, data=json.dumps({"content": content}).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": UA})
    urllib.request.urlopen(req, timeout=20).read()


def notify(cfg: dict) -> None:
    lr = data_dir() / "last_run.json"
    new_ids = set(json.loads(lr.read_text()).get("new", [])) if lr.exists() else set()
    jobs = [j for j in load()["jobs"] if j["id"] in new_ids and j["active"]]
    webhook = os.environ.get("RADAR_DISCORD_WEBHOOK", "").strip()
    for rule in cfg.get("alerts", []):
        hits = [j for j in jobs if matches(j, rule)]
        if not hits:
            continue
        print(f"  alert '{rule.get('name','')}': {len(hits)} new")
        if not webhook:
            continue
        chunk = f"🐒 **{rule.get('name','New postings')}** — {len(hits)} new\n"
        for j in hits[:40]:
            line = _line(j) + "\n"
            if len(chunk) + len(line) > 1900:
                _post(webhook, chunk)
                chunk = ""
            chunk += line
        if len(hits) > 40:
            chunk += f"…and {len(hits) - 40} more on the dashboard\n"
        if chunk:
            _post(webhook, chunk)
