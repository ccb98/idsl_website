#!/usr/bin/env python3
"""Regenerate the publication list in publications.html from data/publications.json.

Only the region between <!-- pubs:start --> and <!-- pubs:end --> is rewritten, so the
page header, menu and footer can still be edited by hand.

Usage:  python3 tools/build_publications.py
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "publications.json"
PAGE = ROOT / "publications.html"
START, END = "<!-- pubs:start -->", "<!-- pubs:end -->"

esc = lambda t: html.escape(t or "", quote=True)


def entry_html(e):
    parts = ['<li class="pub">']
    if e.get("venue"):
        parts.append(f'<span class="date venue pub-venue">{esc(e["venue"])}</span>')
    parts.append(f'<strong>{esc(e["title"])}</strong>')
    if e.get("authors"):
        parts.append(f'<span class="date pub-authors">{esc(e["authors"])}</span>')
    links = e.get("links") or []
    if links:
        anchors = " ".join(f'<a href="{esc(l["url"])}">{esc(l["label"])}</a>' for l in links)
        parts.append(f'<span class="pub-links">{anchors}</span>')
    parts.append("</li>")
    return "".join(parts)


def build():
    entries = json.loads(DATA.read_text(encoding="utf8"))
    by_year = {}
    for e in entries:
        by_year.setdefault(e.get("year"), []).append(e)
    years = sorted((y for y in by_year if y), reverse=True) + ([None] if None in by_year else [])
    sections = []
    for y in years:
        items = by_year[y]
        label = str(y) if y else "Year not specified"
        sections.append(
            f'<section class="sec"><h2>{label} <span class="venue">{len(items)}</span></h2>'
            f'<ul class="plain">{"".join(entry_html(e) for e in items)}</ul></section>'
        )
    block = f"{START}{''.join(sections)}{END}"

    page = PAGE.read_text(encoding="utf8")
    if START in page and END in page:
        page = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda m: block, page, flags=re.S)
    else:  # first run: replace the existing sections, then keep the markers for next time
        first = page.index('<section class="sec">')
        last = page.index("<script>", first)
        page = page[:first] + block + page[last:]
    PAGE.write_text(page, encoding="utf8")
    print(f"Wrote {len(entries)} publications in {len(years)} year groups to {PAGE.name}")


if __name__ == "__main__":
    build()
