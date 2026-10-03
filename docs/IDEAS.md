# Ideas, roughly in order of payoff

1. **Auto-tailor in one click.** Dashboard button that sends the posting + your `.tex` resume to the
   Claude API with the tailoring skill's instructions, compiles the PDF, and the extension uploads
   *that* resume on the form. Biggest time saver, and it keeps a copy per application in the tracker.
2. **Detect "submitted" automatically.** On Greenhouse/Lever/Ashby/Workday the confirmation page has a
   known shape ("Thank you for applying"). The extension could offer "Log this?" right there instead of
   you remembering to click I applied.
3. **Email status sync.** Read rejection/OA/interview emails (Gmail filter or the Gmail API) and move the
   tracker status for you. This is the "track status when results come out" piece.
4. **Workday account helper.** Every Workday tenant wants a new account. Store one strong password
   pattern per tenant in Chrome's password manager and have the extension recognise the tenant.
5. **Referral finder.** For each starred job, link straight to a LinkedIn search for alumni from your
   school at that company.
6. **Repost detection.** Flag postings whose title + company were seen before and closed. Reposts often
   mean the first round didn't fill the role.
7. **Better fit score.** Swap keyword matching for embeddings of your resume vs. the posting text.
8. **More sources.** Any company on Greenhouse/Lever/Ashby is one line in `config.toml`. Others
   (SmartRecruiters, Workable) have public APIs too and fit the same `boards.py` pattern.
