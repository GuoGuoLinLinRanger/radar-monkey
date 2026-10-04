# Source research: where the job data lives and how to get it

Research date: 2026-09-30. Everything below was verified by actually fetching the data from this environment (see `scripts/` and `data/samples/`).

## TL;DR

| Source | What it is | Best access | Auth | Apply link | Pay | Posted date | Verdict |
|---|---|---|---|---|---|---|---|
| intern-list.com (Jobright) | Webflow shell around a Jobright iframe | `POST jobright.ai/swan/mini-sites/list` JSON API, category `intern:us:*` / `intern:ca:*` | none | Jobright page only | structured string, ~55-68% coverage | epoch ms (7 h bug, fixable) | **Primary for intern page** |
| newgrad-jobs.com (Jobright) | Same shell, same API | same endpoint, category `newgrad:us:*` / `newgrad:ca:*` | none | Jobright page only | structured string, ~99% coverage | same | **Primary for full-time page** |
| interninsider.me | Static Next.js export on CloudFront | sitemap `sitemap-seo/jobs-open` + JSON-LD on each job page | none | login-gated, never exposed | prose only, ~35% mention a figure | ISO date, but sometimes employer's original date | **Secondary for intern page** |
| Jobright GitHub READMEs (36 repos) | Markdown tables, last 7 days only | raw.githubusercontent.com | none | Jobright page only | none | "Sep 30" no year | Cross-check only |
| Airtable shared views on intern-list.com | Legacy embed, filtered subset | `airtable.com/v0.3/view/.../readSharedViewData` with signed accessPolicy scraped from embed page | none but fragile | Jobright page only | same string | ISO date | Fallback only |

Two corrections to the names in the original ask:

- `internlist.com` (no hyphen) is a parked GoDaddy domain. The Jobright site is **`intern-list.com`**.
- The Jobright full-time sibling is **`newgrad-jobs.com`**, not `newgradlist.com`.

## 1. Jobright (intern-list.com and newgrad-jobs.com)

### How the sites work

Both are Webflow pages. Each category button swaps one iframe to `https://jobright.ai/minisites-jobs/{intern|newgrad}/{us|ca}/{category}?embed=true`, a Next.js "minisite" that calls a public JSON API. Older Airtable embeds are still wired as a fallback but the visible grid is the minisite. The header counters come from `POST https://jobright.ai/api/intern-list/conf` (today: intern US 76,136 total, 6,724 new today; new grad US 117,620 total, 63,013 new).

### The list API

```
POST https://jobright.ai/swan/mini-sites/list?position=0&count=1000
Content-Type: application/json
{"category": "intern:us:swe"}
```

- No auth, no cookies, no bot challenge. Works with any user agent. 20 rapid calls all returned 200 in about 0.4 s each. AWS ALB, permissive CORS.
- `count` has no practical cap. `count=6000` returned all 5,542 intern SWE rows in one 4.5 MB response in about 1 s. The fetcher pages anyway in case a cap appears.
- Sorted by `postedAt` descending. Window is a rolling ~5 months for interns (oldest 2026-05-01) and ~30 days for new grad.
- Optional body filters: `title`, `company`, `industry`, `location`, `workModel` (1 on site, 2 remote, 3 hybrid), `h1bSponsored`, `isNewGrad`, `expLevel`, `salary` (object).
- Category ids are in `docs/jobright_categories.json` (extracted from the minisite JS bundle). US intern has 23 categories, CA intern 9, US new grad 21, CA new grad 13. `gb` exists but is empty.

Row shape:

```json
{"jobId": "6abd5f144ac55253f5d5d091",
 "tabCategory": ["intern:us:swe", "intern:us:ml_ai"],
 "postedAt": 1790770340000,
 "properties": {"title": "...", "company": "...", "location": "Beachwood, OH; Cleveland, OH",
   "salary": "$21.37-$28.84/hr", "workModel": "On Site", "industry": ["Healthcare"],
   "companySize": "10000+", "qualifications": "1. ...\n2. ...", "h1bSponsored": "No",
   "isNewGrad": false, "hireTime": "2026", "graduateTime": "2027-December",
   "expLevel": null, "jobFunction": null, "roleType": null}}
```

### The detail API (optional enrichment)

```
GET https://jobright.ai/swan/share/job/<jobId>
```

About 0.3 s per call, no auth. Returns `jobResult` with `jobSeniority` ("Intern", "Entry Level"), `employmentType` ("Internship", "Full-time"), `publishTime` (exact UTC), `salaryDesc` / `minSalary` / `maxSalary` (annualized), `isH1bSponsor`, `isCitizenOnly`, `isClearanceRequired`, `isDeleted` (closure signal), `jobSummary`, `coreResponsibilities`, `skillSummaries`, and `companyResult` with `companyURL`, size, description, LinkedIn, Glassdoor rating, H1B stats. Same JSON is in the job page's `__NEXT_DATA__`.

### Field coverage measured today

| Field | intern:us:swe (n=5,542) | newgrad:us:swe (n=2,117) |
|---|---|---|
| title, company, location, work model, industry, company size, posted | 100% | 100% |
| salary string present | 55% (2,240 hourly, 581 annual, 122 monthly, 42 weekly, 83 "Unpaid") | 99.9% (mostly annual, some hourly) |
| salary parsed to numbers by our regex | 100% of present | all but 1 |
| multi-location rows (semicolon separated) | 14% | small |
| H1B: Yes / No / Not Sure | 85 / 2,471 / 2,986 | 5 / 95 / 50 per 150 |
| hireTime / graduateTime | ~69% / ~8% | null |
| expLevel, jobFunction, roleType, isNewGrad | always null / false | always null / false |

### Quirks that matter

1. **`postedAt` is 7 hours early.** Jobright converts the UTC publish time to Los Angeles local time and then serializes that wall clock as if it were UTC. Reinterpreting the naive value as America/Los_Angeles and converting back to UTC matches the detail API's `publishTime` exactly. `scripts/fetch_jobright.py` does this.
2. **No employer apply link for visitors.** Every apply button goes to `https://jobright.ai/jobs/info/<jobId>`. That page's Apply Now handler opens `applyLink ?? originalUrl` only when present, and those fields are stripped from `__NEXT_DATA__`, the detail API and the JSON-LD for anonymous users. Otherwise it opens a sign-up modal. Every `/swan/job/*` and `/swan/jobs/*` endpoint returns 401 "Cookie not found". Getting the real ATS URL needs a logged-in Jobright session.
3. **Salary is a free-text range** in five unit styles (`/hr`, `/yr`, `/mon`, `/wk`, `Unpaid`) with occasional bad data (`$0-$32/hr`, `$34.93-$53.42/yr` which is really hourly, `K6-K8/mon`, `PLN34-PLN0/hr`). Jobright's own annualization is hourly × 2080 and monthly × 12, which we replicate.
4. **"New grad" means 0 to 2 years.** `isNewGrad` is false on every row. Detail `jobSeniority` is "Entry Level" on most and "Entry, Mid Level" on some. Filter by title keywords if the user wants strictly new-grad.
5. **Jobs sit in several category tabs** (45% of intern rows), so dedupe on `jobId` across categories and keep the `tabCategory` set.
6. **`isDeleted` can be true on rows still in the list**, even brand new ones. Treat it as a soft signal, not a hard filter, until observed longer.
7. The API is undocumented and internal. The category strings live in a hashed Next.js chunk under `static.jobright.ai/_next/static/chunks/pages/minisites-jobs/`. If the list call starts returning 400, re-extract them from there.

## 2. Intern Insider (interninsider.me)

### How the site works

Static Next.js export served from S3 + CloudFront, rebuilt once a day around 13:40 to 13:52 UTC. No `__NEXT_DATA__`, no client-side data API of any kind (bundles reference only a newsletter endpoint). The data is baked into HTML. Listing pages are capped at 60 items with no pagination, so the only complete inventory is the sitemap. The site claims 36,665 open internships from 5,592 companies. No bot protection on the apex domain: 40 concurrent page fetches all succeeded in under 3 s. `robots.txt` allows `/internships/*`.

### Access method

1. `GET https://interninsider.me/sitemap-seo/jobs-open` (6.3 MB): one `<loc>` per open posting with `<lastmod>` = date posted. Diff the UUID set against the store each day. New UUIDs are inserts, missing ones are closures. About 1,000 to 2,700 new per weekday.
2. For each new UUID, fetch `/internships/{company-slug}/{title-slug}-{uuid}` (~180 KB) and parse the `JobPosting` JSON-LD block plus the badge strip in the `seo-d1` div.

### Fields (from the 40 newest today)

| Field | Coverage | Notes |
|---|---|---|
| id (UUID), title, company, location, posted date, industry | 100% | `datePosted` is absolute ISO |
| Paid badge | 39/40 | absence means unpaid |
| term(s) | 40/40 | e.g. Summer 2027, Winter 2027, rolling |
| remote | 4/40 | badge or `jobLocationType: TELECOMMUTE` |
| visa sponsorship | 0/40 (5/38 in the larger probe) | badge |
| pay amount | 14/40 | prose only, no `baseSalary`; mix of hourly, monthly, annual |
| apply link | 0% | goes to `app.interninsider.me/.../apply` behind a Vercel challenge and login. Employer URL, careers email and recruiter are never exposed publicly |
| deadline | present but 34/38 are a placeholder 2026-12-31 | |
| description | 100% | rewritten by Intern Insider into 4 standard sections, not the employer's text |
| role family, degree level | not a field | only via listing membership / description text |

### Quirks that matter

1. **No apply link at all.** As a source of links it is useless. Its value is breadth (36k postings vs 5.5k SWE on Jobright), term/season, paid flag, and field-of-study tags.
2. **`datePosted` can be the employer's original date.** Postings from 2016 and 2018 are still "open" for Summer 2027. Use the date we first saw the UUID in the sitemap as the freshness signal, not `datePosted`.
3. The weekly beehiiv newsletter (`newsletter.interninsider.me`) does contain direct ATS links for ~45 curated roles a week. HTML only, no RSS.
4. Their GitHub repo `RibbonxInternInsider/2024-Internships-US-Canada` is stale (April 2024).

## 3. Other Jobright surfaces (not recommended as primary)

- **GitHub READMEs** (`github.com/jobright-ai`, 36 repos, e.g. `2026-Software-Engineering-New-Grad`): table of Company, Title, Location, Work Model, Date. Only the last 7 days (639 SWE rows today), no salary, links to the same `jobright.ai/jobs/info/<id>` pages. Updated by a bot ~20 times a day. Same `jobId`s as the API, so useful only as a sanity check. `api.github.com` is blocked in this sandbox but `raw.githubusercontent.com` works.
- **Airtable shared views**: the embed page exposes a signed `accessPolicy` URL that returns all rows of a view in one call (2,440 rows for US SWE). Works, but the base is wiped and re-inserted daily so Airtable record ids are not stable, the view is a filtered subset (only 364 of the API's newest 1,000 ids appear), and the app/share ids change. Keep as a fallback only.
- **Webflow CMS pages** on intern-list.com (`/swe-intern-list` etc.): ~255 curated jobs per category, 5 categories. Not worth scraping.

## 4. Tooling notes

- Playwright cannot run in this sandbox because the preinstalled Chromium does not trust the outbound proxy's CA. It was not needed: nothing is client-rendered beyond the iframe and API calls above.
- `api.github.com` and `newgradlist.com` are blocked by the sandbox proxy.
- Everything in `scripts/` is standard-library Python 3, no dependencies.
