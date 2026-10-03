# LaTeX

The template is the user's visual identity; only text inside existing content macros changes.

## 1. Baseline

```bash
which pdflatex || (apt-get update -qq && apt-get install -y -qq \
  texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended latexmk poppler-utils)
# texlive-fonts-extra for fontawesome/academicons; texlive-xetex if the preamble uses fontspec.
cp resume.tex original.tex
latexmk -pdf -interaction=nonstopmode original.tex     # -xelatex if fontspec
pdftoppm -png -r 150 original.pdf baseline
```

View `baseline-1.png` and keep it. Note the page count and how many lines each block takes; that is the budget. If the original does not compile, fix the environment; never alter the template to force a compile. If it truly cannot compile, say so and deliver the page as `.md`.

## 2. Edit rules

- Work on a copy named for the role. Never edit the upload in place.
- Change only text inside `\resumeItem{...}` (or the template's equivalent), skills rows, and the order of project entries. To add an entry, clone a sibling's macro structure exactly.
- Heading macros (`\resumeSubheading`, `\resumeProjectHeading`, education) stay byte-identical:

```bash
grep -n 'resumeSubheading\|resumeProjectHeading\|resumeJobHeading' original.tex > /tmp/a
grep -n 'resumeSubheading\|resumeProjectHeading\|resumeJobHeading' tailored.tex > /tmp/b
diff /tmp/a /tmp/b     # only line numbers may differ
diff original.tex tailored.tex   # content lines only; a changed preamble, macro, \vspace, or font command is a defect
```

- Escape `%`, `&`, `#`, `_`. Never a bare `~` for "approximately" (it is a non-breaking space); write `\textasciitilde{}30\%`.
- Flag: `\resumeItem{...} % EXAMPLE: assumes …`, invisible in the PDF. `grep -c '% EXAMPLE' tailored.tex` equals the flagged rows in the verdict table.

## 3. Compile and inspect

```bash
latexmk -pdf -interaction=nonstopmode tailored.tex
grep -i "overfull" tailored.log | head
pdfinfo tailored.pdf | grep Pages            # must be 1
pdftoppm -png -r 150 tailored.pdf check
```

Look at `check-1.png` beside `baseline-1.png`; the log is not enough. One page; formatting identical to baseline; no orphan of one or two words on a wrapped item; last lines reasonably full; nothing overflowing; the page comfortably full; bold in the page's pattern. Fix by rewording, recompile; two to four rounds is normal, and again after any later rewrite.

## 4. Fit, with words only

When a line runs long, cut in this order and stop as soon as it fits:

1. Filler and articles: "responsible for designing" → "designed"; "in order to" → "to"; drop *various*, *successfully*, and any "the" the user's bullets would not have.
2. Notation: "43 percent" → "43\%"; "hours per week" → "hrs/week" if the page already abbreviates.
3. A stack name that already appears on another line.
4. A secondary number, when the line carries two and the headline stays.
5. A stack parenthetical, when the stack is in the skills rows and on another line.

Never cut the mechanism, the headline number, the replaced world or the named alternative, the adoption clause, a detail a CONTEXT block calls out, or anything on a line the user marked keep. If it still does not fit after step 5, the line is carrying two claims; move one to the block's also-plausible list.

When the page runs long: shorten lines before removing any (a line shrunk to one line keeps its artifact and headline number and pays with stack names, secondary numbers, and purpose clauses); remove a line only inside its block's allocation; never a whole block; never Courses without the user's note allowing it. When a last line is nearly empty, extend with a relevant detail (flagged if the resume does not support it). Every cut and every shortening is reported in chat with its reason.
