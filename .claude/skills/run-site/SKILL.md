---
name: run-site
description: Serve the static ALIA site locally, screenshot pages in headless Chrome, check console errors and links, and find the PR preview. Use to see a change working.
---

# Run and check the site

The repo root is the site. There is no build step.

## Serve
Start the server in the background. Use port 8800.

    python3 -m http.server 8800 --bind 127.0.0.1

Check it: `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8800/` should print 200.
Stop it: `pkill -f "http.server 8800"`.
The deploy workflow builds the search index (Pagefind). Locally, search needs
`npx --yes pagefind@1.5.2 --site .` first. Do not commit the result.

## Look at a page
Screenshot, with console messages:

    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new \
      --disable-gpu --hide-scrollbars --window-size=1280,2400 --virtual-time-budget=8000 \
      --enable-logging=stderr --v=0 --screenshot=/tmp/page.png http://127.0.0.1:8800/PATH/

Use the scratchpad folder instead of /tmp. Read the PNG to see it. Console lines
contain `CONSOLE`. Ignore `JQMIGRATE`, `gstatic`, `WebGPU` and the search autofocus note.
Sliders and animations differ between runs, so two screenshots are never identical.
Use `--window-size=420,2400` to see the mobile layout (the footer text is hidden on desktop).

## Check links
    python3 -I .github/scripts/check_links.py .

It exits 1 on any missing target that is not in `.github/scripts/known_broken.txt`.
The hook runs it after each HTML or CSS edit.

## Compare with the PR preview and production
- Preview: `https://aliassisi.github.io/pr-preview/pr-N/` (built by the PR workflow).
  It copies only uploads the PR changed. Other media loads from production.
- Production: `https://aliassisi.github.io/`. Deploy runs on push to `main`.
- `gh pr checks N` shows the preview run.
- Check media by URL: `curl -sI URL | head -1`.
