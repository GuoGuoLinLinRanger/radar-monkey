"""Builds the static site: site/index.html + site/jobs.js (works from file:// too)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from .store import load

ROOT = Path(__file__).resolve().parent.parent
SLIM_DESC = 2500  # characters of posting text shipped to the browser


def build(out: str = "site") -> Path:
    db = load()
    out_dir = ROOT / out if not Path(out).is_absolute() else Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = []
    for j in db["jobs"]:
        j = dict(j)
        j.pop("source_ids", None)
        j.pop("enriched", None)
        if j.get("description"):
            j["description"] = j["description"][:SLIM_DESC]
        jobs.append(j)
    payload = json.dumps({"generated": db.get("generated", ""), "jobs": jobs}, separators=(",", ":"))
    (out_dir / "jobs.js").write_text("window.RADAR_DATA=" + payload + ";\n", encoding="utf-8")
    html = (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
    stamp = (db.get("generated") or "0").replace(":", "").replace("+", "")
    html = html.replace('src="jobs.js"', f'src="jobs.js?v={stamp}"')
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")
    print(f"  built {out_dir}/index.html with {len(jobs)} jobs ({len(payload)//1024} KB)")
    return out_dir
