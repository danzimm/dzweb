# dzweb

## Site workflow

- Edit source files under `site/`; do not edit generated files under `sitegen/`.
- Start hpp's watcher before making site changes with `python3 hpp/hpp.py --in-dir theme/site --in-dir site --listen --kqueue --port 8000`; it regenerates `sitegen/` and serves the site at `http://127.0.0.1:8000`.
- Keep the watcher running while editing and after handoff. Do not stop the watcher unless the user explicitly asks you to stop it.
- Do not manually rerun hpp after every source change, and do not start a separate `python3 -m http.server` for this site.
- If hpp dependencies are missing in the active Python environment, install them from `hpp/requirements.txt` before starting the watcher.
- After each source change, wait for the watcher to finish processing the affected files before reviewing or taking screenshots. Confirm the generated `sitegen/` file reflects the edit, or wait for the watcher output showing the relevant file was written.
- Visually inspect affected pages through the watcher server at desktop and mobile widths before handoff.
- When taking webpage screenshots, use `scripts/screenshot-codex.sh` and save files under `.codex-screenshots/`.

## JavaScript-free requirement

- This site must render and function without JavaScript.
- Do not introduce JavaScript, JavaScript dependencies, client-side frameworks, inline event handlers, or runtime-loaded assets that require JavaScript.
- Preserve the same visual result in a JavaScript-disabled browser.
