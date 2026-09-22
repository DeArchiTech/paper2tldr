# paper2tldr

A Claude Code plugin that turns an academic PDF into a **one-page** PDF review.

Three sections, always the same shape:

| Section | What it is |
|---|---|
| **TLDR / 80-20** | One boxed claim — the single idea worth keeping. A verdict, not a summary. |
| **The Keys** | 3–4 numbered points: the problem, the mechanism, how it's measured, what the experiment actually showed — including the failures. |
| **AI's Take** | How strong the evidence really is, where it sits next to what you already know, and one line you can use. |

The point is the constraint. One page forces a verdict; ten pages let you restate the abstract.

## Install

```
/plugin marketplace add DeArchiTech/paper2tldr
/plugin install paper2tldr@paper2tldr
```

## Use

Give Claude a paper and ask for the 80/20:

```
~/Downloads/some_paper.pdf — give me the one-pager on this
```

It reads the whole paper (not the abstract), writes the markdown, renders it, checks the render
for overflow, and trims until it fits one page. It will not publish or send the result anywhere.

## Requirements

- `poppler-utils` — `pdftotext`, `pdfinfo`, `pdftoppm`
- Python with `weasyprint`, `markdown`, `latex2mathml`:

```bash
python3 -m venv ~/.venv && ~/.venv/bin/pip install weasyprint markdown latex2mathml
```

The renderer (`skills/paper2tldr/scripts/md_to_pdf.py`) ships with the plugin. It's a standalone
Markdown → PDF converter using WeasyPrint with an academic stylesheet; a document's own `<style>`
block overrides the defaults, which is how the one-page fitting works.

## Notes on the one-page rule

Cutting a few words reclaims nothing — the text re-wraps and you end up on the same line count.
Cut whole sentences. Shrinking the type is the last resort, and never below 10.5pt.

## Licence

MIT
