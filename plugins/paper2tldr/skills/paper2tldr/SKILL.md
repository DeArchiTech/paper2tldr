---
name: paper2tldr
description: Turn a PDF paper into a 1-page PDF review — TLDR/80-20, short numbered key points, then AI's Take — all point form. Trigger when the user gives a paper PDF and asks for the 80/20, a one-pager, a review, or "summarize this paper". Do NOT deploy or publish anything.
---

# Paper → 1-Page TLDR

Input: one PDF paper. Output: **one** 1-page PDF (plus its markdown source). Nothing is deployed.

## Setup (once)

The build step needs `pdftotext`/`pdftoppm` (poppler) and three Python packages:

```bash
python3 -m venv ~/.venv && ~/.venv/bin/pip install weasyprint markdown latex2mathml
```

Any virtualenv works — just use its `python3` in Step 3. Never install with
`--break-system-packages` on an externally-managed Python.

## Workflow

### Step 1 — Read the whole paper, not the abstract

```bash
pdftotext "<paper>.pdf" /tmp/paper.txt && wc -w /tmp/paper.txt
```

Read it in chunks with `sed -n 'A,Bp'`. Cover abstract → model/method → experiment → conclusion.
**Look specifically for the parts an abstract hides:** what the authors admit went wrong, what
their comparison actually shows, and any contradiction between the abstract and the model.
Those are usually the most valuable lines in the report.

### Step 1b — Over 30 pages? Treat it as a book, and find the chapter

Anything longer than ~30 pages is not a paper — it is a thesis, a volume, or a whole
proceedings, and reviewing all of it is the wrong job.

```bash
pdfinfo "<paper>.pdf" | grep Pages
```

If it is over 30 pages:

1. **Read the first two pages.** A download cover sheet (ResearchGate, a publisher stamp) usually
   names the single chapter the file was fetched for. That chapter is the paper.
2. **Otherwise find the contents** — `grep -n "Contents" paper.txt` — and take the chapter's start
   page plus the *next* entry's start page. That is the range.
3. **Map pages to lines.** The chapter title appears twice: once in the contents, once at its own
   opening. `grep -n "<chapter title>" paper.txt` gives both; read from the second hit down to the
   next chapter heading or the chapter's own `References`.
4. **A thesis with no cover sheet is different** — there the whole document *is* the paper. Read it
   all, but lead with the chapters that carry the result, not the literature review.
5. **If nothing points at one chapter, ask which one** rather than reviewing the whole volume.

The citation line then names the chapter, with the volume as the venue:
`Review of <author>, <chapter title> (<volume>, <publisher/series>, <year>, <chapter> pp.)`

### Step 2 — Write the markdown, three sections only

```
<style>                          ← paste the block below verbatim
# <A title naming the subject, not the paper's full title>
<p style="font-size:9.5pt;color:#52514e;margin:0 0 0.6em 0">Review of <author>,
<i><full title></i> (<venue>, <date>, <n> pp.)</p>

## TLDR / 80-20      → ONE boxed claim: what is worth keeping from this paper
## The Keys          → numbered points, bold claim + evidence, 20-30 words each
## AI's Take         → points, same 20-30 word budget (see below)
```

The style block:

```html
<style>
@page { margin: 1.9cm 2.2cm 1.6cm 2.2cm; }
table { page-break-inside: auto; }
h2, h3 { page-break-after: auto; }
th:first-child, td:first-child { white-space: nowrap; }
body { font-size: 11pt; }
p { margin: 0.3em 0; }
h1 { font-size: 18pt; margin: 0 0 0.15em 0; }
h2 { font-size: 12.5pt; margin: 0.65em 0 0.2em 0; padding-bottom: 0.08em; }
li { margin: 0.15em 0; }
</style>
```

The TLDR box:

```html
<div style="border-left:3px solid #2a78d6;padding:0.1em 0 0.1em 0.8em;margin:0.45em 0">
<b>The one-line verdict.</b><br>
The principle worth keeping, in plain words.
</div>
```

**What each section owes the reader**

| Section | Job | Budget |
|---|---|---|
| TLDR / 80-20 | The single transferable idea. Not a summary — a verdict. | ~40 words |
| The Keys | The problem · the central mechanism · how it is scored/measured · what the experiment showed, including its failures. Real numbers, not adjectives. | **20-30 words per point** |
| AI's Take | How strong the evidence actually is · where it sits among things the reader already knows · one line they can use in their own work. | **20-30 words per point** |

**Everything is point form, including AI's Take.** Each point is a bold lead-in claim followed by
its evidence, 20-30 words total. Never a paragraph, never a single line — a point under ~18 words
cannot carry a finding, and one over ~32 is a paragraph wearing a bullet.

**More points beats longer points.** A 1-page report runs roughly 12 Keys and 5 Take points. Past
about 12 points, group them under short bold subheads (*What it claims* · *How it was tested* ·
*Where it breaks*) so the page still scans. Audit before building: strip the markdown, count the
words in every `- ` line, and flag anything outside 18-32.

### Longer variants

The same grammar scales. Only the point count changes — never the point length.

| Source | Pages |
|---|---|
| One paper, one video | 1 |
| One book | 2.5 |
| A comparison of two sources | 2 |

Bullets render ~420 words per page against ~520 for prose, so word targets do not transfer between
the two. Fit by cutting whole points.

**Voice:** plain words, short sentences, no hedging, no praise for its own sake. Say the paper is
weak when it is weak. Numbers from the paper go in as numbers.

### Step 3 — Build

```bash
~/.venv/bin/python3 "${CLAUDE_PLUGIN_ROOT}/skills/paper2tldr/scripts/md_to_pdf.py" <name>.md && \
pdfinfo <name>.pdf | grep Pages
```

### Step 4 — Make it fit ONE page, in this order

1. **Cut words.** Target ~450 rendered words (`pdftotext <name>.pdf - | wc -w`). Aim for that
   before the first build and most of this step disappears.
2. Check the overflow, do not guess:
   `pdftotext -layout -f 2 -l 2 <name>.pdf - | sed '/^$/d' | head`
3. Cut whole sentences, not words — re-wrapping eats small trims, so shaving 5 words usually
   reclaims nothing. One spilled line ≈ one sentence.
4. **Last resort only:** `body { font-size: 11pt }` → `10.5pt`. Say that you did it and offer to
   cut a paragraph instead. Never go below 10.5pt.

### Step 5 — Look at it, then report

```bash
pdftoppm -r 80 -f 1 -l 1 -png <name>.pdf pg    # then read pg-1.png
```

Report: the path, the three section contents in one line each, and anything you shrank.
**Do not deploy, publish, or send it anywhere** unless the user says so in that message.

## Traps

- **Don't hard-wrap paragraphs in the markdown** — the `nl2br` extension turns wrapped lines into
  line breaks. One paragraph = one long line.
- **No LaTeX.** Use Unicode: `×  ÷  ≤  ≥  →  ⇔  ∞`. Inside raw HTML, `>` must be `&gt;`.
- **Escape `R\*`** and similar when an asterisk starts emphasis.
- All styling lives in the document's own `<style>` block, which overrides the script's defaults.
  Don't edit `scripts/md_to_pdf.py`.

## Reference

Worked example: `example_report.md` in this skill folder — a 2013 genetic-algorithm paper on
resource-constrained project scheduling, the first report built this way.
