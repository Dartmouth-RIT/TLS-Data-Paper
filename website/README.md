# QTLS — Dataset Website

A single-page, self-contained portal for the QTLS coherent-control dataset. The
content is generated **directly from the experiment READMEs** in
`../src/dataset_creation_scripts/*/README.md` — each experiment card opens its
own documentation in a reader panel.

## Files

| File | Purpose |
|---|---|
| `build_site.py` | Reads every experiment `README.md` and generates `index.html` |
| `index.html` | The built site — one self-contained HTML document (inline CSS/JS, no external assets) |

`index.html` is a complete standalone document (doctype, `<meta charset>`,
responsive viewport, favicon), so it hosts directly on any static host.

## Rebuild

Re-run whenever an experiment README changes, so the site stays in sync:

```bash
cd website
python build_site.py
```

Requires only the Python standard library (no third-party packages).

## View locally

`index.html` is fully self-contained — open it directly in a browser, or serve
the folder:

```bash
cd website
python -m http.server 8000        # then open http://localhost:8000
```

## Deploy to GitHub Pages (automated)

Deployment is handled by GitHub Actions — the workflow at
`.github/workflows/deploy-pages.yml` rebuilds `index.html` from the READMEs and
publishes it on every push to `main` that touches `website/` or any experiment
README (and can be run manually from the **Actions** tab).

**One-time setup** (in the GitHub repo, not in code):

1. Push this branch and merge it into `main`.
2. Go to **Settings → Pages**.
3. Under **Build and deployment → Source**, choose **GitHub Actions**.

That's it. The next push to `main` builds and deploys automatically; the live URL
appears in the workflow run and under Settings → Pages, typically:

```
https://<owner>.github.io/TLS-Data-Paper/
```

The site uses only inline assets and in-page anchor links, so it works unchanged
at that project sub-path — no base-URL configuration needed.

> **Fallback (no Actions):** you can instead set Source to **Deploy from a
> branch** and point it at a `/docs` folder — copy `index.html` there and commit
> it. The Actions route is preferred because it rebuilds from the READMEs
> automatically, so the site can never drift from the docs.

## Design

- **Dark quantum theme** — deep navy/black ground, quantum-cyan (`#00D9FF`) and
  electric-purple (`#7657FF`) accents, glassmorphism cards, an animated particle
  field, and Apple-style scroll reveals.
- **Sections:** hero, overview, the full ordered list of experiments (each opens
  its README), and access / reproducibility.
- Responsive (desktop / tablet / mobile) and honors `prefers-reduced-motion`.

## Notes

- The site embeds the README **text**; it does not bundle the large `.pkl`/`.csv`
  datasets. Those are rebuilt from the dataset-creation scripts on demand.
- Fonts are referenced by name (Space Grotesk / Inter / JetBrains Mono) with a
  system fallback. To pin them exactly, self-host the font files and add
  `@font-face` rules.

Uses code and simulation methods from the Fitzpatrick Lab, Dartmouth College.
