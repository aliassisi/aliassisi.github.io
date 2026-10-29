#!/usr/bin/env python3
"""Fill the "Altri corsi" boxes of the course pages from data/related-courses.json.

Usage:
  python3 -I .github/scripts/build_related.py SITE_DIR

Each course in "corsi" has, per language ("it", "en"), a title, a url, a
two-line subtitle and the pages that show the boxes ("pagine", default: the
url). "suggerimenti" lists the ids of its three boxes, in order. A course
without "suggerimenti" is only a box other pages link to.

Only the text between <!-- related:start --> and <!-- related:end --> changes.
build_corsi.py writes the markers (they are in the course templates) and
fills them with the same code, so the two scripts agree.

The data is checked first: three boxes per course, known ids, no page that
suggests itself, no link to italiancookingfood, every linked page present.
Safe to run again.
"""
import html
import json
import os
import re
import sys

INIZIO, FINE = "<!-- related:start -->", "<!-- related:end -->"
ESCLUSI = ("italiancookingfood",)
N_BOX = 3


def esc(s):
    return html.escape(s, quote=True)


def leggi(site):
    with open(os.path.join(site, "data", "related-courses.json"), encoding="utf-8") as f:
        return json.load(f)["corsi"]


def pagine(voce):
    return voce.get("pagine", [voce["url"]])


def controlla(site, corsi):
    """Stop with a message if the data would give a wrong or dead box."""
    errori = []
    for id_, c in corsi.items():
        for lingua in ("it", "en"):
            v = c[lingua]
            if any(x in v["url"] for x in ESCLUSI):
                errori.append(f"{id_}: {v['url']} is excluded")
            if not os.path.isfile(os.path.join(site, v["url"], "index.html")):
                errori.append(f"{id_}: {v['url']}/index.html does not exist")
        if "suggerimenti" not in c:
            continue
        s = c["suggerimenti"]
        if len(s) != N_BOX or len(set(s)) != N_BOX:
            errori.append(f"{id_}: needs {N_BOX} different suggestions, has {s}")
        for o in s:
            if o not in corsi:
                errori.append(f"{id_}: unknown suggestion {o}")
            elif o == id_ or any(corsi[o][l]["url"] in pagine(c[l]) for l in ("it", "en")):
                errori.append(f"{id_}: suggests itself ({o})")
    if errori:
        sys.exit("related-courses.json:\n  " + "\n  ".join(errori))


def lingua_di(pagina):
    return "en" if pagina.startswith("en/") else "it"


def voci(corsi, pagina):
    """The <li> boxes for one page, one link each. Title and subtitle are
    separate elements, with a space between them for readers and search."""
    lingua = lingua_di(pagina)
    trovati = [c for c in corsi.values() if "suggerimenti" in c and pagina in pagine(c[lingua])]
    if len(trovati) != 1:
        sys.exit(f"related-courses.json: {pagina} is in {len(trovati)} courses, needs 1")
    righe = []
    for o in trovati[0]["suggerimenti"]:
        v = corsi[o][lingua]
        righe.append(
            f'        <li><a href="https://aliassisi.github.io/{v["url"]}/index.html">'
            f'<b>{esc(v["titolo"])}</b> <small>{"<br>".join(esc(x) for x in v["sottotitolo"])}</small></a></li>')
    return "\n".join(righe)


def blocco(corsi, pagina):
    """The markers and the boxes, as the templates hold them."""
    return f"{INIZIO}\n{voci(corsi, pagina)}\n{FINE}"


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    site = sys.argv[1]
    corsi = leggi(site)
    controlla(site, corsi)
    for c in corsi.values():
        if "suggerimenti" not in c:
            continue
        for lingua in ("it", "en"):
            for p in pagine(c[lingua]):
                dest = os.path.join(site, p, "index.html")
                with open(dest, encoding="utf-8") as f:
                    s = f.read()
                if s.count(INIZIO) != 1 or s.count(FINE) != 1:
                    sys.exit(f"{p}/index.html: needs one {INIZIO} and one {FINE}. Run build_corsi.py first.")
                nuovo = re.sub(re.escape(INIZIO) + r".*?" + re.escape(FINE),
                               lambda m: blocco(corsi, p), s, flags=re.S)
                if nuovo != s:
                    with open(dest, "w", encoding="utf-8", newline="\n") as f:
                        f.write(nuovo)
                print(f"{'wrote' if nuovo != s else 'same '} {p}/index.html ({lingua})")


if __name__ == "__main__":
    main()
