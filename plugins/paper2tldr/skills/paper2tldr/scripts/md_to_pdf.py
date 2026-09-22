#!/usr/bin/env python3
"""
md_to_pdf.py — Convert Markdown files to academic-style PDF via weasyprint

Usage:
    python3 md_to_pdf.py input.md
    python3 md_to_pdf.py input.md output.pdf
    python3 md_to_pdf.py input.md --open
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

import latex2mathml.converter
import markdown
from weasyprint import HTML, CSS


ACADEMIC_CSS = """
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,600;1,400&family=Source+Code+Pro:wght@400;600&display=swap');

@page {
    size: A4;
    margin: 2.5cm 3cm 2.5cm 3cm;
    @bottom-center {
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 10pt;
        color: #555;
    }
}

body {
    font-family: 'EB Garamond', Georgia, 'Times New Roman', serif;
    font-size: 11.5pt;
    line-height: 1.65;
    color: #1a1a1a;
    max-width: 100%;
    text-align: justify;
    hyphens: auto;
}

h1 {
    font-size: 20pt;
    font-weight: 600;
    text-align: center;
    margin-top: 0;
    margin-bottom: 0.3em;
    color: #111;
    letter-spacing: 0.01em;
    line-height: 1.25;
}

h2 {
    font-size: 13.5pt;
    font-weight: 600;
    margin-top: 1.8em;
    margin-bottom: 0.4em;
    color: #111;
    border-bottom: 1px solid #ccc;
    padding-bottom: 0.15em;
}

h3 {
    font-size: 12pt;
    font-weight: 600;
    font-style: italic;
    margin-top: 1.3em;
    margin-bottom: 0.3em;
    color: #222;
}

h4 {
    font-size: 11.5pt;
    font-weight: 600;
    margin-top: 1em;
    margin-bottom: 0.2em;
    color: #333;
}

/* Title block — first h1 + immediately following p or blockquote treated as abstract */
h1 + p em, h1 + p strong {
    font-size: 10pt;
    color: #444;
}

p {
    margin: 0.5em 0 0.7em 0;
}

/* Abstract / metadata block */
blockquote {
    font-style: italic;
    border-left: 3px solid #aaa;
    margin: 1em 1.5em;
    padding: 0.4em 0.8em;
    color: #444;
    font-size: 11pt;
}

/* Code blocks */
pre {
    font-family: 'Source Code Pro', 'Courier New', monospace;
    font-size: 9pt;
    background: #f6f6f6;
    border: 1px solid #ddd;
    border-left: 3px solid #888;
    padding: 0.7em 1em;
    margin: 0.8em 0;
    line-height: 1.45;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-all;
}

code {
    font-family: 'Source Code Pro', 'Courier New', monospace;
    font-size: 9pt;
    background: #f2f2f2;
    padding: 0.1em 0.3em;
    border-radius: 2px;
}

pre code {
    background: none;
    padding: 0;
}

/* Tables */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
    font-size: 10.5pt;
}

th {
    background: #1a1a1a;
    color: #fff;
    font-weight: 600;
    padding: 0.5em 0.8em;
    text-align: left;
    letter-spacing: 0.03em;
}

td {
    padding: 0.4em 0.8em;
    border-bottom: 1px solid #ddd;
    vertical-align: top;
}

tr:nth-child(even) td {
    background: #f8f8f8;
}

tr:last-child td {
    border-bottom: 2px solid #aaa;
}

/* Horizontal rule */
hr {
    border: none;
    border-top: 1px solid #ccc;
    margin: 1.5em 0;
}

/* Lists */
ul, ol {
    margin: 0.5em 0 0.7em 0;
    padding-left: 1.8em;
}

li {
    margin-bottom: 0.25em;
}

/* Strong / em */
strong {
    font-weight: 600;
    color: #111;
}

em {
    font-style: italic;
}

/* Page break hints */
h2 {
    page-break-after: avoid;
}

pre, table {
    page-break-inside: avoid;
}
"""


def latex_to_mathml(tex: str, display: bool = False) -> str:
    try:
        mode = "display" if display else "inline"
        return latex2mathml.converter.convert(tex, display=mode)
    except Exception:
        # Fall back to showing the raw LaTeX in a code span
        delim = "$$" if display else "$"
        return f"<code>{delim}{tex}{delim}</code>"


def replace_math(html: str) -> str:
    """Replace $...$ and $$...$$ in HTML text nodes with MathML."""
    # Display math first ($$...$$), non-greedy
    html = re.sub(
        r'\$\$(.+?)\$\$',
        lambda m: latex_to_mathml(m.group(1), display=True),
        html,
        flags=re.DOTALL,
    )
    # Inline math ($...$) — avoid matching empty or already-processed tags
    html = re.sub(
        r'\$([^$\n]+?)\$',
        lambda m: latex_to_mathml(m.group(1), display=False),
        html,
    )
    return html


def convert(input_path: Path, output_path: Path) -> bool:
    md_text = input_path.read_text(encoding="utf-8")

    html_body = markdown.markdown(
        md_text,
        extensions=[
            "tables",
            "fenced_code",
            "codehilite",
            "nl2br",
            "sane_lists",
        ],
        extension_configs={
            "codehilite": {
                "css_class": "highlight",
                "guess_lang": False,
            }
        },
    )

    html_body = replace_math(html_body)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
{html_body}
</body>
</html>"""

    try:
        HTML(string=html, base_url=str(input_path.parent)).write_pdf(
            str(output_path),
            stylesheets=[CSS(string=ACADEMIC_CSS)],
        )
        return True
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Convert Markdown to academic PDF")
    parser.add_argument("input", help="Input .md file")
    parser.add_argument("output", nargs="?", help="Output .pdf file (optional)")
    parser.add_argument("--open", action="store_true", help="Open PDF after generating")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output) if args.output else input_path.with_suffix(".pdf")

    print(f"Converting {input_path} → {output_path} ...")

    if convert(input_path, output_path):
        print(f"Done: {output_path}")
        if args.open:
            subprocess.Popen(["xdg-open", str(output_path)])
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
