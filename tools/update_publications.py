#!/usr/bin/env python3
"""Find new papers by the lab director in OpenAlex and add them to data/publications.json.

New papers are appended with their DOI link so they appear on the site the next time
publications.html is rebuilt. Review them (a pull request does this when the weekly
GitHub Action runs). To permanently skip a paper, add its title to data/excluded_titles.txt.

Usage:
    python3 tools/update_publications.py            # add new papers, rebuild the page
    python3 tools/update_publications.py --dry-run  # only list what would be added

Optional environment variables:
    OPENALEX_API_KEY   a free OpenAlex API key (higher rate limits)
    OPENALEX_MAILTO    an email address to identify the script to OpenAlex (polite pool)
"""
import argparse
import difflib
import html
import json
import os
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build_publications  # noqa: E402

DATA = ROOT / "data" / "publications.json"
EXCLUDED = ROOT / "data" / "excluded_titles.txt"
CFG = json.loads((ROOT / "tools" / "config.json").read_text(encoding="utf8"))

SKIP_TYPES = {"paratext", "dataset", "editorial", "dissertation", "conference-abstract", "peer-review", "erratum"}
SKIP_TITLE = re.compile(r"(?i)^(session details|proceedings of|introduction to|guest editorial|arc 20\d\d$)")


def norm(t):
    return re.sub(r"[^a-z0-9]", "", html.unescape(t or "").lower())


def is_duplicate(n, pool):
    for h in pool:
        if n == h:
            return True
        if len(n) > 20 and len(h) > 20 and (n[:30] == h[:30] or n in h or h in n):
            return True
        if difflib.SequenceMatcher(None, n, h).ratio() > 0.85:
            return True
    return False


def fetch(url):
    # curl keeps this dependency-free and uses the system certificate store
    out = subprocess.run(["curl", "-s", "-m", "60", url], capture_output=True, text=True).stdout
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {}


def openalex_works():
    author = CFG["openalex_author_id"]
    key, mailto = os.environ.get("OPENALEX_API_KEY"), os.environ.get("OPENALEX_MAILTO")
    works, page = [], 1
    while True:
        params = {
            "filter": f"author.id:{author}",
            "per-page": "100",
            "page": str(page),
            "select": "title,publication_year,type,primary_location,authorships,doi",
        }
        if key:
            params["api_key"] = key
        if mailto:
            params["mailto"] = mailto
        data = fetch("https://api.openalex.org/works?" + urllib.parse.urlencode(params))
        if "results" not in data:
            sys.exit(f"OpenAlex request failed: {str(data)[:200]}")
        works += data["results"]
        if len(data["results"]) < 100:
            return works
        page += 1


def to_entry(w):
    title = html.unescape(w["title"]).strip()
    source = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
    if source.startswith("arXiv"):
        source = "arXiv preprint"
    year = w.get("publication_year")
    venue = f"{source}, {year}".strip(", ") if year else source
    authors = ", ".join(a["author"]["display_name"] for a in w["authorships"])
    links = [{"label": "DOI", "url": w["doi"]}] if w.get("doi") else []
    return {"title": title, "authors": authors, "venue": venue, "year": year, "links": links}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    entries = json.loads(DATA.read_text(encoding="utf8"))
    excluded = [norm(l) for l in EXCLUDED.read_text(encoding="utf8").splitlines() if l.strip() and not l.startswith("#")] if EXCLUDED.exists() else []
    pool = [norm(e["title"]) for e in entries] + excluded

    added = []
    # prefer published versions over preprints when both exist
    for w in sorted(openalex_works(), key=lambda w: (w.get("type") == "preprint", -(w.get("publication_year") or 0))):
        title = html.unescape(w.get("title") or "").strip()
        if not title or w.get("type") in SKIP_TYPES or not title.isascii() or len(title) < 8 or SKIP_TITLE.match(title):
            continue
        n = norm(title)
        if is_duplicate(n, pool):
            continue
        pool.append(n)
        added.append(to_entry(w))

    if not added:
        print("No new publications found.")
        return
    print(f"{len(added)} new publication(s):")
    for e in added:
        print(f"  {e['year']}  {e['title'][:90]}  [{e['venue'][:40]}]")
    if args.dry_run:
        return
    DATA.write_text(json.dumps(entries + added, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
    build_publications.build()


if __name__ == "__main__":
    main()
