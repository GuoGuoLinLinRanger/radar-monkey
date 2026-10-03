# Packages

Each folder here with a `SKILL.md` is a Claude skill. It's kept separate from the job
collector so you can edit it on its own.

| Folder | What it does |
| --- | --- |
| `tight-job-tailor/` | Reads a posting, researches the company, and tailors your resume (LaTeX preferred) to it. Original by Leviathune. |

## Build the `.skill` file

```bash
python scripts/package.py      # writes dist/tight-job-tailor.skill
```

Pushing a change here also rebuilds it automatically: grab it from the repo's **Releases → Latest build**.
Upload it in Claude under **Settings → Capabilities → Skills**.

## Using it with the dashboard

Open any posting on the dashboard and click **Copy for resume tailoring**. Paste that into
Claude, attach your resume (`.tex` works best), and the skill takes it from there.

## Adding another skill

Make a new folder with a `SKILL.md` whose `name:` matches the folder name. The packaging
script and the release workflow pick it up on their own.
