"""Fills tests/fixtures/application_form.html with the real extension code in headless Chrome.

Needs:  pip install playwright && playwright install chromium
Run:    python tests/test_autofill.py
Add a field to the fixture whenever you hit a form the extension gets wrong.
"""
import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
PROFILE = {
    "first_name": "Yi", "last_name": "Chen", "email": "yi@example.com", "phone": "5195551234",
    "linkedin": "https://linkedin.com/in/yi", "school": "University of Waterloo", "degree": "Bachelor's",
    "grad_year": "2028", "grad_month": "April", "work_auth_us": "No", "need_sponsor_us": "Yes",
    "how_heard": "LinkedIn", "gender": "I don't wish to answer",
}
EXPECT = {
    "fn": "Yi", "ln": "Chen", "pf": "Yi", "em": "yi@example.com", "sch": "University of Waterloo",
    "deg": "Bachelor's Degree", "gy": "2028", "why": "Because I like rockets.",
    "gender": "Decline To Self Identify", "hb": "LinkedIn",
}


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        await pg.goto((ROOT / "tests/fixtures/application_form.html").as_uri())
        await pg.add_script_tag(path=str(ROOT / "extension/fields.js"))
        await pg.add_script_tag(path=str(ROOT / "extension/fill.js"))
        report = await pg.evaluate("d => window.__rmRun(d)", {
            "profile": PROFILE,
            "answers": [{"q": "why do you want to work", "a": "Because I like rockets."}],
            "resume": {"name": "r.pdf", "type": "application/pdf", "dataUrl": "data:application/pdf;base64,JVBERi0xLjQK"},
        })
        got = await pg.evaluate("""() => ({fn:fn.value, ln:ln.value, pf:pf.value, em:em.value, sch:sch.value, deg:deg.value,
            gy:gy.value, why:why.value, gender:gender.value, hb:hb.textContent.trim(), res:res.files.length,
            auth:[...document.getElementsByName('auth')].find(x=>x.checked)?.parentElement.textContent.trim(),
            sp:[...document.getElementsByName('sp')].find(x=>x.checked)?.parentElement.textContent.trim()})""")
        await b.close()
    bad = {k: (v, got.get(k)) for k, v in EXPECT.items() if got.get(k) != v}
    for k, v in {"auth": "No", "sp": "Yes", "res": 1}.items():
        if got.get(k) != v:
            bad[k] = (v, got.get(k))
    print(json.dumps(report))
    if bad:
        raise SystemExit(f"FAILED (expected, got): {bad}")
    print("autofill OK")


asyncio.run(main())
