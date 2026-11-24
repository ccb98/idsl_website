#!/usr/bin/env python3
"""Add search/share metadata to every page and generate sitemap.xml, robots.txt and 404.html.

The site address comes from tools/config.json ("base_url"). If you publish at a different
address, edit that value and run:  python3 tools/seo.py

The script is safe to re-run: it replaces its own block (between <!-- seo:start --> and
<!-- seo:end -->) in each page.
"""
import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "tools" / "config.json").read_text(encoding="utf8"))
BASE = CFG["base_url"].rstrip("/") + "/"
SITE = CFG["site_name"]
IMAGE = BASE + CFG["share_image"]

DESCRIPTIONS = {
    "index.html": "The Intelligent Digital Systems Lab (iDSL) at Imperial College London designs high-performance, energy-efficient digital systems for machine learning and computer vision.",
    "research.html": "iDSL research areas: machine learning, computer vision, and robotics and UAVs, with algorithms and hardware designed together.",
    "funded-research.html": "Funded projects at iDSL: the Wellcome Optical Oscilloscope, the APRIL AI Hub, HAMLET and AI-ISP.",
    "research-projects.html": "Research projects at iDSL in machine learning, computer vision and robotics, including the fpgaConvNet toolflow.",
    "fpgaconvnet.html": "fpgaConvNet is an open-source toolflow from iDSL that maps CNN models onto FPGAs, with benchmark results and publications.",
    "fpgaconvnet-visualisation.html": "Interactive visualisation of the fpgaConvNet optimiser mapping LeNet onto a ZedBoard FPGA, one design step at a time.",
    "people.html": "The people of the Intelligent Digital Systems Lab at Imperial College London: faculty, researchers, PhD students and alumni.",
    "director.html": "Prof. Christos Bouganis, Director of the Intelligent Digital Systems Lab at Imperial College London.",
    "github.html": "Open-source toolflows and research code from iDSL on GitHub (ICIdsl).",
    "publications.html": "Publications from iDSL grouped by year, with links to papers, code and slides.",
    "videos.html": "Demo videos, talks and papers from iDSL's work on UAVs, SLAM and FPGA acceleration.",
    "join.html": "Join iDSL and contact the lab: PhD opportunities, what we look for, scholarship expectations, address and email.",
}

START, END = "<!-- seo:start -->", "<!-- seo:end -->"
esc = lambda t: html.escape(t, quote=True)

ORG_JSONLD = {
    "@context": "https://schema.org",
    "@type": "ResearchOrganization",
    "name": SITE,
    "url": BASE,
    "logo": BASE + "favicon.svg",
    "parentOrganization": {"@type": "CollegeOrUniversity", "name": "Imperial College London"},
    "address": {
        "@type": "PostalAddress",
        "streetAddress": "South Kensington Campus",
        "addressLocality": "London",
        "postalCode": "SW7 2AZ",
        "addressCountry": "GB",
    },
}


def block(page, title, desc):
    url = BASE if page == "index.html" else BASE + page
    lines = [
        START,
        f'<meta name="description" content="{esc(desc)}">',
        f'<link rel="canonical" href="{esc(url)}">',
        '<link rel="icon" type="image/svg+xml" href="favicon.svg">',
        '<meta name="theme-color" content="#1b4fd6">',
        f'<meta property="og:site_name" content="{esc(SITE)}">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(desc)}">',
        f'<meta property="og:url" content="{esc(url)}">',
        f'<meta property="og:image" content="{esc(IMAGE)}">',
        f'<meta property="og:image:alt" content="{esc(SITE)}, Imperial College London">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{esc(title)}">',
        f'<meta name="twitter:description" content="{esc(desc)}">',
        f'<meta name="twitter:image" content="{esc(IMAGE)}">',
    ]
    if page == "index.html":
        lines.append('<script type="application/ld+json">' + json.dumps(ORG_JSONLD) + "</script>")
    lines.append(END)
    return "".join(lines)


def process(page):
    path = ROOT / page
    s = path.read_text(encoding="utf8")
    m = re.search(r"<title>(.*?)</title>", s, flags=re.S)
    title = html.unescape(m.group(1)).strip()
    s = re.sub(re.escape(START) + r".*?" + re.escape(END), "", s, flags=re.S)
    s = re.sub(r"(<title>.*?</title>)", lambda mm: mm.group(1) + block(page, title, DESCRIPTIONS[page]), s, count=1, flags=re.S)
    path.write_text(s, encoding="utf8")


def sitemap():
    rows = []
    for page in DESCRIPTIONS:
        loc = BASE if page == "index.html" else BASE + page
        mod = date.fromtimestamp((ROOT / page).stat().st_mtime).isoformat()
        rows.append(f"  <url><loc>{esc(loc)}</loc><lastmod>{mod}</lastmod></url>")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(rows) + "\n</urlset>\n"
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n", encoding="utf8")


def not_found():
    s = (ROOT / "join.html").read_text(encoding="utf8")
    s = re.sub(re.escape(START) + r".*?" + re.escape(END), "", s, flags=re.S)
    s = re.sub(r"<title>.*?</title>", f"<title>Page not found | {esc(SITE)}</title>", s, count=1, flags=re.S)
    s = s.replace("<head>", f'<head><base href="{esc(BASE)}">', 1)
    s = s.replace("</title>", '</title><meta name="robots" content="noindex">', 1)
    s = s.replace(" class=on", "").replace(' class="on"', "")
    body = ('<section class="pagehead"><div class="wrap"><h1>Page not found</h1>'
            "<p>The page you were looking for does not exist or has moved.</p></div></section>"
            '<main><div class="wrap"><div class="cta" style="margin-top:0"><h2>Let us help you find it</h2>'
            '<p>Try the home page, or browse our research, people and publications.</p>'
            '<a class="btn" href="index.html">Go to the home page</a> <a class="btn alt" href="publications.html">Publications</a></div></div></main>')
    s = re.sub(r"</header>.*?<footer>", lambda m: "</header>" + body + "<footer>", s, count=1, flags=re.S)
    (ROOT / "404.html").write_text(s, encoding="utf8")


if __name__ == "__main__":
    for page in DESCRIPTIONS:
        process(page)
    sitemap()
    not_found()
    print(f"SEO tags added to {len(DESCRIPTIONS)} pages; wrote sitemap.xml, robots.txt, 404.html (base {BASE})")
