---
name: paper2tldr
description: Turn a PDF paper into a 1-page PDF review — TLDR/80-20, 3-4 key points, then AI's Take. Trigger when the user gives a paper PDF and asks for the 80/20, a one-pager, a review, or "summarize this paper". Do NOT deploy or publish anything.
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

### Step 2 — Write the markdown, three sections only

```
<style>                          ← paste the block below verbatim
# <A title naming the subject, not the paper's full title>
<p style="font-size:9.5pt;color:#52514e;margin:0 0 0.6em 0">Review of <author>,
<i><full title></i> (<venue>, <date>, <n> pp.)</p>

## TLDR / 80-20      → ONE boxed claim: what is worth keeping from this paper
## The Keys          → 3-4 numbered points, bold claim + 2-4 sentences each
## AI's Take         → 2-3 short paragraphs (see below)
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
| The Keys | The problem · the central mechanism · how it is scored/measured · what the experiment showed, including its failures. Real numbers, not adjectives. | ~90 words each |
| AI's Take | ¶1 how strong the evidence actually is. ¶2 where it sits among things the reader already knows. ¶3 one line they can use in their own work. | ~150 words total |

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
