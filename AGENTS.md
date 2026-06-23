# dzweb

## Site workflow

- Edit source files under `site/`; do not edit generated files under `sitegen/`.
- Regenerate the site after every source change with `python3 hpp/hpp.py --in-dir theme/site --in-dir site`.
- Serve the generated output with `python3 -m http.server --bind 127.0.0.1 --directory sitegen` when local review is needed.
- Visually inspect affected pages after regeneration at desktop and mobile widths before handoff.
- When taking webpage screenshots, use `scripts/screenshot-codex.sh` and save files under `.codex-screenshots/`.

## JavaScript-free requirement

- This site must render and function without JavaScript.
- Do not introduce JavaScript, JavaScript dependencies, client-side frameworks, inline event handlers, or runtime-loaded assets that require JavaScript.
- Preserve the same visual result in a JavaScript-disabled browser.
