# AIdeator Landing

Static multi-route marketing site for AIdeator.

## Run

- Open `index.html` directly for quick visual checks.
- For route testing (`/docs`, `/pricing`, `/compare`, etc.) serve the folder with a static server.

## Validate SEO

- `npm run seo:validate`
- `npm run seo:validate:strict`

## Key files

- `index.html`: primary conversion page
- `styles.css`: token-aligned visual system
- `site.config.json`: identity, CTAs, and per-route SEO metadata
- `config-loader.js`: metadata + JSON-LD helpers
- `shared-layout.js`: shared header/footer mount
- `forms.js`: waitlist/contact form submission
- `scripts/validate-seo.mjs`: metadata + sitemap validator