# Intelligent Digital Systems Lab website

Static website for the Intelligent Digital Systems Lab (iDSL) at Imperial College London. It is plain HTML, CSS and local image assets, so there is nothing to install. A few small Python scripts in `tools/` (standard library only) keep the publication list and search metadata up to date.

## Preview locally

```sh
python3 -m http.server 8000
```

Then open <http://localhost:8000>. Stop the server with `Ctrl+C`.

## Pages

- `index.html` — Home
- `research.html` — Research themes
- `funded-research.html` — Funded projects
- `research-projects.html` — Projects by research area
- `fpgaconvnet.html`, `fpgaconvnet-visualisation.html` — fpgaConvNet toolflow page and interactive visualiser (data in `fpgaconvnet/`)
- `people.html` — Group members and alumni
- `director.html` — Meet the Director
- `github.html` — Research code and repositories
- `publications.html` — Publications (generated, see below)
- `videos.html` — Video highlights
- `join.html` — Opportunities, application guidance and contact details
- `contact.html` — redirect to `join.html#contact` (old address kept so links keep working)
- `404.html` — Page not found

## Publications

The list on `publications.html` is generated from `data/publications.json`. Do not edit the list in the HTML by hand.

- **Add or correct a paper:** edit `data/publications.json` (title, authors, venue, year, links), then run `python3 tools/build_publications.py`.
- **Find new papers automatically:** `python3 tools/update_publications.py` looks up the director's papers in OpenAlex, adds any that are missing and rebuilds the page. Use `--dry-run` to only list them.
- **Never add a paper:** put its title on its own line in `data/excluded_titles.txt`.
- **Weekly automation:** `.github/workflows/update-site.yml` runs every Monday, adds new papers and opens a pull request. Review and merge it to publish. In the repository settings, turn on *Actions → General → Allow GitHub Actions to create and approve pull requests*. Optionally add a free OpenAlex API key as the secret `OPENALEX_API_KEY` for higher rate limits.

## Search and sharing metadata

`python3 tools/seo.py` adds the description, favicon, share-card and canonical tags to every page and regenerates `sitemap.xml`, `robots.txt` and `404.html`. The site address is `base_url` in `tools/config.json`; change it there if the site is published somewhere else, then re-run the script. Page descriptions are in the `DESCRIPTIONS` table at the top of `tools/seo.py`; add a line there when you add a page.

## Page views

The site can count visits with [GoatCounter](https://www.goatcounter.com) (free for non-commercial use, no cookies, no personal data, so no consent banner). Sign up, choose a site code (it gives you `CODE.goatcounter.com`), put it in `tools/config.json` as `"goatcounter_code"`, then run `python3 tools/seo.py` and push. Leave it empty to switch counting off.

## Checking links

`python3 tools/check_links.py` tests every external link and groups the results as OK, blocked (bot protection or a login wall, not necessarily broken), unreachable and broken. The weekly workflow runs it too and shows the summary in the Actions run.

## Publishing on GitHub Pages

Push the repository, then in *Settings → Pages* choose *Deploy from a branch*, branch `main`, folder `/ (root)`. The empty `.nojekyll` file tells GitHub to serve the files as they are.

The site will be served at <https://ccb98.github.io/idsl_website/> (set as `base_url` in `tools/config.json`). Because this is a project site under a sub-path, search engines only read a `robots.txt` placed at the root of `ccb98.github.io`; the one here is harmless, and the sitemap can be submitted directly in Google Search Console instead.
