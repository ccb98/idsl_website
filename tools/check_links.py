#!/usr/bin/env python3
"""Check every external link on the site and print a short report.

Status groups:
  OK           the link answered normally
  BROKEN       404 / 410 (the page is gone)
  BLOCKED      403 / 401 / 429 / 999 / 202, usually bot protection or a login wall, so it cannot be
               verified automatically (it may be fine for a person)
  UNREACHABLE  no answer at all (host down, DNS failure, or blocked from this network)

Usage:  python3 tools/check_links.py [--fail-on-broken]
Writes a Markdown summary to $GITHUB_STEP_SUMMARY when run in GitHub Actions.
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = json.loads((ROOT / "tools" / "config.json").read_text(encoding="utf8"))["base_url"]


def links():
    found = defaultdict(set)
    for page in sorted(ROOT.glob("*.html")):
        for u in re.findall(r'href="(https?://[^"]+)"', page.read_text(encoding="utf8")):
            u = html.unescape(u)
            if not u.startswith(BASE):  # the site's own address is not published until it goes live
                found[u].add(page.name)
    return found


def status(url):
    def code(extra):
        out = subprocess.run(["curl", "-sL", "-m", "25", "-o", "/dev/null", "-w", "%{http_code}", *extra, url],
                             capture_output=True, text=True).stdout.strip()
        return out or "000"

    c = code(["-I"])
    if c not in ("200", "000"):  # some servers reject HEAD; retry with a one-byte GET (not for dead hosts)
        c = code(["-r", "0-0"])
    return c


def group(c):
    if c in ("200", "206", "301", "302"):
        return "OK"
    if c in ("404", "410"):
        return "BROKEN"
    if c in ("401", "403", "429", "999", "202", "405"):
        return "BLOCKED"
    if c == "000":
        return "UNREACHABLE"
    return "BLOCKED" if c.startswith("4") else "BROKEN"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fail-on-broken", action="store_true")
    args = ap.parse_args()

    found = links()
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = dict(zip(found, ex.map(status, found)))

    groups = defaultdict(list)
    for u, c in results.items():
        groups[group(c)].append((c, u))

    lines = [f"Checked {len(found)} external links: " + ", ".join(f"{len(groups[g])} {g.lower()}" for g in ("OK", "BLOCKED", "UNREACHABLE", "BROKEN"))]
    for g in ("BROKEN", "UNREACHABLE"):
        if groups[g]:
            lines.append(f"\n{g} ({len(groups[g])}):")
            hosts = defaultdict(int)
            for c, u in sorted(groups[g]):
                if g == "UNREACHABLE":
                    hosts[re.match(r"https?://([^/]+)", u).group(1)] += 1
                else:
                    lines.append(f"  {c}  {u}  (on {', '.join(sorted(found[u]))})")
            for h, n in hosts.items():
                lines.append(f"  {n} links on {h}")
    report = "\n".join(lines)
    print(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        Path(summary).write_text("```\n" + report + "\n```\n", encoding="utf8")
    if args.fail_on_broken and groups["BROKEN"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
