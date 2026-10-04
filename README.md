# Radar Monkey 🐒

Finds early-career job postings, lets you filter them a lot of ways, tracks your applications,
and fills application forms for you. It refreshes itself every 3 hours on GitHub, for free.

```
radar/        Python that collects postings (no installs needed, Python 3.11+)
dashboard/    The web page: filters, starring, application tracker
extension/    Chrome extension: autofill + "I applied" logging
packages/     The resume-tailoring Claude skill, packaged on its own
config.toml   Sources, company watchlist, Discord alerts
```

## Where the jobs come from

| Source | What it adds |
| --- | --- |
| SimplifyJobs lists on GitHub | Most postings. Direct apply links, term, degree, sponsorship notes. |
| Jobright lists on GitHub | Work model (on site / hybrid / remote). |
| Your watchlist | Companies you name in `config.toml`. Polled straight from their Greenhouse, Lever or Ashby board, so you see a posting the hour it goes up. |
| Greenhouse, Lever, Ashby public APIs | Pay range and full posting text for postings on those sites. |

All of these are public feeds or official public APIs. Nothing logs in or scrapes behind a login.

## Set it up (about 10 minutes)

1. **Make the repo.** Create an empty repo on GitHub, then from this folder:
   ```bash
   git remote add origin https://github.com/YOU/radar-monkey.git
   git push -u origin main
   ```
2. **Turn on the website.** Repo → Settings → Pages → Source: **GitHub Actions**.
3. **Run it once.** Repo → Actions → *Update jobs* → **Run workflow**. After a few minutes your dashboard is at
   `https://YOU.github.io/radar-monkey/`. From then on it updates every 3 hours on its own.
4. **(Optional) Discord pings.** In Discord: channel settings → Integrations → Webhooks → copy URL.
   In GitHub: Settings → Secrets and variables → Actions → New secret named `RADAR_DISCORD_WEBHOOK`.
   Edit the `[[alerts]]` in `config.toml` to choose what pings you.

Private repo? Pages on private repos needs GitHub Pro, which is free with the GitHub Student Pack.
Your tracker data never goes to GitHub either way; it stays in your browser.

### Run it on your own computer instead

```bash
python -m radar all      # fetch, alert, build
python -m radar serve    # open http://localhost:8765
```

## The dashboard

- **Filters:** search with `-word` to exclude, country, work model, posted within, term, field,
  application site (Workday, Greenhouse…), visa/citizenship, hide senior/PhD/master's/co-op titles,
  minimum pay, only new since you last looked, blocked companies, and a **fit score** from your skills
  (set them in Settings).
- **Saved filters:** set things up once, save, switch in one click.
- **Tracker:** star postings, mark "I applied", then move them through OA → interview → offer.
  It sets a follow-up date 2 weeks out, nudges you when it's due, flags applications with no reply after
  30 days, and tells you if a starred posting closed. Back up or export to CSV any time.
- **Copy for resume tailoring:** copies the posting in a format the tailoring skill reads.

## The Chrome extension

1. Chrome → `chrome://extensions` → turn on **Developer mode** → **Load unpacked** → pick the `extension` folder.
2. Its settings page opens. Fill in your profile, upload your resume, add answers to questions you see a lot.
3. On an application page, click the extension → **Fill this page** (or press **Alt+Shift+F**).
   Green outline = filled. Dashed = needs you.
4. After you submit, click **I applied**. It shows up in your dashboard tracker next time it's open.
5. Typed a good answer to an odd question? **Remember my answers on this page** saves it for next time.

Workday forms are multi-page: press Alt+Shift+F on each page.

**About terms of service:** the extension only acts when you click, fills fields the way you would,
and never submits, clicks "next", solves captchas or applies in bulk. That's the same thing your
browser's built-in autofill and tools like Simplify do. Mass auto-submitting is what gets accounts
flagged, so this deliberately doesn't do it. You stay the one who reviews and submits.

## Change things

- Add or remove sources, watchlist companies, alerts: `config.toml`.
- Add a new source: write a `fetch()` in `radar/sources/` that returns `new_job(...)` records,
  then call it in `radar/__main__.py`.
- The tailoring skill: see `packages/README.md`.

Working on the code? Start with `docs/DEVELOPING.md`. Ideas for what to build next: `docs/IDEAS.md`.
