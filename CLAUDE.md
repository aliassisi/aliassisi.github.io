# ALIA Assisi website

A static site, first copied from the old WordPress site (Elementor, Vamtam theme).
It is served by GitHub Pages at https://aliassisi.it/. Italian pages are at the
root. English pages are under `en/`. There is no backend.

## Layout
- Pages: `<slug>/index.html`, for example `method/index.html`, `en/home/index.html`.
- Files: `assets/plugins`, `assets/themes`, `assets/uploads`, `assets/core`
  (they were `wp-content/*` and `wp-includes`).
- `pagefind/`: search index. Deploy rebuilds it. Do not edit it.
- `.github/scripts/`: the build and check scripts (`build_*.py`, `legal_pages.py`, `faq_jsonld.py`, `check_links.py`, `runtime_check.py`).

## How changes ship
1. Branch, edit, open a PR.
2. The PR gets a preview at `https://aliassisi.it/pr-preview/pr-N/`.
3. Merge to `main`. The "Deploy production" workflow publishes to `gh-pages`.
`.claude/` and `CLAUDE.md` are not published.

## How to edit
The HTML in this repo is the source. The old WordPress site is gone, so there is no re-crawl.
Edit the page directly. For pages built from data (see below), edit `data/*.json`
and run the build script.

## Check your work
- `python3 -I .github/scripts/check_links.py .` finds missing link targets.
  Known misses are in `.github/scripts/known_broken.txt`. A hook runs it after edits.
- Run the site and look at it: use the `run-site` skill. Do not call a change done
  until you have looked at the page.

## Course pages
- The main content of the course pages (every course in `data/alia.json`:
  Standard, intensive, exam prep, religious students, thematic) comes from `data/alia.json` (one block per course, its `"pagine"` list the files) and
  `.github/templates/corso-contenuto.html`. Header, menu, footer and the page's
  top section (title over the background video) stay as they are; only the line
  under the title comes from the course's `"hero"`. Do not replace that section.
  Run `python3 -I .github/scripts/build_corsi.py .` after editing.
- Optional blocks: `"libro"` (a course book section) and `"temi"` (a list of themes,
  each with its own enrolment link if it has `"voce_modulo"`).
- "Altri corsi" (three boxes at the end of each course page) comes from
  `data/related-courses.json`: per course a title, url, two-line subtitle and three
  suggestion ids. `build_corsi.py` and `.github/scripts/build_related.py` fill the
  part between `<!-- related:start -->` and `<!-- related:end -->`. Never suggest
  `italiancookingfood`; the script refuses it.
- English pages use `corso-contenuto-en.html`. Each course's `"en"` block in
  `data/alia.json` holds the English texts and pages.
- Enrolment: every "Iscriviti" button opens the configurator with the course chosen
  (`configuratore/index.html?corso=<id>`, `&tema=N`, `&formula=N`). The configurator
  is built by `python3 -I .github/scripts/build_configuratore.py .` from `data/alia.json`
  and `data/configuratore.json` (accommodation, extras, activities, payment methods),
  with `.github/templates/configuratore.js` and `.css`. The form sends the enrolment
  to a Google Apps Script (`.github/apps-script/`, set up as in its `ISTRUZIONI.md`):
  its URL is `"invio"` in `data/configuratore.json`. Empty, or if sending fails, the
  form falls back to an email the student sends (mailto).
- Styles: `.github/templates/alia-course.css`, copied to `assets/alia/`, limited to
  `.ali-course`. Its reset block undoes theme rules on tables, `dt`, `small`, links.

## Main menu
- The main menu (IT and EN, desktop, burger and sticky headers) comes from
  `data/menu.json`. Run `python3 -I .github/scripts/build_menu.py .` after editing.
  It keeps the language switcher.

## Events (Vivere ad Assisi)
- `vivere-ad-assisi/` and `en/life-in-assisi/` show "Cosa succede ad Assisi e dintorni"
  (`#eventi`). The events are in `data/eventi-assisi.json`, edited by hand: one entry per
  event with `inizio`, `fine`, `ora`, `titolo`, `luogo`, `descrizione_it`, `descrizione_en`,
  `link`, optional `immagine`, `nota_it`, `nota_en`. Set `aggiornato` to the day you edit.
- `assets/alia/eventi.js` shows the next 6 that have not ended, and "Mostra altri" adds 6 more at a time; past ones drop off by
  themselves. With none, the fixed list in `.github/snippets/vivere-ad-assisi-it.html` and
  `life-in-assisi-en.html` shows. The pages are built by `legal_pages.py`.

## Workshop dates
- The workshop dates on `attivita-facilities-e-laboratori/` and `en/school-activity/`
  (and the "Scegli le date" box) come from `data/laboratori.json`. Run
  `python3 -I .github/scripts/build_laboratori.py .` after editing. Past dates are
  left out at build time, and a small script on the page hides dates that pass later.

## Search engines (SEO)
- Deploy and preview run `.github/scripts/build_seo.py` on their copy of the site.
  It adds canonical, hreflang, meta description, Open Graph and (on the homes) the
  school's JSON-LD, and writes `sitemap.xml` and `robots.txt`. Nothing is committed.
- Titles and descriptions: `data/seo.json`, keyed by page folder (`""` is the IT home).
  Course pages without an entry use their `"hero"` from `data/alia.json`.
  New page: add it there. Duplicate page: add it to `"canonical"`.
- To see the result locally: copy the site to a temp folder and run the script on it.

## Gotchas
- Colours: ardesia `#3D5570` for titles, boxes, buttons and the logo. Long text is dark ardesia
  `#2D4058`, weight 300 (rule at the end of `assets/alia/footer.css`, plus each custom
  block's base rule). New text blocks should follow this.
- A path shows up in three forms: plain `assets/uploads/x`, JSON `\/assets\/uploads\/x`,
  and inside `&quot;` data attributes. Change all three.
- Keep the WordPress body classes. Elementor CSS selects on them.
- The contact and newsletter forms post nowhere yet. Do not rely on them.
- `build_preview.py` rewrites paths for previews. If you change how media is linked,
  test a PR preview, not only the local server.

## Writing
Short, plain sentences in commits and PR text. Say what is not checked.
