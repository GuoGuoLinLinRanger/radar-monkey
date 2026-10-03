# Writing

## What proves a trait

A resume never proves a trait by naming it. It proves it with a behavior the reader can see.

| Trait | Weak (what most resumes say) | Strong (what proves it) |
|---|---|---|
| Fast-moving | "agile environment" | shipped in days or weeks; N releases on feedback; same-day production fix |
| Product-oriented / customer contact | "built features"; "collaborated with stakeholders" | who the work was for, what they did before, what changed; interviewed N users |
| High-agency / ownership | "implemented tickets"; "contributed to" | identified, designed, shipped, monitored; the whole lifecycle on one system |
| Comfortable with ambiguity | "startup project" | a working thing from a vague ask, with no spec |
| Technical depth | "used React and Python" | a hard performance, correctness, or architecture problem with the mechanism named |
| Generalist / many moving parts | "full-stack" | one line visibly crossing client, server, data, infra; systems named beside each other |
| Learns quickly | "fast learner" | an unfamiliar technology picked up and shipped with inside a stated window |
| Scope / leadership | "senior engineer" | team size led, systems owned, a standard others adopted |
| Operates production | "maintained services" | monitoring, on-call, incidents caught, reliability numbers |
| Collaboration / communication | "strong communicator" | a design doc reviewed by named teams; a review that changed a design; a write-up others reused |
| Domain depth | a domain word in a skills list | the domain's own metrics and rules handled |

## The slot map

Showing a trait is filling a slot in a line the user would have written, not restructuring the sentence.

| Slot | Position | Carries | Example |
|---|---|---|---|
| Verb | first word | ownership, seniority | Designed and shipped / Architected / Led / Built — never Helped, Worked on |
| Artifact | object of the verb | the system a reader remembers; the domain | a fraud-scoring service, a claims-routing service |
| Stack | in / on / with | breadth or depth; exact terms | in Python and Go; on PostgreSQL |
| Purpose | to … | what it does, for whom | to flag high-risk orders before checkout |
| Replaced world / alternative | replacing X / instead of X | judgment; automation | replacing manual review queues; instead of blanket bans |
| Scope | for N users / across N services / with N teams | reach, moving parts | across 30+ microservices |
| Who asked / who reviewed | , reviewed with the X and Y teams / from N user interviews / at the X team's request | collaboration, design review, customer contact — rides inside a kept line, so a standing note never blocks it | , reviewed with the support and payments teams |
| Speed | ; shipped in N weeks | hits the ground running | ; shipped in 6 weeks |
| Result | number on a participle or after a semicolon | impact | cutting review time 40% |
| Adoption | ; adopted as … / ; standard across … | influence | ; adopted as release standard across 3 teams |

A leadership noun ("Led a 10-developer team") carries scope; collaboration, design review, and customer contact are carried only by a reviewer, a requester, or a user named in the line. A line with only verb, artifact, and result shows impact and nothing else; that is a task. The same facts with purpose, replaced world, scope, and speed filled are evidence for four traits and still read as one resume line. The senior signals (ownership verb, time to ship, alternative, scope, adoption) are slots filled by default, best case, flagged. A page where the only filled reach-slot is speed shows one trait; spread the reaches across who asked, the alternative, the scope, and the adoption.

## Shapes

Every new line is written in a shape already on the user's page. Read their visible bullets for how a line opens, where the stack sits, how the purpose is stated, how the result lands. Content changes for the job; shape does not, because a page where four lines read like the user and two read like a model is worse than either.

Default shape, for a page with no usable bullets: **[Verb] [artifact] [in/on stack] to [purpose], [result on a participle]; [adoption clause]** — *Built a fraud-scoring service in Python to flag high-risk orders before checkout, replacing manual review queues; adopted across 3 storefronts.* Three variants of the same shape: artifact-first as above, outcome-first (*Enabled … by shipping …*), number-first (*Cut … by …*). Vary openers across a block; never two lines in a block on the same verb or the same result phrase.

A block of three or four lines reads as one system when the nouns carry from line to line (the thing → the hard part inside it → how it shipped or was protected → how it is kept alive); when the seat was not one system, tell what happened, and never add a line to complete a pattern.

## Scan positions, and choosing over adding

A reader's eye goes heading → the first words of the first bullet → bold → numbers → the first items of a skills row. A trait must be recognizable from those alone:

- The first bullet of each block carries the block's top trait for this posting and its domain, in its first five words. This is the heading's second line; headings themselves never change.
- The artifact name carries the domain: "RTOS file-system test pipeline," not "test pipeline"; "payments ledger migration," not "migration." At most four words. A domain word replaces a generic word and never extends a name that was already specific; if the domain does not fit, it goes in the purpose slot.
- Where the posting's own word is the natural word ("race condition," "design review"), use it. Recognition, not stuffing.
- Order is free and costs nothing: the top-trait bullet first in its block, the relevant project first, exact terms first in each skills row.

Nothing is added to make a trait scannable: no heading descriptor, no summary line, no tagline, no third bold fragment, no extra words. If a line grows past the user's line length to become scannable, the domain moves to the purpose slot instead.

## Bold

Bold what the user's visible bullets bold, in the same amount: usually the artifact and the headline number; at most two fragments per line; each at most four words; never a parenthetical stack list, never a clause. A line with no number bolds one fragment. When the posting gates on a stack term ("Go", "Rust") and the line carries it, that term is one of the two fragments — it is the word this reader scans for. If a comment states a bold policy the visible bullets do not follow, the bullets win.

## Not resume text

- Narrative openers (Took, Gave, Chose, Turned, Ran, Drove, Owned): a resume line opens on a verb of making — one the user's page already uses, or Built, Designed, Shipped, Engineered, Rebuilt, Cut, Saved, Led.
- Possessives standing in for a system ("its control plane"): name the system. Back-references ("the pipeline") on a later line: name it again.
- Relative clauses anywhere: "that evaluates" → "to evaluate"; "which reduced" → ", reducing" or "; cut".
- Reduced relatives ("failures the system had been swallowing" → "previously silent failures"), "now the…," "currently."
- Appositive tags hung on a comma or semicolon (", live in 6 weeks", "; 3x faster triage"): a speed or result rides a verb — "; shipped in 6 weeks", "; cut triage time 3x". The arc "from design doc to production in N weeks" is a story, whatever verb opens it; the speed slot is the bare "; shipped in N weeks".
- A second sentence after the semicolon ("; two review comments changed the data model"): the tail is a participle or a verb phrase with the same subject, never a new subject.
- Noun piles (four nouns in a row) and bare participles that read as reduced relatives ("fraud controls scoring order risk signals"): put the purpose back — "to score order risk".
- Articles the user's bullets do not use; casual verbs (Gave, Got, Made, Demoed); two coordinated main verbs ("Demoed X and shipped Y" → one main verb, the rest on a participle); filler verbs (utilized, leveraged, helped, assisted, was responsible for); words without a job (seamless, robust, scalable, successfully, various, solution, efforts, in order to).
- "choosing X over Y" for a decision: the rejected alternative rides "instead of X" or "replacing X" — *bit-packing state into request metadata instead of a shared cache*.
- More than two -ing clauses; more than four technologies; a line over ~32 words is two claims.

## Tell, keyword, prose, show

| | Line | What the reader takes away |
|---|---|---|
| Tell | High-agency engineer who owned the dispute tool end to end | Nothing; adjectives are skipped |
| Keyword | Owned end-to-end development of a dispute-handling tool in React + FastAPI for the support team, cutting resolution time 40% | Impact, plus a keyword doing the trait's work; survives a search, not a read |
| Prose | Took the support team's spreadsheet dispute process to a shipped React + FastAPI tool in 3 weeks, working from their complaints rather than a spec; cut resolution time 40% | The right content in the wrong register; reads as a story |
| Show | Built a dispute-handling tool in React and FastAPI to replace the support team's spreadsheet process, cutting resolution time 40%; shipped solo in 3 weeks from agent complaints rather than a spec | Ownership, speed, ambiguity, customer contact, judgment, impact — none named; reads like the other lines on the page |

Show is Keyword with its slots filled. Slots the user has not given a fact for are filled best case and named in the flag.

Before/after, same facts:

| Before | After |
|---|---|
| Worked on improving the performance of the search API by introducing a caching layer built on Redis, which resulted in a 45% reduction in p95 latency for the roughly 2,000 internal users who rely on it daily | Added a Redis caching layer to the search API to cut p95 latency 45% for ~2,000 daily internal users |
| Took the inventory sync service from design doc to production in 6 weeks: Go at 5K events/sec, retiring nightly CSV imports | Designed an inventory sync service in Go to process 5K events/sec, replacing nightly CSV imports; shipped in 6 weeks |
| Surfaced 100% of failures the pipeline had been swallowing by monitoring stage errors across 2M jobs/day | Engineered per-stage monitoring in Datadog to flag pipeline errors across 2M jobs/day, surfacing 100% of previously silent failures |
| Helped improve API performance | Identified an N+1 query bottleneck in a high-traffic API and redesigned the fetch path to cut p95 latency 58% |

Lines proposed from the seat use the same shapes. The surroundings of the dispute tool, written as resume lines: *Wrote the design doc for the dispute tool, reviewed with the support and payments teams, moving sync from polling to queue-backed writes to cut stale reads to zero* — *Traced a double-submit race between the dispute form and the ledger writer and fixed it in 2 days with an idempotency key, replacing a manual reconciliation step* — *Carried on-call for the dispute service for 8 weeks, catching 3 incidents before agents noticed*. Each names a noun only that seat has, each fills a senior slot (a decision with its alternative, a bug traced in N days, production operated), each lands on a result, each is flagged in full, and none hands the sentence to a second subject after the semicolon, leans on a possessive ("its review"), or opens on Ran, Took, or Drove.

## Flags

Any line with an assumed fact ends with a flag naming each assumption: `.tex` — `\resumeItem{...} % EXAMPLE: assumes solo; 3 weeks; no spec`; Markdown and chat — the line, then `[EXAMPLE: assumes …]`. A line assumed in full says `whole line assumed from <seat / c-line / README>`. A fact taken from seat research rather than the resume or chat is flagged with its source (`% EXAMPLE: "LangGraph" from your repo README — confirm`). Reframing, tightening, and reordering the user's own facts need no flag; a new number, role, beneficiary, mechanism, stack, or line does. When the user confirms or corrects, edit the line and remove the flag; when they say a line is untrue, remove the line. The application skill downstream refuses a resume that still carries the marker; never strip flags to get past it.

## Files and chat

**Benchmark file**, one section per block, in resume order. Opens with one line: assumed facts are filled best case and listed beside each line; the user finalizes line by line. Each block, in this order: the ceiling lines (tag, trait aimed at, assumptions); the real points (visible, then c-lines); the verdict table; the also-plausible lines.

Verdict table columns: **#** · **Your point** · **Verdict** (Keep / Reframe / Cut / Shrink / Displaced by / Unhidden / Also plausible / Stays hidden) · **On the page** (the line exactly as it appears, or —) · **Class** (NEW / RETOLD / UNCHANGED, with the citation for UNCHANGED) · **Assumes / slots** (each assumed fact; which slot carries which trait; any conflict resolved or note overruled).

**Coverage table**, closing the benchmark file and, short, the chat: one row per qualitative line in the posting, in the posting's order. Columns: **They asked for** · **Carried by** (block and bullet) · **Phrase** (the words a reader infers it from) · **Scan position** (first bullet / opener / bold / number / skills row / mid-line). Each of the first three rows needs two carrying lines and at least one scan position that is not mid-line. An empty row is a slot to fill best case or an honest "no seat holds this," said in Flags.

**Flags section**, closing the benchmark file after the coverage table, so nothing in the file points at a section that does not exist: conflicts and how they were resolved; live notes followed and overrides recommended; skills changes; cuts to fit; the assumptions whose truth would most change the page.

**Chat**: profile with scan phrases → the page block by block as was → now, every line verbatim with its flag, class, and trait → coverage table → Flags. No prose summary of the page and no "see file."
