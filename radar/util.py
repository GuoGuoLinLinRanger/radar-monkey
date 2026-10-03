"""Small shared helpers. Standard library only, so the Action needs no installs."""
from __future__ import annotations

import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

UA = "RadarMonkey/2.0 (personal job tracker; +https://github.com)"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def iso_from_ts(ts: float | int | None) -> str:
    if not ts:
        return ""
    if ts > 1e12:  # milliseconds
        ts = ts / 1000
    return datetime.fromtimestamp(ts, timezone.utc).replace(microsecond=0).isoformat()


def parse_iso(s: str) -> float:
    if not s:
        return 0.0
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def get(url: str, *, as_json: bool = False, timeout: int = 30, retries: int = 2):
    """GET a URL. Returns text/JSON, or None on failure (never raises)."""
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8", "replace")
            return json.loads(body) if as_json else body
        except urllib.error.HTTPError as e:
            if e.code in (404, 410, 403):
                return None
        except Exception:
            pass
        time.sleep(1.5 * (attempt + 1))
    return None


def slug(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"\(.*?\)|\[.*?\]", " ", s)
    return re.sub(r"[^a-z0-9]+", "", s)


def short_hash(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:12]


def strip_html(s: str) -> str:
    if not s:
        return ""
    s = html.unescape(s)  # Greenhouse double-escapes
    s = re.sub(r"(?i)<br\s*/?>|</p>|</li>|</h\d>|</div>", "\n", s)
    s = re.sub(r"(?i)<li[^>]*>", "• ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t\xa0]+", " ", s)
    s = re.sub(r"\n\s*\n\s*\n+", "\n\n", s)
    return s.strip()


def clean_url(u: str) -> str:
    """Drop tracking params so the same job matches across sources."""
    if not u:
        return ""
    u = u.strip()
    u = re.sub(r"[?&]utm_[^&#]*", "", u)
    u = re.sub(r"[?&](ref|source|src|gh_src|lever-source)=[^&#]*", "", u)
    u = re.sub(r"\?&", "?", u).rstrip("?&")
    return u
