#!/usr/bin/env python3
"""Build the course configurator pages from data/alia.json and data/configuratore.json.

Usage:
  python3 -I .github/scripts/build_configuratore.py SITE_DIR

The configurator is configuratore/index.html (Italian) and
en/configuratore/index.html (English). Each page keeps its crawled WordPress
page; only the HTML widget with the configurator is replaced by:
  - a link to assets/alia/configuratore.css (source: .github/templates/configuratore.css)
  - <div id="cfg-wrap">, filled by assets/alia/configuratore.js
    (source: .github/templates/configuratore.js)
  - the data, as JSON in <script id="cfg-dati">.
Courses, prices, start dates and closures come from alia.json. Accommodation,
extra services, activities and payment methods come from configuratore.json.

A course page opens the configurator with ?corso=<id> (the course id in
alia.json, or "privati", "online", "calendimaggio"). The configurator then
shows only that course. &tema=N picks a theme, &formula=N a row of the
private or online lessons price table.

Safe to run again on a page it already changed.
"""
import hashlib
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(HERE, "..", "templates")
INIZIO, FINE = "<!-- configuratore -->", "<!-- /configuratore -->"
PAGINE = {"it": "configuratore", "en": "en/configuratore"}
ICONE = {
    "standard": "ti-book", "intensivo": "ti-books", "super_intensivo": "ti-bolt",
    "esame_intensivo": "ti-certificate", "esame_super": "ti-rosette",
    "religiosi_22": "ti-building-church", "religiosi_26": "ti-building-church",
    "tematico_22": "ti-palette", "tematico_26": "ti-photo",
    "privati": "ti-user", "online": "ti-device-laptop", "calendimaggio": "ti-flag",
}
# Links of the enrolment form to the conditions the student accepts.
LINK = {
    "it": {"termini": "../termini-e-condizioni/index.html", "privacy": "../privacy-policy/index.html"},
    "en": {"termini": "../terms-and-conditions/index.html", "privacy": "../privacy-policy/index.html"},
}


def testo(v, lingua):
    """A text that is either one string or {"it": ..., "en": ...}."""
    return v if isinstance(v, str) else v[lingua]


def in_lingua(blocco, lingua):
    """A course block with its "en" fields merged in for English."""
    return {**blocco, **blocco["en"]} if lingua != "it" and "en" in blocco else blocco


def corsi(ali, lingua):
    out = []
    for c in ali["corsi"]:
        t = in_lingua(c, lingua)
        out.append({
            "id": c["id"], "tipo": "settimane", "icona": ICONE[c["id"]],
            "nome": t["nome"], "livelli": t["livelli"], "ore": c["ore"],
            "gruppo": sum(c["mattina"]), "individuali": sum(c["pomeriggio"]),
            "tariffe": ali["tariffe"][c["tariffa"]],
            "temi": [v["titolo"] for v in t.get("temi", {}).get("voci", [])],
        })
    for chiave in ("privati", "online"):
        c = ali[chiave]
        t = in_lingua(c, lingua)
        formule = c["formule"]
        if lingua != "it":
            formule = [{**f, **e} for f, e in zip(formule, t["formule"])]
        out.append({
            "id": chiave, "tipo": "lezioni", "icona": ICONE[chiave], "nome": t["nome"],
            "dal": c.get("dal"), "al": c.get("al"),
            "in_sede": chiave == "privati",
            "formule": [{"nome": f["nome"], "nota": f["nota"], "studenti": f.get("studenti", 1),
                         "prezzi": {int(n): p for n, p in f["prezzi"].items()}} for f in formule],
        })
    c = ali["calendimaggio"]
    out.append({
        "id": "calendimaggio", "tipo": "pacchetto", "icona": ICONE["calendimaggio"],
        "nome": in_lingua(c, lingua)["nome"], "dal": c["dal"], "al": c["al"], "prezzo": c["prezzo"],
    })
    return out


def dati(ali, cfg, lingua):
    return {
        "lingua": lingua,
        "email": cfg["email"],
        # The address of the Google Apps Script that receives enrolments. Empty: email only.
        "invio": cfg.get("invio", ""),
        "link": LINK[lingua],
        "corsi": corsi(ali, lingua),
        "date_inizio": sorted(ali["date_inizio"]),
        "chiusure": [{"dal": c["dal"], "al": c["al"], "nome": c[lingua]} for c in ali["chiusure"]],
        "alloggi": [{
            "id": a["id"], "icona": a["icona"], "prezzi": a.get("prezzi"), **a[lingua],
            "camere": [{"id": r["id"], "prezzi": r["prezzi"], **r[lingua]} for r in a.get("camere", [])],
        } for a in cfg["alloggi"]],
        "extra": [{"id": e["id"], "icona": e["icona"], "prezzo": e["prezzo"], "nome": e[lingua]}
                  for e in cfg["extra"]],
        "attivita_settimanali": [testo(a, lingua) for a in cfg["attivita_settimanali"]],
        "attivita": [{"nome": a[lingua], "date": a["date"]} for a in cfg["attivita"]],
        "pagamenti": [{"id": p["id"], "nome": p[lingua]} for p in cfg["pagamenti"]],
    }


def blocco(d, css, js):
    j = json.dumps(d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return (f"{INIZIO}\n"
            '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.10.0/tabler-icons.min.css">\n'
            f'<link rel="stylesheet" href="{css}">\n'
            '<div id="cfg-wrap"></div>\n'
            f'<script id="cfg-dati" type="application/json">{j}</script>\n'
            f'<script src="{js}"></script>\n'
            f"{FINE}")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    site = sys.argv[1]
    with open(os.path.join(site, "data", "alia.json"), encoding="utf-8") as f:
        ali = json.load(f)
    with open(os.path.join(site, "data", "configuratore.json"), encoding="utf-8") as f:
        cfg = json.load(f)

    out = os.path.join(site, "assets", "alia")
    os.makedirs(out, exist_ok=True)
    versione = {}
    for nome in ("configuratore.css", "configuratore.js"):
        shutil.copyfile(os.path.join(TEMPLATES, nome), os.path.join(out, nome))
        # ?v= changes with the file, so browsers do not keep an old copy.
        with open(os.path.join(out, nome), "rb") as f:
            versione[nome] = hashlib.sha256(f.read()).hexdigest()[:8]

    for lingua, p in PAGINE.items():
        dest = os.path.join(site, p, "index.html")
        with open(dest, encoding="utf-8") as f:
            s = f.read()
        rel = os.path.relpath(out, os.path.dirname(dest)).replace(os.sep, "/")
        nuovo = blocco(dati(ali, cfg, lingua),
                       f"{rel}/configuratore.css?v={versione['configuratore.css']}",
                       f"{rel}/configuratore.js?v={versione['configuratore.js']}")
        if INIZIO in s:
            s = re.sub(re.escape(INIZIO) + r".*?" + re.escape(FINE), lambda m: nuovo, s, count=1, flags=re.S)
        else:
            # First run: the crawled widget, from the icons stylesheet to the end of its script.
            m = re.search(r'<link rel="stylesheet" href="https://cdn\.jsdelivr\.net/npm/@tabler/[^"]*">'
                          r'.*?<div id="cfg-wrap">.*?\}\)\(\);\s*</script>', s, re.S)
            if not m:
                sys.exit(f"{dest}: configurator widget not found.")
            s = s[:m.start()] + nuovo + s[m.end():]
        with open(dest, "w", encoding="utf-8", newline="\n") as f:
            f.write(s)
        print(f"wrote {p}/index.html ({lingua})")


if __name__ == "__main__":
    main()
