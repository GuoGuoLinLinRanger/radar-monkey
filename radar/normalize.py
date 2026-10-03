"""Turn messy source fields into the clean fields the dashboard filters on."""
from __future__ import annotations

import re

US_STATES = set(
    "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM "
    "NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC PR".split()
)
CA_PROV = set("AB BC MB NB NL NS NT NU ON PE QC SK YT".split())  # no "CA": that's California
CA_WORDS = (
    "canada", "toronto", "vancouver", "montreal", "montréal", "waterloo", "ottawa", "calgary",
    "edmonton", "kitchener", "mississauga", "markham", "quebec", "québec", "winnipeg", "halifax",
    "burnaby", "richmond hill", "oakville", "guelph", "hamilton, on", "london, on",
)
US_WORDS = ("united states", "usa", "u.s.", " us", "us-", "nationwide", "san francisco", "new york",
            "seattle", "bay area", "silicon valley", "boston", "chicago", "austin")
US_ABBR = {"SF", "NYC", "LA", "SOUTH SF", "DC", "SV", "PHL", "ATL", "CHI"}


def countries_of(locations: list[str]) -> list[str]:
    found: set[str] = set()
    for loc in locations:
        low = " " + loc.lower()
        if any(w in low for w in CA_WORDS):
            found.add("CA")
            continue
        toks = {t.strip().upper() for t in re.split(r"[,/|;()\-]", loc)}
        if toks & CA_PROV:
            found.add("CA")
        elif toks & (US_STATES | US_ABBR) or any(w in low for w in US_WORDS):
            found.add("US")
        elif "remote" in low and len(low.strip()) < 20:
            found.add("US")  # these lists are US-first; bare "Remote" is almost always US
        elif loc.strip():
            found.add("Other")
    return sorted(found) or ["Other"]


def work_model_of(given: str, locations: list[str]) -> tuple[str, bool]:
    """Returns (model, remote_ok)."""
    g = (given or "").strip().lower()
    locs = " ".join(locations).lower()
    remote_ok = "remote" in g or "remote" in locs
    if "hybrid" in g or "hybrid" in locs:
        return "Hybrid", remote_ok
    if "remote" in g:
        return "Remote", True
    if g in ("on site", "onsite", "on-site", "in office", "in-office"):
        return "On Site", remote_ok
    if locations and all("remote" in l.lower() for l in locations):
        return "Remote", True
    return "", remote_ok


ATS_PATTERNS = [
    ("Greenhouse", r"greenhouse\.io|gh_jid="),
    ("Lever", r"lever\.co"),
    ("Ashby", r"ashbyhq\.com"),
    ("Workday", r"myworkdayjobs\.com|workday\.com"),
    ("iCIMS", r"icims\.com"),
    ("SmartRecruiters", r"smartrecruiters\.com"),
    ("SuccessFactors", r"successfactors|sapsf"),
    ("Taleo", r"taleo\.net"),
    ("Oracle", r"oraclecloud\.com"),
    ("Jobvite", r"jobvite\.com"),
    ("Workable", r"workable\.com"),
    ("BambooHR", r"bamboohr\.com"),
    ("Eightfold", r"eightfold\.ai"),
    ("Rippling", r"rippling\.com"),
    ("Jobright", r"jobright\.ai"),
]


def ats_of(url: str) -> str:
    for name, pat in ATS_PATTERNS:
        if re.search(pat, url or "", re.I):
            return name
    return "Other"


SENIOR = re.compile(r"(?i)\b(senior|sr\.?|staff|principal|lead|manager|director|head of|architect)\b|\b(ii|iii|iv|2|3)\s*$")
TERM = re.compile(r"(?i)\b(summer|fall|autumn|winter|spring)\s*[-'’]?\s*(20\d\d)\b")


def title_flags(title: str) -> list[str]:
    t = title or ""
    flags = []
    if SENIOR.search(t):
        flags.append("senior")
    if re.search(r"(?i)\bph\.?d\b|doctoral", t):
        flags.append("phd")
    if re.search(r"(?i)\bmaster'?s?\b|\bms\b|\bm\.s\.", t):
        flags.append("masters")
    if re.search(r"(?i)co-?op", t):
        flags.append("coop")
    return flags


def terms_from_title(title: str) -> list[str]:
    out = []
    for season, year in TERM.findall(title or ""):
        s = season.capitalize().replace("Autumn", "Fall")
        out.append(f"{s} {year}")
    return out


CATEGORY_MAP = {
    "software engineering": "Software",
    "data science, ai & machine learning": "AI/ML/Data",
    "hardware engineering": "Hardware",
    "product management": "Product",
    "quantitative finance": "Quant",
}


def category_of(c: str, title: str = "") -> str:
    c = (c or "").strip()
    c = CATEGORY_MAP.get(c.lower(), c)
    if c:
        return c
    t = (title or "").lower()
    if re.search(r"data|machine learning|\bml\b|\bai\b|analyt", t):
        return "AI/ML/Data"
    if re.search(r"quant|trad", t):
        return "Quant"
    if re.search(r"hardware|fpga|asic|embedded|firmware|electrical", t):
        return "Hardware"
    if re.search(r"product manag|\bpm\b", t):
        return "Product"
    return "Software"


def sponsorship_of(raw: str = "", text: str = "") -> str:
    """yes | no | citizen | unknown"""
    r = (raw or "").lower()
    if "citizenship" in r or "clearance" in r:
        return "citizen"
    if "does not" in r or "no sponsor" in r:
        return "no"
    if "offers" in r:
        return "yes"
    t = (text or "").lower()
    if re.search(r"u\.?s\.? citizen(ship)? (is )?required|must be a u\.?s\.? citizen|security clearance|itar", t):
        return "citizen"
    if re.search(r"(not|unable to|will not|won't|cannot) (provide |offer )?(visa )?sponsor", t):
        return "no"
    if re.search(r"visa sponsorship (is )?available|will sponsor|we sponsor", t):
        return "yes"
    return "unknown"


# ---------- pay ----------

HOURS_PER_YEAR = 2080
_PAY_RE = re.compile(
    r"(?P<cur>CA\$|C\$|US\$|\$|USD|CAD)\s?(?P<a>\d[\d,]*(?:\.\d+)?)\s?(?P<ak>[kK])?"
    r"(?:\s*(?:-|–|—|to)\s*(?:CA\$|C\$|US\$|\$|USD|CAD)?\s?(?P<b>\d[\d,]*(?:\.\d+)?)\s?(?P<bk>[kK])?)?"
    r"(?P<tail>[^\n]{0,40})"
)


def make_pay(lo: float, hi: float, unit: str, currency: str = "USD") -> dict:
    """unit: hr | yr | mo | wk. Returns pay dict with hourly + annual ranges."""
    if not lo and not hi:
        return {}
    lo, hi = float(lo or hi), float(hi or lo)
    if hi < lo:
        lo, hi = hi, lo
    to_hr = {"hr": 1, "yr": 1 / HOURS_PER_YEAR, "mo": 12 / HOURS_PER_YEAR, "wk": 1 / 40}[unit]
    hmin, hmax = lo * to_hr, hi * to_hr
    if hmax < 7 or hmax > 600:  # junk
        return {}
    return {
        "currency": currency, "unit": unit,
        "hourly_min": round(hmin, 2), "hourly_max": round(hmax, 2),
        "annual_min": round(hmin * HOURS_PER_YEAR), "annual_max": round(hmax * HOURS_PER_YEAR),
    }


def pay_from_text(text: str) -> dict:
    if not text:
        return {}
    best: dict = {}
    for m in _PAY_RE.finditer(text):
        a = float(m["a"].replace(",", "")) * (1000 if m["ak"] else 1)
        b = float(m["b"].replace(",", "")) * (1000 if m["bk"] else 1) if m["b"] else a
        tail = (m["tail"] or "").lower()
        if re.match(r"\s?(m|mm|b|bn|million|billion)\b", tail):
            continue
        ctx = text[max(0, m.start() - 80): m.start()].lower()
        cur = "CAD" if "ca" in m["cur"].lower() or "c$" in m["cur"].lower() or "cad" in tail else "USD"
        if re.search(r"hour|/hr|\bhr\b|hourly", tail + ctx):
            unit = "hr"
        elif re.search(r"month|/mo\b", tail):
            unit = "mo"
        elif re.search(r"week|/wk", tail):
            unit = "wk"
        elif max(a, b) >= 20000:
            unit = "yr"
        elif max(a, b) <= 250:
            unit = "hr"
        else:
            continue
        if not re.search(r"pay|salary|compensation|wage|rate|range|base|hour|annual|per year", ctx + tail):
            continue
        p = make_pay(a, b, unit, cur)
        if p and (not best or p["annual_max"] > best["annual_max"]):
            best = p
    return best


QUAL_HEAD = re.compile(
    r"(?im)^\s*(?:#+\s*)?(?:minimum |basic |preferred |required )?(qualifications|requirements|"
    r"what you(?:'|’)ll need|what we(?:'|’)re looking for|who you are|you (?:have|bring|might be)|"
    r"about you|skills)\b.*$"
)


def qualifications_from(text: str, limit: int = 1400) -> str:
    if not text:
        return ""
    m = QUAL_HEAD.search(text)
    if not m:
        return ""
    chunk = text[m.end(): m.end() + limit * 2]
    stop = re.search(r"(?im)^\s*(?:#+\s*)?(benefits|perks|about (us|the company)|compensation|pay|salary|"
                     r"equal opportunity|eeo|what we offer|why join)\b", chunk)
    if stop:
        chunk = chunk[: stop.start()]
    return chunk.strip()[:limit]
