# Intelligent Digital Systems Lab website

Static website for the Intelligent Digital Systems Lab (iDSL) at Imperial College London. It is built with plain HTML, CSS and local image assets, so no package installation or build step is required.

## Preview locally

From the repository root, run:

```sh
python3 -m http.server 8000
```

Then open <http://localhost:8000> in a browser. Stop the server with `Ctrl+C`.

## Pages

- `index.html` — Home
- `research.html` — Research themes
- `research-projects.html` — Projects by research area
- `funded-research.html` — Funded projects
- `people.html` — Group members and alumni
- `director.html` — Meet the Director
- `publications.html` — Publications
- `github.html` — Research code and repositories
- `videos.html` — Video highlights
- `join.html` — Opportunities and application guidance
- `contact.html` — Contact details

## Publish with GitHub Pages

For the short organization URL `https://icidsl.github.io/`, the site files need to be at the root of the `icidsl.github.io` repository in the `ICIdsl` organization.

In that repository, open **Settings → Pages** and choose **Deploy from a branch**, then select the `main` branch and the `/(root)` folder. The root `index.html` is the site entry point. GitHub Pages will publish the static files without a separate build step.

## Updating content

Edit the relevant HTML page and commit the change to the publishing branch. Keep image paths relative to the repository root (for example, `images/people/christos-bouganis.webp`). Project photos and figures are stored under `images/projects/`.
