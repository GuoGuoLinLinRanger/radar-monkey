---
name: tight-job-tailor
description: The compact job-tailor. Research a job posting and its company, work out who they are actually hiring, then tailor the user's real resume to that profile — in the user's own sentence shapes and page proportions, with every trait the posting names carried by a phrase a reader recognizes on a scan, and every reach filled best case and flagged on its line. Use whenever the user shares a job posting, description, or link (with or without a resume) and asks what the role wants, whether it's worth applying, or to tailor, rebuild, adapt, upgrade, or "fix up" their resume for a specific job — including "what do they want here," "make my resume fit this," "what am I missing," "does my resume work for this." Also when a posting and a .tex/.pdf/.docx resume are pasted together without an explicit ask. Prefer this over job-tailor.
---

# Tight Job Tailor

One question drives the run: **if the exceptional version of this candidate — same seats, same titles, same dates — had written their resume for this exact posting, what would be on the page?** That page is the target. The resume the user hands over is the starting material, not the target: a general page shows perhaps a tenth of what they did in each seat, the handful of lines they judged safest for a reader they had not met. The other nine tenths happened — the design doc and who reviewed it, the incident traced, the users talked to, the tooling around the main system, the on-call, the second project — and a specific posting asks for traits the general page was never built to show. So most lines on a tailored page are about work the base never mentioned: proposed from the seat, written best case, flagged for the user to confirm or delete in a minute each. One turn, always ending in the resume file; the user finalizes line by line afterward.

## Priorities

When rules collide, the higher one wins.

1. **The page reads as the person in the profile.** The posting's first three qualitative asks are demonstrated where a ten-second scan lands; every top trait is shown by a behavior, not told by a word; the senior signals (ownership, speed, a decision with a named alternative, scope, adoption) are on the page. This is the goal. Everything below serves it.
2. **In the user's shapes and proportions.** Every line reads like the lines already on their page; each block keeps its bullet count within one of the base; identity lines, headings, and the template are untouched; nothing is merged, no visible block is deleted; live standing notes are followed. This is the constraint.
3. **Best case, flagged.** Every slot the material leaves empty is filled with the most favorable version plausible for the seat, and every assumption is named on its line. What the user says in chat is fact: unflagged, without argument. Nothing halts for a missing fact and nobody gets a questionnaire. This is the engine.

Three kinds of line. **Made up** — a system, product, customer, or team that never existed: banned. **Proposed from the seat** — the surroundings of work that demonstrably happened, with the specifics (who, how many, how long) filled best case and named in the flag: required; most of the page. **Superficial edit** — a visible bullet with the verb upgraded or a stack name added: necessary, nowhere near sufficient. A real line is not safer than a flagged one; the user deletes a wrong flagged line in seconds, and a real line that carries nothing for this reader costs the page a slot.

The test for tailored: swap in a different posting with a different qualitative list. Would the page change substantially — different lines leading blocks, different work surfaced, different slots filled? If the same page would serve both postings, it is tailored to neither.

## Inputs

The posting (text or URL); the resume (`.tex` preferred, comments readable; PDF, DOCX, or text also work, then the page is delivered as `.md`); anything the user says about the team or their work. An analysis file from an earlier run skips Part 1. Corrections after delivery apply to the same files. Depth is deep by default (10–20 searches); quick means the posting, the homepage, the careers page, and at most three searches.

## Part 1 — Who are they hiring

### 1. Read the posting

Write a two-sentence guess at who they want and what they are reacting against before searching; keep it in the analysis notes so the research has something to overturn. Then:

- **The qualitative list is the spec.** "Who we're looking for," "you should join us if," "what we value," "you are expected to," the adjectives inside team descriptions. Pull every quality, in order, verbatim; it is the checklist the finished page is judged against. A list reused across the company's postings is the company's bar and is weighted up; reused on the full-time posting, the intern is judged against the full-time bar, and the profile says so. Template means generic HR text that could describe any company, nothing else.
- **Manager's lines** (named products, precise asks, "in your first week") outweigh requirement bullets. Repeated themes are emphasis; repeated tool names are vocabulary.
- **Gates** (location, authorization, degree, a co-op count, a required project), **level** against pay and years, and **why the seat exists**. A gate the resume's own material can meet — a hidden seat that makes the count, a graduation date — is met on the page, not mentioned in Flags.

### 2. Research the company

`references/research.md` says where to look, what to pull out, and how to decide **who reads the resume first** and what they can see in seconds. That reader sets what counts as a strong signal in Part 2.

### 3. Write the hiring profile

Four to eight ranked traits in plain words. For each: what it means at this company, in one specific sentence; the **tell** (the word a resume would use); the **show** (the behavior a reader infers it from — who asked, what shipped, how fast, what it replaced, who adopted it); and the **scan phrase**, the four or five words a reader would recognize it by. Then, briefly: at-a-glance (three to five things the top third must show), exact terms (vocabulary only), early-career or experienced, uncertainties.

## Part 2 — The page

### 4. Read the material, in this order

Whatever is read first becomes the anchor, and the visible bullets are the one thing that must not be.

1. **The profile**, and its show column: the behaviors the page must carry.
2. **The seats**: employer, title, dates, for every block — commented-out blocks included; a hidden seat is still a seat. Research each (`references/research.md`, last section): the user's live URLs, the employer's engineering blog or docs for the product area the block implies, links left in comments. Note what that team ships, at what scale, in what stack, and what a person with this title there plausibly touched. Never research the person.
3. **The comments**: commented-out `\resumeItem` lines are real work the user chose not to show — number them c1, c2, … and treat them as points. Prose comments are standing instructions with no date. **Live** (they refer to lines or labels on the current page, or state a clean policy): follow, and say so. **Stale** (they name lines or labels no longer on the page): background; the visible page wins. Never delete a visible line because a comment says so; never restore something the user removed because a stale comment mentions it. Where the profile argues against a live note, recommend the override in Flags; do not apply it. A note about what a seat was ("mostly dev tooling") bounds what can be proposed for it. Context blocks, `VERIFY` flags, and links travel with their lines; a detail a context block calls out is protected when lines are shortened. Precedence when material disagrees: chat, then the visible page, then live comments, then stale ones.
4. **The visible bullets, last**: for the facts they state, and for the shapes — how a line opens, where the stack sits, how the purpose is stated, how the result lands, what is bold and how often — plus the proportions: bullets per block, which employers and projects are visible, whether Courses is there.

Compile the original now (`references/latex.md` §1) so the budget is known; do not edit it. Do not ask the user for more; what is missing is filled in step 5.

### 5. Write the ceiling block for each seat

Before re-reading a block's visible bullets, answer the frontier question for that seat: **what would the exceptional holder of this exact seat have on the page for this posting?** Five to seven lines, aimed at the profile's top traits, in the user's shapes. Generate from the seat, ground each line, then fill its slots.

**Generate.** Around any shipped system sit the parts a general resume never mentions. Pick the ones this seat plausibly had and this posting wants, and write each as a line that names a noun only this seat has:

- who asked for it, and what they did before it existed
- the design doc, and who reviewed it; the decision the review settled, with the alternative named
- the hard bug — a race, a migration, a corrupted state — traced and fixed, in N days
- the rollout: flags, canary, staged regions, the rollback that was not needed
- the tooling around it: CLI, dashboard, test harness, load test, CI job
- how it was measured: the benchmark, the eval set, the A/B, the SLO
- operating it: on-call carried, N incidents caught, the alert that fired
- the users or teams talked to, and what changed after
- the second and third projects of the term
- the standard others adopted; the write-up others reused

The surroundings belong to the user's own systems in that seat — the ones their points name — not to everything the team owned. A stack only the posting suggests stays out, inside a proposed line as much as anywhere; a stack the seat plausibly held goes in, flagged.

**Ground.** Every line is tagged: `sharpens #n` (a visible point re-told with a slot newly filled; a paraphrase is not a line), `unhides #cn`, `adjacent to #n` (the surroundings of a visible point, from the list above), or `seat` (something this seat plausibly held that the profile wants, grounded in the seat research). At least two lines per block are `unhides`, `adjacent`, or `seat`; a block whose lines all trace to visible bullets has not been benchmarked. Drop only what cannot be grounded: a line that could be pasted into anyone's resume, or that names a system, customer, or team nothing in the seat suggests.

**Fill.** The slot map (`references/writing.md`) is the engine of showing: verb (ownership), artifact (the system a reader remembers), stack, purpose, replaced world or rejected alternative, scope, speed, result, adoption. Fill every empty slot with the most favorable version plausible for the seat — consistent with the title, the dates, the seat research, and the real points; within plausible, favorable: owned rather than assisted, shipped rather than prototyped, used rather than demoed, fast rather than eventually. Placeholder numbers are plausible for the seat and dates, and are numbers a reader can feel (before → after, hours per week, incidents, adoption). Spread the reaches: at most one speed slot per block; the others carry who asked, the alternative, the scope, the adoption, the operating. Every assumption is recorded beside its line; a fact pulled from seat research (a README, the employer's blog) is flagged with its source until the user confirms it.

### 6. Plan the page from the ceiling down

Fill the page from the ceiling lines, in the order of the posting's asks, and check the base's facts against it — not the other way round.

- **Reserve the carriers first.** Before any other slot is filled, choose one line for each of the posting's first three asks that will carry it where the eye lands — the first five words, a bold fragment, a number — in the top two blocks or the first project. Only then fill the remaining slots. An ask left to a trailing clause because a good line took its slot first is the most common way a page fails. A collaboration, design-review, or customer-contact ask is carried by a reviewer, a requester, or a user named in the line, not by a leadership noun; when no slot is free for its own line, it rides a kept line as the who-asked slot (`references/writing.md`), which no standing note blocks. When the ask is itself about review or feedback ("give and receive feedback," "code review," "design reviews"), the review is the opener, not the mid-line slot: "Reviewed N pull requests across M teams …" or "Wrote the design doc for X, reviewed with …" — a real review line the base holds (a standard set across teams) is reframed before a proposed one is written.
- **The top block is the ten-second read.** Its first two bullets carry two of the posting's top three asks in scan positions — the first five words, a bold fragment, a number. A trailing clause or a beneficiary phrase ("for infra teams") is not a carrier for a top-three ask; the eye never reaches it. If the seat's visible work cannot carry the ask there, its surroundings can. When the seat's domain is far from the posting's, the top block carries the posting's non-domain asks (ownership, speed, scale, collaboration, users) and the domain asks lead the next block and the titles.
- **Each block** keeps its bullet count within one of the base; inside a block, every line may change. The first bullet carries the block's top trait for this posting, and its domain, in its first five words. Rank every candidate line, real or proposed, by the asks it carries for this posting; between two lines carrying the same ask, the real one wins; a proposed line takes a slot when it carries a top-three ask no real line in the block can, displacing the line that carries the least. A real line that carries a named responsibility of the posting is not displaced by a proposed line aimed at a trait the posting never names. Never merge two of the user's bullets; never remove a visible employer, project, or section — shrink to one line instead, keeping the artifact and the headline number and paying with stack names, secondary numbers, and purpose clauses.
- **Hidden blocks get a verdict too.** A commented-out seat returns to the page when a gate or a top trait asks for it — a co-op count, a title or work in the posting's own domain — funded by the blocks that serve this reader least giving up at most one line each. The posting decides, not a guess about the team: a domain the posting names in its title or three or more times in its body is a top trait, and a hidden seat whose title carries that domain returns, because a title is the strongest scan position on the page. A returning seat costs its heading plus one line, paid by the blocks that serve this reader least — never by growing another block, and never deferred for space: a page that names the return as an override and leaves the seat hidden is the failed page. An empty identity field in a returning heading (a blank location) is filled with the most plausible value and flagged, never left to render a bare separator.
- **Live notes decide which facts stay, not how they are told.** A line a note keeps is kept as facts and re-told toward the posting through its slots (who it served, what it replaced, what it caught), so a note never costs the page a trait. Where a note and the profile still disagree, the note wins on the page and the override is recommended in Flags, with the line it would put in.
- Projects and skills rows are ordered so the relevant one leads.

Verdict per real point (visible and commented): **Keep** (cited: the trait and scan position it already carries) · **Reframe** · **Cut** or **Shrink** (why) · **Displaced by** (the ceiling line that takes its slot) · **Unhidden** · **Also plausible** (did not fit) · **Stays hidden**. Then two checks. Also-plausible: no line left there may carry one of the first three asks better than a line on the page — an ask whose page carriers are all mid-line or trailing counts as uncarried — and if one does, swap them. Senior signals: the page carries at least one time-to-ship and at least one decision with its rejected alternative named (a context block in the file often hands one over); if neither is on the page, fill the slot on the line that most plausibly held it.

Classify every planned line: **NEW** (not on the base page: unhidden, adjacent, seat), **RETOLD** (a visible fact with at least one slot newly filled or a different lead), **UNCHANGED** (cited). Target: at least a third of the bullets NEW, at least one NEW line in every block of two or more bullets, and every RETOLD line different from its base line in a filled slot, not only in wording. Below that, the page has not been benchmarked; return to step 5.

### 7. Build the page

- Every line in one of the user's shapes; the traits in the slots; the opener verb + artifact; every line lands on a result — a number, a replaced world, or an adoption — so that no proposed line is the one numberless bullet on the page. A design-review line carries the decision it settled, with the alternative named, and what changed. The artifact name is the category a reader recognizes ("fraud controls," not "per-request risk heuristics"), at most four words; a domain word replaces a generic word and never extends a name that was already specific; a domain that does not fit goes in the purpose slot. Where the posting's own word is the natural word ("design review," "race condition"), use it. Recognition, not stuffing.
- Register (`references/writing.md`): results land on a participle, a semicolon, or an outcome-first opener; one main verb per line; the alternative is named as "instead of X" or "replacing X," never "choosing X over Y"; no relative clauses, no narrative openers, no possessive standing in for a system, no appositive tags, no second sentence after a semicolon. No two lines in a block open on the same verb or land on the same result phrase. Read each new line against its neighbors; a line that would not pass for the user's own is rewritten before anything else happens.
- Bold in the user's pattern: usually the artifact and the headline number, at most two fragments, each at most four words, never a parenthetical stack; a line without a number bolds one fragment; when the posting gates on a stack term the line carries, that term takes the artifact's bold and the headline number keeps its own; a number the file marks unverified or a placeholder is never the bold one.
- Skills rows: reorder so exact terms lead; add a term only when a bullet earns it, and flag it on the row when that bullet is flagged; remove only posting-irrelevant terms and only to hold the row's line count; list every change.
- Flags: any line with an assumed fact ends `% EXAMPLE: assumes …` in `.tex` (`[EXAMPLE: assumes …]` in Markdown and chat), naming each assumption; a line assumed in full says so and names its source; a `VERIFY` the user left travels inside the same marker. The application skill downstream refuses a file that still carries the marker, which is the finalize checklist working; never strip a flag to get past it.
- Fit: exactly one page, template untouched, `references/latex.md` for the loop and the order in which words may be cut. Never cut a mechanism, a headline number, a replaced world, an adoption clause, a protected detail, or a kept line to fit.

### 8. Review, then deliver

Re-read the finished page in this order and fix before delivering; the answers become Flags.

1. **Ten seconds as the first reader.** For each of the posting's first three qualitative asks: which phrase carries it, and where does the eye land — first bullet of a block, first five words, bold, a number, a skills row? Mid-line, a trailing clause, or a beneficiary phrase is carried, not seen; for the ten-second read it is absent. Absent while a ceiling line carries it → that line goes on the page now, displacing the weakest line for this posting; never a heading descriptor, a summary line, or added words. Then the top block alone: do its first two bullets carry two of the three asks where the eye lands?
2. **The diff test.** Count NEW / RETOLD / UNCHANGED against the targets in step 6, and give each UNCHANGED line its citation. Below target → back to step 5 for the blocks that fell short. Then the swap test: would a different posting change this page substantially?
3. **Register.** Any narrative opener, relative clause, reduced relative, possessive for a system, appositive tag, second sentence after a semicolon, casual verb, three -ing clauses, or a line the user would not have written → rewrite.
4. **Grounding.** Any noun that nothing in the seat suggests, or a stack only the posting suggests → cut. Any assumed fact — number, role, stack, mechanism, research-sourced detail, whole line — without a flag → flag it.
5. **Constraints.** One page; template diff clean; identity lines byte-identical (a blank field in a returning heading, filled and flagged, is the one exception); every block within one line of its base count; nothing merged, no visible block gone; live notes followed and any override recommended, not applied; bold in the base's pattern.

Deliver, resume first: `<First>_<Last>_Resume_<Company>.tex` + PDF (or `.md`); `<company>-<role>-analysis.md` (profile, research notes, sources, the handoff block); `<company>-<role>-benchmark.md` (per block, in this order: the ceiling lines with tags and the trait each aims at; the real points including c-lines; the verdict table with each page line, its class, its assumptions and slots; the also-plausible lines; then the coverage table and the Flags section). The run is not finished until the resume file exists; if something blocks it, say so at the top and deliver the page as `.md`.

In chat, in this order: the profile with its scan phrases; the page block by block, each line as **was →** (the base line, or *not on base*) **now →** (the line verbatim, its flag, its class, the trait it shows); the coverage table (trait → line → phrase → scan position); Flags (conflicts and how they were resolved, recommended overrides with the line each would put in, skills changes, cuts to fit, and at most five assumptions whose truth would most change the page). Then stop. When corrections come: a stated fact replaces the guess it corrects and its flag goes; a wording instruction is applied to the line it names and the same pattern to every sibling line unasked; "not true" deletes the line.

## Handoff

At the end of the analysis file; the application skill reads `role`, `company`, `gates`, `exact_terms`, `priorities`.

```yaml
job_analysis:
  role: "Software Engineer, New Grad"
  company: "Nooks"
  analyzed_on: "2026-09-08"
  depth: "deep"
  who_reads_first: "founder or hiring manager, reads every application"
  early_career: true
  gates: ["hybrid SF, in office 3 days"]
  priorities:
    - trait: "Ownership end to end"
      means_here: "takes a vague customer problem through design, ship, monitoring; posting repeats it four times"
      tell: "end-to-end owner"
      show: "a line that opens on the artifact and carries who asked, what shipped, and what changed for them"
      scan: "Designed and shipped … for N teams"
  at_a_glance: ["a shipped, linkable product in the top third", "a scale number in the first bullet"]
  exact_terms: ["TypeScript", "React", "Node.js", "Python"]
  uncertainties: ["team size not findable; assumed small from funding stage"]
```
