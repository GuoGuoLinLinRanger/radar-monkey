"""python -m radar [update|build|notify|serve|all]"""
from __future__ import annotations

import argparse
import functools
import http.server
import time
import tomllib
from pathlib import Path

from . import build as B
from . import notify as NT
from . import store
from .sources import boards, jobright, simplify

ROOT = Path(__file__).resolve().parent.parent


def load_cfg(path: str) -> dict:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    return tomllib.loads(p.read_text()) if p.exists() else {}


def update(cfg: dict) -> None:
    now = time.time()
    age = cfg.get("keep", {}).get("max_age_days", 60)
    src = cfg.get("sources", {})
    fresh: list[dict] = []
    if src.get("simplify", {}).get("enabled", True):
        fresh += simplify.fetch(src.get("simplify", {}), age, now)
    if src.get("jobright", {}).get("enabled", True):
        fresh += jobright.fetch(src.get("jobright", {}), age, now)
    if cfg.get("watch", {}).get("boards"):
        fresh += boards.fetch(cfg["watch"], age, now)
    if not fresh:
        raise SystemExit("No postings fetched from any source; keeping old data.")
    db, new_ids = store.merge(fresh, cfg)
    store.save(db, new_ids)
    active = sum(j["active"] for j in db["jobs"])
    print(f"  total {len(db['jobs'])} jobs ({active} open), {len(new_ids)} new this run")


def main() -> None:
    ap = argparse.ArgumentParser(prog="radar")
    ap.add_argument("cmd", choices=["update", "build", "notify", "serve", "all"])
    ap.add_argument("--config", default="config.toml")
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    cfg = load_cfg(a.config)
    if a.cmd in ("update", "all"):
        print("Updating…"); update(cfg)
    if a.cmd in ("notify", "all"):
        print("Alerts…"); NT.notify(cfg)
    if a.cmd in ("build", "all", "serve"):
        print("Building…"); B.build()
    if a.cmd == "serve":
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT / "site"))
        print(f"Open http://localhost:{a.port}  (Ctrl+C to stop)")
        http.server.ThreadingHTTPServer(("127.0.0.1", a.port), h).serve_forever()


if __name__ == "__main__":
    main()
