# ALIA Assisi website

A static copy of the WordPress site at aliassisi.it (Elementor, Vamtam theme).
It is served by GitHub Pages at https://aliassisi.github.io/. Italian pages are at the
root. English pages are under `en/`. There is no backend.

## Layout
- Pages: `<slug>/index.html`, for example `method/index.html`, `en/home/index.html`.
- Files: `assets/plugins`, `assets/themes`, `assets/uploads`, `assets/core`
  (they were `wp-content/*` and `wp-includes`).
- `pagefind/`: search index. Deploy rebuilds it. Do not edit it.
- `.github/scripts/`: the build and check scripts (`cleanup.py`, `postprocess.py`, `prune_plugins.py`, `check_links.py`, `runtime_check.py`). `.github/crawl/`: the URL lists.

## How changes ship
1. Branch, edit, open a PR.
2. The PR gets a preview at `https://aliassisi.github.io/pr-preview/pr-N/`.
3. Merge to `main`. The "Deploy production" workflow publishes to `gh-pages`.
`.claude/` and `CLAUDE.md` are not published.

## Two ways to edit (for now)
- **Re-crawl:** content changes happen in WordPress. Run
  `bash .github/scripts/crawl.sh`. It crawls, runs `cleanup.py` then
  `postprocess.py`, and replaces the site files. The raw crawl lives outside the repo,
  in `../aliassisi-crawl`.
- **Edit HTML directly:** fine for a quick fix. But a re-crawl wipes it.
  If the fix should last, also add a rule to `.github/scripts/postprocess.py`.
  Prefer the rule. Run it as `python3 -I .github/scripts/postprocess.py SITE_DIR`
  on a fresh `cleanup.py` output, never twice on the same folder.

## Check your work
- `python3 -I .github/scripts/check_links.py .` finds missing link targets.
  Known misses are in `.github/scripts/known_broken.txt`. A hook runs it after edits.
- Run the site and look at it: use the `run-site` skill. Do not call a change done
  until you have looked at the page.

## Course pages
- The main content of the course pages (every course in `data/ali.json`:
  Standard, intensive, exam prep, religious students, thematic) comes from `data/ali.json` (one block per course, its `"pagine"` list the files) and
  `.github/templates/corso-contenuto.html`. Header, menu, footer and the page's
  top section (title over the background video) stay as they are; only the line
  under the title comes from the course's `"hero"`. Do not replace that section.
  Run `python3 -I .github/scripts/build_corsi.py .` after editing.
- Optional blocks: `"libro"` (a course book section) and `"temi"` (a list of themes,
  each with its own enrolment link if it has `"voce_modulo"`).
- English pages use `corso-contenuto-en.html`. Each course's `"en"` block in
  `data/ali.json` holds the English texts and pages.
- Styles: `.github/templates/ali-course.css`, copied to `assets/ali/`, limited to
  `.ali-course`. Its reset block undoes theme rules on tables, `dt`, `small`, links.

## Gotchas
- A path shows up in three forms: plain `assets/uploads/x`, JSON `\/assets\/uploads\/x`,
  and inside `&quot;` data attributes. Change all three.
- Keep the WordPress body classes. Elementor CSS selects on them.
- The contact and newsletter forms post nowhere yet. Do not rely on them.
- `alia.evonove.webfactional.com` must never appear. `postprocess.py` fails if it does.
- Links to old aliassisi.it pages and files still exist. They work only while WordPress is online.
- `build_preview.py` rewrites paths for previews. If you change how media is linked,
  test a PR preview, not only the local server.

## Writing
Short, plain sentences in commits and PR text. Say what is not checked.
