# Context for Claude (Claude Code reads this automatically)

Radar Monkey: personal tool that collects early-career job postings, shows them on a filterable
dashboard with an application tracker, and has a Chrome extension that autofills applications.

- Read `docs/DEVELOPING.md` first: layout, data flow, the job record schema, where things live.
- Collector is Python 3.11+, standard library only. Keep it that way (the GitHub Action does no installs).
- Dashboard is one file, `dashboard/index.html`, plain JS, no build step. Data arrives as `window.RADAR_DATA` from `jobs.js`.
- Extension is Manifest V3, plain JS. `fill.js` is injected on click only.
- Never change `job_id()` in `radar/sources/__init__.py`; saved tracker entries depend on it.
- The extension must never submit forms, click "next"/"apply", or act without a user click.
- `packages/tight-job-tailor/` is a Claude skill by someone else; don't edit it unless asked.
- Before finishing a change: `python -m unittest discover tests`; for extension changes also `python tests/test_autofill.py`.
- Keep UI copy plain and short, sentence case.
