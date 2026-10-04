# Working on Radar Monkey

## What you need installed

| Tool | Why | Check |
| --- | --- | --- |
| Python 3.11 or newer | Runs the collector. Uses only the standard library, so no `pip install` for the app itself. | `python --version` |
| Git + a GitHub account | Hosting, the auto-update Action, and GitHub Pages. | `git --version` |
| Google Chrome (or Edge, Brave, Arc) | Running the extension. | |
| A code editor | VS Code works well. | |
| Optional: Playwright | Only for `tests/test_autofill.py`. `pip install playwright && playwright install chromium` | |
| Optional: Discord webhook | New-job pings. | |

No API keys are needed. Every source is a public feed or public API.

## Daily loop

```bash
python -m radar update     # fetch postings into data/jobs.json (about 30 s)
python -m radar serve      # build + open http://localhost:8765
```

After the first `update`, run `python -m radar build` whenever you edit `dashboard/index.html`
and refresh the page. You don't need to re-fetch.

Extension: edit files in `extension/`, then click the reload icon on its card at `chrome://extensions`
and refresh the job page. Errors show up under the card's "Errors" button and in the page console.

Tests:

```bash
python -m unittest discover tests     # collector logic, instant
python tests/test_autofill.py         # extension fill engine in headless Chrome
```

## How the pieces connect

```
 config.toml
     │
 radar/sources/*.py ──► new_job() records ──► radar/store.py ──► data/jobs.json
  simplify, jobright,      (one shape for       merge, dedupe,        │
  boards (watchlist)        every source)       first_seen, closed,   │
                                                pay enrichment        │
                                                                      ▼
                                     radar/build.py ──► site/index.html + site/jobs.js
                                                                      │
                          ┌───────────────────────────────────────────┘
                          ▼
                 dashboard (browser)  ◄── postMessage ──►  extension/bridge.js
                 tracker in localStorage                    apps in chrome.storage
                                                                  ▲
                                         popup.js ── background.js ── fill.js + fields.js
                                                                  (injected on click)
```

On GitHub, `.github/workflows/update.yml` runs the same commands every 3 hours. Job history is kept on
a separate `data` branch (one commit, force-pushed) so first-seen times survive between runs.

## The job record

Every source returns this shape via `new_job()` in `radar/sources/__init__.py`:

| Field | Example | Notes |
| --- | --- | --- |
| `id` | `a1b2c3d4e5f6` | Hash of company + title + kind. **The tracker keys on this; don't change the formula.** |
| `kind` | `intern` / `newgrad` | Which tab it shows on. |
| `title`, `company` | | |
| `locations`, `countries` | `["Toronto, ON"]`, `["CA"]` | Countries: `US`, `CA`, `Other`. |
| `work_model`, `remote_ok` | `Hybrid`, `true` | Empty string when unknown. |
| `url`, `alt_urls`, `ats` | | `ats` is detected from the URL (Workday, Greenhouse…). |
| `posted_at`, `first_seen`, `last_seen` | ISO times | |
| `terms`, `category`, `degrees` | `["Summer 2027"]`, `Software` | |
| `sponsorship` | `yes` / `no` / `citizen` / `unknown` | |
| `flags` | `["senior", "coop"]` | From the title. |
| `pay` | `{hourly_min, hourly_max, annual_min, annual_max, currency, unit}` | Empty `{}` when unknown. |
| `description`, `qualifications` | text | Only for enriched or watchlist postings. |
| `active`, `closed_at` | | |
| `sources` | `["simplify", "jobright"]` | |

## Where to change common things

| I want to… | Edit |
| --- | --- |
| Add a job source | New file in `radar/sources/` with `fetch(cfg, max_age_days, now) -> list[new_job(...)]`, then call it in `radar/__main__.py` `update()`. |
| Add a dashboard filter | `DEFAULT_F` (default value), the filters HTML, `filtered()`, and `activeFilterCount()` in `dashboard/index.html`. |
| Add a tracker status | `STATUSES` and a `--s-<name>` color in `dashboard/index.html`. |
| Teach autofill a new question | Add a row to `PROFILE` and a rule to `RULES` in `extension/fields.js`. Rules are checked top to bottom; put specific patterns above general ones. |
| Fix autofill on one site | Add the broken field to `tests/fixtures/application_form.html`, make `test_autofill.py` fail, then fix `fill.js`. |
| Change how often it updates | `cron` in `.github/workflows/update.yml`. |
| Change alerts | `[[alerts]]` in `config.toml`; matching logic in `radar/notify.py`. |

## Gotchas

- The dashboard loads data with `<script src="jobs.js">`, not `fetch`, so it works when opened as a file.
- Tracker data lives only in the browser. Use **Back up** before clearing site data or switching browsers.
- `fill.js` can be injected many times into one page; it guards with `if (window.__rmRun) return`.
  After editing it, reload the job page so the old copy is gone.
- Greenhouse application forms often sit in an iframe from another domain. That only works because those
  domains are in `host_permissions` in `manifest.json`. Add new ATS domains there.
- GitHub turns off scheduled Actions in repos with no activity for 60 days. Any push turns them back on.
